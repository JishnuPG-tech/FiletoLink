# 11. Acceptance checklist and release gates

Mark each item `PASS`, `FAIL`, `BLOCKED` or `NOT APPLICABLE`. A blank item is not a pass.

## A. Product truth

- [ ] Product name and repository relationship are clear.
- [ ] Every advertised capability is backed by current source or a live verification.
- [ ] Unverified features are omitted from public claims.
- [ ] No fabricated metrics, users, testimonials, ratings, awards or uptime promises.
- [ ] Pricing/checkout is absent unless a real offer and working server-side flow exist.
- [ ] Download/install buttons are absent unless a real current release is configured.
- [ ] Product diagrams are accurate or visibly labeled as illustrative.
- [ ] Privacy/terms text reflects the real service and is reviewed before publication.

## B. Visual quality

- [ ] FlashFile design tokens are centralized as CSS custom properties.
- [ ] Default theme uses Obsidian / Crimson-Coral, with cyan as a restrained signal color.
- [ ] Typography roles and responsive sizes are consistent.
- [ ] Hero, workflow, feature, compatibility, FAQ and CTA sections have distinct compositions.
- [ ] Site avoids repetitive generic card grids and generic gradient blobs.
- [ ] Glass effects are selective and have solid fallbacks.
- [ ] Main content is readable regardless of particle state.
- [ ] All target viewport sizes were inspected.

## C. Particles and motion

- [ ] One canvas and one renderer are used.
- [ ] Background is behind the content and has `pointer-events: none`.
- [ ] Scroll progress is normalized, bounded and passed without per-pixel React re-renders.
- [ ] Scene changes are smooth, deterministic and reversible while scrolling up.
- [ ] Anchor navigation updates the scene without reset or flashing.
- [ ] DPR and particle count adapt to the device.
- [ ] Hidden tab pauses or reduces rendering.
- [ ] Scene responds to theme tokens without a full recreation.
- [ ] WebGL failure has a CSS fallback.
- [ ] Renderer, geometry, materials, observers and listeners are cleaned up.
- [ ] OS reduced-motion preference is honored from initial render.
- [ ] Manual motion control works and is easy to find.
- [ ] Reduced motion removes non-essential scroll-linked parallax and continuous movement.
- [ ] Native scrolling remains usable; no wheel hijacking or hidden scrollbar.

## D. Navigation and CTA

- [ ] Header CTA uses the verified public Telegram bot URL.
- [ ] Hero CTA uses the same central link utility.
- [ ] Final CTA uses the same central link utility.
- [ ] Start parameters are safe, non-sensitive and syntactically valid.
- [ ] Every internal anchor/route is valid and has correct scroll offset.
- [ ] No links use `href="#"` as a fake action.
- [ ] No unconfigured download/source/docs/contact links are rendered.
- [ ] External links use valid schemes and appropriate new-tab behavior.
- [ ] Telegram CTA was clicked on desktop and Android if available.

## E. Interaction and accessibility

- [ ] Skip link exists and works.
- [ ] Single H1 and logical heading hierarchy.
- [ ] Keyboard focus is visible in both themes.
- [ ] Text/control contrast is measured, not guessed.
- [ ] Header, mobile menu and FAQ work without a mouse.
- [ ] Escape closes the mobile menu and focus returns appropriately.
- [ ] Canvas is decorative to assistive technology.
- [ ] Product diagrams have text alternatives.
- [ ] No information is only visible on hover.
- [ ] Page works at 200% zoom and 320px width without unintended horizontal scroll.
- [ ] A manual reduced-motion option is available.
- [ ] No flashing content or auto-playing sound.
- [ ] Automated accessibility audit has no critical violations.
- [ ] Manual keyboard and screen-reader spot checks are recorded.

## F. Responsive and browser behavior

- [ ] 1440x900 verified.
- [ ] 1280x800 verified.
- [ ] 768x1024 verified.
- [ ] 390x844 verified.
- [ ] 320x700 verified.
- [ ] Current Chrome verified.
- [ ] Current Firefox verified if available.
- [ ] Safari/iOS verified if available.
- [ ] No clipped CTA, overlapped header or unreadable navigation.
- [ ] Browser back/forward and direct route reload behave correctly.

## G. Technical quality

- [ ] Package lock is committed.
- [ ] Clean install works.
- [ ] Type check passes.
- [ ] Lint passes.
- [ ] Unit tests pass.
- [ ] Browser/E2E tests pass where configured.
- [ ] Frontend production build passes.
- [ ] Production assets load from the actual base path.
- [ ] Console contains no critical errors.
- [ ] Internal and configured external links pass checks.
- [ ] No secrets or private tokens appear in static build assets or source maps.

## H. Existing service regression

- [ ] Root HTML request returns the intended marketing site.
- [ ] Root non-HTML/API request keeps the established JSON contract.
- [ ] HEAD behavior is intentional and verified.
- [ ] `/status` contract is preserved.
- [ ] Watch/player route is preserved.
- [ ] Stream and HTTP range behavior are preserved where used.
- [ ] Webhook path is preserved.
- [ ] Admin paths and authorization behavior are preserved.
- [ ] Existing health checks work.
- [ ] Unknown routes return a real 404 rather than a fake marketing success.

## I. Production, SEO and operations

- [ ] Canonical site URL is correct.
- [ ] Title, description, favicon and Open Graph metadata are correct.
- [ ] Open Graph image exists and is reachable.
- [ ] Sitemap/robots policy matches intended indexing.
- [ ] Structured data contains only verified facts.
- [ ] Security headers have been tested with WebGL and production assets.
- [ ] Static asset caching is correct.
- [ ] Staging verification is recorded if staging exists.
- [ ] Production verification is recorded if deployed.
- [ ] Rollback instructions exist.
- [ ] Build commit and actual test results are recorded.

## J. Final release decision

Release status:
- [ ] PASS: all required items pass and production config is verified.
- [ ] PASS WITH DOCUMENTED EXCEPTIONS: only approved non-critical items are open.
- [ ] BLOCKED: a primary CTA, product claim, route preservation check, required test or production configuration is not verified.

Any missing bot username, domain, release URL, legal review or deployed browser verification must be listed explicitly. Do not convert a blocked gate into a pass because the page looks finished.
