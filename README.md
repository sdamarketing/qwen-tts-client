# Qwen TTS Client

Production-клиент для OpenClaw `tts-local-cli`, который проксирует синтез на удаленный `Qwen TTS Server`.

Базовый путь:

- `OpenClaw (tts-local-cli)`
- `qwen_tts_proxy_opus.sh` (тонкий launcher)
- `qwen_tts_runtime.py` (валидация/retry/diagnostics)
- `Qwen TTS Server /tts`
- возврат `OGG/Opus` или `WAV` (по настройке сервера)

## Что делает проект

- интерактивно запрашивает endpoint и API key удаленного TTS;
- генерирует `~/.openclaw/qwen_tts_client.env` с retry/timeout/hints настройками;
- настраивает `~/.openclaw/openclaw.json` под `tts-local-cli` без удаления других providers;
- мигрирует legacy-ключи (`audioAsVoice`, `textLimit`) в `maxTextLength`;
- выполняет smoke-test и проверяет выходной аудиофайл.

## Быстрый запуск

```bash
cd products/qwen-tts-client
chmod +x ./scripts/install_qwen_tts_client.sh
./scripts/install_qwen_tts_client.sh
```

После установки проверь в чате OpenClaw:

- `/tts status`
- `/tts latest`
- `/tts chat on`
- `/tts persona off`

## Новые возможности OpenClaw 2026.4.25+

Клиент совместим с расширенным TTS workflow:

- chat-level override: `/tts chat on|off|default`;
- ручная озвучка последнего ответа: `/tts latest`;
- persona override: `/tts persona <id>|off`;
- per-agent/per-channel overlays через OpenClaw-конфиг (`agents.list[].tts`, `channels.<channel>.accounts.<id>.tts`).

## Структура

- `scripts/install_qwen_tts_client.sh` — интерактивный установщик;
- `scripts/qwen_tts_proxy_opus.sh` — shell launcher для Local CLI;
- `scripts/qwen_tts_runtime.py` — runtime транспорт в удаленный `/tts`;
- `deploy/openclaw/profiles/remote-api` — готовый профиль OpenClaw для remote TTS;
- `.env.example` — шаблон клиентских переменных;
- `docs/` — production runbook клиента.
