# OpenClaw Profile (Remote API)

Этот проект использует один production-профиль клиента:

- `remote-api` — OpenClaw не запускает локальный TTS и получает финальный `OGG/Opus` от удаленного сервера.

## Файлы

- `remote-api/openclaw.tts.json5` — фрагмент для `messages.tts`;
- `remote-api/openclaw-node.env.example` — пример переменных окружения gateway.

## Принцип

- `tts-local-cli` активируется как primary provider;
- `qwen_tts_proxy_opus.sh` запускает `qwen_tts_runtime.py`;
- runtime делает HTTPS вызов в удаленный `/tts` и поддерживает retry/timeout/diagnostics;
- локальная генерация отсутствует, локальная конверсия не выполняется.
