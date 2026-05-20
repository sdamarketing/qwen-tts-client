# Публикация на npmjs.com из GitHub Actions

## Ошибки в CI

| Код | Причина |
|-----|---------|
| `403` + bypass 2fa | `NPM_TOKEN` — не Automation / без bypass 2FA |
| `EOTP` | В workflow передан `NPM_TOKEN` типа **Publish** — npm требует OTP, в CI его нет |
| `404` Not Found | Пакет/scope ещё **не существует** на npmjs, или Trusted Publisher привязан **не к тому** npm-аккаунту, который владеет `@sdamarketing` |

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

### Первый publish (если CI даёт `404`)

Scoped-пакет `@sdamarketing/qwen-tts-client` должен появиться на npmjs **один раз** под аккаунтом, который владеет scope (сейчас maintainer: **alekhm**).

1. Локально (логин `npm whoami` = этот аккаунт):

```bash
npm run publish:npm -- --otp=123456
```

2. На npmjs: **Package settings → Trusted publishing** — тот же аккаунт, repo `sdamarketing/qwen-tts-client`, workflow `publish.yml`.

3. Следующие версии — только CI; **подними `version`** в `package.json` (повтор `1.0.0` даст conflict, не 404).

Проверка:

```bash
npm view @sdamarketing/qwen-tts-client version
```

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

## Повторная публикация той же версии

```text
403 You cannot publish over the previously published versions: 1.0.0
```

Версии на npm **неизменяемы**. Подними patch в `package.json` (`npm version patch`) и снова `npm run publish:all`.

## Локально с 2FA

```bash
npm run publish:npm -- --otp=123456
```
