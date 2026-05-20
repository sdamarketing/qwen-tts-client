# NPM_TOKEN для GitHub Actions

Ошибка в CI:

```text
403 Forbidden - Two-factor authentication or granular access token with bypass 2fa enabled is required
```

Значит секрет `NPM_TOKEN` в репозитории **не подходит** для публикации без OTP (типично: Classic **Publish** token или granular token **без** bypass 2FA).

## Что сделать на npmjs.com

1. Войти под аккаунтом, у которого есть право публиковать `@sdamarketing/*` (владелец org **sdamarketing** на npm или привязанный пользователь).
2. Открыть [Access Tokens](https://www.npmjs.com/settings/~/tokens).

### Вариант A — Classic Automation (проще)

- **Generate New Token → Classic Token**
- Type: **Automation** (не Publish, не Read-only)
- Скопировать токен один раз → в GitHub: **Settings → Secrets → Actions → `NPM_TOKEN`**

Automation-токены предназначены для CI и не требуют `--otp` при publish, если на аккаунте включена 2FA.

### Вариант B — Granular Access Token

- **Generate New Token → Granular Access Token**
- Permissions: **Read and write** для нужных packages / org `sdamarketing`
- Обязательно включить: **Bypass two-factor authentication for automation**
- Сохранить как `NPM_TOKEN` в GitHub Secrets

## Проверка org scope

Пакет называется `@sdamarketing/qwen-tts-client`. На npm должна существовать org (или scope) **sdamarketing**, и токен должен быть создан пользователем с правом publish в этот scope.

Связка GitHub org ↔ npm: [npm organization settings](https://www.npmjs.com/settings/sdamarketing/packages) (если используете npm Teams).

## После обновления секрета

1. Обновить `NPM_TOKEN` в `https://github.com/sdamarketing/qwen-tts-client/settings/secrets/actions`
2. Re-run workflow **Publish package**
3. Если версия `1.0.0` уже опубликована — поднять `version` в `package.json` перед повтором

## Локальная публикация с 2FA

```bash
npm run publish:npm -- --otp=123456
```
