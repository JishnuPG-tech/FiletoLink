# FlashFile Professional Webapp: Product and Engineering Plan

**Status:** Proposed implementation plan  
**Source snapshot reviewed:** `93d5c263e1d104e485aec0096bffd2da36bf2930`  
**Primary implementation target:** FlashFile web experience backed by Thunder / FileToLink  
**Research date:** 7 November 2026

## 1. Executive direction

Build FlashFile as a workspace-first web application for creating, validating, previewing, streaming, and organizing links. Keep the existing Telegram bot and HTTP streaming endpoints as the media backend. The web app should feel like a polished software product, not only a marketing landing page.

The recommended visual direction is **FlashFile Obsidian + Crimson-Coral**: near-black surfaces, a restrained coral-red action color, precise typography, thin borders, a small amount of cyan for system/status information, and the existing Spirit curl-noise particle effect limited to the hero. Use motion to explain state changes, not as decoration on every element.

A **Claude Editorial** theme is the planned alternative if the product owner rejects the primary look. That alternative uses warm graphite, ivory text, terracotta accents, and the existing Instrument Serif + Inter typography pairing. Keep both palettes token-driven so switching themes does not require rewriting component styles.

## 2. Repository findings that affect the plan

The reviewed source snapshot contains:
- The Python / aiohttp Thunder service and the existing `/f/{hash}/{name}`, `/watch/f/{hash}/{name}`, and `/status` routes.
- `Thunder/template/index.html`, a branded landing-page draft with a URL launcher, M3U export, aria2 command export, StringTune initialization, and the Spirit particle shader.
- `webapp/src/components/canvas/TransmissionCore.tsx`, a React/Three.js particle component.
- The larger Apex + Jellyfin subsystem, which is distinct from FileToLink's direct-link experience.

The `webapp/` directory in this snapshot is not yet a complete frontend application. It has a particle component but no frontend `package.json`, Vite configuration, app entry point, route tree, or component system. The root Dockerfile also does not build a React application today. The existing page is therefore a design starting point, not proof that a complete React webapp is already wired into the deployed service.

The source branch requires care before integration. GitHub's current `main` ref was observed at `513653d5455cf89a1ec856c83297d8f709237378`, while the reviewed Spirit UI snapshot is `93d5c263e1d104e485aec0096bffd2da36bf2930`. GitHub's compare reports the branch histories as diverged: this feature branch is 7 commits ahead and 1 commit behind `main`. This branch intentionally preserves the newer UI snapshot; reconcile the main-only commit before merging or deploying.

One additional routing constraint is important: Thunder's root handler negotiates on the request `Accept` header. In the reviewed source, browser-like HTML requests are intended to render `index.html`, while non-HTML requests receive a machine-readable JSON status object. A direct Firecrawl probe received JSON, so confirm the real browser route during integration rather than assuming the landing page is live. Keep this compatibility behavior and mount the actual workspace under `/app/`; preserve `/status`, streaming, watch, webhook, and admin routes.

## 3. Product goals

1. Make the primary task obvious within a few seconds: paste a FlashFile URL, open its preview, copy a link, or prepare a batch.
2. Preserve reliable direct streaming and downloads without introducing a second media pipeline.
3. Provide a useful guest experience. Do not require account creation until the backend has a real user/session API.
4. Surface truthful health information from existing endpoints. Never simulate service health or invent usage statistics.
5. Make batch workflows practical: validate, deduplicate, reorder, export M3U, and copy an aria2 command.
6. Keep the particle background beautiful but optional. Performance, keyboard access, and reduced-motion preferences take priority.
7. Treat subscription payment as a manually verified UPI flow until an actual provider verification API exists.

## 4. Proposed information architecture

### Public / entry views

| Route | Purpose | First-release scope |
|---|---|---|
| `/app/` | Main workspace | Primary quick actions, paste a stream URL, recent local history, system status |
| `/app/links` | Link Lab | Inspect/normalize a supported FlashFile link, choose preview, stream, or download |
| `/app/batch` | Batch Studio | Multi-line input, duplicate removal, validation state, ordering, M3U and aria2 export |
| `/app/watch` | Player launch surface | Route to existing `/watch/` URL format; retain native player controls for supported media |
| `/app/status` | Service status | Read from existing `/status` and show latency, active clients, and workload only when returned |
| `/app/plans` | Access plans | Only show payment options when payment is enabled; clearly explain manual proof review |
| `/app/settings` | Preferences | Theme, motion preference, copy format, local history controls |

Keep backend endpoints such as `/status`, `/f/`, and `/watch/` separate from client-side routes. SPA fallback should apply only under `/app/`, never to arbitrary stream or API paths.

### Main navigation

Desktop: compact left rail with Workspace, Link Lab, Batch Studio, Status, and Plans. Use a narrow top bar for page title, global actions, theme selection, and system status.

Mobile: one-column layout with a small header and a bottom navigation bar. Keep the paste-link field and main action visible without requiring a user to scroll. Avoid shrinking desktop tables into tiny text; turn batch rows into stacked cards on small screens.

## 5. Core user journeys

### A. Open a single link

1. Paste a supported FlashFile link.
2. Parse the URL locally and identify whether it matches a known `/f/` or `/watch/f/` shape.
3. Show a preview of the destination and explicit actions: Open preview, Stream, Download, Copy URL.
4. Use existing backend routes for real requests. Display honest not-found, unavailable, or unsupported-format states.
5. Keep the original URL visible and copyable.

The first release must not claim to validate arbitrary internet URLs server-side. If a future URL preview endpoint is added, it needs allowlisting and SSRF protection. A browser-side format check is not proof that a remote file is reachable.

### B. Prepare a batch

1. Paste multiple supported URLs, one per line.
2. Normalize whitespace, remove exact duplicates, and show invalid rows before export.
3. Let users reorder or remove rows.
4. Export an M3U playlist and copy a correctly quoted aria2 command.
5. Clearly show which rows were only syntactically checked and which were actually reachable.

### C. Play or download

1. Open the existing watch/stream route.
2. Keep standard playback controls, keyboard support, and a visible retry path.
3. Show loading, not-found, unsupported-codec, and network errors separately.
4. Avoid promising transcoding or universal browser codec support. Preserve the backend's existing direct-stream behavior.

### D. View status

1. Fetch the existing `/status` endpoint.
2. Display returned bot status, version, active client count, workload distribution, and uptime where available.
3. Show a timestamp for the last successful check and a clear offline/unknown state.
4. Do not infer uptime from a successful page render or present synthetic metrics.

### E. Payment

1. Display price and UPI details only when payment is enabled on the backend.
2. Open the existing `/pay` route or a documented UPI intent.
3. Tell users that payment proof is reviewed by an administrator.
4. Send proof submission through a documented, authenticated backend API or the existing Telegram bot flow. Do not add a fake web form that claims to verify payments automatically.

## 6. Visual system

### Primary theme: FlashFile Obsidian + Crimson-Coral

| Token | Value | Use |
|---|---|---|
| `--bg-base` | `#08090D` | Main background |
| `--bg-surface` | `rgba(16, 18, 27, .78)` | Navigation and elevated panels |
| `--bg-card` | `rgba(22, 25, 38, .88)` | Cards and menus |
| `--border-glass` | `rgba(255, 255, 255, .08)` | Subtle separation |
| `--accent-brand` | `#FF3B5C` | Primary actions and active states |
| `--accent-secondary` | `#E02447` | Gradient endpoint and depth |
| `--accent-cyan` | `#38BDF8` | Limited system / information accent |
| `--text-primary` | `#F8FAFC` | Main text |
| `--text-secondary` | `#94A3B8` | Supporting text |
| `--text-muted` | `#64748B` | De-emphasized metadata |
| `--font-serif` | Instrument Serif | Hero/editorial display only |
| `--font-display` | Plus Jakarta Sans | Titles and compact labels |
| `--font-body` | Inter | Body copy, controls, navigation |
| `--font-mono` | JetBrains Mono | URLs, hashes, status values, commands |

Use coral for one dominant action at a time. Do not make every card glow, use cyan as a second primary action color, or combine strong blur, gradients, borders, and shadows on the same surface. Keep content areas quieter than the hero.

### Alternative: Claude Editorial

If the product owner rejects the primary palette, keep the same component layout and switch tokens:
- Warm graphite background, ivory/off-white text, terracotta action color.
- Instrument Serif for editorial headings and Inter for functional UI.
- Fewer gradients, softer contrast between surfaces, and almost no glass blur.
- The same status, error, focus, and success semantics. Theme changes must never change behavior.

Implement theme changes through CSS variables and a `data-theme` attribute. The React particle component should read the shared particle tokens instead of owning a separate hard-coded palette.

## 7. Spirit particles and motion rules

Use the Spirit curl-noise particles as a hero atmosphere, not a global background under forms, tables, dialogs, or the player.

- Desktop budget: up to 650 particles. Tablet budget: around 420. Small mobile budget: around 220 to 240.
- Read colors from shared CSS tokens: primary brand coral, deep coral secondary, restrained cyan highlight. Use the same tokens for the fallback glow.
- Keep the background decorative (`aria-hidden`) and behind content. It must not intercept pointer input.
- Detect `prefers-reduced-motion` and WebGL support. Show a static radial fallback instead of running the effect.
- Pause animation when the hero is out of view. Keep device-pixel-ratio caps conservative on mobile.
- Dispose of Three.js geometry, material, renderer, animation frame, observers, and event listeners on unmount.
- Re-check the pinned Three.js shader APIs before upgrading from the current legacy shader version.

Use StringTune for only the interactions its public API supports. Its documented core pattern is `getInstance()`, `use(module)`, and `start(60)`, with markup attributes and module outputs. Verify the exports for `StringMagnetic` and `StringParallax` against the installed package before relying on them. Do not read private runtime fields.

Use CSS transitions for small interface states and one animation system for larger component transitions. Recommended ranges are 140–180 ms for hover/focus feedback and 180–260 ms for small view transitions. Do not animate width/height on every frame, delay task feedback for visual effects, or hijack native scrolling.

## 8. Frontend architecture

### Recommended stack

- React + TypeScript + Vite for a maintainable routed application.
- Tailwind CSS for layout and responsive styling.
- shadcn/ui components with Radix primitives for dialog, dropdown, tabs, tooltip, menu, and accessible interaction patterns.
- Iconsax as the intended visual icon family, subject to a quick package and bundle check. Keep one icon system, preserve text labels for important actions, and use accessible labels for icon-only controls.
- StringTune for selected scroll/cursor effects only. CSS or a single established React motion library should handle component transitions.
- Small typed API module in `src/lib/api.ts`; do not spread raw `fetch()` calls through page components.

### Suggested layout

```text
webapp/
  package.json
  vite.config.ts
  tsconfig.json
  src/
    app/
      App.tsx
      router.tsx
      providers.tsx
    components/
      layout/
      navigation/
      feedback/
      links/
      batch/
      player/
      canvas/TransmissionCore.tsx
    pages/
      WorkspacePage.tsx
      LinkLabPage.tsx
      BatchStudioPage.tsx
      StatusPage.tsx
      PlansPage.tsx
      SettingsPage.tsx
    lib/
      api.ts
      links.ts
      validators.ts
      clipboard.ts
    styles/
      globals.css
      themes.css
    types/
      api.ts
  tests/
```

### Deployment pattern

Build the frontend in a Node-based Docker build stage and copy the generated static `dist/` output into the existing Python runtime image. No Node server needs to run in production. Serve the compiled assets under `/app/` through the gateway or aiohttp static routing. Keep the Telegram streaming service as the backend and preserve its internal ports.

The exact static mount must be covered by integration tests. Avoid a broad SPA fallback that captures `/f/`, `/watch/`, `/status`, webhook, or admin endpoints.

## 9. Phased delivery plan

### Phase 0: baseline and contract verification

- Confirm the intended source branch and reconcile the current `main` ref with the reviewed UI commit.
- Map all current routes and determine whether `Thunder/template/index.html` is actually served.
- Record current response contracts for `/status`, `/f/`, `/watch/`, `/pay`, and gateway health routes.
- Capture a baseline of direct link, preview, download, and Telegram bot behavior.
- Do not deploy or change the status endpoint in this phase.

**Exit criteria:** route map and source branch agreed; no frontend work has changed link semantics.

### Phase 1: frontend shell and design tokens

- Create the actual Vite + React + TypeScript application and build configuration.
- Add CSS theme tokens, typography, layout shell, responsive navigation, focus ring, button/input variants, toast/error patterns, loading skeleton, and empty states.
- Integrate the particle component through the shared tokens.
- Build the frontend in Docker and serve it under `/app/`.

**Exit criteria:** static assets load in the combined image; app routes do not swallow backend routes; mobile and reduced-motion layouts work.

### Phase 2: Link Lab

- Implement supported FlashFile URL parsing and clear error messages.
- Wire preview, stream, download, and copy actions to the existing routes.
- Add loading, not-found, network error, copied feedback, and unsupported URL states.
- Add safe clipboard fallback and keyboard-only interaction.

**Exit criteria:** all displayed actions perform real work; no placeholder actions are presented as complete.

### Phase 3: Batch Studio

- Add URL parsing, deduplication, list reordering, removal, and per-row validation state.
- Export M3U and aria2 commands from validated rows.
- Add import/export tests for empty rows, spaces, quotes, query strings, and duplicate links.
- Only add server-side URL probing if an allowlisted API and SSRF controls are designed and tested.

**Exit criteria:** exported playlist entries match the user's selected order and rows.

### Phase 4: Player and status

- Add player launch and error-state handling around existing watch/stream behavior.
- Wire status and latency to actual service responses.
- Display unknown/offline when polling fails, with retry controls.
- Preserve native video controls and direct-play behavior.

**Exit criteria:** player errors are distinguishable; status values are sourced and timestamped.

### Phase 5: plans, preferences, and local history

- Connect the plan screen to explicit payment configuration and the current manual verification process.
- Add theme selection, reduced-motion preference, copy format, and clear-local-history controls.
- Store only non-sensitive history locally unless backend identity and retention rules are agreed.
- Do not store Telegram credentials, bot tokens, raw access tokens, or private session state in browser storage.

**Exit criteria:** plans are hidden or clearly disabled when unavailable; no false payment-success state is possible.

### Phase 6: polish and release hardening

- Add responsive refinements, non-blocking route transitions, error boundaries, and lazy loading.
- Audit contrast, focus visibility, screen-reader labels, keyboard navigation, dialog behavior, and reduced motion.
- Test slow networks, unavailable upstreams, small screens, high-DPI screens, and no-WebGL mode.
- Measure initial JS size, layout shifts, interaction response, and particle GPU cost.
- Deploy only after owner review and a working rollback path.

## 10. Test and release gates

Required automated tests:
- URL parser: canonical `/f/`, preview `/watch/f/`, malformed hash, unsafe protocol, encoded filename, query strings.
- Batch export: line endings, duplicates, reordering, quotes, empty input, large lists.
- API layer: success, 404, 5xx, timeout, offline response, malformed status payload.
- Theme: primary token and alternative theme both update particle colors; fallback glow matches.
- Motion: reduced-motion setting prevents animation and keeps a usable static fallback.
- Lifecycle: particle resources and observers are cleaned up on unmount.
- Accessibility: keyboard path through navigation, forms, dialogs, copy buttons, and batch controls.
- Deployment: SPA route works while all stream, watch, status, webhook, and admin routes retain their prior behavior.

Release is blocked by any broken streaming route, any fake success message, any payment state that bypasses manual verification, missing reduced-motion fallback, or unresolved source-branch drift.

## 11. Risks and non-goals

- **No arbitrary local upload:** the reviewed backend is Telegram-driven. Do not expose an upload control until an actual upload route exists.
- **No automatic UPI verification:** manual proof review remains authoritative until a genuine provider integration is added.
- **No invented account system:** subscriptions exist in MongoDB and Telegram commands, but a web session/auth API must be specified before a logged-in web dashboard is promised.
- **No promise of transcoding:** browser playback still depends on codecs and the existing streaming path.
- **No unbounded particle animation:** reduce the effect or disable it based on device constraints and user preferences.
- **No blind deployment:** current main/source branch drift must be resolved before production rollout.

## 12. Research references

- [Particle Love](https://particle-love.com/) — reference for the Spirit curl-noise particle aesthetic.
- [StringTune official quick start](https://tune.fiddle.digital/docs/quick-start/) — documented instance, module registration, and runtime startup.
- [StringTune overview](https://tune.fiddle.digital/docs/overview/) — public API, built-in versus custom modules, and runtime model.
- [shadcn/ui documentation](https://ui.shadcn.com/docs) — editable, composable UI components.
- [Radix Primitives](https://www.radix-ui.com/primitives/docs/components) — accessible unstyled interaction primitives.
- [MDN prefers-reduced-motion](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/prefers-reduced-motion) — respect reduced-motion preferences.
- [MDN animation performance](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Animation_performance_and_frame_rate) — animation cost and responsiveness.
- [Three.js WebGLRenderer](https://threejs.org/docs/pages/WebGLRenderer) — renderer lifecycle and GPU-resource disposal.
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/) — accessible interaction patterns.

These references inform implementation choices; they do not mean the future webapp has already passed performance or accessibility testing.
