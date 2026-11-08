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
