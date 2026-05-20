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

### Установка из npm (npmjs.com)

После `npm run publish:all` пакет доступен на обоих реестрах. С npmjs.com ставится **без** `.npmrc`:

```bash
npm install -g @sdamarketing/qwen-tts-client
qwen-tts-install
```

### Установка из GitHub Packages

Скопируй `.npmrc.github.example` в `~/.npmrc` и задай `GITHUB_TOKEN` (`read:packages`), либо:

```bash
npm install -g @sdamarketing/qwen-tts-client --registry=https://npm.pkg.github.com
```

### Публикация в оба реестра (maintainers)

Один tarball, два реестра (имя и версия совпадают):

```bash
# npmjs.com — нужен OTP или NPM_TOKEN с publish
npm run publish:npm

# GitHub Packages — GITHUB_TOKEN с write:packages
export NODE_AUTH_TOKEN="$GITHUB_TOKEN"
npm run publish:github

# или оба подряд
npm run publish:all
```

На npmjs.com для scoped-пакета обязателен `--access public` (уже в скрипте `publish:npm`).

CI: при Release workflow `.github/workflows/publish.yml` публикует в npmjs и GitHub Packages **параллельно**.

Секрет **`NPM_TOKEN`**: Classic token типа **Automation** (или granular с **Bypass 2FA for automation**). Иначе CI получит `403` — см. [docs/02-npm-ci-token.md](docs/02-npm-ci-token.md).

Прокси для ручного smoke-test:

```bash
qwen-tts-proxy "Проверка TTS" /tmp/qwen-tts-smoke.ogg
```

### Установка из git

```bash
git clone https://github.com/sdamarketing/qwen-tts-client.git
cd qwen-tts-client
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
