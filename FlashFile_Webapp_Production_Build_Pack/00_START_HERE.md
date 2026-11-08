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
