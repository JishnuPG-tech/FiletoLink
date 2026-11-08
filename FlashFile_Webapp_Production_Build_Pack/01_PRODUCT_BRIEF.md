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
