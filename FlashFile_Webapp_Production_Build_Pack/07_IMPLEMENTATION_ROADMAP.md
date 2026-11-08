# 07. Implementation roadmap

This is an ordered implementation plan. Phases may be split into more commits, but must not be skipped. The finish condition is the acceptance checklist, not the completion of the last phase title.

## Phase 0. Repository reconnaissance and claim audit

### Actions
- Inspect branch, uncommitted work and current repository tree.
- Read current route definitions, templates, frontend files, container configuration, environment examples, deployment manifests and tests.
- Identify actual public bot username/URL, production host, live status response, release artifact and available product screenshots.
- Trace the complete current bot-to-link-to-player/download workflow.
- Build a feature evidence matrix. Include file/line or live test evidence for every planned public claim.
- Record route contracts that must not change.

### Outputs
- A short architecture inventory.
- A route preservation matrix.
- Feature evidence matrix with `verified`, `needs verification`, `not available` states.
- List of required configuration values.

### Exit gate
No code is edited until the current app structure is understood. Unknown values remain unknown; the agent does not guess.

## Phase 1. Production frontend foundation

### Actions
- Add or complete the Vite/React/TypeScript build in the existing `webapp/` location if appropriate.
- Configure a package lock, type checking, linting, unit tests and production build.
- Establish CSS token files and semantic HTML structure.
- Create shared config validation for required public URLs.
- Configure base path and static output so the current backend can serve the build.
- Preserve existing Python entrypoints and endpoints.

### Outputs
- Clean frontend shell.
- Reproducible scripts.
- A working production build.
- Minimal application route setup and metadata.

### Exit gate
A clean install produces a build; server route tests prove existing product endpoints are preserved.

## Phase 2. Visual system and real content skeleton

### Actions
- Implement the Obsidian/Crimson-Coral token system.
- Add typography, grid, spacing and responsive primitives.
- Build the header, mobile navigation, hero, workflow, feature blocks, compatibility, FAQ, final CTA and footer.
- Use source-backed copy only.
- Add real screenshots if provided; otherwise build accurate and clearly labeled workflow diagrams.
- Add the Claude-style fallback tokens only if all states can be tested.

### Outputs
- A complete responsive product page with motion temporarily disabled or static.
- All CTA destination wiring through centralized utilities.
- Empty/missing release and bot configuration states handled explicitly.

### Exit gate
At every target viewport, the page has deliberate hierarchy and useful information without relying on animation.

## Phase 3. Three.js particle scene and scroll synchronization

### Actions
- Inspect/reuse `TransmissionCore.tsx`.
- Separate scene creation, uniform updates and teardown.
- Add `uScrollProgress`, section phase and CSS-token colors.
- Build deterministic scene states along the page.
- Integrate the scene with Motion’s scroll value or one lightweight native-scroll observer.
- Add visibility pausing, adaptive particle count, DPR cap, resize handling, WebGL fallback, theme observation and full disposal.
- Implement OS reduced-motion and manual motion control.

### Outputs
- One consistent background scene that shifts with scroll.
- No duplicate scene across sections.
- CSS fallback and low-motion mode.

### Exit gate
Scroll down/up/fast/slow and navigate via anchors without flashes, scroll trapping or drift. The page remains fully usable without WebGL.

## Phase 4. Working controls and source-backed features

### Actions
- Wire Telegram buttons through the central deep-link helper.
- Add optional start parameters by CTA placement.
- Wire docs/status/source/download links only when configured and real.
- Add FAQ accordion, mobile navigation, motion control and theme control if enabled.
- Test status data if integrated; otherwise use a plain link.
- Remove every dead link and nonfunctional control.

### Outputs
- All buttons and navigation links have meaningful, verifiable behavior.
- Feature blocks reflect tested capabilities.

### Exit gate
No production CTA points to `#`, a placeholder domain, an absent artifact, or an invented page.

## Phase 5. Accessibility, performance, SEO and content review

### Actions
- Test keyboard-only navigation, skip link, focus order, focus visibility, screen reader labels and mobile target sizes.
- Add reduced-motion behavior and ensure the page does not require animation to reveal content.
- Measure contrast in every theme.
- Run Lighthouse/PageSpeed or equivalent local performance checks.
- Verify page metadata, canonical URL, Open Graph image, favicon, sitemap, robots policy and JSON-LD only where facts are accurate.
- Review body copy for unsubstantiated claims and awkward boilerplate.
- Optimize images, fonts, JavaScript chunks and particle workload.

### Outputs
- Accessibility and performance report.
- SEO/meta verification.
- Corrected copy and responsive defects.

### Exit gate
No critical accessibility bug, no critical console errors, no broken links, and performance target met or a specific measured exception is documented.

## Phase 6. Release build and deployment verification

### Actions
- Build from a clean checkout using the documented commands.
- Build the production container with Node build stage and the existing runtime stage if that best fits the repository.
- Run endpoint regression tests in the same order/conditions as production.
- Deploy to staging if available.
- Verify the actual public domain, HTTPS, bot link in desktop/Android Telegram, deep links, metadata, status, player/stream routes and 404 behavior.
- Test the site at the target mobile and desktop sizes.
- Inspect the browser console and network waterfall.
- Create a rollback note.

### Outputs
- Build log or CI evidence.
- Staging verification checklist.
- Release notes and rollback instructions.

### Exit gate
Production-ready means every item in `11_ACCEPTANCE_CHECKLIST.md` passes. If staging, bot URL or release artifact is unavailable, label those gates as blocked rather than claiming full completion.

## Commit boundaries

Suggested sequence:
1. `chore(webapp): scaffold production frontend and test scripts`
2. `feat(webapp): add FlashFile product page and design tokens`
3. `feat(webapp): synchronize TransmissionCore with page scroll`
4. `feat(webapp): wire Telegram links and accessible interactions`
5. `test(webapp): add responsive, accessibility and route regression coverage`
6. `build(deploy): integrate frontend assets without changing service contracts`

Do not combine large refactors of bot, file streaming and marketing UI into one broad commit.

## Required implementation note

At the end of each phase, report what files changed, which commands actually ran, their exit codes, what remains blocked, and the next phase. Do not write “done” if the build was not run. Do not claim browser testing without actual browser evidence.
