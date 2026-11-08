# 06. Technical architecture and repository integration

## 1. Architecture objective

Deliver a maintainable marketing/product frontend inside the existing FiletoLink codebase without disrupting the current Python service, Telegram bot, file routes, player/watch behavior, status endpoint, webhook, admin or streaming endpoints.

The reviewed repository snapshot had a Three.js React component under `webapp/src/components/canvas/TransmissionCore.tsx` and a Python/Jinja landing template path, but did not contain a complete frontend build pipeline. Reinspect the live branch before implementation. Do not assume the snapshot is still current.

## 2. Recommended stack

- React + TypeScript.
- Vite as the frontend build tool.
- Three.js for the existing particle scene.
- Motion for React (`motion/react`) for DOM transitions, in-view reveals and scroll-linked values.
- CSS variables as the authoritative design-token layer.
- Tailwind CSS only as a utility layer if configured cleanly; do not bury design tokens inside ad hoc utility strings.
- shadcn/ui and Radix primitives selectively for accessible components such as accordion, dialog or mobile navigation. Use only what the design needs.
- Lucide React for functional icons.
- Vitest and React Testing Library for UI tests; Playwright for browser-level interaction tests, if the existing CI/environment supports them.
- Existing Python/FastAPI or Starlette routing and Jinja infrastructure remains responsible for current backend APIs and product endpoints unless repository inspection proves a different stack is now in place.

Pin versions through a package lock. Use currently supported stable releases at implementation time. Do not invent version numbers in documentation or install several overlapping animation libraries.

## 3. Repository discovery must happen first

Before edits, inspect:
- top-level folders and current branch/status,
- `webapp/` contents and `package.json` if present,
- `Thunder/server/stream_routes.py` or equivalent route file,
- template rendering utilities,
- current main template,
- `Dockerfile` and deployment config,
- Python requirements/lock files,
- tests and CI workflows,
- current paths for `/status`, `/watch`, `/stream`, webhooks, admin endpoints and static assets,
- current bot username or public bot URL configuration,
- existing service URL and status payload,
- current README and license.

Produce a concise inventory before implementation, then make a plan based on what really exists.

## 4. Frontend project layout

Recommended structure. Adapt to existing naming if the repository already has an equivalent structure.

```text
webapp/
  index.html
  package.json
  package-lock.json
  tsconfig.json
  vite.config.ts
  postcss.config.js                 # only if needed by the chosen CSS setup
  public/
    favicon.svg
    og-image.png                    # supplied/created and verified, not fake remote URL
    robots.txt                      # only if deployment requires a static copy
  src/
    main.tsx
    App.tsx
    router.tsx
    styles/
      tokens.css
      base.css
      motion.css
    content/
      site-config.ts
      features.ts
      faq.ts
    components/
      layout/
        SiteHeader.tsx
        SiteFooter.tsx
        MobileNav.tsx
      marketing/
        HeroSection.tsx
        WorkflowSection.tsx
        FeatureSection.tsx
        CompatibilitySection.tsx
        FaqSection.tsx
        FinalCtaSection.tsx
      canvas/
        TransmissionCore.tsx
        ParticleFallback.tsx
      ui/
        ButtonLink.tsx
        IconButton.tsx
        SectionHeading.tsx
        MotionPreferenceControl.tsx
    hooks/
      useMotionPreference.ts
      useScrollProgress.ts
      useActiveSection.ts
    lib/
      telegram-links.ts
      config-validation.ts
      metadata.ts
      reduced-motion.ts
    pages/
      HomePage.tsx
      DocsPage.tsx                    # only if docs are included
      PrivacyPage.tsx                 # based on real privacy content
      TermsPage.tsx                   # reviewed actual terms
    tests/
      telegram-links.test.ts
      reduced-motion.test.ts
      navigation.test.tsx
```

If the project uses file-based routes or existing organization, preserve it. The required capability and constraints matter more than the exact folder names.

## 5. Build and serve integration

The project already has a backend route that handles HTML for the root path in the reviewed snapshot. It also has API/status and streaming routes. Integrate the frontend using the route model that fits the present application.

Preferred integration if using the existing Python server:

1. Vite builds production assets into a known directory such as `webapp/dist/`.
2. Static hashed frontend assets are mounted under a dedicated prefix such as `/site-assets/` or the existing safe asset prefix.
3. The server’s public marketing routes return the built `index.html` for HTML requests.
4. Existing API, streaming, webhook, administrative and status routes stay registered with higher specificity and maintain their current behavior.
5. The frontend must not catch every unknown URL and return HTML for API clients or media requests.
6. Root content negotiation stays intentional: browsers requesting `text/html` receive the site; JSON/API clients retain the established JSON/status response.
7. Provide a health check to confirm the Python service remains healthy independently of frontend assets.

Do not blindly add a catch-all route. FastAPI/Starlette route order and specificity can change which handler receives `/status`, `/watch`, `/stream`, webhook or admin requests. Add a route regression test for each important pre-existing endpoint.

### Alternative deployment

A separate static-hosted frontend can be used if it has a stable public domain and all required cross-origin/CORS behavior is configured. In that case:
- the primary Telegram CTA remains an external link,
- the status link targets the real status origin,
- API calls must use an explicitly configured API base URL,
- CORS and security headers are reviewed,
- canonical URLs and Open Graph metadata use the public marketing domain,
- no secrets are placed in Vite `VITE_*` variables.

Do not choose a separate deployment only to avoid understanding the existing route structure.

## 6. Root route contract

- `GET /` with an HTML-accepting browser request: marketing page.
- `HEAD /`: preserve the currently intended lightweight/JSON behavior, or implement a valid HEAD response without rendering a large page. Document the decision.
- Non-HTML root/API requests: preserve the current JSON response where that is part of the service contract.
- `/status`: preserve the existing service-status payload or page. If a separate branded status page is desired, route it explicitly without breaking clients that expect JSON.
- Existing `/watch`, stream, webhook, admin and bot-related endpoints: unchanged unless a dedicated migration is planned and approved.

## 7. Router and rendering

The marketing site can use a single-page route with anchor sections, plus explicit lightweight routes for docs/privacy/terms if needed. If a client-side router is used:
- configure server fallback only for known public site paths,
- return 404 for unknown public routes rather than a false success page,
- preserve existing backend routes,
- test refresh/deep-link behavior at every public route.

For SEO-sensitive routes, use server-generated metadata or static multi-page output if practical. A client-side effect that changes `document.title` after hydration is not sufficient by itself for all indexing/preview behavior.

## 8. Configuration model

Keep public configuration in one typed module. Values may come from `import.meta.env` at build time. Examples:

- `VITE_SITE_NAME`
- `VITE_PUBLIC_SITE_URL`
- `VITE_TELEGRAM_BOT_USERNAME` or `VITE_TELEGRAM_BOT_URL`
- `VITE_PUBLIC_REPO_URL`
- `VITE_PUBLIC_DOCS_URL`
- `VITE_PUBLIC_STATUS_URL`
- `VITE_PUBLIC_DOWNLOAD_URL` only when a real release exists
- `VITE_PUBLIC_RELEASE_VERSION` only when verified
- `VITE_PUBLIC_SUPPORT_URL` only when verified
- `VITE_ENABLE_DOWNLOAD_CTA=false` by default
- `VITE_ENABLE_STATUS_WIDGET=false` until the status contract is verified

The final naming can vary, but a configuration validation utility must enforce consistency and prevent placeholder links from reaching production.

All `VITE_*` values are public. Never place bot tokens, API keys, private endpoint secrets, signing keys, cookies or database credentials in the frontend environment.

## 9. Telegram link utility

Create one tested helper that accepts a configured username/URL and a placement slug. It should return a validated HTTPS `https://t.me/<username>?start=<safe_parameter>` URL or a clear configuration error.

Rules:
- no user-supplied secret data in URL parameters,
- no arbitrary redirect URL from query strings,
- no untrusted bot username assembled from visitor input,
- use `URL` and `URLSearchParams`, not manual string concatenation,
- allow only approved tracking placement values,
- if the exact bot URL is supplied as config, validate the host and expected path,
- test invalid/missing/badly encoded values.

## 10. Status data

If a status widget is implemented, source it from a verified endpoint. Define the schema first; do not assume the endpoint returns a particular JSON shape.

Expected UI states:
- Loading: concise neutral label.
- Operational: only when a successful response explicitly defines the service as operational.
- Degraded/maintenance: reflect a recognized response state.
- Unavailable: no successful fetch or unknown state; never convert request failure to green.

Use timeout/abort, a restrained refresh interval, caching only where valid, and an accessible text label. A static status link is safer than polling if the status API contract is unclear.

## 11. Content architecture

Move repeated static content to typed data modules only where it improves maintainability. Avoid building a dynamic CMS model for a small marketing site.

Each feature entry should contain:
- stable `id`,
- title,
- concise description,
- evidence source or implementation comment,
- active/verified flag,
- optional illustration source,
- optional CTA destination.

The rendering layer must filter out unverified features from public content. This is a guard against stale copy.

## 12. Testing architecture

Unit tests:
- Telegram deep-link URL creation and validation.
- Config validation and gated buttons.
- Scroll progress clamp and reduced-motion logic.
- Feature content excludes unverified claims.

Component tests:
- primary CTA uses configured URL.
- mobile menu opens/closes and restores focus.
- FAQ keyboard interaction.
- motion toggle changes the state.
- no download CTA without a real configured download URL.
- status failure does not show “operational.”

End-to-end tests:
- load root and verify the hero/primary CTA.
- use header anchor links.
- scroll to final CTA.
- test desktop and mobile menu.
- test reduced-motion setting.
- refresh every public route.
- verify existing service endpoints and HTML/JSON content negotiation.
- check all anchors and configured external destinations.

## 13. Build commands

Adapt if scripts already exist. A sensible minimum is:

```bash
cd webapp
npm ci
npm run typecheck
npm run lint
npm run test -- --run
npm run build
```

If the project’s script names differ, document the exact supported commands in README. Do not report checks as passed unless the command actually ran and succeeded.

## 14. Integration exit gate

The frontend cannot be merged/released until:
- a clean install works from the lockfile,
- type check, lint, tests and build pass,
- browser route refresh works,
- the production HTML loads hashed assets correctly,
- root HTML and JSON behavior remains correct,
- every existing route regression test passes,
- Telegram CTA destination is configured and verified,
- no placeholder route is linked in production.
