#!/usr/bin/env python3
import json
import os
import socket
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


def _write_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=str(path.parent), prefix=".qwen-tts-", delete=False) as temp_file:
        temp_file.write(payload)
        temp_name = temp_file.name
    os.replace(temp_name, str(path))


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
            with urllib.request.urlopen(request, timeout=timeout_sec) as response:
                content = response.read()
                content_type = response.headers.get("Content-Type", "")
                if not content:
                    raise RuntimeError("server returned empty audio payload")
                if not content_type.startswith("audio/"):
                    raise RuntimeError(f"unexpected content-type: {content_type}")
                _write_atomic(out_path, content)
                elapsed_ms = (time.perf_counter() - started_at) * 1000
                print(
                    f"[qwen-tts-runtime] request_id={request_id} attempt={attempt + 1} status=ok "
                    f"latency_ms={elapsed_ms:.2f} bytes={len(content)} content_type={content_type}",
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

    print(f"[qwen-tts-runtime] request_id={request_id} status=failed error={last_error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
