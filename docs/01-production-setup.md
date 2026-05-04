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

- создаёт `~/.openclaw/qwen_tts_client.env`;
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

Если `/tts status` показывает лимит 1500, а синтез падает с **`max 600`**, в `~/.openclaw/openclaw.json` в `messages.tts` всё ещё стоит `maxTextLength: 600`. Поставь **не меньше 1500** (или перезапусти актуальный `install_qwen_tts_client.sh` — он поднимет лимит минимум до 1500, не урезая более высокий, если ты его задавал).

## Ручной профиль (без установщика)

Если нужно применить настройки вручную:

- взять фрагмент `deploy/openclaw/profiles/remote-api/openclaw.tts.json5`;
- использовать пример env `deploy/openclaw/profiles/remote-api/openclaw-node.env.example`.

## Архитектура

`OpenClaw` -> `tts-local-cli` -> `qwen_tts_proxy_opus.sh` -> `qwen_tts_runtime.py` -> `https://<server>/tts` -> `OGG/Opus | WAV`

OpenClaw для `outputFormat: opus` передаёт путь вида `…/speech.opus` и **считает формат по расширению**: если записать туда WAV, озвучка падает с `provider_error`. `qwen_tts_runtime.py` проверяет сигнатуру `OpusHead` в Ogg и при необходимости **транскодирует в Opus через `ffmpeg`**. На gateway/host должен быть доступен `ffmpeg`, если сервер отдаёт не Opus-in-Ogg.

Если `tts-local-cli` стабильно падает с `provider_error`, а с ноутбука `curl` до `/tts` работает: у процесса gateway часто заданы `HTTP_PROXY`/`HTTPS_PROXY`. Рантайм по умолчанию **не** использует системный прокси для `CENTRAL_TTS_BASE_URL` (Tailscale и приватные URL так не ломаются). Если TTS доступен **только** через прокси — выставь `CENTRAL_TTS_USE_SYSTEM_PROXY=1` в `qwen_tts_client.env`.

Если в логах видно **`503` / `no tunnel here`** на URL вида `*.lhr.life` / `trycloudflare.com` — временный туннель к машине с TTS **умер**; подними туннель заново или переключи `CENTRAL_TTS_BASE_URL` на постоянный хост (например Tailscale `*.ts.net`), затем перезапусти gateway.

## Расширенный payload `/tts`

`qwen_tts_runtime.py` отправляет backward-compatible тело:

- обязательно: `text`
- опционально: `voice`, `model`, `persona`, `target`, `requestId`, `sessionHints`

Старый контракт (только `text`) продолжает работать.
