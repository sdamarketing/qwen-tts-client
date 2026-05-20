# Qwen TTS Client

**EN:** OpenClaw `tts-local-cli` provider — HTTP proxy to a remote Qwen TTS Server (`/tts`), output OGG/Opus (ffmpeg transcode if needed).

**RU:** Провайдер OpenClaw `tts-local-cli` — HTTP-прокси на удалённый Qwen TTS Server (`/tts`), на выходе OGG/Opus (при необходимости — ffmpeg).

## Flow / Цепочка

```text
OpenClaw → tts-local-cli → qwen_tts_proxy_opus.sh → qwen_tts_runtime.py → POST /tts → *.opus
```

## Install / Установка

**npm (npmjs.com):**

```bash
npm install -g @sdamarketing/qwen-tts-client
qwen-tts-install
```

**npm (GitHub Packages):** see `.npmrc.github.example`, then the same commands with `--registry=https://npm.pkg.github.com`.

**git:**

```bash
git clone https://github.com/sdamarketing/qwen-tts-client.git
cd qwen-tts-client
./scripts/install_qwen_tts_client.sh
```

**EN:** `qwen-tts-install` writes `~/.openclaw/qwen_tts_client.env`, copies scripts to `~/.openclaw/bin/`, patches `~/.openclaw/openclaw.json` (`tts-local-cli`), runs a smoke test.

**RU:** `qwen-tts-install` создаёт env, копирует скрипты в `~/.openclaw/bin/`, правит `openclaw.json`, делает smoke-test.

## CLI (npm bin)

| Command | Role |
|---------|------|
| `qwen-tts-install` | `scripts/install_qwen_tts_client.sh` |
| `qwen-tts-proxy` | `scripts/qwen_tts_proxy_opus.sh` → `qwen_tts_runtime.py` |

```bash
qwen-tts-proxy "text" /tmp/out.opus
```

## Env / Переменные

File: `~/.openclaw/qwen_tts_client.env` (template: `.env.example`). Loaded via `QWEN_TTS_CLIENT_ENV`.

| Variable | Required | Default (in code) |
|----------|----------|-------------------|
| `CENTRAL_TTS_BASE_URL` | yes | — |
| `CENTRAL_TTS_API_KEY` | yes | — |
| `CENTRAL_TTS_TARGET` | no | `voice-note` |
| `CENTRAL_TTS_TIMEOUT_SEC` | no | `120` |
| `CENTRAL_TTS_RETRIES` | no | `2` |
| `CENTRAL_TTS_RETRY_BACKOFF_MS` | no | `350` |
| `CENTRAL_TTS_FFMPEG_TIMEOUT_SEC` | no | same as timeout |
| `CENTRAL_TTS_USE_SYSTEM_PROXY` | no | off (`1` = use `HTTP_PROXY`) |
| `CENTRAL_TTS_VOICE`, `MODEL`, `PERSONA` | no | — |
| `CENTRAL_TTS_SESSION_HINTS_JSON` | no | — |

**POST body:** `text` + optional `voice`, `model`, `persona`, `target`, `requestId`, `sessionHints`.

## Repo layout / Структура

| Path | Purpose |
|------|---------|
| `scripts/install_qwen_tts_client.sh` | Interactive installer |
| `scripts/qwen_tts_proxy_opus.sh` | OpenClaw entrypoint |
| `scripts/qwen_tts_runtime.py` | HTTP client, retry, Opus check, ffmpeg |
| `deploy/openclaw/profiles/remote-api/` | Manual `openclaw.json` + env samples |
| `docs/` | Setup and publish notes |

## Maintainers / Публикация

```bash
npm run publish:npm      # registry.npmjs.org (--otp if 2FA)
npm run publish:github   # NODE_AUTH_TOKEN=GITHUB_TOKEN, write:packages
npm run publish:all
```

CI: `.github/workflows/publish.yml` on Release (npmjs OIDC + GitHub Packages).
