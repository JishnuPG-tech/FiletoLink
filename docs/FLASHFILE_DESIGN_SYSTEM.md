# FlashFile Design System

**Status:** Proposed  
**Default appearance:** FlashFile Obsidian + Crimson-Coral  
**Alternative:** Claude Editorial, activated only if the product owner rejects the default

## 1. Design principles

1. Functional first. The link, stream, download, or export action must be visually obvious.
2. Dark, not noisy. Use black-charcoal surfaces and one dominant coral-red action color.
3. Atmosphere belongs in the hero. The Spirit particle canvas does not sit behind forms, menus, data tables, or the player.
4. Typography is part of the identity. Use Instrument Serif for large editorial moments; use Inter for functional text.
5. One icon style. Use Iconsax if its React package passes the build and bundle check. Do not mix icon styles across navigation and actions.
6. Motion has a purpose. Small transitions help users understand focus, progress, and completion. They must never block task feedback.
7. Theme is data. Components read CSS tokens and do not hard-code brand colors into individual views.

## 2. Tokens

```css
:root,
[data-theme="flashfile"] {
  color-scheme: dark;
  --bg-base: #08090d;
  --bg-surface: rgba(16, 18, 27, 0.78);
  --bg-card: rgba(22, 25, 38, 0.88);
  --border-glass: rgba(255, 255, 255, 0.08);
  --border-hover: rgba(255, 255, 255, 0.18);

  --accent-brand: #ff3b5c;
  --accent-secondary: #e02447;
  --accent-gradient: linear-gradient(135deg, #ff3b5c 0%, #e02447 100%);
  --accent-glow: rgba(255, 59, 92, 0.28);
  --accent-cyan: #38bdf8;
  --accent-emerald: #10b981;

  --particle-color-primary: #ff3b5c;
  --particle-color-secondary: #e02447;
  --particle-color-highlight: #38bdf8;
  --particle-glow-primary: rgba(255, 59, 92, 0.22);
  --particle-glow-secondary: rgba(56, 189, 248, 0.08);

  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --focus-ring: #ff91a4;

  --radius-xl: 20px;
  --radius-lg: 14px;
  --radius-md: 10px;
  --radius-sm: 7px;

  --font-serif: "Instrument Serif", Georgia, serif;
  --font-display: "Plus Jakarta Sans", Inter, sans-serif;
  --font-body: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;

  --motion-fast: 150ms;
  --motion-control: 180ms;
  --motion-view: 240ms;
}
```

The root tokens should match the landing template. The app should not introduce a second palette that slowly diverges.

## 3. Alternative Claude Editorial palette

This is a planned alternate token map, not the default:

```css
[data-theme="claude"] {
  color-scheme: dark;
  --bg-base: #171512;
  --bg-surface: #211d18;
  --bg-card: #29241e;
  --border-glass: rgba(245, 238, 226, 0.12);
  --border-hover: rgba(245, 238, 226, 0.22);
  --accent-brand: #d97757;
  --accent-secondary: #b85f3a;
  --accent-gradient: linear-gradient(135deg, #d97757 0%, #b85f3a 100%);
  --accent-glow: rgba(217, 119, 87, 0.2);
  --particle-color-primary: #d97757;
  --particle-color-secondary: #b85f3a;
  --particle-color-highlight: #f2ba93;
  --particle-glow-primary: rgba(217, 119, 87, 0.22);
  --particle-glow-secondary: rgba(242, 186, 147, 0.05);
  --text-primary: #f4ede2;
  --text-secondary: #c1b5a7;
  --text-muted: #948677;
  --focus-ring: #f2ba93;
}
```

Keep the same information architecture and component states between themes. Only tokens and approved decorative treatments change. The light/warm variant should be implemented after core UI behavior exists, not before.

## 4. Typography

- Hero: Instrument Serif, 56–72 px desktop, 42–48 px mobile, tight but readable line-height.
- Page title: Plus Jakarta Sans, 28–36 px desktop, 24–30 px mobile.
- Section title: Plus Jakarta Sans, 18–22 px.
- Body: Inter, 14–16 px, line-height around 1.5.
- Field labels and metadata: Inter, 12–13 px with sufficient contrast.
- URL, hash, file identifier, command: JetBrains Mono, 12–14 px; allow line-wrap or horizontal scrolling without clipping.

Avoid applying uppercase tracking to long labels and avoid using the serif face for status labels or controls.

## 5. Layout grid

- Max content width: 1320 px.
- Desktop: 248 px compact navigation rail, flexible content column, 24–32 px page gutters.
- Tablet: 72 px icon rail or collapsible drawer, 20 px gutters.
- Mobile: single column, 16 px gutters, full-width primary actions and bottom navigation.
- Workspace spacing: 8 px base grid.
- Panel padding: 20–24 px desktop, 16 px mobile.
- Cards should be separated mainly by surface and border; reserve stronger shadow/glow for overlays and one primary action.

## 6. Component specifications

### Buttons
- Primary: coral gradient, high-contrast label, one per main region.
- Secondary: transparent or muted surface with a thin border.
- Tertiary: text action with a visible hover/focus state.
- Destructive: clearly differentiated state, never use the primary brand color alone to imply danger.
- Icon-only buttons need an accessible name and a tooltip on desktop.

### Inputs
- 44–48 px target height.
- Persistent label or visible placeholder plus an accessible label.
- Clear focus ring, error text, and optional helper text.
- Paste action should work with keyboard and context menu.
- Do not clear the user's URL when an API request fails.

### Cards and panels
- Use translucent surfaces sparingly. If backdrop blur causes text contrast or GPU cost issues, use a solid surface instead.
- Provide loading, empty, error, and success states for each data panel.
- Keep content and actions in the same predictable position across cards.

### Dialogs and menus
- Use Radix-backed shadcn components.
- Trap focus, return focus to the trigger, support Escape when appropriate, and use proper heading/description semantics.
- Never rely on hover alone for a core action.

### Status
- Show a status label and the time of the last successful poll.
- Use icons plus text, not color alone.
- Unknown is different from offline. Do not keep old green status indefinitely after polling fails.

### Batch rows
- One URL per row with a row number, validation status, and accessible remove/reorder actions.
- On mobile, rows become stacked cards and controls retain adequate target size.
- Exports must reflect visible ordering and exclude rows marked invalid unless the user explicitly includes them.

## 7. Spirit particle theme contract

The particle layer uses these CSS variables:

- `--particle-color-primary`
- `--particle-color-secondary`
- `--particle-color-highlight`
- `--particle-glow-primary`
- `--particle-glow-secondary`

Both implementations, `Thunder/template/index.html` and `webapp/src/components/canvas/TransmissionCore.tsx`, must read these variables. Never hard-code three.js color uniforms in either file without using the tokens.

The particle element is decorative, pointer-transparent, and hidden from assistive technology. It must:
- detect reduced motion and WebGL availability;
- render a static glow fallback when animation is unavailable;
- pause when not visible;
- adapt its particle budget to viewport size;
- clean up observers, event listeners, animation frames, geometry, material, and renderer on unmount.

## 8. Motion rules

| Use | Target | Rule |
|---|---|---|
| Hover/focus | 140–180 ms | No layout movement |
| Button pressed | 100–140 ms | Subtle scale or color change only |
| Small view transition | 180–260 ms | Respect reduced motion |
| Toast | 180–240 ms | Do not delay its appearance |
| Particle motion | Continuous, hero only | Pause off-screen; no WebGL under reduced motion |
| Loading | As needed | Prefer skeleton/progress indicators tied to real work |

Use StringTune for verified, scoped effects such as progress, responsiveness, and selected cursor motion. Keep the public API usage documented and avoid duplicate motion systems for the same property.

## 9. Quality gates

- Keyboard-only complete flow for link, batch, status, and plans.
- Visible focus on every interactive element.
- Accessible labels for icon-only buttons; semantic headings; form errors announced correctly.
- Reduced-motion mode removes nonessential motion and particle rendering.
- Contrast measured against the final colors, not judged by eye alone.
- Test desktop, tablet, mobile, 200% zoom, slow network, WebGL disabled, and failed backend.
- Bundle and performance review before adding animation or icon packages.
