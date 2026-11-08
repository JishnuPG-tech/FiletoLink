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
