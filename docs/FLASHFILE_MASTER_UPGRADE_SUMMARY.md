# FlashFile: Master Architecture, Upgrade Chronology & Engineering Specification

**Project:** FlashFile (High-Speed Telegram File-to-Link & Instant 4K Streaming Engine)  
**Target Environments:** Hugging Face Spaces (Docker / Debian Bookworm), VPS / Cloud Container, Local Development  
**Live Production URL:** https://jishnupg-filetolink.hf.space/  
**Official Bot:** [@flashfilezbot](https://t.me/flashfilezbot)  
**Updates Channel:** [t.me/flashfilez](https://t.me/flashfilez)  
**Developer Profile:** [JishnuPG-tech](https://github.com/JishnuPG-tech)  
**Repositories:**
- GitHub: `https://github.com/JishnuPG-tech/FiletoLink.git`
- Hugging Face Space: `https://huggingface.co/spaces/Jishnupg/FileToLink`
**Document Purpose:** Complete technical handover, architectural specification, and historical upgrade log designed for autonomous AI agents and engineers to achieve immediate 100% operational understanding of the system.

---

## 1. Executive Summary & Purpose Hierarchy

FlashFile transforms Telegram's cloud storage into a high-throughput, resume-capable direct HTTP download and instant streaming platform.

```
                  ┌────────────────────────────────────────┐
                  │          FLASHFILE CORE PURPOSE        │
                  └────────────────────────────────────────┘
                                      │
            ┌─────────────────────────┴─────────────────────────┐
            ▼                                                   ▼
┌──────────────────────────────────────┐    ┌──────────────────────────────────────┐
│       PRIMARY PURPOSE (PRIORITY 1)   │    │      SECONDARY PURPOSE (PRIORITY 2)  │
│  Telegram File -> Direct Link        │    │      Instant 4K Streaming            │
│  • Chrome, Brave, IDM, 1DM, Browser  │    │  • VLC, MX Player, Cinema Web Player │
│  • HTTP 206 Multi-threaded Chunks    │    │  • Zero Local Phone Storage Used     │
│  • 100% Pause & Resume Support       │    │  • Direct-from-RAM Chunk Streaming   │
└──────────────────────────────────────┘    └──────────────────────────────────────┘
```

---

## 2. Brand Identity & Entity Reference

Every trace of the former legacy identity ("Thunder" / "Apex") has been completely purged and replaced across all code, templates, HTML meta headers, and bot strings:

| Property | Value | Notes |
| :--- | :--- | :--- |
| **Project Name** | **FlashFile** | Clean, modern file-to-link brand |
| **Telegram Bot** | `@flashfilezbot` | Verified Pyrogram / Pyrofork bot username |
| **Telegram Channel** | `https://t.me/flashfilez` | Official announcement & updates channel |
| **Developer Name** | `JishnuPG-tech` | Displayed across bot footer & web apps |
| **Developer GitHub** | `https://github.com/JishnuPG-tech` | Canonical open-source repository owner |
| **Web Endpoint** | `https://jishnupg-filetolink.hf.space/` | Hugging Face Spaces production deployment |
| **Telegram DC Support**| Datacenters 1 through 5 | Full multi-datacenter file chunk routing |

---

## 3. High-Level Architecture & Traffic Flow

The container runs a multi-tier supervisor orchestrating microservices on internal ports, unified behind a single edge gateway on port `7860`:

```mermaid
flowchart TD
    Client["User / Client (Browser / Telegram / IDM / VLC)"]

    subgraph EdgeGateway["Apex Gateway (Port 7860 - Uvicorn + FastAPI)"]
        Router{"Reverse Proxy Router\n(gateway/main.py)"}
        StaticSPA["Static Showcase Webapp\n(/ -> webapp/dist)"]
        StreamProxy["Direct File Stream Proxy\n(/f/*, /watch/*)"]
        DispatchesProxy["Live Dispatches Teleprinter\n(/api/live-dispatches, /dispatches)"]
    end

    subgraph BackendServices["Backend Microservices"]
        F2L["FlashFile Engine (Port 8081)\nPyrofork MTProto Client Pool + aiohttp"]
        Jellyfin["Jellyfin Media Server (Port 8096)\nInternal Local SQLite Cache"]
    end

    subgraph StorageTier["Data & Cache Layer"]
        MongoDB[("MongoDB Database\nFile metadata, OTT keys, User passes")]
        BinChannel[("Telegram Bin Channel\nPersistent File Message Storage")]
        LocalDisk[("Local Container Fast Disk\n/opt/jellyfin-local & RAM Buffers")]
    end

    Client -->|HTTP Port 7860| Router
    Router -->|GET /| StaticSPA
    Router -->|GET /f/{hash}/{name}| StreamProxy -->|Proxy Pass 8081| F2L
    Router -->|GET /watch/f/{hash}/{name}| StreamProxy -->|Proxy Pass 8081| F2L
    Router -->|GET /api/live-dispatches| DispatchesProxy -->|Proxy Pass 8081| F2L

    F2L -->|MTProto Chunk Streaming| BinChannel
    F2L -->|Store & Query Records| MongoDB
```

---

## 4. Master Upgrade & Evolution Chronology

Below is the chronological log of all architectural upgrades, bugs eliminated, and features delivered from inception to the present:

### Phase 1: Brand Migration & Identity Overhaul
- **Commit:** `9884124`
- **Actions:**
  - Migrated brand name from `Thunder` to `FlashFile`.
  - Re-routed all bot commands, help cards, welcome prompts, and about strings to `@flashfilezbot`, `https://t.me/flashfilez`, and `JishnuPG-tech`.
  - Repointed repository URLs to `https://github.com/JishnuPG-tech/FiletoLink.git`.
  - Updated webapp metadata, titles, favicons, open graph cards, and footer disclaimers.

### Phase 2: Authentic Thermal Printer Audio Synthesizer
- **Commit:** `b81a9d9`
- **Actions:**
  - Designed a Web Audio API procedural audio synthesizer inside `webapp/src/components/TestimonialEmber.tsx`.
  - Generates real mechanical receipt sounds without external audio files:
    1. **Stepper Motor Churn:** Low-frequency pulse wave (55 Hz–110 Hz) with periodic notch steps.
    2. **Paper Friction Screech:** Band-passed white noise (1200 Hz–3200 Hz) imitating thermal head friction.
    3. **Paper Tear / Snap:** High-frequency transient burst upon receipt tear.
    4. **Keypad Ticks:** Crisp micro-transients on receipt switch navigation.
  - Added user toggleable mute/unmute control with state persistence.

### Phase 3: Mobile Viewport & CSS Alignment Overhaul
- **Commits:** `e621a77`, `6d5162e`, `37ba96f`
- **Actions:**
  - Fixed mobile vertical gaps and black empty voids by constraining minimum page height and fluid container scaling.
  - Eliminated touch scroll-hijack glitches on mobile devices by adjusting CSS touch-action and overflow properties.
  - Configured cache invalidation headers on Gateway to prevent stale webapp bundles from remaining cached on mobile browsers.

### Phase 4: Live Teleprinter Dispatches & Database Integration
- **Commits:** `4c0a22f`, `a61bd52`, `09ec96f`, `a8da220`
- **Actions:**
  - **Live Dispatch Extractor:** Created `Thunder/utils/dispatches.py` with multi-tier extraction:
    1. Primary: In-memory live dispatch ring buffer updated every time a user requests a file.
    2. Secondary: MongoDB collection query for recent successful file links.
    3. Tertiary: Telegram Bin Channel probe using message scanning.
  - **Pyrogram MTProto Fix:** Resolved `[400 BOT_METHOD_INVALID]` error caused by bot accounts calling forbidden `get_chat_history()`. Replaced with batched `get_messages(chat_id, message_ids=batch)` ID range scanning.
  - **Purged Fake Receipts:** Removed hardcoded mock movies (`Breaking Bad S05E14`, `Dune: Part Two`, `Interstellar`) from frontend defaults. All receipts are 100% genuine database extractions.
  - **Fixed 4-Paper Repeat Bug:** Solved receipt printer looping back from paper #4 to #1 by removing destructive `setCurrentIndex(0)` invocations on polling cycles and implementing fingerprint payload hashing (`dispatchesSigRef`).

### Phase 5: Security Hardening & Zero-Hardcoded Secrets
- **Commits:** `e9803c0`, `e319f61`, `ec37f1c`
- **Actions:**
  - **Audit & Extraction:** Stripped hardcoded UPI IDs, subscription amounts, TMDB API tokens, internal URLs, and ports from source code, converting them to strict environment variables in `Thunder/vars.py`.
  - **HTTP Header Injection Defense:** Protected `Content-Disposition` against CRLF (`\r\n`) injection attacks, stripped quotes, and added RFC 5987 `filename*=UTF-8''` compliance for non-ASCII/regional filenames.
  - **Public Hash Validation:** Hardened `validate_public_hash` against path traversal (`../`), null-bytes, NoSQL injections, and invalid lengths (enforcing exact 20-character hex strings).
  - **Byte-Range Parser Security:** Fortified `parse_range_header` against inverted byte ranges (`bytes=500-100`), out-of-bounds start offsets, negative indices, and NaN/garbage payloads.
  - **Vendored Cinema Player Assets:** Embedded Vidstack player assets directly within the repository, eliminating external CDN dependencies and third-party script injection risks.
  - **Automated Security Test Suite:** Built `tests/test_flashfile_security.py` with 24 initial test cases validating byte-range handling, header injection defense, hash sanitization, and secret isolation.

### Phase 6: Telegram Bot Formatting & Professional Message Typography
- **Commit:** `0c87bdd`
- **Actions:**
  - **Removed Dangling Emojis:** Eliminated trailing emojis from all message headings (e.g., `⚡ FlashFile — Your Links are Ready! ⚡` -> `⚡ **FlashFile**`). Prevents mobile Telegram from wrapping a lonely emoji onto its own empty line.
  - **Clean Filename URL Quoting:** Refactored `quote_media_name()` in `Thunder/utils/bot_utils.py` to sanitize spaces, dashes, and parentheses into dots (`re.sub(r'[^a-zA-Z0-9._-]+', '.', ...)`). Eliminates ugly 5-line `%20%28%29` percent-encoding slop.
  - **Professional Action Buttons:** Replaced generic rocket and desktop emojis with standard media action icons: `[ 📥 Fast Download ] [ ▶️ Stream Online ]`.

### Phase 7: Curated OTT Release Updates Autopilot Overhaul
- **Commit:** `0c87bdd`
- **Actions:**
  - **Strict Today & Upcoming Only Rule:** Implemented `check_release_timing(release_date_raw, today)`. Replaced legacy `-10 days` lookback. Any release with `release_date < today` is **strictly rejected**.
  - **Standardized Announcements:**
    - Today Releases: `📣 '{title}' {year} {language} {media_kind} Streaming Today From {platform}`
    - Upcoming Releases: `📣 '{title}' {year} {language} {media_kind} Streaming {date_str} From {platform}`
  - **Blockbuster Hype Scoring Algorithm:** Added scoring weights for trending titles, `vote_average >= 7.0`, vote volume, Indian regional languages (`hi`, `ta`, `te`, `ml`, `kn`), and anticipated blockbuster keywords (*Ramayana*, *Jailer 2*, *Godzilla Minus One*, *Kalki*, *Pushpa*, *Salaar*, *Devara*, *Kantara*, etc.).
  - **Test Suite Expansion:** Expanded `tests/test_flashfile_security.py` to 32 test cases, adding 8 tests validating URL quoting, OTT timing logic, and message layout.

---

## 5. Security & Configuration Reference

### Environment Variables & Secrets Table

| Variable Name | Required | Default in Code | Purpose |
| :--- | :---: | :--- | :--- |
| `API_ID` | **Yes** | None | Telegram MTProto API ID from my.telegram.org |
| `API_HASH` | **Yes** | None | Telegram MTProto API Hash from my.telegram.org |
| `BOT_TOKEN` | **Yes** | None | Telegram Bot Token from @BotFather |
| `BIN_CHANNEL` | **Yes** | None | Telegram Channel ID used for persistent media message storage |
| `OWNER_ID` | **Yes** | None | Telegram User ID of the bot administrator |
| `DATABASE_URL` | **Yes** | None | MongoDB connection URI (`mongodb+srv://...`) |
| `URL` | **Yes** | `https://jishnupg-filetolink.hf.space/` | Fully-qualified public URL of the deployment |
| `TMDB_API_KEY` | Optional | `""` | TMDB v3 API key for OTT Autopilot & metadata |
| `UPI_ID` | Optional | `""` | Merchant UPI ID for subscription pass payments |
| `SUB_PRICE` | Optional | `₹10 / 30 Days` | Pricing display string for subscription gate |
| `PORT` | Optional | `8080` (or `8081`) | Internal HTTP server listen port |
| `OTT_CHANNEL_ID` | Optional | Falls back to `FORCE_CHANNEL_ID` | Target Telegram channel for curated OTT release updates |
| `OTT_SCHEDULE_HOUR`| Optional | `9` (9:00 AM) | Scheduled hour for daily OTT autopilot broadcast |
| `OTT_TIMEZONE_OFFSET`| Optional| `5.5` (IST) | Timezone offset in hours (5.5 = UTC+5:30) |

---

## 6. Verification & Automated Test Suite

The project includes an automated regression test suite located at [`tests/test_flashfile_security.py`](file:///C:/Users/JISHNU%20PG/Videos/FigCraft/FiletoLink/tests/test_flashfile_security.py).

### Running the Test Suite
```bash
# In workspace root:
$env:PYTHONPATH="."
pytest tests/test_flashfile_security.py -v
```

### Coverage Overview (32 Test Cases):
1. **`TestByteRangeSecurity` (11 tests):**
   - Valid standard, open-ended, suffix, and single-byte ranges.
   - Rejection of inverted ranges, out-of-bounds offsets, zero suffixes, and malformed headers.
2. **`TestHeaderInjectionDefense` (3 tests):**
   - CRLF (`\r\n`) injection blocking in `Content-Disposition`.
   - Quote escaping and injection neutralization.
   - RFC 5987 UTF-8 encoding verification for international titles.
3. **`TestPublicHashValidation` (7 tests):**
   - Verification of 20-character hex hash acceptance and normalization.
   - Rejection of non-hex characters, path traversal (`../../`), NoSQL payloads, and truncated hashes.
4. **`TestMarkdownResilience` (1 test):**
   - Backtick sanitization in filenames preventing Markdown formatting corruption.
5. **`TestZeroHardcodedSecrets` (2 tests):**
   - Verifies zero hardcoded UPI IDs or fallback credentials exist in source code.
6. **`TestCleanFilenameUrlQuoting` (2 tests):**
   - Validates that `quote_media_name()` converts spaces/brackets to dots without `%20%28%29` slop.
7. **`TestCuratedOttReleaseTimingFilter` (5 tests):**
   - Strictly rejects past dates (`rdate < today`).
   - Accurately tags today's releases (`rdate == today`).
   - Formats upcoming releases within 60 days.
   - Rejects distant future (>60 days) and unparseable dates.
8. **`TestProfessionalMessageFormatting` (1 test):**
   - Validates that message headers start cleanly without duplicate trailing emojis.

---

## 7. Deployment Instructions & Dual-Remote Operations

The repository maintains two synchronized Git remotes:
1. `origin`: GitHub (`https://github.com/JishnuPG-tech/FiletoLink.git`)
2. `space`: Hugging Face Space (`https://huggingface.co/spaces/Jishnupg/FileToLink`)

### Deploying Changes:
```bash
# 1. Run local tests
$env:PYTHONPATH="."
pytest tests/test_flashfile_security.py -q

# 2. Commit changes
git add -A
git commit -m "feat/fix: <description>"

# 3. Push to both remotes
git push origin main
git push space main
```

---

## 8. Guidance for Autonomous AI Agents

When another AI agent inspects or modifies this repository:
1. **Never re-introduce the name "Thunder" or "Apex":** FlashFile is the canonical identity.
2. **Maintain Strict Secret Isolation:** Never hardcode credentials, private tokens, or payment addresses in Python files. Always read from `os.getenv()` or `Thunder/vars.py`.
3. **Preserve Audio Synthesizer in Webapp:** The Web Audio API synthesizer in `TestimonialEmber.tsx` is fully algorithmic and requires no external MP3/WAV assets.
4. **Preserve OTT Date Filtering:** Never permit `rdate < today` in `Thunder/bot/plugins/ott_autopilot.py`. Only releases occurring today or scheduled within 60 days are valid for broadcast.
5. **Keep URL Paths Clean:** Always route filename encoding through `quote_media_name()` so that URLs remain compact, clean, and free of percent-encoding.
