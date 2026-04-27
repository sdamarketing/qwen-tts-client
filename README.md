# Qwen TTS Client

Тонкий production-клиент для OpenClaw, который не генерирует аудио локально.

Клиентский поток:

- OpenClaw (`tts-local-cli`)
- локальный proxy-скрипт
- удаленный `Qwen TTS Server` API (`/tts`)
- возврат финального `OGG/Opus`

## Что делает проект

- интерактивно запрашивает endpoint и API key удаленного TTS;
- генерирует `.env` клиента;
- настраивает `~/.openclaw/openclaw.json` под `tts-local-cli`;
- оставляет только один активный TTS provider;
- выполняет smoke-test и проверяет выходной `ogg`.

## Быстрый запуск

```bash
cd products/qwen-tts-client
chmod +x ./scripts/install_qwen_tts_client.sh
./scripts/install_qwen_tts_client.sh
```

После установки проверь в чате OpenClaw:

- `/tts status`
- `/tts provider tts-local-cli`

## Структура

- `scripts/install_qwen_tts_client.sh` — интерактивный установщик;
- `scripts/qwen_tts_proxy_opus.sh` — runtime bridge в удаленный `/tts`;
- `deploy/openclaw/profiles/remote-api` — готовый профиль OpenClaw для remote TTS;
- `.env.example` — шаблон клиентских переменных;
- `docs/` — production runbook клиента.
