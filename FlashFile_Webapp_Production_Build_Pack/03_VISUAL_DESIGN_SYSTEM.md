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
