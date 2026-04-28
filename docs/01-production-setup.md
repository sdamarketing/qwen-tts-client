# 01. Production Setup

## Цель

Подключить OpenClaw-клиент к удаленному `Qwen TTS Server` через `tts-local-cli`, без локальной генерации.

## Предпосылки

- установлен и хотя бы один раз запущен OpenClaw (должен существовать `~/.openclaw/openclaw.json`);
- есть рабочий endpoint сервера `/tts`;
- есть API key сервера.

## Установка

```bash
cd products/qwen-tts-client
chmod +x ./scripts/install_qwen_tts_client.sh
./scripts/install_qwen_tts_client.sh
```

Скрипт:

- создаёт `.env`;
- устанавливает `qwen_tts_proxy_opus.sh` и `qwen_tts_runtime.py` в `~/.openclaw/bin`;
- патчит `~/.openclaw/openclaw.json` на `tts-local-cli` без удаления остальных providers;
- чистит legacy-ключи `audioAsVoice` / `textLimit`;
- выполняет smoke-test.

## Проверка в OpenClaw

- `/tts status`
- `/tts latest`
- `/tts chat on`
- `/tts persona off`
- отправить тестовое сообщение для озвучки

Если после обновления OpenClaw видишь ошибку `Unrecognized keys: "audioAsVoice", "textLimit"`, значит остались старые ключи в `messages.tts`. Удалить их и оставить `maxTextLength`.

## Ручной профиль (без установщика)

Если нужно применить настройки вручную:

- взять фрагмент `deploy/openclaw/profiles/remote-api/openclaw.tts.json5`;
- использовать пример env `deploy/openclaw/profiles/remote-api/openclaw-node.env.example`.

## Архитектура

`OpenClaw` -> `tts-local-cli` -> `qwen_tts_proxy_opus.sh` -> `qwen_tts_runtime.py` -> `https://<server>/tts` -> `OGG/Opus | WAV`

## Расширенный payload `/tts`

`qwen_tts_runtime.py` отправляет backward-compatible тело:

- обязательно: `text`
- опционально: `voice`, `model`, `persona`, `target`, `requestId`, `sessionHints`

Старый контракт (только `text`) продолжает работать.
