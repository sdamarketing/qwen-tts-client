# Publish / Публикация

Package: `@sdamarketing/qwen-tts-client`

## Registries / Реестры

| Registry | Script | CI |
|----------|--------|-----|
| npmjs.com | `npm run publish:npm` | job `publish-npmjs`, OIDC Trusted Publisher |
| GitHub Packages | `npm run publish:github` | job `publish-github`, `GITHUB_TOKEN` |

```bash
npm run publish:all
```

**RU:** Версии immutable — перед повтором: `npm version patch`.

## npmjs CI

- Workflow: `.github/workflows/publish.yml`
- **EN:** Trusted Publisher on npm (repo `sdamarketing/qwen-tts-client`, file `publish.yml`). No `NPM_TOKEN` in workflow.
- **RU:** Trusted Publisher на npm; секрет `NPM_TOKEN` в workflow не используется.

| Error | Fix |
|-------|-----|
| `EOTP` | Remove `NPM_TOKEN` secret or use Automation token only in local publish |
| `404` | First publish locally: `npm run publish:npm -- --otp=…`, then configure Trusted Publisher |
| `403` same version | Bump `version` in `package.json` |

## GitHub Packages

```bash
export NODE_AUTH_TOKEN="$GITHUB_TOKEN"
npm run publish:github
```

Install: `.npmrc.github.example` or `--registry=https://npm.pkg.github.com`.
