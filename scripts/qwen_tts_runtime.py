#!/usr/bin/env python3
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path


def _normalize_text(value: str) -> str:
    return value.encode("utf-8", errors="replace").decode("utf-8", errors="replace")


def _load_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    raw = path.read_bytes()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        # Keep runtime resilient on hosts where env was edited with mixed encodings.
        content = raw.decode("utf-8", errors="replace")
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        cleaned = value.strip().strip("'").strip('"')
        data[key.strip()] = _normalize_text(cleaned)
    return data


def _env(name: str, default: str = "") -> str:
    return _normalize_text(os.environ.get(name, default).strip())


def _positive_int(value: str, default: int) -> int:
    try:
        num = int(value)
        return num if num > 0 else default
    except ValueError:
        return default


def _truthy_env(name: str) -> bool:
    return _env(name, "").lower() in ("1", "true", "yes", "on")


def _build_url_opener() -> urllib.request.OpenerDirector:
    """
    Gateway processes often inherit HTTP_PROXY/HTTPS_PROXY. urllib honors them by default,
    which breaks private / Tailscale TTS URLs. Disable system proxies unless explicitly opted in.
    """
    if _truthy_env("CENTRAL_TTS_USE_SYSTEM_PROXY"):
        return urllib.request.build_opener()
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _write_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=str(path.parent), prefix=".qwen-tts-", delete=False) as temp_file:
        temp_file.write(payload)
        temp_name = temp_file.name
    os.replace(temp_name, str(path))


def _content_type_base(headers) -> str:
    raw = (headers.get("Content-Type") or "").strip()
    return raw.split(";", 1)[0].strip().lower()


def _is_opus_in_ogg(content: bytes) -> bool:
    if len(content) < 4 or content[:4] != b"OggS":
        return False
    scan = min(len(content), 131072)
    return b"OpusHead" in content[:scan]


def _is_riff_wave(content: bytes) -> bool:
    return len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WAVE"


def _looks_json_error(content: bytes) -> bool:
    stripped = content.lstrip()
    return bool(stripped) and stripped[:1] == b"{"


def _http_audio_acceptable(content_type: str, content: bytes) -> bool:
    if content_type.startswith("application/json") or content_type.startswith("text/html"):
        return False
    if content_type.startswith("audio/"):
        return bool(content) and not _looks_json_error(content)
    if content_type in ("application/ogg", "application/octet-stream", "binary/octet-stream", ""):
        return bool(content) and not _looks_json_error(content)
    return False


def _ffmpeg_to_opus_file(payload: bytes, out_path: Path, timeout_sec: int) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError(
            "TTS response is not Opus-in-Ogg; install `ffmpeg` to transcode (e.g. apt install ffmpeg)."
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_name(f".qwen-tts-ffmpeg-{uuid.uuid4().hex[:10]}.opus")
    try:
        proc = subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                "pipe:0",
                "-c:a",
                "libopus",
                "-b:a",
                "64k",
                str(tmp),
            ],
            input=payload,
            capture_output=True,
            timeout=max(timeout_sec, 5),
        )
        if proc.returncode != 0:
            err = (proc.stderr or b"").decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"ffmpeg transcode failed (exit {proc.returncode}): {err[:800]}")
        if not tmp.exists() or tmp.stat().st_size == 0:
            raise RuntimeError("ffmpeg produced empty output")
        os.replace(str(tmp), str(out_path))
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def _ensure_output_audio(content: bytes, content_type: str, out_path: Path, transcode_timeout: int) -> None:
    """
    OpenClaw tts-local-cli picks format from the OUTPUT FILE EXTENSION only.
    For voice-note it expects real Opus-in-Ogg at *.opus; writing WAV bytes there causes provider_error.
    """
    suffix = out_path.suffix.lower()
    want_opus_file = suffix in (".opus", ".ogg")

    if not want_opus_file:
        _write_atomic(out_path, content)
        return

    if _is_opus_in_ogg(content):
        _write_atomic(out_path, content)
        return

    if _looks_json_error(content) and not _is_riff_wave(content):
        preview = content[:800].decode("utf-8", errors="replace")
        raise RuntimeError(f"server returned JSON instead of audio: {preview}")

    if _is_riff_wave(content) or content_type in ("audio/wav", "audio/x-wav", "audio/wave"):
        _ffmpeg_to_opus_file(content, out_path, transcode_timeout)
        return

    if content_type in ("audio/mpeg", "audio/mp3") or (
        len(content) >= 2 and content[0:1] == b"\xff" and (content[1] & 0xE0) == 0xE0
    ):
        _ffmpeg_to_opus_file(content, out_path, transcode_timeout)
        return

    if content[:4] == b"OggS":
        _ffmpeg_to_opus_file(content, out_path, transcode_timeout)
        return

    if content_type.startswith("audio/") or content_type in (
        "application/ogg",
        "application/octet-stream",
        "binary/octet-stream",
    ):
        _ffmpeg_to_opus_file(content, out_path, transcode_timeout)
        return

    raise RuntimeError(f"cannot map TTS payload to Opus file (content-type={content_type!r}, {len(content)} bytes)")


def _build_payload(text: str, request_id: str) -> dict[str, object]:
    session_hints: dict[str, str] = {
        "source": "qwen-tts-client",
        "runtime": "local-cli",
        "host": socket.gethostname(),
    }
    extra_hints = _env("CENTRAL_TTS_SESSION_HINTS_JSON")
    if extra_hints:
        try:
            parsed = json.loads(extra_hints)
            if isinstance(parsed, dict):
                for key, value in parsed.items():
                    session_hints[_normalize_text(str(key))] = _normalize_text(str(value))
        except json.JSONDecodeError:
            pass

    payload: dict[str, object] = {
        "text": _normalize_text(text),
        "requestId": _normalize_text(request_id),
        "target": _env("CENTRAL_TTS_TARGET", "voice-note"),
        "sessionHints": session_hints,
    }
    if _env("CENTRAL_TTS_VOICE"):
        payload["voice"] = _env("CENTRAL_TTS_VOICE")
    if _env("CENTRAL_TTS_MODEL"):
        payload["model"] = _env("CENTRAL_TTS_MODEL")
    if _env("CENTRAL_TTS_PERSONA"):
        payload["persona"] = _env("CENTRAL_TTS_PERSONA")
    return payload


def main() -> int:
    text = sys.argv[1] if len(sys.argv) > 1 else ""
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    default_env = Path.home() / ".openclaw" / "qwen_tts_client.env"
    env_path = Path(_env("QWEN_TTS_CLIENT_ENV", str(default_env)))
    if not text or out_path is None:
        print("usage: qwen_tts_runtime.py <text> <output_path>", file=sys.stderr)
        return 2

    for key, value in _load_env_file(env_path).items():
        os.environ.setdefault(key, value)

    base_url = _env("CENTRAL_TTS_BASE_URL")
    api_key = _env("CENTRAL_TTS_API_KEY")
    if not base_url or not api_key:
        print(f"CENTRAL_TTS_BASE_URL or CENTRAL_TTS_API_KEY missing in {env_path}", file=sys.stderr)
        return 1

    timeout_sec = max(_positive_int(_env("CENTRAL_TTS_TIMEOUT_SEC", "120"), 120), 5)
    max_retries = _positive_int(_env("CENTRAL_TTS_RETRIES", "2"), 2)
    retry_backoff_ms = _positive_int(_env("CENTRAL_TTS_RETRY_BACKOFF_MS", "350"), 350)
    request_id = f"qtts-{uuid.uuid4().hex[:12]}"
    payload = _build_payload(text=text, request_id=request_id)
    request_url = f"{base_url.rstrip('/')}/tts"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    url_opener = _build_url_opener()

    last_error = "unknown error"
    for attempt in range(0, max_retries + 1):
        started_at = time.perf_counter()
        request = urllib.request.Request(
            request_url,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": api_key,
                "X-Request-Id": request_id,
            },
            data=body,
        )
        try:
            with url_opener.open(request, timeout=timeout_sec) as response:
                content = response.read()
                content_type = _content_type_base(response.headers)
                if not content:
                    raise RuntimeError("server returned empty audio payload")
                if not _http_audio_acceptable(content_type, content):
                    raise RuntimeError(f"unexpected content-type: {content_type or '(missing)'}")
                transcode_timeout = max(
                    _positive_int(_env("CENTRAL_TTS_FFMPEG_TIMEOUT_SEC", str(timeout_sec)), timeout_sec),
                    5,
                )
                _ensure_output_audio(content, content_type, out_path, transcode_timeout)
                elapsed_ms = (time.perf_counter() - started_at) * 1000
                out_size = out_path.stat().st_size if out_path.exists() else 0
                print(
                    f"[qwen-tts-runtime] request_id={request_id} attempt={attempt + 1} status=ok "
                    f"latency_ms={elapsed_ms:.2f} bytes_in={len(content)} bytes_out={out_size} "
                    f"content_type={content_type or '(missing)'}",
                    file=sys.stderr,
                )
                return 0
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="ignore")
            last_error = f"http {exc.code}: {error_body}"
        except Exception as exc:  # pragma: no cover
            last_error = str(exc)

        elapsed_ms = (time.perf_counter() - started_at) * 1000
        print(
            f"[qwen-tts-runtime] request_id={request_id} attempt={attempt + 1} status=retry "
            f"latency_ms={elapsed_ms:.2f} error={last_error}",
            file=sys.stderr,
        )
        if attempt < max_retries:
            time.sleep((retry_backoff_ms / 1000.0) * (attempt + 1))

    hint = ""
    if not _truthy_env("CENTRAL_TTS_USE_SYSTEM_PROXY"):
        le = last_error.lower()
        if any(s in le for s in ("timed out", "connection refused", "unreachable", "name or service not known", "nodename", "tunnel", "proxy")):
            hint = " | hint: TTS uses direct TCP (no HTTP_PROXY); set CENTRAL_TTS_USE_SYSTEM_PROXY=1 if you need a proxy."
    print(f"[qwen-tts-runtime] request_id={request_id} status=failed error={last_error}{hint}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
