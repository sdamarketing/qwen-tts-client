# Публикация на npmjs.com из GitHub Actions

## Ошибки в CI

| Код | Причина |
|-----|---------|
| `403` + bypass 2fa | `NPM_TOKEN` — не Automation / без bypass 2FA |
| `EOTP` | В workflow передан `NPM_TOKEN` типа **Publish** — npm требует OTP, в CI его нет |

**Рекомендуемый способ:** [npm Trusted Publishers](https://docs.npmjs.com/trusted-publishers) (OIDC). Секрет `NPM_TOKEN` для publish **не нужен**.

## Trusted Publisher (рекомендуется)

Один раз на npmjs.com (под аккаунтом с правом publish `@sdamarketing/*`):

1. Открой настройки пакета `@sdamarketing/qwen-tts-client` → **Publishing access** → **Trusted publishing**  
   (или org: https://www.npmjs.com/settings/sdamarketing/packages)
2. **Add GitHub Actions trusted publisher**
   - Repository: `sdamarketing/qwen-tts-client`
   - Workflow filename: `publish.yml`
   - Environment: пусто (если не используете GitHub Environment)
3. В GitHub **удали секрет `NPM_TOKEN`** (если есть) — иначе старый токен может мешать.
4. Re-run workflow **Publish package**.

Workflow уже настроен: `id-token: write`, `npm publish --provenance`, **без** `NODE_AUTH_TOKEN`.

Первый publish scoped-пакета иногда делают локально один раз:

```bash
npm run publish:npm -- --otp=123456
```

После появления пакета на npmjs — дальнейшие версии через CI + Trusted Publisher.

## Запасной вариант: NPM_TOKEN

Если Trusted Publisher не используете:

1. [Access Tokens](https://www.npmjs.com/settings/~/tokens) → Classic **Automation** (не Publish)  
   или Granular с **Bypass two-factor authentication for automation**
2. Секрет `NPM_TOKEN` в GitHub Actions
3. В workflow **временно** вернуть:

```yaml
env:
  NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

Не смешивайте Trusted Publisher и Publish-токен в одном job — будет `EOTP` или `403`.

## После смены версии

Если версия уже на registry — подними `version` в `package.json` перед повторным publish.

## Локально с 2FA

```bash
npm run publish:npm -- --otp=123456
```
