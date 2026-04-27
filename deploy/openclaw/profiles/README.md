# OpenClaw Profile (Remote API)

Этот проект использует один production-профиль клиента:

- `remote-api` — OpenClaw не запускает локальный TTS и получает финальный `OGG/Opus` от удаленного сервера.

## Файлы

- `remote-api/openclaw.tts.json5` — фрагмент для `messages.tts`;
- `remote-api/openclaw-node.env.example` — пример переменных окружения gateway.

## Принцип

- активен только `tts-local-cli`;
- `qwen_tts_proxy_opus.sh` делает HTTPS вызов в удаленный `/tts`;
- локальная конверсия аудио отсутствует.
