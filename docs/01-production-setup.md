# 01. Production Setup

## Цель

Подключить OpenClaw-клиент к удаленному `Qwen TTS Server` без локальной генерации.

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
- устанавливает `qwen_tts_proxy_opus.sh` в `~/.openclaw/bin`;
- патчит `~/.openclaw/openclaw.json` на `tts-local-cli`;
- выполняет smoke-test.

## Проверка в OpenClaw

- `/tts status`
- `/tts provider tts-local-cli`
- отправить тестовое сообщение для озвучки

Если после обновления OpenClaw видишь ошибку `Unrecognized keys: "audioAsVoice", "textLimit"`, значит остались старые ключи в `messages.tts`. Удалить их и оставить `maxTextLength`.

## Ручной профиль (без установщика)

Если нужно применить настройки вручную:

- взять фрагмент `deploy/openclaw/profiles/remote-api/openclaw.tts.json5`;
- использовать пример env `deploy/openclaw/profiles/remote-api/openclaw-node.env.example`.

## Архитектура

`OpenClaw` -> `tts-local-cli` -> `qwen_tts_proxy_opus.sh` -> `https://<server>/tts` -> `OGG/Opus`
