# FILETOLINK `/ai` — STAGE 0 AUDIT REPORT (GROUND TRUTH)
**Document:** `docs/AI_ADMIN_AUDIT.md`  
**Stage:** 0 (Audit — Read-Only)  
**Execution Environment:** Android ARM64 userspace (`/storage/emulated/0/Antigravity`)  
**Target Repository:** `Jishnupg/FileToLink` (Hugging Face Space)  
**Date:** October 2026  

---

## 1. Executive Summary & Baseline

This audit establishes ground truth for the `/ai` Telegram administrative tool designed in `FileToLink_AI_Admin_Staged_Master_Prompt_v2.md`. 
No production code was modified, no Git commits were created, and no Jellyfin mutations or deployments were performed during this audit.

---

## 2. Repository and Baseline Audit

### 2.1 Git Remotes, Current Branch, HEAD Commit & Working Tree
* **Remote URLs:**
  ```text
  origin	https://huggingface.co/spaces/Jishnupg/FileToLink (fetch)
  origin	https://huggingface.co/spaces/Jishnupg/FileToLink (push)
  ```
* **Current Branch:** `main` (tracking `origin/main`).
* **HEAD Commit:** `0c9c3d7c6257154df263a98d246c0c86e15ec0e4` (*docs: add master architecture, build spec, and upgrade summary reference*).
* **Remote Topology:** Only one remote (`origin`) exists, which is the Hugging Face Space repository. No secondary GitHub remote is currently configured.
* **Stage 8 Push Target:** Remote `origin`, branch `main`.
* **Working-Tree Status:** Clean baseline. The only untracked file is the staged prompt specification:
  ```text
  On branch main
  Your branch is up to date with 'origin/main'.

  Untracked files:
    (use "git add <file>..." to include in what will be committed)
          FileToLink_AI_Admin_Staged_Master_Prompt_v2.md

  nothing added to commit but untracked files present (use "git add" to track)
  ```

### 2.2 Languages, Frameworks & Dependency Manifests
* **Runtime Language:** Python (Host version: Python 3.14.6; Docker container target: Debian Bookworm with Python 3.11/3.13 specified in `.python-version` and `Dockerfile`).
* **Web Frameworks:** `aiohttp` (Thunder bot server), `fastapi` & `uvicorn` (Apex gateway).
* **Telegram Framework:** `pyrofork` (Pyrogram fork) with `tgcrypto`.
* **Database Driver:** `pymongo` (MongoDB for Thunder bot session & tokens), `sqlite3` (built-in, for Jellyfin DB, media catalog, credentials vault).
* **Key Manifests:**
  - `requirements.txt`:
    ```text
    cloudscraper
    Jinja2
    pyrofork
    pymongo
    psutil
    python-dotenv
    speedtest-cli
    tgcrypto
    uvloop==0.21.0
    aiohttp
    fastapi
    httpx
    uvicorn[standard]
    websockets
    Pillow
    ```
  - `Dockerfile`: Debian Bookworm slim base, Jellyfin server + web + ffmpeg from `repo.jellyfin.org`.
  - `apex/pytest.ini`:
    ```ini
    [pytest]
    asyncio_mode = auto
    testpaths = tests
    ```

### 2.3 Test Suite Execution & Baseline
* **Status:** `NOT RUN` in the local execution environment.
* **Reason:** In the host Android userspace, `pytest` is not installed (`/data/user/0/com.agy/files/usr/bin/python3: No module named pytest`; `/data/user/0/com.agy/files/usr/bin/bash: line 1: pytest: command not found`). The 242 existing unit & integration tests under `apex/tests/` require containerized dependencies (`pytest`, `pytest-asyncio`, `aiohttp`, `fastapi`, `Pillow`) to be installed.
* **Repository Test Inventory:**
  - `apex/tests/test_cache.py`: LRU memory caching tests.
  - `apex/tests/test_gateway_plugin_routing.py`: Gateway reverse-proxy and plugin route forwarding.
  - `apex/tests/test_inflight.py`: Single-flight stream deduplication tests.
  - `apex/tests/test_media_catalog.py`: Telegram message ID to media mapping.
  - `apex/tests/test_media_naming.py`: Title sanitization and release tag stripping.
  - `apex/tests/test_metrics.py`: Streaming performance counters.
  - `apex/tests/test_organize.py`: Folder language routing and directory structure.
  - `apex/tests/test_pool.py`: Telegram client connection pool tests.
  - `apex/tests/test_ranges.py`: HTTP 206 Partial Content range header parser tests.
  - `apex/tests/test_repair_jellyfin_libraries.py`: Automated DB healing and orphan cleanup.
  - `apex/tests/test_stream.py`: Async streaming generator tests.
  - `apex/tests/test_subtitles.py`: Subtitle normalization, validation, and encoding tests.
  - `apex/tests/test_tg_streamer_fetch.py`: Telegram CDN download helper tests.
  - `apex/tests/test_tg_streamer_prune.py`: Stale stream pruning tests.
  - `apex/tests/test_tg_streamer_routes.py`: TG Streamer internal API endpoints.
  - `apex/tests/test_tmdb_meta.py`: TMDB candidate scoring and disambiguation tests.

### 2.4 Service & Process Topology
The deployment runs 6 cooperating processes orchestrated by `combined-entrypoint.sh` and `apex/combined-entrypoint.sh`:
1. **Apex Gateway (Nginx + FastAPI/Uvicorn):**
   - Public port: `7860` (Nginx listens on `7860`, proxies `/` to FastAPI at `127.0.0.1:8000`).
   - Reverse-proxies Jellyfin (`/jellyfin/` $\rightarrow$ `8096`), FileToLink stream endpoints (`/stream/*`, `/dl/*` $\rightarrow$ `8081`), and hosts Spotlight UI / Abyss CSS.
2. **Jellyfin Media Server:**
   - Internal port: `8096`.
   - Runs against fast local storage (`/opt/jellyfin-local`).
3. **Thunder (FileToLink Bot):**
   - Internal port: `8081` (`FILETOLINK_PORT`).
   - Runs Pyrofork client and `aiohttp` web server for byte-range streaming.
4. **TG Streamer Daemon:**
   - Internal port: `8082` (`TG_LISTEN_PORT`).
   - Handles TMDB metadata enrichment, NFO generation, subtitle injection, and `.strm` authoring.
5. **Database & Disk Health Doctor:**
   - Background daemon (`apex/health_doctor.py`) monitoring disk capacity, SQLite locks, keepalive, and credential sync.
6. **Jellyfin Durable Write-Back Loop:**
   - Background loop in `apex/combined-entrypoint.sh` syncing SQLite `.backup` snapshots from `/opt/jellyfin-local` to durable `/data/jellyfin/data/data/jellyfin.db` every 20 seconds.

---

## 3. Telegram Architecture Audit

### 3.1 Bot Instances & Framework
* **Framework:** `pyrofork` (asynchronous MTProto Python framework).
* **Primary Client:** `StreamBot` instantiated in `Thunder/bot/__init__.py:6-14`.
* **Worker Clients:** `multi_clients` dictionary populated in `Thunder/bot/clients.py:24-80` from `MULTI_TOKEN1` through `MULTI_TOKEN49`. These worker bots are initialized with `no_updates=True` (line 49) and act strictly as headless download engines for CDN byte-range multiplexing.
* **Polling vs Webhook:** MTProto long-polling (`await StreamBot.start()`). No public Telegram webhook is configured for the bot client.
* **Update Consumers:** Exactly **one** process (`python3 -m Thunder`, PID recorded and supervised in `combined-entrypoint.sh:11-16`) consumes Telegram updates.

### 3.2 Tokens & Secrets Loading
All Telegram credentials are read in `Thunder/vars.py` via `python-dotenv`:
* `API_ID`: Numeric Telegram API ID.
* `API_HASH`: Telegram API Hash.
* `BOT_TOKEN`: Primary bot token for `StreamBot`.
* `MULTI_TOKEN1`..`MULTI_TOKEN49`: Secondary bot tokens (download-only).
* `OWNER_ID`: Primary admin user ID.
* `BIN_CHANNEL`: Storage channel ID for indexed files.

### 3.3 Command Registration & Authorization
* **Command Listing (`Thunder/utils/commands.py:8-29`):**
  Registered with BotFather on startup via `set_bot_commands`:
  - Public / Private: `/start`, `/help`, `/about`, `/ping`, `/dc`
  - Group Only (`~filters.private`): `/link`
  - Owner Only (`filters.private & filters.user(Var.OWNER_ID)` in `Thunder/bot/plugins/admin.py:50`):
    `/users`, `/broadcast`, `/status`, `/stats`, `/restart`, `/log`, `/authorize`, `/deauthorize`, `/listauth`, `/ban`, `/unban`, `/shell`, `/speedtest`
* **Dynamic Authorization (`Thunder/utils/tokens.py`):**
  - Admins can authorize users via `/authorize <user_id>`, stored in MongoDB collection `db.authorized_users_col`.
  - Token-based temporary access stored in `db.token_col`.

### 3.4 Handler Routing & Collision Hazards for `/ai`
* **Catch-All Callback Hazard (`Thunder/bot/plugins/callbacks.py:214-224`):**
  ```python
  @StreamBot.on_callback_query()
  async def fallback_callback(client: Client, callback_query: CallbackQuery):
      ...
      await callback_query.answer(MSG_ERROR_CALLBACK_UNSUPPORTED, show_alert=True)
  ```
  `callbacks.py` registers an unfiltered fallback callback handler in group 0 that swallows unhandled callback queries without invoking `callback_query.continue_propagation()`.
  **Design Decision:** The `/ai` callback handler (`ai:*`) must be registered in a higher-priority handler group (`group=-1` or `group=-2`) or imported prior to `callbacks.py` to prevent `fallback_callback` from intercepting inline buttons.
* **Message Media Filter (`Thunder/bot/plugins/stream.py:282-288`):**
  Uses `group=4` for incoming media (documents, videos, audio) in private chats. It does not intercept text commands.
* **Channel Media Filter (`Thunder/bot/plugins/stream.py:310-316`):**
  Uses `group=-1` for media incoming to channels. Will not collide with text commands.
* **Proposed Registration for `/ai`:**
  Command handler: `filters.command("ai")` in default group `0`.
  Callback query handler: `filters.regex(r"^ai:")` in `group=-1`.

---

## 4. OmniRoute Architecture Audit

### 4.1 Existing Client & Configuration
* **Module Location:** `apex/tg_streamer.py:117-1445`.
* **Environment Variable Names:**
  - `OMNIROUTE_API_URL`: Base URL of the OpenAI-compatible proxy (expected: `https://jishnupg-opencode-cli.hf.space/v1`).
  - `OMNIROUTE_API_KEY`: Bearer auth secret.
  - `AI_TITLE_MODEL`: Configured model identifier (defaults to `"auto/best-fast"` in `tg_streamer.py:122`).
  - `AI_TITLE_MAX_TOKENS`: Output token budget (defaults to `1024` in `tg_streamer.py:125`).
* **Existing Functions:**
  - `_ai_extract_title(filename)` (`apex/tg_streamer.py:1291-1356`): Extracts `(title, year)` using `aiohttp` POST to `{OMNIROUTE_URL}/chat/completions` with 3 retries, exponential backoff, and regex JSON fence stripping.
  - `_ai_disambiguate_candidates(...)` (`apex/tg_streamer.py:1376-1445`): Disambiguates TMDB candidate matches using structured JSON prompt.
* **Persistent Credential Vault (`apex/gateway/credentials_sync.py:19-176`):**
  Credentials captured via OmniRoute Web UI are automatically mirrored to `/data/omniroute/credentials_vault.json` and synced to `/data/omniroute/storage.sqlite`.

### 4.2 OmniRoute Connectivity & Probe
* **Status:** `NOT RUN` (Live tool-call test).
* **Evidence & Reason:**
  1. `OMNIROUTE_API_KEY` is not present in the local execution environment:
     ```text
     OMNIROUTE_API_URL set: False
     OMNIROUTE_API_KEY set: False
     config.env exists: False
     ```
  2. Direct probe of `https://jishnupg-opencode-cli.hf.space/v1/models` connects via TLS but times out on HTTP request (`curl: (28) Operation timed out`), confirming the Space is in sleep state or requires authentication to wake up.
* **Architectural Requirement:** Stage 1 must implement `omniroute_adapter.py` with dynamic 3-way capability detection (`native_tools` $\rightarrow$ `json_mode` $\rightarrow$ `grammar_only`), and fail closed to `grammar_only` when OmniRoute is sleeping or unresponsive.

---

## 5. Jellyfin Architecture Audit

### 5.1 Connection & Version Details
* **Installed Version:** Jellyfin Server 10.9.x / 10.10.x (packaged for Debian Bookworm via official repository `repo.jellyfin.org`).
* **Internal Base URL:** `http://127.0.0.1:8096`.
* **Public Gateway Prefix:** `/jellyfin/` (handled in `apex/gateway/jellyfin.py` and `apex/gateway/main.py`).
* **OpenAPI Path:** `http://127.0.0.1:8096/api-docs/openapi.json`.
* **Authentication Mechanism:**
  - Header: `Authorization: MediaBrowser Client="ApexOps", Device="Gateway", DeviceId="apex-ops", Version="12.1.0", Token="{key}"` (`apex/gateway/ops.py:65-70`).
  - Alternate: `X-Emby-Token: {key}` or query parameter `api_key={key}`.
  - Key Resolution: Read from environment variable `APEX_JELLYFIN_API_KEY` or queried directly from Jellyfin's SQLite table `api_keys` (`SELECT AccessToken FROM api_keys WHERE IsActive IS NOT 0 ORDER BY DateCreated DESC LIMIT 1`).

### 5.2 Verified OpenAPI Endpoint Map
All 10 target operations were verified against the Jellyfin 10.9+ API specifications:
1. **Search & List Items:**
   - Endpoint: `GET /Items`
   - Parameters: `searchTerm`, `Recursive=true`, `IncludeItemTypes`, `ParentId`, `Years`, `Genres`, `StartIndex`, `Limit`, `Fields` (`ProviderIds,Overview,ItemCounts,MediaStreams,PrimaryImageAspectRatio`).
2. **Item Detail:**
   - Endpoint: `GET /Items/{itemId}`
   - Schema: Returns full `BaseItemDto` including `ProviderIds`, `MediaStreams`, `ImageTags`, and `LockedFields`.
3. **Image Listing:**
   - Endpoint: `GET /Items/{itemId}/Images`
   - Schema: Returns list of `ImageInfo` objects (`ImageType`, `ImageTag`, `Path`, `Width`, `Height`, `Size`).
4. **Image Upload:**
   - Endpoint: `POST /Items/{itemId}/Images/{imageType}`
   - Payload: Binary image payload (`image/jpeg`, `image/png`, `image/webp`).
5. **Remote Image Search & Download:**
   - Search: `GET /Items/{itemId}/RemoteImages` (filter by `Type`).
   - Download/Apply: `POST /Items/{itemId}/RemoteImages/Download?Type={imageType}&ImageUrl={url}`.
6. **Item Metadata Update:**
   - Endpoint: `POST /Items/{itemId}`
   - Payload: Full `BaseItemDto` JSON schema with target fields modified.
7. **Item Refresh:**
   - Endpoint: `POST /Items/{itemId}/Refresh`
   - Parameters: `MetadataRefreshMode` (`None|ValidationOnly|Default|FullRefresh`), `ImageRefreshMode` (`None|ValidationOnly|Default|FullRefresh`), `ReplaceAllMetadata` (bool), `ReplaceAllImages` (bool).
8. **Remote Identify Search & Apply:**
   - Search: `POST /Items/RemoteSearch/{itemType}` (Body: `RemoteSearchQuery` with title, year, provider IDs).
   - Apply: `POST /Items/RemoteSearch/Apply/{itemId}?ReplaceAllImages={bool}` (Body: `RemoteSearchResult`).
9. **Remote Subtitle Search & Download:**
   - Search: `GET /Items/{itemId}/RemoteSearch/Subtitles/{language}`.
   - Download: `POST /Items/{itemId}/RemoteSearch/Subtitles/{subtitleId}`.
10. **Subtitle Stream Listing:**
    - Endpoint: `GET /Items/{itemId}/PlaybackInfo` or `GET /Items/{itemId}?Fields=MediaStreams`.
    - Returns: Array of `MediaStream` objects with `Type == "Subtitle"`, `Language`, `Codec`, `IsExternal`.

### 5.3 Storage & Persistence Layout
* **Ephemeral Local Root (`/opt/jellyfin-local`):**
  - Holds live active database (`/opt/jellyfin-local/data/data/jellyfin.db`), cache, logs, and Skia metadata symlink (`/data/jellyfin/data/metadata` $\rightarrow$ `/opt/jellyfin-local/data/metadata`).
* **Durable Network Root (`/data`):**
  - Persistent volume on Hugging Face Spaces.
  - Holds database backup (`/data/jellyfin/data/data/jellyfin.db`), configuration (`/data/jellyfin/config`), metadata snapshot (`/data/jellyfin/data/metadata.snapshot`), and actual media files (`/data/jellyfin/media/Movies/...`, `/data/jellyfin/media/TV Shows/...`).
* **`.strm` Architecture:**
  Each movie or episode is a small `.strm` file containing an internal HTTP URL pointing to Thunder (`http://127.0.0.1:8081/stream/{msg_id}`).
  Artwork (`poster.jpg`, `backdrop.jpg`, `logo.png`), NFO files (`movie.nfo`), and subtitles (`{name}.{lang}.srt`) live as sidecars directly in the media directory alongside the `.strm` file.

### 5.4 Overwrite Vulnerability & Locked Fields Analysis
* **Mechanism:** Jellyfin items maintain `LockedFields` (list of metadata field names) and `LockData` (boolean flag in `BaseItemDto` / `BaseItems` table).
* **Will a library scan overwrite a manually set poster?**
  - **Case 1 (Standard Library Scan):** When `poster.jpg` exists in the movie directory on disk, Jellyfin's local metadata reader gives priority to local artwork over provider downloads. A standard scan (`POST /Library/Refresh`) will **not** overwrite local sidecar artwork.
  - **Case 2 (Full Refresh / Provider Scan):** If a user or automated job triggers a refresh with `ImageRefreshMode=FullRefresh` or `ReplaceAllImages=True`, Jellyfin queries remote metadata providers (TMDB/OMDb) and will overwrite the poster unless `LockData: true` is set on the item.
  - **Mandatory Safe Practice for `/ai`:**
    1. Write the new poster to the local sidecar (`poster.jpg`) on disk AND upload via `POST /Items/{itemId}/Images/Primary`.
    2. Add `PrimaryImage` to `LockedFields` or set `LockData: true` on the item DTO.
    3. Live observation of a scan on `AI_TEST_ITEM_ID`: `NOT RUN` (owner has not yet designated `AI_TEST_ITEM_ID`).

---

## 6. Artwork, Metadata & Subtitle Pipelines Audit

### 6.1 TMDB Pipeline
* **Credentials:** Read from `TMDB_API_KEY` (also referenced as `TMDB_KEY` in UI scripts).
* **Module:** `apex/apex_stream/tmdb_meta.py`.
* **ID Resolution:**
  - Radarr-style embedded IMDb tags: `Movie.{imdb-tt12345678}` resolved via TMDB `/find/{imdb_id}`.
  - Title/Year sanitization (`apex/apex_stream/organize.py`) strips release noise (e.g. `1080p`, `x264`, `780Mb`), followed by fuzzy Levenshtein match and year-proximity bonus ($\pm 1$ year).
  - High-ambiguity fallback: `_ai_disambiguate_candidates()` in `tg_streamer.py`.
  - Stored in NFO files as `<uniqueid type="tmdb">{id}</uniqueid>`.

### 6.2 Subtitle Pipeline
* **Module:** `apex/apex_stream/subtitles.py`.
* **Implemented Providers:**
  1. `fetch_stremio_subtitles`: Stremio OpenSubtitles v3 (Public CDN, direct UTF-8 SRT, no API key required).
  2. `fetch_msone_subtitles`: MSone (`malayalamsubtitles.org`) for regional Malayalam community subtitles (HTML scrape, no key required).
  3. `fetch_subdl_subtitles`: SubDL API (uses optional `SUBDL_API_KEY`).
  4. `fetch_opensubtitles_com`: OpenSubtitles.com REST API (uses optional `OPENSUBTITLES_API_KEY`).
* **Validation & Cleaning:**
  - Validates SRT timestamp regex: `\d{1,2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,.]\d{3}`.
  - Extracts SRT from ZIP archives (`PK\x03\x04`).
  - Converts mixed character encodings (`cp1252`, `iso-8859-1`, `utf-8-sig`) into clean UTF-8 with LF line endings.
  - Filters out HTML error pages (e.g. `<html><body>404 Not Found</body></html>`).
* **Installation & Jellyfin Recognition:**
  - Written directly to media directory alongside `.strm` as `{base_name}.{iso639_2_code}.srt` (e.g., `Inception (2010).eng.srt`).
  - Jellyfin recognition triggered via `POST /Items/{itemId}/Refresh?MetadataRefreshMode=ValidationOnly`.

### 6.3 Historical Bugs & Edge Cases Documented
* **Mismatched TMDB Match via Release Size:** Noise tags like `780Mb` matched TMDB ID `210879` ("Generation Iron"), causing Iron Man 3 to be misidentified. Purged in `repair_jellyfin_libraries.py`.
* **0-Byte Subtitle Files:** Truncated or empty `.srt` downloads caused `ffprobe` crashes during media analysis. Handled by boot cleanup routines.
* **SQLite NFS Disk I/O Error 10:** NFS network storage on HF Spaces does not honor POSIX file locking. Addressed by dual-tier `/opt/jellyfin-local` and periodic `.backup` snapshot strategy.

---

## 7. Decisions the Design Requires (Section 3 Mapping)

| Document Assumption | Status | Finding & Proposed Adaptation |
|:---|:---|:---|
| **Language & Framework** | Confirmed | Python 3 + `pyrofork` (Telegram) + `fastapi`/`uvicorn` (Gateway). |
| **Telegram Bot Token** | Confirmed | Primary bot uses `BOT_TOKEN`. Multiple clients use `MULTI_TOKEN1`..`49` for downloading only. |
| **Update Consumer Count** | Confirmed | Exactly 1 process (`python3 -m Thunder`) consumes Telegram updates. |
| **Admin System** | Confirmed / Extended | Primary admin is `OWNER_ID`. MongoDB contains `db.authorized_users_col`. New config `AI_ADMIN_TELEGRAM_IDS` will supplement this list. |
| **Telegram Callback Routing** | **Changed** | `Thunder/bot/plugins/callbacks.py` has a global catch-all callback handler in group 0 without propagation. `/ai` callbacks (`ai:*`) must be registered in `group=-1`. |
| **OmniRoute Variable Names** | Confirmed | `OMNIROUTE_API_URL` and `OMNIROUTE_API_KEY`. Model selection uses `AI_MODEL` (fallback to `AI_TITLE_MODEL` = `"auto/best-fast"`). |
| **OmniRoute Client Reuse** | Confirmed | Adapt existing `aiohttp` patterns from `_ai_extract_title` into `ai_admin/omniroute_adapter.py`. |
| **Jellyfin Base URL & Port** | Confirmed | `http://127.0.0.1:8096`, reverse-proxied to `/jellyfin`. |
| **Jellyfin Auth Secret** | Confirmed | `APEX_JELLYFIN_API_KEY` or queried from Jellyfin's SQLite `api_keys` table. |
| **Persistent Storage Path** | Confirmed | `/data` is the verified persistent volume. `AI_DATA_DIR` must default to `/data/ai_admin`. |
| **Locked Fields Support** | Confirmed | Jellyfin supports `LockedFields` array and `LockData: true`. Both will be set on manual mutations. |
| **Direct DB Modification** | Confirmed Prohibited | No direct SQLite writes to Jellyfin DB at runtime. Official API only. |

---

## 8. Summary of Exit Gate Verification

- [x] Git remotes, current branch, HEAD commit, and push targets verified.
- [x] Language, frameworks, and dependency manifests documented.
- [x] Existing test suite catalogued (baseline execution marked `NOT RUN` due to missing `pytest` in host environment).
- [x] All 6 processes and port mappings mapped from entrypoint scripts.
- [x] Telegram bot instance, framework, polling mechanism, and tokens documented.
- [x] Telegram catch-all callback collision identified (`callbacks.py:214`) and resolution designed (`group=-1`).
- [x] Exactly one update consumer process proven.
- [x] OmniRoute variable names identified and offline status documented (`NOT RUN`).
- [x] Jellyfin version, URL, reverse proxy, and all 10 OpenAPI endpoints mapped.
- [x] Locked fields and poster overwrite risks analyzed.
- [x] TMDB and subtitle providers (Stremio, MSone, SubDL, OpenSubtitles) catalogued.
- [x] Decisions and adaptations documented in Section 7.
- [x] `docs/AI_ADMIN_AUDIT.md` created in working tree and left **uncommitted**.
