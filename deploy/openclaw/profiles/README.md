# OpenClaw profiles

**EN:** Static config samples for manual setup (installer patches `openclaw.json` automatically).

**RU:** Примеры конфигурации для ручной настройки (установщик правит `openclaw.json` сам).

## `remote-api/`

| File | Content |
|------|---------|
| `openclaw.tts.json5` | `messages.tts` fragment: `tts-local-cli`, `outputFormat: opus` |
| `openclaw-node.env.example` | Gateway + `CENTRAL_TTS_*` env template |

Paths in json5: replace `~/.openclaw/bin/...` with your `OPENCLAW_HOME` if not default.
