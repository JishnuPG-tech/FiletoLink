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
