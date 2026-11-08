# 08. QA, accessibility and performance plan

## 1. Quality objective

The website must look premium and still behave like a reliable product interface. The particle effect must never reduce content access, hide controls or make the mobile experience worse.

## 2. Test matrix

Minimum viewport matrix:

| Name | Viewport | Key checks |
|---|---|---|
| Large desktop | 1440 × 900 | Hero hierarchy, particle composition, header spacing, section variety |
| Laptop | 1280 × 800 | Hero CTA visibility, layout rhythm, no overflow |
| Tablet portrait | 768 × 1024 | Heading wraps, navigation, canvas workload, section spacing |
| Mobile current | 390 × 844 | Primary CTA, mobile menu, readable copy, touch targets |
| Narrow mobile | 320 × 700 | No horizontal scroll, no clipped buttons or headings |
| Tall mobile | 430 × 932 | Correct section progress and no excessive empty space |

Minimum browser matrix:
- Current Chrome on desktop and Android.
- Current Firefox on desktop.
- Current Safari on iOS/macOS if available.
- Edge on Windows if the service audience uses it.

The exact version should be recorded during release testing rather than guessed in this document.

## 3. Functional checks

- Primary Telegram CTA appears in the header, hero and final CTA.
- Every placement uses the centralized link utility.
- Each generated Telegram URL has the right bot username and expected start parameter.
- Missing or invalid bot configuration prevents a false production-ready state.
- Every internal route and anchor works from a fresh page load.
- All navigation works using keyboard only.
- Mobile menu opens, closes with Escape, restores focus and closes after navigation.
- FAQ items open and close predictably.
- Motion control switches modes immediately and updates the canvas.
- Theme switch, if present, changes CSS colors and particle uniforms together.
- A missing Android release URL hides the download CTA.
- A failed status check never displays green/operational.
- Links that open a new tab use appropriate `rel` attributes.
- Existing backend/status/watch/stream/webhook/admin route contracts pass regression tests.
- There are no placeholder URLs, `href="#"` buttons, dead controls or console errors.

## 4. Accessibility checks

Target: WCAG 2.2 AA for the page and its controls, with additional support for the motion criterion beyond the basic minimum.

- One clear H1; headings follow a logical hierarchy.
- A skip link allows keyboard users to bypass navigation.
- Text and controls maintain measured contrast in each theme.
- Links and buttons are distinguishable without relying on color alone.
- Every interactive element is keyboard-operable and has a visible focus indicator.
- Focus order follows visual and semantic order.
- Mobile menu and accordion expose correct names and states.
- Canvas is decorative and ignored by assistive technology.
- Important product diagrams have equivalent text descriptions.
- Images have meaningful alt text or empty alt for purely decorative assets.
- No information appears only on hover.
- No autoplay audio or flashing effects.
- `prefers-reduced-motion: reduce` removes non-essential large movement.
- A manual motion control is present and easy to find.
- Text remains readable while the particle field is active.
- Zooming to 200% does not remove content or controls.
- At narrow widths, content reflows without horizontal scrolling except explicitly designed code snippets.
- Form fields, if any, have visible labels and useful error messages.

Run an automated audit, but do not treat its score as proof that all accessibility needs are met. Complete keyboard and screen-reader spot checks manually.

## 5. Performance targets

Aim for the “good” Core Web Vitals thresholds at the 75th percentile when field data becomes available:
- Largest Contentful Paint (LCP) ≤ 2.5 seconds.
- Interaction to Next Paint (INP) ≤ 200 milliseconds.
- Cumulative Layout Shift (CLS) ≤ 0.1.

These are targets, not a promise about every user’s device or network. If field data is unavailable, report lab results and do not present lab performance as real-user performance.

Suggested lab goals for the first release:
- Mobile Lighthouse Performance: 90+ where feasible without sacrificing accessibility; investigate any lower result.
- Accessibility: 95+ and no known critical issue.
- Best Practices: 95+ where compatible with the existing service.
- SEO: 90+ with valid metadata and no intentionally blocked indexable pages.

Avoid spending time optimizing to a score while real actions are broken. Functional and accessibility gates take precedence.

## 6. Performance budget

Suggested initial budgets, to be measured in the production build:
- Initial compressed JavaScript: target ≤ 220 KB gzip before optional route chunks where practical. If exceeded, report the actual number and split work.
- Three.js loaded as a separate/lazy chunk if this helps first content display.
- Avoid unnecessary video and huge hero bitmap downloads.
- Use AVIF/WebP for large raster imagery where the hosting pipeline supports them; preserve accessible fallback.
- Self-host only the font weights needed.
- Reserve image aspect ratios to avoid layout shifts.
- Avoid loading animation libraries multiple times through duplicate imports/bundles.
- Keep the particle scene to one canvas and one renderer.
- Mobile canvas DPR starts at no more than 1.25 unless measurement supports more.
- Avoid perpetual rendering when the tab is hidden or reduced motion is active.

Do not enforce an arbitrary bundle-size gate if the actual production output demonstrates a justified need; instead, identify the cause and keep non-critical sections lazy.

## 7. Particle performance tests

- Monitor FPS/frame timing on an ordinary laptop and a mid-range Android phone.
- Compare with the effect on and off.
- Test at DPR 1, 1.25, 1.5 and the actual device DPR cap.
- Test page resize, browser zoom, background tab, WebGL context loss and low-motion mode.
- Ensure the background does not create long tasks during ordinary scrolling.
- Ensure no repeated geometry/material allocation occurs per animation frame.
- Confirm full disposal on route unmount.
- Confirm theme change does not reconstruct the scene.

If the effect creates a measurable interaction delay or scrolling stutter, reduce particles, simplify the shader, lower DPR or pause updates before adding more tuning complexity.

## 8. Security and robustness QA

- No secret in the built JS or source maps.
- No arbitrary user-controlled redirect.
- External links use approved schemes and domains.
- No third-party script loaded without a documented reason.
- No user-provided filename or URL inserted into HTML unsafely.
- All API response data is handled defensively.
- No fake green status during errors.
- Network failures degrade gracefully.
- CSP and security-header compatibility are checked against the actual server, not copied from a generic template.

## 9. SEO and social preview

- Unique descriptive document title.
- Concise meta description describing the verified product.
- Canonical URL uses the real public host.
- Open Graph and social metadata point to an image that exists and matches the brand.
- Favicon is present and crisp on dark browser chrome.
- `robots.txt` and sitemap match the deployment.
- Structured data includes only accurate fields. Do not create fabricated aggregate rating or fake app offers.
- If `SoftwareApplication` schema is used, do so only if the product qualifies and all properties are real. Google does not guarantee a rich result.
- Verify the final page with search-engine preview/test tools where available.

## 10. QA report template

```text
Build commit:
Environment: local / staging / production
Build command and exit code:
Typecheck:
Lint:
Unit tests:
E2E tests:
Existing endpoint regression tests:
Desktop viewport checks:
Mobile viewport checks:
Keyboard checks:
Screen reader spot check:
Reduced motion:
WebGL fallback:
Telegram CTA verified:
Download CTA verified or intentionally absent:
Status behavior:
Lighthouse/PageSpeed results:
Known issues:
Blocked release gates:
Decision: PASS / PASS WITH DOCUMENTED EXCEPTIONS / BLOCKED
```
