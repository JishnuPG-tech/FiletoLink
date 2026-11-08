# 09. Security, deployment and operations

## 1. Security posture

This marketing website should not ask visitors to enter Telegram credentials, OTPs, file tokens or private bot data. The primary action should be a normal HTTPS Telegram deep link. Keep the static public site separate from privileged bot administration.

Use OWASP ASVS as a practical checklist reference for the application boundaries. The site is not automatically secure because it is static; configuration, links, third-party scripts, server routing, headers and deployment remain in scope.

## 2. Secrets and public configuration

Never put these in Vite client variables:
- Telegram bot token.
- Telegram API keys or secret webhook tokens.
- database credentials.
- signing secrets.
- admin passwords.
- private service API keys.
- any credentials copied from `.env`.

`VITE_*` values are public and bundled into the browser. Use a frontend variable only for data a visitor is allowed to see, such as the public bot username or public site URL.

Keep secrets in the existing backend’s environment or secret manager. Do not expose the entire process environment through a config endpoint.

## 3. Telegram URL security

- Public CTA uses `https://t.me/<configured_bot_username>`.
- Avoid visitor-controlled Telegram destination hosts.
- Deep-link placement keys are fixed in source and use safe character sets.
- Do not put internal IDs, file access tokens, usernames, emails or private references into the start parameter.
- Do not claim the user has started the bot; the web page only initiates navigation.
- Do not create an open redirect endpoint such as `/redirect?url=...` for marketing links.

## 4. Content Security Policy and headers

Review actual service behavior before tightening headers. At minimum, consider:
- Content Security Policy that allows only required scripts, styles, fonts, images, connection endpoints and WebGL resources.
- `X-Content-Type-Options: nosniff`.
- A suitable `Referrer-Policy`.
- Frame restrictions such as `frame-ancestors` according to actual embedding requirements.
- HSTS only after confirming HTTPS on all intended hosts and subdomains.
- A `Permissions-Policy` restricting features the site does not use.

Do not paste a rigid CSP that breaks inline styles, Vite hashed assets, WebGL or the current player. Prefer nonces/hashes or externalized code where practical and test in staging. Do not add `unsafe-eval` solely to silence a build error without investigating it.

## 5. External scripts and third parties

- Keep third-party scripts to the minimum necessary.
- Do not load an analytics or heatmap service by default.
- If a remote font provider is used, document that in the privacy review and consider local hosting.
- Do not load marketing widgets, trackers, chat widgets or video embeds without a real requirement.
- If the current template uses an external animation/CDN package, verify the version, source and license before reuse. Prefer lockfile-managed packages for the React build.

## 6. Docker and deployment integration

The exact Dockerfile must be adapted after repository inspection. The likely pattern is:

1. Frontend build stage using a supported Node image.
2. Install with the committed package lock.
3. Run type checks/tests and `vite build`.
4. Copy only the production frontend output into the existing backend runtime image.
5. Keep the production runtime’s existing Python/bot dependencies and command.
6. Mount static assets at a dedicated prefix.
7. Leave bot tokens and service secrets in runtime secret configuration, not in the image or frontend build.

Do not replace the whole existing Dockerfile without understanding its current purpose, entrypoint, healthcheck and architecture. If the platform builds frontend and backend separately, follow the platform’s supported build process and document it.

## 7. Route preservation

Before deployment, test and record:
- `GET /` with `Accept: text/html`.
- `GET /` with `Accept: application/json` or the established API client header.
- `HEAD /` if used by health probes or proxies.
- `/status` and any health route.
- `/watch` or player route.
- stream/range-request routes.
- webhook route and secret validation behavior.
- admin routes and their current authorization behavior.
- unknown public route returns an appropriate 404.

Never let the marketing SPA fallback intercept media range requests, webhook traffic, API paths or admin paths.

## 8. Static caching

- Hashed frontend bundles: long-lived immutable cache headers.
- HTML entry point: short cache or revalidation so deployments update correctly.
- Favicon/social preview: cache policy appropriate to the file naming/versioning.
- Status endpoint: only cache according to actual status freshness requirements.
- Stream/media responses: retain the current correct range and cache behavior. The marketing change must not silently override them.

## 9. Release procedure

1. Confirm all required public configuration is present.
2. Run clean install and frontend checks.
3. Run backend/unit and route regression tests.
4. Build the production frontend and container.
5. Scan the build output for secrets and placeholder URLs.
6. Deploy to staging.
7. Open the real deployed URL in desktop Chrome and Android.
8. Test Telegram CTA, deep-link parameter, FAQ, docs, status and download availability.
9. Check browser console, asset network requests and response codes.
10. Confirm status, watch/stream and webhook paths still function.
11. Run accessibility and performance checks.
12. Capture build ID/commit, test evidence and known issues.
13. Deploy production.
14. Recheck primary path and error handling.
15. Keep a rollback plan tied to the previous known-good build.

## 10. Observability

Use existing error monitoring/logging when available. Do not add a full monitoring vendor solely for the landing page unless it is useful and privacy reviewed.

Track:
- failed frontend asset requests,
- JavaScript exceptions,
- route errors,
- bot-link config missing,
- status widget failures if enabled,
- WebGL fallback frequency only if it can be recorded without unnecessary tracking.

No tracking identifier is needed for the site’s core functionality.

## 11. Privacy, terms and legal copy

The privacy page must reflect actual behavior: hosting logs, server logs, third-party requests, analytics, cookies/local storage, and any personally identifiable information collected by the service. Do not copy a generic policy that states “we collect no data” unless that is verified end-to-end.

The terms page must reflect real responsibility, supported use, prohibited use, service availability and contact information. It must be reviewed by the maintainer before publication. These documents are implementation requirements, not legal advice.

## 12. Rollback

- Keep the previous backend image/deployment reference.
- Ensure new frontend assets can be rolled back with the matching backend route configuration.
- Do not delete old static assets immediately if active HTML may still reference them.
- If frontend issues affect `/`, restore the last known-good landing response without changing bot/streaming APIs.
- Document how to switch the root route back to the stable template if necessary.
