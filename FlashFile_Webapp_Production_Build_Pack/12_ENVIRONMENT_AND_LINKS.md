# 12. Environment and link configuration

This file is a configuration specification. Replace examples with verified values for the deployment. Do not copy secrets into frontend configuration.

## 1. Public frontend environment template

Example `.env.example` for the frontend. These names can be adapted to the existing project, but values must remain public-only.

```dotenv
# Public product/site configuration
VITE_SITE_NAME=FlashFile
VITE_PUBLIC_SITE_URL=https://YOUR-REAL-PUBLIC-DOMAIN

# Required for the primary Telegram CTA. Use the real bot username.
VITE_TELEGRAM_BOT_USERNAME=YOUR_VERIFIED_BOT_USERNAME

# Optional verified public links. Leave blank until confirmed.
VITE_PUBLIC_REPO_URL=https://github.com/JishnuPG-tech/FiletoLink
VITE_PUBLIC_DOCS_URL=
VITE_PUBLIC_STATUS_URL=
VITE_PUBLIC_SUPPORT_URL=

# Do not enable until there is an actual current release artifact.
VITE_ENABLE_DOWNLOAD_CTA=false
VITE_PUBLIC_DOWNLOAD_URL=
VITE_PUBLIC_RELEASE_VERSION=
VITE_PUBLIC_RELEASE_DATE=
VITE_PUBLIC_RELEASE_SHA256=

# Add a status widget only after the endpoint and schema are verified.
VITE_ENABLE_STATUS_WIDGET=false
VITE_PUBLIC_STATUS_API_URL=

# Optional analytics must remain off unless approved and documented.
VITE_ENABLE_ANALYTICS=false
```

`VITE_*` values are included in the browser bundle. Never add `TELEGRAM_BOT_TOKEN`, API credentials, admin credentials or server secrets here.

## 2. Production validation rules

Production configuration should fail the build or the release pipeline when:
- `VITE_PUBLIC_SITE_URL` is missing or not HTTPS, except for an explicit local-development mode.
- `VITE_TELEGRAM_BOT_USERNAME` is missing or invalid.
- a production CTA points to a placeholder URL.
- download CTA is enabled without a verified HTTPS download URL and current release metadata.
- a status widget is enabled without a verified status endpoint.
- an external link has a non-approved scheme or unexpected host.

Do not make development impossible when public configuration is incomplete. Provide a clearly labeled local preview mode that does not masquerade as a production build.

## 3. Telegram deep-link behavior

Base form:

`https://t.me/<BOT_USERNAME>`

Optional start link:

`https://t.me/<BOT_USERNAME>?start=website_hero`

Use fixed, reviewed placement parameters such as:
- `website_header`
- `website_hero`
- `website_features`
- `website_footer`

Keep parameters short and non-sensitive. Telegram documents start parameters for bot deep links. Confirm exact current constraints in Telegram’s official docs at implementation time.

Do not add a second bot token or call the Telegram Bot API directly from browser code. The website needs only the public bot link.

## 4. Approved link registry

Centralize external URLs in one module/config registry. Suggested entries:

```ts
type SiteLinks = {
  telegramBotUrl: string;
  publicRepositoryUrl?: string;
  docsUrl?: string;
  statusUrl?: string;
  supportUrl?: string;
  downloadUrl?: string;
  privacyUrl?: string;
  termsUrl?: string;
};
```

Required behavior:
- Validate all configured URLs before use.
- Use only `https:` for external public routes unless an explicitly verified platform handler is required.
- Do not accept a visitor-supplied destination URL.
- Omit optional links when absent instead of rendering a broken button.
- Validate the production host against the approved registry in tests.

## 5. Download CTA guard

Only enable when all applicable release facts exist:
- official artifact URL,
- platform label such as Android,
- version number,
- release date if displayed,
- integrity checksum/signature if provided by the release process,
- source for release notes.

If any required item is absent, hide the download CTA and do not render a dead placeholder. Do not infer an APK from an app repository or from a mention in a discussion.

## 6. Status integration guard

Before enabling a live status widget, verify:
- exact public endpoint,
- HTTP method,
- success/error response schema,
- meanings of all status values,
- caching/freshness expectations,
- CORS if hosted separately,
- behavior when the endpoint times out.

If the endpoint is only intended for machine-readable clients, keep it as a plain text link or create a separate UI endpoint without changing the original JSON contract.

## 7. Build-time vs runtime configuration

Build-time values:
- public bot username,
- public site URL,
- public repo/docs/support links,
- public verified release URL,
- feature flags for optional public sections.

Runtime backend secrets:
- bot token,
- webhook secret,
- database connection string,
- admin token,
- file-serving signing keys,
- any private service credentials.

Never copy backend secrets into `window.__CONFIG__`, HTML template variables, client source maps or public JSON config.
