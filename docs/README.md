# Qwen TTS Client Docs

Документация по отдельному production-проекту `Qwen TTS Client`.

- [01. Production Setup](01-production-setup.md)

Клиент ориентирован на OpenClaw `2026.4.25+` и учитывает:

- `messages.tts.providers` как основную схему;
- новые команды `/tts latest`, `/tts chat`, `/tts persona`;
- compatibility с per-agent/per-channel overrides без агрессивной зачистки `openclaw.json`.
