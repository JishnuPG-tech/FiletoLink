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
