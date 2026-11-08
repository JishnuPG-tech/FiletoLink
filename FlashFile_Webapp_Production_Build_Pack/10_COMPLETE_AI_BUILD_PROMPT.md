# 10. Complete AI build prompt

Copy the full prompt below into the coding agent working in the actual FiletoLink repository. Attach or paste the other documents in this pack as reference. The agent must implement the website in the repository and verify it, not merely return another plan.

---

## MASTER PROMPT START

You are the lead product designer, frontend engineer, WebGL engineer, accessibility specialist, QA engineer and release engineer for the existing FiletoLink project. Build the FlashFile public product website to the specifications below. Deliver working code in the current repository. Do not answer with only a plan, prototype screenshot or design description.

### A. Objective

Create a premium, polished, product-showcase website for FlashFile, the public-facing product name used for the existing FiletoLink project. The quality bar is the clarity and finish of a leading software product site, with stronger visual identity and a distinctive scroll-synchronised 3D particle backdrop. Do not copy ChatGPT’s exact design, wording, branding or layout. Use its product-information clarity as a quality reference only.

The site must explain the real product, show how its supported workflow works, and provide obvious, working links to the official Telegram bot and verified product resources. It must work on desktop and mobile, remain accessible with reduced motion, load quickly, and preserve every existing backend route.

### B. Non-negotiable rules

1. Inspect the repository before editing. Read current routes, templates, Dockerfile, deployment configuration, env examples, tests, current `webapp/` structure and all relevant project docs. Do not assume the repository matches a previous snapshot.
2. Use the existing Three.js component `webapp/src/components/canvas/TransmissionCore.tsx` if it exists. Inspect and adapt it. Do not blindly overwrite it.
3. Do not break `/status`, `/watch`, stream/range endpoints, webhooks, admin paths, bot routes, existing JSON contracts or health checks.
4. Do not invent the Telegram bot username. Find it in verified public configuration or ask the maintainer through an explicit blocked configuration note. Do not use a placeholder destination in a production-ready build.
5. Do not invent an Android app, APK, pricing model, checkout flow, user accounts, testimonials, usage numbers, service-level promises, file compatibility, retention policy, encryption claim or availability percentage.
6. Do not create fake interactions. Every visible button must navigate to a real destination or perform a real in-page action. A visual product example must be labeled as illustrative when it is not an actual app view.
7. Do not claim a test passed unless you ran it and observed its successful exit/output. If a tool or environment is unavailable, report the exact limitation and mark the related release gate blocked.
8. Do not use generic AI marketing copy. Avoid boilerplate like “revolutionize your workflow,” “unlock productivity,” “next-generation,” “seamless experience,” “powerful all-in-one platform,” “built for everyone,” “magic,” and vague claims without concrete behavior.
9. Do not make every section the same rounded-card grid. Use a clear editorial hierarchy, distinct section compositions, specific diagrams, generous space and real product evidence.
10. No forced scrolling, hidden scrollbar, mousewheel interception, auto-playing sound, full-screen load gate, unskippable intro, cursor replacement or large motion that prevents reading.
11. Never expose secrets in frontend code, Vite variables, static files, source maps or logs.
12. Do not push, merge or deploy production unless the current task explicitly authorizes those actions. Work on the expected feature branch and state what is local vs deployed.

### C. Required references

Read these pack documents before implementation:
- `01_PRODUCT_BRIEF.md`
- `02_INFORMATION_ARCHITECTURE_AND_COPY.md`
- `03_VISUAL_DESIGN_SYSTEM.md`
- `04_PARTICLE_AND_MOTION_SPEC.md`
- `05_COMPONENTS_AND_INTERACTIONS.md`
- `06_TECHNICAL_ARCHITECTURE.md`
- `07_IMPLEMENTATION_ROADMAP.md`
- `08_QA_ACCESSIBILITY_PERFORMANCE.md`
- `09_SECURITY_DEPLOYMENT_OPERATIONS.md`
- `11_ACCEPTANCE_CHECKLIST.md`
- `12_ENVIRONMENT_AND_LINKS.md`

If a requirement conflicts with the current working code, preserve working product/backend contracts and adapt the site integration. Explain the conflict and chosen resolution in the final report.

### D. First step: repository inventory

Before editing, output and record:
- current branch and working-tree status,
- frontend folders and package scripts,
- framework/runtime and current app entry points,
- current HTML/root response behavior and content negotiation,
- existing status, watch, stream, webhook, admin and health routes,
- current particle implementation and cleanup lifecycle,
- Docker/build/deployment structure,
- actual Telegram bot destination and public website URL if available,
- real product workflows found in code,
- features that cannot be verified,
- tests already present and commands available.

Then create a concise implementation map. Do not ask for preferences already resolved in this prompt. If a critical public URL is missing, continue implementing the configurable site but mark the production CTA gate blocked; do not fabricate the URL.

### E. Visual direction

Use the default **Obsidian / Crimson-Coral** theme:
- background `#08090D`, raised background `#0D0F15`, surfaces `#11131B` and `#171A23`,
- primary coral `#FF3B5C`, deep coral `#E02447`,
- cyan signal accent `#38BDF8`, used sparingly,
- primary text `#F8FAFC`, secondary `#B5BCC9`, muted `#7F899B` only where measured contrast supports it,
- borders as subtle translucent white,
- editorial headline face: Instrument Serif,
- functional typography: Plus Jakarta Sans with Inter/system fallbacks,
- technical labels: JetBrains Mono.

Use CSS variables as the token source of truth and provide the Claude-style warm graphite/ivory/terracotta fallback from the design-system document if it can be implemented consistently. Do not let the fallback dilute the FlashFile default brand.

A premium aesthetic means disciplined type, precise spacing, readable contrast, careful alignment, good responsiveness and real product storytelling. It does not mean every element must be blurred, glowing or animated.

Glassmorphism is allowed only where layering is meaningful, such as the scrolled header or compact motion control. Provide a solid surface fallback. The main content must remain readable on a stable backdrop.

Use Lucide React for regular controls. Do not use emoji as the primary icon language. Use real product screenshots when the maintainer supplies them. If none exist, create a specific workflow diagram and visibly label it `Illustrative workflow`.

### F. Required page content

Implement the home/product page with these sections in a strong visual rhythm:
1. Site header with brand mark, Features, How it works, Compatibility, FAQ and primary `Open bot` CTA.
2. Hero with eyebrow `TELEGRAM-POWERED FILE WORKFLOW`, headline `Your files. Easier to access through Telegram.`, verified supporting copy, primary `Open FlashFile on Telegram` CTA and secondary `See how it works` anchor.
3. A small capabilities strip that lists only verified features and no fake metrics.
4. A visually clear workflow sequence using the real bot behavior.
5. Feature sections explaining real supported link/watch/playback/download/playlist behavior only after code verification.
6. Compatibility and limitations section with precise current details. Hide or mark unverified capabilities; do not claim universal compatibility.
7. A real screenshot or a clearly labeled illustrative product diagram.
8. FAQ with 6–8 useful, source-backed answers.
9. Final Telegram CTA section.
10. Footer with only valid docs, source, status, privacy, terms, contact and release links.

Use the exact content structures in `02_INFORMATION_ARCHITECTURE_AND_COPY.md`, but adjust facts based on the actual code. Make the copy concise, specific and human-written in tone. Avoid unsupported superlatives and generic promises.

Do not create pricing, account, upload or dashboard sections unless the real product already supports them. Do not display a download/install CTA without a verified release artifact. Do not publish privacy/terms text that makes unverified guarantees.

### G. Working CTA behavior

Create one typed configuration module and one tested Telegram URL helper. It must:
- read the real public bot username/URL from public build configuration,
- create a valid `https://t.me/<bot_username>` destination,
- optionally add a safe, short `start` parameter for a predefined CTA placement,
- use URL/URLSearchParams rather than hand-built query concatenation,
- never include user data, secrets, file IDs or personal data in the start parameter,
- reject invalid hosts and missing configuration,
- give a meaningful non-production warning when config is missing,
- fail the production configuration check or clearly block release when the bot link is not verified.

The main CTA must open Telegram. Do not claim the bot successfully started because the site cannot verify the outcome. Test the link in a desktop browser and, if available, Android.

All navigation uses real anchors. Every button does something. Do not use `href="#"`, a fake disabled button, a fake progress indicator or a dead `Download` action.

### H. Particle scene: 3D, scroll-linked, synced

Use Particle Love “The Spirit” as the approved motion/art-direction reference, then use the existing `TransmissionCore` code and enhance it to match the spec. Keep exactly one canvas and one renderer. The canvas is decorative, has `aria-hidden="true"`, sits behind content, and does not capture pointer events.

The scene must respond to the page’s normalized scroll progress. Use a single source of scroll truth such as Motion’s `useScroll()` value or a passive scroll observer. Pass values into the Three.js scene through refs/uniforms; do not force React re-renders on each scroll pixel.

Create smooth, deterministic state changes:
- 0.00–0.18 hero: contained orbital transmission core,
- 0.18–0.38 how-it-works: particles open into directional paths,
- 0.38–0.62 features: paths become more organized with sparse signal points,
- 0.62–0.82 detail/compatibility: cloud shifts aside and contracts,
- 0.82–1.00 final CTA/footer: field converges and settles.

Map progress to bounded group rotation, flow spread, direction and subtle camera movement. Interpolate smoothly and reversibly. Scrolling up must return the scene naturally. Never recreate WebGL on each section change or make it flash.

Suggested uniform fields include `uTime`, `uScrollProgress`, `uSectionPhase`, `uPointer`, `uColorPrimary`, `uColorSecondary`, `uColorHighlight` and `uMotionScale`. Read particle colors from CSS custom properties so theme changes also update the shader.

Adaptive initial caps to benchmark:
- mobile: approximately 100–160 particles,
- tablet/coarse hardware: approximately 180–300,
- desktop: approximately 360–650.

Set a conservative device-pixel-ratio cap, target around 1.25 on mobile and 1.5–1.75 on desktop. Use `renderer.setAnimationLoop()` or a fully managed animation loop with cleanup. Pause when the tab is hidden and reduce work when offscreen. Handle resize, WebGL context loss, theme changes and component unmount. Dispose geometries, materials, observers, listeners and renderer resources correctly. Do not allocate new objects every animation frame.

The visual effect must remain behind stable contrast overlays. Do not animate foreground text at the same intensity as the particles.

### I. DOM animation and scrolling

Use Motion for React for small section reveals, active-section updates, button interactions and layout transitions. Use opacity and modest transform changes. Do not animate every word or force visitors through a staged narrative before they can read the page.

Use native scrolling by default. Add `scroll-behavior: smooth` for anchor navigation only when reduced motion is not active. Use anchor links with valid hashes and `scroll-margin-top` for header offset. Only add Lenis if its integration is tested against touch, keyboard, focus, browser history and particle synchronization. Do not hide the scrollbar or hijack wheel events.

### J. Accessibility requirements

- Target WCAG 2.2 AA for ordinary content/controls.
- Add a keyboard skip link.
- Use semantic landmarks, a single H1 and a logical heading hierarchy.
- Ensure measured contrast for body text, buttons, borders and focus rings in each enabled theme.
- Provide clear `:focus-visible` states.
- Mobile menu must support keyboard interaction, Escape and focus restoration.
- FAQ uses accessible accordion behavior.
- Canvas and decorative art must not be announced as meaningful content.
- Add text alternatives for meaningful workflow diagrams.
- Honor `prefers-reduced-motion: reduce` and supply an obvious manual Motion On/Reduced control.
- Reduced motion disables perpetual particle rotation, large parallax and scroll-driven camera movement. All content remains visible.
- Respect reduced motion before the first render, so there is no initial animation flash.
- No content can depend on hover or animation to become available.
- Ensure responsive reflow at 320px and 200% zoom.

### K. Performance requirements

- Keep the page useful when WebGL is disabled.
- Lazy-load the Three.js scene/chunk if it improves first content display.
- Provide a CSS glow/particle fallback on WebGL failure.
- Keep the particle count, DPR and shader workload adaptive.
- Reserve image sizes; optimize images and font weights.
- Avoid large third-party scripts and analytics by default.
- No perpetual rendering while the tab is hidden or the user has reduced motion enabled.
- Aim at good Core Web Vitals where measurable: LCP ≤ 2.5s, INP ≤ 200ms and CLS ≤ 0.1 at the 75th percentile for real-user data. Lab tests are not field data.
- Run Lighthouse or an equivalent tool, record actual scores, and fix layout shifts, long tasks and broken assets.

### L. Technical architecture

Use React + TypeScript + Vite unless repository inspection shows a better existing frontend that should be preserved. Use CSS variables as the token source of truth. Use current supported stable dependency versions and commit the lockfile. Keep Motion and Three.js as the motion stack; do not add multiple overlapping animation frameworks.

Use Radix/shadcn primitives selectively for accessible controls. Do not wrap everything in a generic component library style. The UI must reflect the custom FlashFile design system.

If serving through the existing Python backend, build the frontend into a known production directory, mount hashed assets under a dedicated static prefix, and serve the built HTML only for public marketing routes and browser HTML requests. Preserve the current root JSON/status contract for non-HTML requests. Avoid a catch-all route that steals `/status`, `/watch`, stream/range, webhook, admin or API requests. Add explicit route regression tests.

If the frontend is separately hosted, configure a canonical public site URL and API/status base URLs. Do not add unnecessary CORS coupling.

### M. SEO and content truth

Implement real title/description, canonical URL, Open Graph metadata, a verified social preview image, favicon, sitemap and robots behavior. Use structured data only where it describes actual software and real facts. Never invent ratings, prices, customer counts, product release data or availability figures.

Maintain a feature-evidence matrix. Every public capability claim must map to source or a live test. Unverified features must be omitted or documented as blocked for the maintainer, never promoted as complete.

### N. Security

- No bot token or private credential in frontend code, Vite variables or source maps.
- No arbitrary external redirect.
- No user-controlled external URL loaded without validation.
- No Telegram credentials collected by the site.
- No fake service status.
- No third-party tracker by default.
- Review CSP/security headers against the actual runtime; do not blindly paste a policy that breaks WebGL or hashed assets.
- Do not replace the project’s deployment container without understanding current runtime commands and secrets.

### O. Testing

Add or update:
- typecheck and lint scripts,
- unit tests for Telegram URL creation/config validation,
- feature evidence gating tests,
- motion/reduced-motion tests,
- component tests for mobile navigation and FAQ,
- Playwright E2E tests if available,
- route regression tests for root HTML/JSON behavior and all known critical existing service routes,
- link checking for internal routes and approved external links.

Run the exact commands and capture actual exit codes. Then perform browser checks at 1440x900, 1280x800, 768x1024, 390x844 and 320x700. If browser automation is not available, clearly distinguish automated code/test evidence from manual visual verification.

### P. Required work sequence

1. Inspect and report the repository state.
2. Audit real product claims and routes.
3. Build frontend scaffolding/build pipeline.
4. Create tokens and static page structure.
5. Add responsive sections and actual content.
6. Implement Telegram CTA/config utility.
7. Integrate scroll-synced particles and reduced-motion behavior.
8. Add accessible interactive components.
9. Add SEO/security/deployment wiring.
10. Write and run tests.
11. Build and inspect production output.
12. Report remaining blockers and release status.

Work in small changes. After each phase, report files changed, commands run, actual results and remaining work. Do not spend time generating a throwaway screenshot instead of building the implementation.

### Q. Definition of done

The work is done only when:
- the site has a unique and coherent FlashFile visual identity,
- it reads like a polished professional product page rather than generic AI output,
- the hero and sections explain only real supported capabilities,
- the Telegram bot CTA is correct and verified,
- download CTA is absent unless a verified app release is configured,
- particle animation syncs to document scroll in both directions,
- reduced motion, low-performance devices and missing WebGL are handled,
- desktop/mobile navigation works with keyboard and touch,
- there are no dead buttons or placeholder links,
- existing backend endpoints and JSON contracts are preserved,
- clean build, typecheck, lint and tests pass,
- actual browser and responsive checks are recorded,
- production build assets load correctly from the deployed path,
- no secrets enter public assets,
- documentation explains setup, configuration, test commands, deployment and rollback,
- any unverified bot/deployment/feature gate is explicitly marked blocked rather than described as complete.

### R. Final report format

Return a factual implementation report containing:
1. Summary of shipped behavior.
2. Major files created/changed.
3. Exact install/build/test commands and their exit results.
4. Frontend bundle size and actual visual/performance test results when measured.
5. Which public capabilities were verified and their evidence.
6. Telegram destination verification result.
7. Routes checked for regression.
8. Accessibility/reduced-motion checks.
9. Deployment state: local, staging or production. Never blur these states.
10. Known issues, missing configuration and blocked release gates.
11. What the maintainer must supply next, if anything.

Do not call the work production-ready if any required release gate remains unverified.

## MASTER PROMPT END
