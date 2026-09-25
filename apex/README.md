---
title: Apex Media Platform
emoji: 🎬
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# 🚀 Apex Media Platform

A high-performance media server hosted on **Hugging Face Spaces** with persistent storage support.

Apex combines an official **Jellyfin** media server with a **Telegram MTProto streaming gateway** (`Pyrogram`) that streams personal media on demand directly from Telegram, without permanently writing full video files to disk.

---

## 📦 Hosted Services & Endpoints

| Application | Path | Internal Port | Description |
| :--- | :--- | :--- | :--- |
| **Jellyfin Media Server** | `/jellyfin/` | `8096` | Official Jellyfin interface (Direct Play media, Continue Watching, Movies & Shows). |
| **Apex Gateway** | `/` | `7860` | Nginx + FastAPI proxy frontend (this dashboard). |
| **Gateway Health** | `/health` | `8000` | Health status and upstream diagnostics. |
| **Telegram Streamer** | `/tg-stream/` | `8080` | MTProto streamer (range streaming, webhook ingestion, health). |
| **Ops / Data API** | `/apex/ops/*` | `8000` | Admin-gated access to the `/data` volume (tree view, Jellyfin reset/init/scan). |

> **Ops API note:** every `/apex/ops/*` route requires an
> `Authorization: Bearer <key>` header where `<key>` matches the space's
> `APEX_OPS_KEY` (falling back to `APEX_SECRET_KEY` or `HF_TOKEN`). This is how
> the software storage volume can be inspected and re-initialized from outside
> the container.

---

## ⚙️ Configuration & Environment Secrets

Configure these in **HF Space Settings → Variables and secrets**:

| Variable | Description |
| :--- | :--- |
| `TELEGRAM_API_ID` | Telegram API application ID |
| `TELEGRAM_API_HASH` | Telegram API application hash |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot token for MTProto authentication |
| `API_ID` / `API_HASH` | FileToLink-compatible fallbacks for the shared Telegram API credentials |
| `JELLYFIN_MULTI_TOKEN1`, `JELLYFIN_MULTI_TOKEN2`, ... | Jellyfin-only temporary playback bots |
| `TELEGRAM_ALLOWED_CHAT_IDS` | Comma-separated list of allowed source channel/group chat IDs |
| `TMDB_API_KEY` | The Movie Database v3 API key for automated metadata & poster fetching |
| `APEX_SECRET_KEY` | Secret key protecting the `/apex/ops/*` admin endpoints |
| `APEX_OPS_KEY` | Optional dedicated key for `/apex/ops/*` (falls back to `APEX_SECRET_KEY` / `HF_TOKEN`) |
| `APEX_WEBHOOK_SECRET` | Optional secret token required by Telegram webhook posts |

> Legacy `TG_API_ID` / `TG_API_HASH` / `TG_BOT_TOKEN` / `TG_CHANNEL_ID` variable
> names are also accepted as fallbacks to keep existing spaces working.
> Jellyfin does not use FileToLink's `BOT_TOKEN`; its primary bot remains
> configured independently through `TELEGRAM_BOT_TOKEN`.

---

## 🔧 Jellyfin Integration

The Telegram streamer:
1. Receives channel posts (via `setWebhook` or the in-app webhook route).
2. Indexes the message `file_id` into `/data/jellyfin/file_ids.json`.
3. Writes lightweight `.strm` pointers into `/data/jellyfin/media/` that point at the
   internal streaming endpoint (`http://127.0.0.1:8080/stream/{chat_id}/{message_id}/video.mp4`).
4. Fetches TMDB poster art and triggers a Jellyfin library refresh.

Obsolete Go-era `.strm` files (containing `8084` / `apx_`) are purged automatically on boot.

---

## 💾 Storage Architecture

* **`/data` (Attached HF Storage Bucket):**
  * Jellyfin configuration, database, cache and logs under `/data/jellyfin/`.
  * Virtual media library (`/data/jellyfin/media/Movies`, `/data/jellyfin/media/TV Shows`)
    with `.strm` pointers, `.nfo` metadata and posters.
  * Telegram file-index cache (`/data/jellyfin/file_ids.json`).
  * Apex session state (`/data/apex/session/`) and backups (`/data/apex/backups/`).
* **`/tmp` (High-Speed Ephemeral Disk):**
  * Temporary chunk cache for HTTP Range video streaming.

### Media catalog, duplicates, and re-publishing

The streamer maintains a durable SQLite catalog at
`/data/jellyfin/media_catalog.sqlite`. Telegram source identity
(`chat_id` + `message_id`) is tracked separately from a canonical movie or
episode identity, so repeated uploads do not create duplicate Jellyfin
entries. Existing `file_ids.json` and subtitle cache data remain readable for
backward-compatible migration.

If a publication is missing, a repeated upload recreates its `.strm` and
metadata publication instead of being skipped. The streamer also exposes
`/tg-stream/reconcile` to repair missing publications and `/tg-stream/republish`
to explicitly republish an indexed source:

```bash
curl -X POST "https://<space>/tg-stream/republish?chat_id=-100123&message_id=42"
curl -X POST "https://<space>/tg-stream/reconcile"
```

The default runtime profile is deliberately CPU-conservative for a small
Hugging Face Space: eight global streams, two streams per Telegram client,
two MTProto transmissions per bot, and one metadata worker. Extra Telegram
clients start with a short delay so a restart does not make all Jellyfin
temporary bots reconnect at once. These can be
tuned with `APEX_STREAM_MAX_GLOBAL`, `APEX_STREAM_MAX_PER_CLIENT`,
`APEX_TELEGRAM_MAX_CONCURRENT`, `APEX_TELEGRAM_EXTRA_START_DELAY`, and
`APEX_METADATA_WORKERS`.

When Telegram returns `FloodWait`, the affected Jellyfin client is placed in
cooldown for at least Telegram's requested duration and is excluded from
failover selection during that period. This prevents tight retry loops while
another temporary bot serves the request.

Jellyfin temporary bots are intentionally separate from FileToLink's
`MULTI_TOKEN1`, `MULTI_TOKEN2`, and later variables. Configure the Jellyfin
pool with `JELLYFIN_MULTI_TOKEN1`, `JELLYFIN_MULTI_TOKEN2`, and so on.
Both services can then stream at the same time without selecting the same
Telegram bot account.

### Ingestion review and diagnostics

Uploads with an unidentified or low-confidence title are stored in the durable
catalog review queue instead of being published as `Unknown Media`. Review and
maintenance endpoints require a bearer token matching `APEX_OPS_KEY`,
`APEX_SECRET_KEY`, or `TG_REVIEW_ADMIN_KEY`:

```bash
curl -H "Authorization: Bearer <admin-key>" \
  "https://<space>/tg-stream/review?status=review"

curl -H "Authorization: Bearer <admin-key>" \
  "https://<space>/tg-stream/diagnostics/<chat-id>/<message-id>"

curl -X POST -H "Authorization: Bearer <admin-key>" \
  "https://<space>/tg-stream/reconcile"
```

The catalog runs a low-frequency Jellyfin duplicate reconciliation loop. Its
minimum interval is five minutes and can be increased with
`APEX_RECONCILE_INTERVAL` (seconds, default `900`). The review queue preserves
the original filename, caption, parsed metadata, confidence, and retry state
across restarts.

Review jobs can be approved with a corrected filename or rejected:

```bash
curl -X POST -H "Authorization: Bearer <admin-key>" \
  -H "Content-Type: application/json" \
  -d '{"file_name":"Example Movie 2024 1080p.mkv"}' \
  "https://<space>/tg-stream/review/<chat-id>/<message-id>/approve"

curl -X POST -H "Authorization: Bearer <admin-key>" \
  "https://<space>/tg-stream/review/<chat-id>/<message-id>/reject"
```

Optional signed stream URLs are enabled by setting
`APEX_STREAM_SIGNING_KEY`. Set `APEX_REQUIRE_SIGNED_STREAMS=true` only after
all existing `.strm` files have been regenerated, because legacy unsigned
`.strm` pointers are intentionally accepted while migration is in progress.
Signed pointers expire after 24 hours and are refreshed on reconciliation.

The catalog also records series episode identities and source variants, which
supports duplicate-episode detection and season completeness reporting without
creating duplicate Jellyfin publications.

---

## 🔐 Accessing & Re-initializing `/data`

Because persistent storage is only mounted inside the space container, the gateway
exposes gated endpoints (protected by `APEX_SECRET_KEY`):

```bash
# Inspect the volume tree
curl -H "Authorization: Bearer $APEX_OPS_KEY" \
  "https://jishnupg-apex.hf.space/apex/ops/tree?path=/data"

# Wipe & rebuild the Jellyfin folder layout (destructive)
curl -X POST -H "Authorization: Bearer $APEX_OPS_KEY" \
  "https://jishnupg-apex.hf.space/apex/ops/jellyfin/reset"

# Idempotently create the standard directory skeleton
curl -X POST -H "Authorization: Bearer $APEX_OPS_KEY" \
  "https://jishnupg-apex.hf.space/apex/ops/jellyfin/init"

# Trigger a Jellyfin library refresh once booted
curl -X POST -H "Authorization: Bearer $APEX_OPS_KEY" \
  "https://jishnupg-apex.hf.space/apex/ops/jellyfin/scan"
```

---

## 📄 License & Credits
* [Jellyfin](https://jellyfin.org/) — GNU GPL
* [Pyrogram](https://github.com/pyrogram/pyrogram) — LGPLv3
* Powered by [Hugging Face Spaces](https://huggingface.co/spaces)