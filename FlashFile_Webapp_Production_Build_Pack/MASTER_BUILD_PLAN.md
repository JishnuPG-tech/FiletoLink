# FlashFile complete production webapp build plan

This master document combines the key plan documents in one file. The standalone files remain available in the ZIP pack.


---

# FlashFile production webapp build pack

Version: 1.0  
Prepared: 7 November 2026  
Project: FlashFile, using the existing FiletoLink repository as the implementation source

## What this pack is

This is an implementation-ready product and engineering specification for a premium public website that explains FlashFile, demonstrates its real workflows, and sends users to the Telegram bot. It includes the visual system, motion/3D behavior, route and component specifications, backend integration plan, delivery sequence, tests, and one complete AI coding-agent prompt.

This pack is downloadable and stands alone. It does not require opening a GitHub issue or reading documentation hosted in a repository.

## Files in this pack

| File | Purpose |
|---|---|
| `01_PRODUCT_BRIEF.md` | Product goal, positioning, users, evidence rules, scope and success measures |
| `02_INFORMATION_ARCHITECTURE_AND_COPY.md` | Routes, page sections, content model, CTA behavior, draft copy and FAQ |
| `03_VISUAL_DESIGN_SYSTEM.md` | Color, typography, layout, surfaces, responsive behavior and Claude-style fallback |
| `04_PARTICLE_AND_MOTION_SPEC.md` | Scroll-synced Three.js particle system, movement map, transitions and reduced-motion behavior |
| `05_COMPONENTS_AND_INTERACTIONS.md` | Component inventory, interaction states, navigation, links, dialogs and product previews |
| `06_TECHNICAL_ARCHITECTURE.md` | Frontend stack, repository integration, route preservation, configuration and project structure |
| `07_IMPLEMENTATION_ROADMAP.md` | Ordered development phases, work products and exit criteria |
| `08_QA_ACCESSIBILITY_PERFORMANCE.md` | Automated/manual testing, WCAG-oriented checks, browser/device matrix and performance budget |
| `09_SECURITY_DEPLOYMENT_OPERATIONS.md` | Link safety, configuration, metadata, Docker/build/deploy and operational checks |
| `10_COMPLETE_AI_BUILD_PROMPT.md` | Master prompt for an AI coding agent to implement and verify the site in the actual repository |
| `11_ACCEPTANCE_CHECKLIST.md` | Release gate checklist and explicit definitions of done |
| `12_ENVIRONMENT_AND_LINKS.md` | Configuration template, Telegram deep-link rules and safe feature flags |
| `13_RESEARCH_REFERENCES.md` | Official source links that informed architecture, motion, accessibility and SEO decisions |
| `MASTER_BUILD_PLAN.md` | One continuous document for reading or giving to an implementation agent |

## Product definition

FlashFile is the product-facing name in this design brief. FiletoLink is the repository/project name. The site should act as a product showcase and trusted starting point, not pretend to be a full authenticated dashboard unless real backend functionality exists for that workflow.

The main action is **Open FlashFile on Telegram**. It must link to a verified bot URL configured at build time. A download button must only exist if a real, current release artifact is configured. A pricing or checkout area must only exist if actual pricing and a real checkout flow are supplied. Do not invent subscriptions, ratings, usage counts, privacy guarantees, service-level promises, or platform downloads.

## Critical accuracy rule

Some features are visible in the reviewed project context, including a Telegram-oriented file-link workflow, stream/watch routes, a status endpoint, playlist/batch-related UI, and aria2 command export. Before marketing any feature, the implementation agent must inspect the current source and deployed behavior. A feature that has not been verified must be marked as pending in the build notes and omitted from public claims until verified.

## Recommended visual direction

Default theme: **Obsidian / Crimson-Coral**. Use a near-black canvas, disciplined coral accent, selective electric-cyan signal color, large editorial typography, deliberate whitespace, thin technical dividers, and restrained glass surfaces. The particle system is a signature backdrop, not an excuse to put every component inside a translucent card.

Use the existing `webapp/src/components/canvas/TransmissionCore.tsx` when it exists in the target branch. Inspect it first, keep useful behavior, and improve it rather than replacing it blindly. The target repository snapshot previously had a particle component but did not have a complete Vite application shell. Reconfirm the current repository state before creating files.

## How to use this pack

1. Read this file and the product brief.
2. Give `10_COMPLETE_AI_BUILD_PROMPT.md` to the coding agent together with this entire pack.
3. Require the agent to inspect the repository and report current state before editing.
4. Implement in small, testable phases. Do not accept a pretty screenshot as proof of a working site.
5. Do not call the build production-ready until every release-gate item in `11_ACCEPTANCE_CHECKLIST.md` has passed.

## What this pack does not claim

The documents are a build specification. They are not proof that the webapp has already been implemented, built, tested in a browser, or deployed. Those actions must happen in the repository and deployment environment.


---

# 01. Product brief

## 1. Product and project

- Product name: **FlashFile**.
- Existing codebase/project: **FiletoLink**.
- Product type: Telegram-powered file access and link workflow, subject to verifying which capabilities are active in the current code and deployed environment.
- Deliverable: a premium, responsive, accessible public-facing product website.
- Primary outcome: a visitor understands the product, can verify what it does, and can open the official Telegram bot in one deliberate action.

## 2. Product statement

FlashFile should make the workflow around supported Telegram-hosted files easier to understand and use. The website explains the flow, shows real product evidence, documents supported paths, and directs the visitor to Telegram or another verified product surface.

Do not position it as a cloud drive, file host, transcoder, account platform, Android application, privacy product, or payment service unless the source and the live deployment substantiate that claim.

## 3. Experience principles

1. Product first. Explain what it does before showing implementation details.
2. Trust through evidence. Use real screenshots, accurate diagrams, working links, and explicit limitations. Do not fake testimonials, counters, badges, reviews, downloads, or status indicators.
3. One main action. Telegram is the primary conversion path. Other actions help the visitor learn or inspect the service.
4. Distinct visual identity. The interface should feel built for FlashFile rather than assembled from a generic SaaS template.
5. Performance before decoration. The 3D background is an enhancement. The full site must remain complete when WebGL is unavailable.
6. User-controlled movement. Scroll-linked particles and transitions need a clear reduced-motion mode and a visible motion toggle.
7. Honest product status. A visual mockup cannot masquerade as a functioning file picker, player, upload flow, or account dashboard.
8. Reuse working infrastructure. Do not disturb stream, watch/player, status, webhook, admin, or bot endpoints to make the marketing website easier to build.

## 4. Primary audiences

- Telegram users who want to understand how to use the bot.
- Existing users who need a quick return path to Telegram, help, or status.
- Technical users who want to understand supported workflows and compatibility.
- Maintainers who need a website that can be deployed with the existing service and maintained without a large CMS.

## 5. User journeys

### Journey A: new visitor

1. Opens the website.
2. Reads a clear hero statement and sees the main product workflow.
3. Checks features and limitations.
4. Clicks **Open FlashFile on Telegram**.
5. Telegram opens to the configured bot, with an optional, harmless attribution parameter such as `start=website_hero`.

### Journey B: visitor evaluating the product

1. Opens the website.
2. Reads “How it works.”
3. Reviews supported behavior and common questions.
4. Opens documentation or the source repository if configured.
5. Starts the bot after deciding it fits their use case.

### Journey C: returning user

1. Opens the site.
2. Uses the visible Telegram CTA or help/status link.
3. Does not have to scroll through the entire pitch to find the main action.

### Journey D: mobile user

1. Opens the site on a small screen.
2. Gets a fast, legible page with a lightweight particle layer or static fallback.
3. Uses a keyboard-accessible mobile menu and the same Telegram CTA.
4. Does not lose scroll position or content to cinematic transitions.

## 6. Product claims and evidence gates

The coding agent must create a `feature-evidence` table in its implementation notes, with a source file or live URL for every public claim.

| Capability | Current evidence status from the reviewed project context | Publishing rule |
|---|---|---|
| Telegram bot-based file workflow | Existing project purpose is Telegram oriented | Verify the current bot command flow and public bot username before writing exact instructions |
| Generated/shareable links | Present in the project’s intended workflow | Verify route format, link lifetime and error behavior before describing guarantees |
| Browser watch/player or streaming routes | Stream/watch route code exists in the reviewed context | Confirm what file types work and whether the endpoint is public before advertising compatibility |
| Playlist/batch builder | Related controls were present in a landing-page snapshot | Verify output format, limits, browser support, and whether the feature is still retained |
| aria2 command export | Related control was present in a landing-page snapshot | Verify its actual output and explain that it provides a command, not a download manager |
| Service status endpoint | `/status` or equivalent status route exists in the reviewed context | Verify response fields and make the website consume it only if the endpoint is intended to be public |
| Android download | No verified release artifact was established in the reviewed context | Hide the CTA until an official release URL, version and checksum/source are provided |
| Pricing / checkout | No verified paid-plan or checkout system was established | Do not display pricing cards, fake checkout buttons or “Upgrade” flows |
| Accounts / user dashboard | Not established | Do not invent sign-in, accounts, saved history, or user settings |
| Privacy/security guarantees | Must be verified against actual architecture | Do not use “end-to-end encrypted,” “zero knowledge,” “private by design,” or storage-retention claims without evidence |
| Usage metrics/testimonials | Not established | Do not fabricate numbers, star ratings, customer logos, quotes, or adoption claims |

This table is a gate, not marketing copy.

## 7. Scope

### Must ship

- Responsive landing/product page.
- Product overview and accurate feature descriptions.
- A visually clear how-it-works section.
- Primary Telegram CTA in the header, hero, and final CTA section.
- Verified supporting links to help/docs, status, source, privacy, and terms where available.
- A real contact/support route only if one is configured.
- Scroll-linked Three.js particle background that responds smoothly to document scroll and section progress.
- Motion-safe static fallback and a visible pause/reduce-motion control.
- Mobile navigation, clear focus states, accessible FAQ accordion, visible link destinations where appropriate.
- SEO title, description, canonical URL configuration, Open Graph metadata, social preview image, sitemap and robots policy.
- Production build and automated tests.
- Deployment route integration that leaves existing backend endpoints operational.

### May ship if the real product supports it

- Feature pages with detailed examples.
- Status indicator sourced from a documented public status endpoint.
- Android download button linked to a signed/current release.
- Changelog derived from real releases.
- Documentation route with real commands and examples.
- Video or product screenshot gallery.
- Optional usage/pricing details backed by actual product policy.

### Explicitly out of scope unless separately approved

- Fake browser-side bot simulation.
- A web dashboard that implies login or file history without a supported backend.
- File uploads into a new cloud storage backend.
- Automatic link validation of user-submitted URLs from the marketing site.
- Collecting Telegram credentials.
- Payment collection or subscription management without a real processor and server-side validation.
- Auto-playing sound, forced scroll, cursor replacement, scroll hijacking, full-screen popups on load, or motion that prevents reading.

## 8. Primary conversion and CTA taxonomy

Primary button label: **Open FlashFile on Telegram**.

Short label for a compact header: **Open bot**.

Secondary hero action: **See how it works**.

Other allowed actions when their destinations exist:
- **Read the guide**.
- **Check service status**.
- **View source**.
- **Download for Android** only when a verified release asset exists.
- **Open web player** only when the destination is real and supported.

Avoid vague button labels such as “Explore,” “Discover more,” “Get started now,” or “Learn more” when the destination can be stated precisely.

## 9. Success measures

Measure only what the deployment can accurately collect and only after reviewing privacy implications.

- Telegram CTA click-through rate.
- Clicks on documentation/help links.
- Successful navigation to a real status page.
- Broken internal/external links detected in CI.
- Core Web Vitals and frontend error rate.
- Percentage of users who can complete the page with keyboard-only navigation.

Do not add an analytics SDK by default. If analytics are requested, document what is collected, use privacy-respecting configuration, and make the privacy notice accurate.

## 10. Acceptance summary

The product site is not done merely because it renders. It must have accurate content, working real destinations, responsive layouts, scroll-linked but controlled 3D, a non-WebGL fallback, no critical accessibility issues, preserved backend endpoints, reproducible build instructions, passing tests, and a verified production build.


---

# 02. Information architecture and content specification

## 1. Site map

Keep the initial release compact. Do not create routes simply to make the product seem larger.

| Route | Page purpose | Status |
|---|---|---|
| `/` | Main premium product showcase | Required |
| `/#features` | Feature section anchor | Required |
| `/#how-it-works` | Workflow explainer | Required |
| `/#compatibility` | Supported workflows and constraints | Required if supported details are verified |
| `/#faq` | Common questions | Required |
| `/docs` | Practical usage guide | Required only if current instructions are available; otherwise link to an existing guide |
| `/status` | Existing public status endpoint/page | Preserve existing backend behavior. Do not replace with a fake status page |
| `/privacy` | Actual privacy notice | Required before adding analytics, cookies, or user-data collection. Must reflect real operations |
| `/terms` | Actual terms and limitations | Publish only after content is reviewed by the maintainer |
| `/changelog` | Verified release history | Optional, only if sourced from actual releases |
| `/download` | Verified software release landing route | Do not create until an artifact is available |

The main page can be a single high-quality long page. Do not force visitors through multi-page navigation if anchors are sufficient.

## 2. Header

Desktop layout:
- Left: FlashFile mark and wordmark.
- Center/right: Features, How it works, Compatibility, FAQ.
- Far right: primary button `Open bot` with Telegram icon.
- Header starts transparent over the hero; when scrolling, becomes a dark, lightly blurred surface with a 1px border.

Mobile layout:
- Wordmark left.
- Telegram CTA as the visible icon/button when width permits.
- Accessible menu trigger on the right.
- Menu opens in a compact overlay/sheet with a dark opaque base, not a translucent pane that harms contrast.
- Close on Escape and after selecting a route/anchor. Restore focus to the menu trigger.

The header must never cover anchor targets. Give sections `scroll-margin-top` equal to the header plus a small visual buffer.

## 3. Main page structure

Recommended order:

1. Announcement/status strip, only if useful and real.
2. Hero with product statement, subheading, primary/secondary CTA, product visualization and small proof label.
3. Product value strip containing 3 concise facts about what is actually supported. No vanity counters.
4. How it works: a 3- or 4-step visual flow from the source-verified workflow.
5. Feature deep dive: feature sections with alternating text and product-specific diagrams.
6. Playlist/batch workflow only if present and verified.
7. Watch/stream workflow only if present and verified.
8. Compatibility and limits: state supported routes/formats and what is not supported. Hide unverified claims.
9. Product preview: screenshots or an accurate in-DOM diagram based on source. Label a diagram as illustrative if it is not a live product surface.
10. FAQ: short, specific answers.
11. Final CTA section, with the same Telegram destination as the header and hero.
12. Footer with docs, source, status, privacy, terms, maintainer contact and current build version only where each is configured.

Do not make every section a rounded rectangle. Use full-width editorial layouts, thin dividers, inset diagrams, occasional glass panels, and changes in alignment to create hierarchy.

## 4. Proposed hero copy

Use this as a precise starting point. Adjust claims after inspecting the actual bot workflow.

Eyebrow: `TELEGRAM-POWERED FILE WORKFLOW`

Headline: `Your files. Easier to access through Telegram.`

Supporting copy: `FlashFile connects the supported file workflow to shareable links and useful playback or download paths. Start with the Telegram bot, then use the options your setup supports.`

Primary button: `Open FlashFile on Telegram`

Secondary button: `See how it works`

Microcopy: `Opens Telegram. No Telegram password is requested by this website.`

Important: keep the last line only if the site truly never requests or proxies Telegram credentials. The intended site should not ask for credentials at all.

Avoid unsupported claims like “instant,” “unlimited,” “private,” “secure,” “the fastest,” “works with every file,” or numeric speed/size limits unless measured and verified.

## 5. Hero product visualization

Preferred visual hierarchy:
- Back layer: dark 3D particle transmission core, subtle glow, section-linked state.
- Foreground: editorial headline, a narrow supporting paragraph, two clear buttons.
- Side or lower area: real screenshot or a clean illustrative sequence of the Telegram workflow.
- Small annotation: `BOT → SHAREABLE LINK → SUPPORTED DESTINATION`, but only after verifying this is the actual flow.

Do not build a fake file uploader with a `Browse files` button that cannot perform the action. Do not make an example URL look like a live generated link. If a simulated graphic is required, give it a visible `Illustrative workflow` caption and use non-routable example domains such as `example.invalid`.

## 6. How-it-works content model

Use four steps if the actual flow supports them; collapse to three if not.

1. **Open the bot**. The user launches the configured Telegram bot.
2. **Send or select supported content**. Explain the accepted input based on the current bot commands and help text.
3. **Get the supported output**. Describe exactly what is returned, including any limits or expiry behavior that exists in source.
4. **Use the result**. Explain browser viewing, downloading, playlist, or external-tool options only if the code supports them.

Each step should include:
- one sentence describing the action,
- one sentence describing what the user sees,
- one source-backed visual,
- a link to the detailed instructions if available.

## 7. Feature block patterns

### Shareable link

Title: `A link for the supported file workflow`

Body should explain what produces the link, whether it is public or tokenized, and any expiry/permission behavior only after checking implementation. Do not make permanence or privacy guarantees by implication.

### Browser playback / watch page

Title: `Open a supported playback path`

Body should list only verified formats and conditions. State if direct browser playback depends on the file codec, content type, range requests, or browser support. Do not say “plays everything.”

### Batch / playlist utilities

Title: `Prepare multiple items in one workflow`

Body should describe the precise list syntax, output format, item limit, and errors based on the actual utility. If the feature is not active, do not display it.

### Download-tool command export

Title: `Continue with your preferred download tool`

Body should explain that FlashFile prepares a command or list for an external tool. Do not claim to install, control or run the user’s download manager.

## 8. FAQ specification

Only publish the answer after source verification. Use direct answers, not vague marketing language.

- **How do I start?** Open the official configured Telegram bot and follow its current `/start` instructions.
- **Do I need to install a separate app?** Explain actual requirements. Do not claim that an Android app is available unless a current release artifact exists.
- **Which files are supported?** Link to a verified compatibility list. Avoid “all file types.”
- **Can I open results in a browser?** Explain the supported watch/link behavior and browser limitations.
- **Does the website ask for my Telegram login?** It should not. The CTA opens Telegram using a public deep link. No Telegram password or OTP should be collected by this website.
- **Are links permanent?** Answer from backend implementation. If retention or expiry is unknown, say that the current documentation does not specify it and do not promise permanence.
- **Is there a paid plan?** Show only if a real plan and policy exist. Otherwise omit the question or state a verified pricing status.
- **Where can I get help?** Link to a real help route, bot command, contact address, or issue page.
- **Where can I inspect the source?** Link to the configured repository URL if public.
- **What if the bot or link is unavailable?** Link to the real status route and explain any actual recovery guidance.

Do not publish more than 6–8 FAQ items on the first version unless genuine support evidence shows a need.

## 9. CTA placement and destinations

| Location | Label | Destination behavior |
|---|---|---|
| Header | `Open bot` | Configured Telegram bot URL with a safe placement start parameter |
| Hero primary | `Open FlashFile on Telegram` | Same verified bot destination |
| Hero secondary | `See how it works` | Scroll to the workflow section; preserve native keyboard/accessibility behavior |
| Feature module | `Read the guide` | Real guide route only |
| Compatibility area | `View supported options` | In-page section or real docs route |
| Status | `Check service status` | Existing verified public `/status` endpoint/page |
| Final CTA | `Open FlashFile on Telegram` | Same bot destination |
| Download block | `Download for Android` | Hidden until official artifact URL, version and integrity details are configured |
| Source footer | `View source` | Current canonical repository URL from config |

All buttons must be actual links for navigation. Use a `<button>` only for an in-page state change. External destination links should be clearly indicated when needed and tested.

## 10. Content tone

- Concrete, technical but accessible.
- One claim per sentence.
- Explain what a user does and what happens next.
- Avoid invented customer outcomes and generic claims such as “unlock your productivity,” “seamless experience,” “next-generation platform,” “all in one,” “revolutionary,” and “built for everyone.”
- Do not use emojis as the main icon system.
- Do not call the website “AI-powered.” There is no requirement to add AI.
- Do not copy ChatGPT’s actual design or text. Match the quality of its product clarity, not its brand.


---

# 03. Visual design system

## 1. Creative direction

Default visual identity: **Obsidian / Crimson-Coral**. The page should look like a carefully art-directed file utility with a technical edge, not a generic AI SaaS landing page.

Visual cues:
- Particle reference: Particle Love “The Spirit” by Lusion. Recreate the visual concept in the project’s own Three.js scene; make the form respond to scroll progress and recolor through FlashFile tokens. Do not paste a generic particles plugin into an otherwise generic template.
- Near-black background with restrained depth and fine surface texture.
- Coral as the primary action color.
- Cyan as an occasional transmission/status signal, not a second primary accent.
- Editorial serif headline paired with a clean sans-serif for functional text.
- Technical micro-labels, narrow dividers and precise alignment.
- Large open areas so the particle field can breathe.
- Product diagrams and real screenshots instead of stock-photo hero art.
- Glassmorphism only where it communicates layering, such as the top navigation or a compact floating control.

Avoid:
- An entire page made of the same 3-column card grid.
- Purple-blue gradient blobs.
- Floating random glass cards that do not represent product concepts.
- Neon borders around every control.
- Fake terminal windows, fake analytics dashboards, fake counters and fake user avatars.
- Overuse of pill badges.
- Scroll animations that make the content harder to read.

## 2. Color tokens

Use CSS custom properties as the source of truth. Do not duplicate hex values across component styles.

```css
:root {
  color-scheme: dark;
  --ff-bg: #08090D;
  --ff-bg-raised: #0D0F15;
  --ff-surface: #11131B;
  --ff-surface-strong: #171A23;
  --ff-surface-glass: rgba(17, 19, 27, 0.72);
  --ff-border: rgba(248, 250, 252, 0.10);
  --ff-border-strong: rgba(248, 250, 252, 0.18);
  --ff-text: #F8FAFC;
  --ff-text-secondary: #B5BCC9;
  --ff-text-muted: #7F899B;
  --ff-accent: #FF3B5C;
  --ff-accent-hover: #FF5570;
  --ff-accent-deep: #E02447;
  --ff-accent-soft: rgba(255, 59, 92, 0.13);
  --ff-signal: #38BDF8;
  --ff-signal-soft: rgba(56, 189, 248, 0.10);
  --ff-success: #48D6A0;
  --ff-warning: #F6C56B;
  --ff-danger: #FF647C;
  --ff-particle-primary: #FF3B5C;
  --ff-particle-secondary: #E02447;
  --ff-particle-highlight: #38BDF8;
  --ff-focus-ring: #8BD7FF;
}
```

Contrast requirements:
- Do not use `--ff-text-muted` for small body copy on the main background unless actual contrast is measured and meets the chosen WCAG target.
- All body text and functional controls must be legible without needing the background animation.
- Text on a coral button must be tested. Prefer white text only if measured contrast supports it; otherwise use a dark label with an accessible coral shade.
- Color cannot be the only way to communicate status.

## 3. Claude-style fallback theme

This is an optional alternative visual theme, not a second brand identity that appears randomly. Apply it through `[data-theme="claude-editorial"]` and test every interactive state.

```css
[data-theme="claude-editorial"] {
  --ff-bg: #171512;
  --ff-bg-raised: #1D1A16;
  --ff-surface: #24201B;
  --ff-surface-strong: #2B261F;
  --ff-surface-glass: rgba(36, 32, 27, 0.78);
  --ff-border: rgba(244, 237, 226, 0.12);
  --ff-border-strong: rgba(244, 237, 226, 0.22);
  --ff-text: #F4EDE2;
  --ff-text-secondary: #D0C4B4;
  --ff-text-muted: #A99B8A;
  --ff-accent: #D97757;
  --ff-accent-hover: #E58A69;
  --ff-accent-deep: #B85F3A;
  --ff-accent-soft: rgba(217, 119, 87, 0.14);
  --ff-signal: #F2BA93;
  --ff-signal-soft: rgba(242, 186, 147, 0.10);
  --ff-particle-primary: #D97757;
  --ff-particle-secondary: #B85F3A;
  --ff-particle-highlight: #F2BA93;
  --ff-focus-ring: #FFD6B9;
}
```

The default should remain the FlashFile Obsidian / Crimson-Coral theme. The fallback can be developer-configurable or exposed as a user theme switch only if it is fully implemented and persisted without tracking the user.

## 4. Typography

Use a four-role type system.

- Display/headline: Instrument Serif. Use for the main hero heading and perhaps one short editorial accent line. Do not set all UI copy in serif.
- Interface/body: Plus Jakarta Sans.
- Neutral fallback: Inter or system sans-serif.
- Technical labels/code: JetBrains Mono.

Load licensed font files locally when practical. If loading from a font provider, use only required weights, provide sensible fallbacks, and ensure font failure does not move major content dramatically. Do not use a font family without verifying its license and weight availability.

Suggested scales, responsive with `clamp()`:

| Role | Desktop target | Mobile target | Notes |
|---|---:|---:|---|
| Hero | 4.5–6rem | 2.8–3.5rem | Tight but readable line-height; control measure to 10–13 words per line |
| H2 | 3–4rem | 2.15–2.7rem | Avoid same size for all sections |
| H3 | 1.35–1.7rem | 1.2–1.45rem | Product feature titles |
| Body large | 1.125–1.25rem | 1–1.1rem | Supporting copy |
| Body | 1rem | 1rem | 1.55–1.75 line-height |
| Micro-label | 0.7–0.8rem | 0.68–0.75rem | Use uppercase sparingly, add letter spacing |
| Code | 0.85–0.95rem | 0.8–0.9rem | Wrap or horizontally scroll safely |

Do not use micro-labels as the only explanation for an important feature.

## 5. Layout and spacing

- Maximum main content width: 1200–1280px.
- Large hero maximum width: about 1440px.
- Standard page gutters: 5–6vw desktop, 24px tablet, 18–20px narrow mobile.
- Grid: 12 columns on wide screens; 8 or 4 on smaller viewports.
- Base spacing scale: 4, 8, 12, 16, 24, 32, 48, 64, 88, 112, 144px.
- Section vertical rhythm: 112–160px desktop; 72–96px mobile.
- Body reading measure: 60–72 characters per line.
- Buttons must be at least 44px high on touch screens; do not compress the main CTA to fit the header.

Use `min()`, `max()` and `clamp()` to keep content flexible. Avoid hard-coded viewport-height layouts that clip content on mobile browser chrome changes.

## 6. Surface and glass rules

Glass should be used selectively:
- Header while scrolled.
- Compact motion-control pill.
- One product status or workflow panel where depth improves the story.

Glass recipe starting point:

```css
.surface-glass {
  background: var(--ff-surface-glass);
  border: 1px solid var(--ff-border);
  backdrop-filter: blur(16px) saturate(125%);
  -webkit-backdrop-filter: blur(16px) saturate(125%);
  box-shadow: 0 18px 52px rgba(0, 0, 0, 0.18);
}
```

Provide a solid background fallback when `backdrop-filter` is unavailable. Do not put body copy directly on top of the particle canvas without a stable contrast overlay.

## 7. Buttons

### Primary
- Coral background.
- High contrast label.
- Telegram icon aligned with label, not larger than the text.
- Horizontal padding 20–24px; min height 48px.
- Hover: slightly brighter coral and subtle 1–2px lift, not a large scale effect.
- Active: reset the lift and use a clear pressed state.
- Focus-visible: 2–3px ring with visible offset.
- Loading state only when a real asynchronous action exists.

### Secondary
- Transparent/dark raised surface.
- Thin border.
- High contrast label.
- No false disabled appearance when it is a navigation link.

### Text link
- Underline on focus and hover or use another visible indicator. Never rely on color alone.

Use anchor elements for navigation; use button elements for true in-page actions.

## 8. Icons and product graphics

- Use one consistent icon library, preferably Lucide React, for standard controls.
- Use a custom SVG mark for the FlashFile brand if the source logo exists. Do not invent a misleading Telegram logo.
- Prefer line icons with consistent stroke weight.
- Product diagrams should be built from actual workflow concepts: Telegram entry, link result, supported playback/download destination. Do not create fictional server graphs, users online counts, bandwidth metrics, or analytics panels.
- Use actual product screenshots supplied by the maintainer. If unavailable, create a schematic diagram with a visible “Illustrative workflow” label.

## 9. Background rules

Layering order:
1. Base background.
2. Soft static radial ambient light.
3. Particle canvas with pointer events disabled.
4. Optional section-local vignette/gradient to keep text readable.
5. Content and controls.

The canvas must never capture pointer or touch events. The site remains readable if the canvas is removed. Keep text and buttons at a higher stacking level than all decorative layers.

## 10. Responsive visual behavior

- Wide desktop: spacious hero, expressive typography, full particle field, two-column feature storytelling where appropriate.
- Small laptop/tablet: keep heading and CTA visible without requiring the user to scroll before understanding the product. Reduce particles and glows.
- Mobile: stack content, limit each text line, reduce particle count, remove major background movement, use solid-backed mobile menu, and preserve native scrolling. Avoid horizontally scrolling feature cards.
- Reduced-motion: no parallax or large scroll-linked translation. Keep content visible without entrance animations.
- Forced-colors/high contrast: ensure controls, borders, focus and labels remain detectable.

## 11. Visual quality bar

Every section must have its own reason to exist and its own composition. Vary text alignment, image position, diagram structure and negative space. Repeated cards may be appropriate for a small feature list but must not dominate the full site. Review at 1440x900, 1280x800, 768x1024, 390x844 and 320x700.


---

# 04. 3D particle and motion specification

## 1. Purpose

The particle field is FlashFile’s signature visual element. Use Particle Love’s “The Spirit” as the primary visual reference for expressive volumetric particles and a living, sculptural field. The Lusion/Particle Love project page identifies “The Spirit” as one of its WebGL particle experiments, and the Google Experiments archive describes Particle Love as a WebGL particle demo collection. Reference the quality, depth and sense of flow. Rebuild the effect inside this project with the existing Three.js component, FlashFile CSS theme tokens and scroll-driven uniforms. Do not hotlink an unverified third-party script, scrape the demo, or assume third-party source code is licensed for reuse.

The field represents files and signals moving through a workflow. It should respond to scroll progress and section context while remaining behind the product content.

The effect must feel considered and continuous. It must not turn the page into a motion demo, obscure the copy, steal focus, block scrolling or consume most of the mobile device’s GPU budget.

## 2. Implementation decision

Use the existing `webapp/src/components/canvas/TransmissionCore.tsx` if present in the target branch. Inspect the component and preserve valid lifecycle safeguards. The reviewed snapshot used direct Three.js rather than React Three Fiber. Continue with direct Three.js unless the existing app already depends on React Three Fiber and there is a clear reason to integrate with it. Do not add two competing 3D frameworks.

Use:
- Three.js for the particle scene, camera and shader uniforms.
- Motion for React (`motion/react`) for DOM reveal/transition and scroll progress hooks.
- A small shared scroll-state bridge or ref so the React tree does not re-render on every frame.
- Native document scroll as the default. Add Lenis only if integration tests prove it stays in sync with native inputs, anchor navigation, touch scrolling, reduced-motion and keyboard navigation. Do not combine multiple independent scroll engines.

## 3. Scene composition

### Initial hero state

- A central asymmetrical particle shell, not a generic perfect glowing sphere.
- Particles form a subtly open, orbital flow, with a few long trajectories that suggest transmission.
- Primary particles use FlashFile coral; a low proportion use deep coral; cyan appears only as a signal highlight.
- The foreground hero content remains the focal point.
- Ambient glow is broad and dim. Avoid hard neon bloom.

### Scroll progression

The scene should echo the organic, volumetric movement of Particle Love “The Spirit”, then evolve as the visitor reaches each page chapter:

- **Progress 0.00–0.18, Hero:** contained particle core, slow orbital rotation, low velocity.
- **Progress 0.18–0.38, How it works:** particles open into directional paths, hinting at a transfer from origin to result.
- **Progress 0.38–0.62, Features:** some paths become parallel and organized; light points form a restrained network.
- **Progress 0.62–0.82, Compatibility/details:** particle cloud contracts and shifts laterally to clear content. Do not dim text contrast.
- **Progress 0.82–1.00, Final CTA/footer:** trajectories converge and settle into a compact core. Keep enough negative space for the CTA.

These are design states, not separate scene reloads. Interpolate uniforms and object transforms so the transition is continuous. Never jump to a new shader or recreate the renderer each time a section enters view.

## 4. Scroll-coupled parameters

The scene should receive normalized `scrollProgress` in the range 0 to 1 and optional `sectionProgress` values. Pass a value through a ref or update uniform fields directly; do not set React component state every animation frame.

Proposed uniforms:

- `uTime`: elapsed time, clamped or wrapped safely.
- `uScrollProgress`: normalized document scroll progress.
- `uSectionPhase`: smoothed section target.
- `uPointer`: normalized mouse/touch position where supported; effect is very subtle and disabled on coarse pointer devices.
- `uColorPrimary`: `--ff-particle-primary`.
- `uColorSecondary`: `--ff-particle-secondary`.
- `uColorHighlight`: `--ff-particle-highlight`.
- `uMotionScale`: 1.0 normally, 0.25 in low-motion mode, 0 for a static view.
- `uViewport`: actual render size for point scale.

Scroll-to-scene behavior:
- Rotate the particle group slowly as the page scrolls, within a bounded range.
- Change trajectory spread using a smooth interpolation curve.
- Move the camera only a small amount; avoid fast zooming toward the viewer.
- Change the particle flow direction between sections.
- Use scroll velocity only as a bounded, short-lived secondary input. Do not create aggressive overshoot when the user scrolls quickly.
- The scene state at any scroll position must be deterministic enough that moving the user up and down does not accumulate drift.

Example mapping concept:

```ts
// Pseudocode: use a smoothed input and derive state from current progress.
const p = clamp(scrollProgress, 0, 1);
const section = smoothstep(0, 1, p);
rotationY = baseRotation + (p * Math.PI * 0.65);
spread = mix(0.72, 1.12, section);
flowAngle = mix(-0.25, 0.65, section);
```

This is a conceptual mapping, not a required literal implementation. Use the same normalized values for forward and backward scrolling. Do not add randomness to the layout on every frame.

## 5. Scroll progress calculation

Use `useScroll()` from Motion for React or a lightweight passive scroll observer. Normalize progress as:

`scrollProgress = scrollY / max(1, documentHeight - viewportHeight)`

Requirements:
- Update the latest value without causing React re-render per pixel.
- Clamp to `[0, 1]`.
- Handle page resize and content/font changes.
- If the page is shorter than the viewport, use progress `0`.
- Honor browser back/forward and hash-anchor navigation.
- Use one source of truth. If Lenis is introduced, derive particle progress from the same scroll state Lenis drives.

## 6. Scroll-triggered DOM animation

Use Motion for React for restrained reveal and interaction transitions.

Approved patterns:
- A section heading reveals with opacity from 0 to 1 and vertical translation no greater than 12–16px.
- A workflow connector draws using scale or stroke progress.
- A feature image reveals with a subtle mask/opacity transition.
- A small product status dot fades between real states.
- An active section indicator changes state based on actual section visibility.

Avoid:
- Large text sliding 100px from the side.
- Animating every word or character in body text.
- Long, staggered reveals that delay access to information.
- Zooming the full page or scaling text blocks on scroll.
- Sticky sections that trap the user for multiple viewport heights.
- Auto-playing carousel motion.

Every essential text and control must remain available when animations are disabled.

## 7. Timing and easing

- Button hover: 120–180ms.
- Menu and accordion: 160–240ms.
- Small reveal: 350–550ms.
- Section state smoothing: 450–800ms equivalent, adjusted to avoid visible lag.
- Avoid a page-load intro that blocks access to content.
- Use a small, consistent easing family, such as a restrained ease-out and a smooth spring for physical interactions.
- Do not animate large blur radii on every frame. Prefer opacity and transform for DOM elements.

## 8. Performance budget and adaptive detail

Initial particle caps to benchmark:
- Narrow mobile: 100–160 points.
- Tablet/coarse hardware: 180–300 points.
- Desktop: 360–650 points.

These are caps, not guarantees. Benchmark on actual devices. If the current shader handles more efficiently and measurement supports it, adjust deliberately.

Renderer requirements:
- One WebGL renderer instance per mounted canvas.
- Limit device pixel ratio (start at 1.25 for mobile and 1.5–1.75 for desktop; benchmark).
- Use `renderer.setAnimationLoop()` or a well-managed animation frame loop with exact cleanup.
- Avoid allocating new vectors, arrays, materials or objects every frame.
- Pause rendering when the document is hidden.
- Consider pausing or reducing update frequency when the canvas is outside the relevant visible region.
- Listen for WebGL context loss and fail back to CSS without crashing the page.
- Disconnect `ResizeObserver`, `IntersectionObserver`, theme observers and event listeners on unmount.
- Dispose of geometries, materials, textures and the renderer at teardown.
- Avoid expensive full-screen post-processing by default.

## 9. Theme synchronization

Read the current colors from CSS custom properties. Do not hardcode colors only inside GLSL.

When `data-theme` or theme-related styles change, update uniforms using a `MutationObserver` or an explicit theme event. If parsing a CSS color is needed, normalize the supported color format in one helper and fail safely to the default tokens. Avoid rebuilding the whole scene when only colors change.

Theme mapping:
- `--ff-particle-primary` → main point color.
- `--ff-particle-secondary` → secondary flow color.
- `--ff-particle-highlight` → restrained signal points.
- `--ff-accent-soft` or dedicated particle glow token → CSS ambient glow.

## 10. Reduced motion and user controls

Implement both:
1. OS preference support with `prefers-reduced-motion: reduce`.
2. A persistent, visible page control named **Motion: On/Reduced** or an equivalent accessible switch.

When reduced:
- Stop continuous particle rotation or render a static frame.
- Remove scroll-driven camera shifts and large parallax.
- Disable large reveal transforms.
- Keep the same information and layout.
- Use a CSS radial glow or a static particle snapshot if WebGL is not required.
- Use the browser’s native scroll behavior instead of forcing smooth scroll.

If the visitor manually selects a setting, persist it locally only if desired. No account or tracking is required. The manual preference should take priority over the system only when explicitly chosen. Provide a clear way to revert to “System”.

## 11. Fallback behavior

Fallback order:
1. WebGL particle scene if supported and enabled.
2. Static CSS radial gradients with a few CSS-rendered points if WebGL fails.
3. Plain background token if any decorative effect fails.

The page must never show a persistent error overlay because WebGL cannot initialise. Text and buttons must be unaffected.

## 12. Smooth scroll policy

Default: native document scrolling with `scroll-behavior: smooth` only when motion is allowed. Anchor links must remain standard links and work with keyboard and browser history.

Optional Lenis integration is allowed only if all of the following are demonstrated:
- no scroll lock,
- no broken anchor focus,
- no broken wheel, trackpad or touch behavior,
- no mismatch between page movement and particle uniforms,
- disabled in reduced-motion mode,
- no competing animation loop,
- no Safari/mobile scroll regression.

Do not hide the scrollbar or intercept wheel events to create artificial cinematic movement.

## 13. Motion acceptance tests

- Scroll down slowly, quickly and in reverse. Particle states remain smooth and reversible.
- Jump to a section using an anchor. Scene progress catches up without a flash or reset.
- Resize while halfway down the page. Canvas size, text and progress remain correct.
- Disable WebGL. The page remains usable.
- Turn off motion from the page control. Scroll-linked movement stops and the setting is announced to assistive technology.
- Enable OS reduced-motion before opening the site. No large movement runs on initial load.
- Leave the tab hidden and return. No runaway rendering loop or giant time jump occurs.
- Open on a low-powered mobile device. The canvas does not prevent text, buttons or scrolling from responding normally.


---

# 05. Components and interaction contracts

## 1. Component inventory

### App shell

- `App`: route and theme boundary.
- `SiteHeader`: logo, desktop navigation, primary Telegram CTA and mobile menu trigger.
- `MobileNav`: accessible drawer/sheet with Escape, focus management and close-on-navigation.
- `SiteFooter`: only real routes and configured external destinations.
- `ScrollProgress`: thin top progress indicator, optionally visible after the hero.
- `MotionPreferenceControl`: explicit motion mode control.
- `TransmissionCore`: Three.js particle background; purely decorative and hidden from assistive technology.

### Page composition

- `HeroSection`: headline, supporting copy, primary/secondary action, verified product visualization.
- `ValueStrip`: three concise, source-backed capabilities or design facts.
- `WorkflowSection`: numbered steps with a clear origin-to-output diagram.
- `FeatureSection`: reusable structure but varied per-section art direction.
- `WorkflowPreview`: real screenshot or clearly labelled illustrative diagram.
- `CompatibilitySection`: supported inputs/output and documented constraints.
- `FaqSection`: semantic accordion.
- `FinalCtaSection`: final primary action with short copy.
- `PrivacyAndLimitationsNote`: where necessary, explain link expiry, data handling or support limits based on actual implementation.

### Shared UI

- `ButtonLink` for navigation links styled as buttons.
- `IconButton` with required accessible label.
- `SectionEyebrow` and `SectionHeading`.
- `FeatureDiagram` with text alternative.
- `FaqItem` implemented using accessible primitives.
- `ExternalLink` with correct target/rel settings when opening new tabs.
- `StatusBadge` only when it displays a real state backed by a source.

Do not add a component library wrapper for every one-line HTML element. Keep the design system small and reusable.

## 2. Interaction states

Every interactive element must define:
- default,
- hover where hover exists,
- focus-visible,
- active/pressed,
- disabled only when genuinely unavailable,
- loading only for asynchronous work,
- success/error when the action can actually succeed or fail.

A navigation link must not simulate a loading spinner. The Telegram link should navigate immediately; the site must not claim that the bot started successfully because it cannot verify the Telegram client’s outcome.

## 3. Telegram destination logic

Use one utility to create Telegram links. Never hardcode a different bot URL in several components.

Inputs:
- configured canonical bot username or bot URL,
- optional placement key such as `website_header`, `website_hero`, `website_features`, `website_footer`,
- optional safe deep-link parameter.

Rules:
- Use only the configured official bot username/URL supplied by the maintainer.
- Use HTTPS `https://t.me/<bot_username>` for the public web CTA.
- The `start` value must be short, non-sensitive, and compatible with Telegram’s allowed characters. Example: `website_hero`.
- Do not encode user data, email addresses, URLs with secrets, file IDs, or tracking identifiers into the start parameter.
- Validate at build/config time that the bot username is a plausible public bot username and the URL resolves to the expected domain.
- If the bot URL is missing, development may show a clear warning state. A production build must fail its configuration validation or hide the CTA with a visible release-blocking check. Never use a made-up username.
- Open a new tab only if that behavior is intentional. If using `target="_blank"`, set `rel="noopener noreferrer"`.
- Check the destination by opening it on desktop and Android. A website cannot guarantee that Telegram is installed.

## 4. Download and install CTA logic

A download button exists only when all are configured:
- verified download/release URL,
- product/platform label,
- current version and release date if shown,
- file size if shown,
- checksum/signature if the project provides one,
- platform compatibility notes.

Never use a fake `#download` destination. If no app release is available, omit the download button rather than showing a disabled marketing control.

## 5. Product diagram behavior

Product previews are explanatory visuals, not fake product functionality.

Allowed:
- Diagram with a source card, transfer path and output card.
- Real screenshot with descriptive alt text.
- Tabs that switch between actual screenshot variants.
- Copy buttons for real documented commands only.

Not allowed:
- A fake link generator that always shows success.
- A fake file upload control with no backend.
- A fake progress bar that runs regardless of an actual request.
- A fake service-status dot that is always green.
- Buttons such as “Play demo,” “Generate link,” or “Start download” unless they trigger a real action in the available code.

## 6. FAQ accordion

- Use a documented accessible accordion primitive, such as Radix/shadcn where appropriate.
- Each trigger must be a real button.
- Provide visible focus.
- Support keyboard navigation according to the primitive’s behavior.
- Do not automatically open/close items based on scroll.
- Keep answer content available to search engines and screen readers.
- Avoid nested interactive elements inside a trigger.

## 7. Mobile navigation

- Menu trigger has an accessible name, `aria-expanded` and `aria-controls`.
- Opening the menu moves focus predictably.
- Closing by Escape restores focus to the trigger.
- Menu links have an adequate touch target.
- If implemented as a modal sheet, prevent background focus while open and restore focus on close.
- Do not rely on a hover state to reveal navigation.

## 8. Scroll and section navigation

- Anchor links update the URL hash and support browser history.
- Add `scroll-margin-top` to each section.
- Use `IntersectionObserver` or Motion’s in-view APIs for active-section indication.
- The active marker is decorative. Screen-reader users can use the same ordinary anchors.
- Do not set `tabindex` on every section. Use logical headings and standard focus behavior.

## 9. Theme and motion settings

If theme switching is exposed:
- The page and particle uniforms update together.
- Contrast is checked in both themes.
- Theme preference is stored locally, not on a server.
- The default stays Obsidian / Crimson-Coral.

If motion preference is exposed:
- Use a real toggle or button with accessible text.
- Reflect the current state visually and programmatically.
- Keep the setting functional when WebGL is already unavailable.
- If manual selection is stored in local storage, handle storage access failures gracefully.

## 10. Errors and edge cases

- If a configured external link is invalid, fail the build or show a clear development warning.
- If a status endpoint is unavailable, show `Status unavailable` rather than a green/healthy state.
- If the particle system fails, switch to the fallback with no blocking error.
- If fonts fail, retain layout using fallbacks.
- If a screenshot fails to load, show a designed fallback and accessible label.
- If a user has JavaScript disabled, critical content must still be discoverable where the chosen rendering architecture allows it. At minimum, provide server-generated initial metadata and a nonblank fallback message if JavaScript is required.


---

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


---

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


---

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


---

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


---

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


---

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


---

# 13. Research references

These official references informed the implementation choices. Verify current API details against the documentation during development, especially if dependencies or framework versions change.

## Animation and scroll

- Motion for React, official docs: https://motion.dev/docs/react
- Motion scroll animations, official docs: https://motion.dev/docs/react-scroll-animations
- Lenis smooth scroll, official site: https://lenis.dev/
- Three.js `WebGLRenderer`, official docs: https://threejs.org/docs/pages/WebGLRenderer
- Particle Love “The Spirit” visual-reference context from its creator’s project page: https://v2.lusion.co/work/particle-love/
- Particle Love archived by Google Experiments: https://shop.experiments.withgoogle.com/particle-love
- Particle Love live experience: https://particle-love.com/

Design implication: use Motion’s scroll-linked values for DOM/progress effects; update Three.js uniforms through refs instead of causing React renders at every scroll event. Use one renderer, cap device pixel ratio, dispose resources, and keep scrolling native unless an added scroll engine is justified by tested behavior.

## Accessibility and motion

- W3C: Understanding WCAG 2.2 success criterion 2.3.3, Animation from Interactions: https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions
- MDN: `prefers-reduced-motion`: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/prefers-reduced-motion
- Radix Primitives accessibility overview: https://www.radix-ui.com/primitives/docs/overview/accessibility
- W3C WCAG 2.2 quick reference: https://www.w3.org/WAI/WCAG22/quickref/

Design implication: user control over non-essential motion is important, especially for parallax and large scroll-linked movement. Keyboard navigation, focus management and semantic states should use accessible primitives where suitable.

## Frontend build

- Vite getting started: https://vite.dev/guide/
- Vite production build guide: https://vite.dev/guide/build
- Official shadcn/ui docs: https://ui.shadcn.com/docs

Design implication: use a reproducible frontend build with a committed lockfile. Verify the correct base path for nested deployments. Use custom tokens to define the actual FlashFile identity, even when starting from reusable UI primitives.

## Telegram links

- Telegram Bot Features / Deep Linking: https://core.telegram.org/bots/features
- Telegram API deep links: https://core.telegram.org/api/links
- Telegram Bot API: https://core.telegram.org/bots/api

Design implication: use public HTTPS bot links and safe start parameters only. Never expose bot tokens in browser code or include sensitive data in link parameters.

## Security

- OWASP Application Security Verification Standard: https://asvs.owasp.org/

Design implication: use a checklist to review input handling, configuration, external destinations, secrets and runtime security. A brochure-style website can still introduce link, script, CSP or deployment risks.

## Performance

- Web Vitals thresholds: https://web.dev/articles/defining-core-web-vitals-thresholds
- MDN animation performance guidance: https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Animation_performance_and_frame_rate

Design implication: measure user experience and avoid unnecessary animation work. Use core metrics as outcome targets, not as a claim of guaranteed performance.

## Search metadata

- Google Search Central: Software app structured data: https://developers.google.com/search/docs/appearance/structured-data/software-app
- Google Search Central: Organization structured data: https://developers.google.com/search/docs/appearance/structured-data/organization

Design implication: only add structured data when the product facts are real. Do not add fake ratings, offers or release information to try to obtain a rich result.

## Repository-specific caveat

The technical decisions above are based on the project snapshot described during planning and must be reconciled with the actual current branch before code changes. This pack is a specification, not proof that a browser build, deployment or production test has already passed.
