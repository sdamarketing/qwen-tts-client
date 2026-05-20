# Setup / Установка

## Prerequisites / Нужно

- **EN:** OpenClaw with existing `~/.openclaw/openclaw.json`
- **RU:** OpenClaw, файл `~/.openclaw/openclaw.json` уже создан
- Remote server with `POST /tts` and API key

## Install / Установка

```bash
qwen-tts-install
# or: ./scripts/install_qwen_tts_client.sh
```

**Installer does / Установщик:**

1. Creates `~/.openclaw/qwen_tts_client.env`
2. Copies `qwen_tts_proxy_opus.sh`, `qwen_tts_runtime.py` → `~/.openclaw/bin/`
3. Sets `messages.tts.provider` = `tts-local-cli` in `openclaw.json` (other providers kept)
4. Sets `maxTextLength` ≥ 1500; removes `audioAsVoice`, `textLimit` if present
5. Renames broken `settings/tts.json` overrides when needed
6. Restarts `openclaw-gateway` (systemd user or launchctl) if present
7. Smoke test → temp `*.ogg`

## Manual config / Вручную

- `deploy/openclaw/profiles/remote-api/openclaw.tts.json5` — merge into `openclaw.json`
- `deploy/openclaw/profiles/remote-api/openclaw-node.env.example` — gateway env sample

## Runtime / Рантайм

**EN:** `qwen_tts_runtime.py` — `urllib` POST to `{BASE_URL}/tts`, header `X-API-Key`, retries, no system proxy by default.

**RU:** POST на `/tts`, заголовок `X-API-Key`, retry; по умолчанию без `HTTP_PROXY`.

- **Opus:** if response is not Opus-in-Ogg and output path ends with `.opus` → **ffmpeg** transcode (ffmpeg must be in `PATH`)
- **Proxy:** `CENTRAL_TTS_USE_SYSTEM_PROXY=1` only if TTS is reachable via proxy
