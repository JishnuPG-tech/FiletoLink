# Thunder/bot/plugins/ott_autopilot.py
"""TMDB Daily OTT Releases Autopilot:
- Runs automatically every morning at 09:00 AM (customizable timezone, default IST UTC+5:30).
- Discovers new digital & OTT streaming releases in specified region (default: IN).
- Strict Deduplication via MongoDB: Never posts already-posted items.
- Only posts if new updates exist; if not, posts nothing (zero spam).
- Formats posts professionally with high-res poster, IMDb rating, genres, audio, OTT platforms, trailer & bot stream buttons.
- Admin commands: /post_ott (manual force scan), /ott_status (check schedule & counts).
"""

import asyncio
import datetime
import urllib.parse
from typing import Any, Dict, List, Optional

import httpx
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from Thunder.bot import StreamBot
from Thunder.utils.database import db
from Thunder.utils.logger import logger
from Thunder.vars import Var

TMDB_BASE = "https://api.themoviedb.org/3"
DEFAULT_TMDB_KEY = "c189b870db5d1a87c1cb51cae8bfa178"

# Provider Mapping for professional display with badges
PROVIDER_MAP = {
    8: "🔴 Netflix",
    119: "🔵 Prime Video",
    122: "⭐ Disney+ Hotstar",
    232: "🟡 Zee5",
    337: "🟣 JioCinema",
    350: "🍎 Apple TV+",
    384: "🟢 SonyLIV",
    220: "🟠 MX Player",
    531: "Paramount+",
    283: "Crunchyroll",
    11: "MUBI",
    1796: "Lionsgate Play",
}

_AUTOPILOT_RUNNING = False
_LAST_RUN_DATE: Optional[str] = None


def get_tmdb_key() -> str:
    return Var.TMDB_API_KEY.strip() or DEFAULT_TMDB_KEY


def get_target_channel() -> Optional[int]:
    return Var.OTT_CHANNEL_ID or Var.FORCE_CHANNEL_ID


def get_local_now() -> datetime.datetime:
    tz = datetime.timezone(datetime.timedelta(hours=Var.OTT_TIMEZONE_OFFSET))
    return datetime.datetime.now(tz)


async def fetch_tmdb_json(client: httpx.AsyncClient, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    api_key = get_tmdb_key()
    if not api_key:
        return None
    full_params = {"api_key": api_key, **params}
    url = f"{TMDB_BASE}{endpoint}"
    try:
        resp = await client.get(url, params=full_params, timeout=12.0)
        if resp.status_code == 200:
            return resp.json()
        logger.debug(f"TMDB request {endpoint} returned status {resp.status_code}")
        return None
    except Exception as e:
        logger.debug(f"TMDB request error for {endpoint}: {e}")
        return None


def extract_ott_platforms(watch_data: Optional[Dict[str, Any]], region: str) -> List[str]:
    if not watch_data or not isinstance(watch_data, dict):
        return []
    results = watch_data.get("results", {})
    region_data = results.get(region) or results.get("IN") or results.get("US") or {}

    platforms = []
    seen_ids = set()

    for category in ("flatrate", "free", "ads", "rent", "buy"):
        items = region_data.get(category, [])
        if isinstance(items, list):
            for provider in items:
                pid = provider.get("provider_id")
                pname = provider.get("provider_name", "")
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    display_name = PROVIDER_MAP.get(pid, f"📺 {pname}")
                    platforms.append(display_name)

    return platforms


async def process_and_post_ott_updates(client: Client, manual: bool = False) -> Dict[str, int]:
    global _LAST_RUN_DATE
    target_channel = get_target_channel()
    if not target_channel:
        logger.warning("[OTT-AUTOPILOT] No target channel configured (set OTT_CHANNEL_ID or FORCE_CHANNEL_ID).")
        return {"scanned": 0, "posted": 0, "skipped": 0, "errors": 0}

    today = get_local_now().date()
    yesterday = today - datetime.timedelta(days=1)
    future_7d = today + datetime.timedelta(days=7)

    stats = {"scanned": 0, "posted": 0, "skipped": 0, "errors": 0}

    bot_info = await client.get_me()
    bot_username = bot_info.username or Var.NAME

    async with httpx.AsyncClient(headers={"User-Agent": "Thunder-FileToLink-OTT/1.0"}) as http_client:
        # Discover Movies (Digital & Physical OTT releases)
        movie_params = {
            "region": Var.OTT_REGION,
            "watch_region": Var.OTT_REGION,
            "with_watch_providers": "8|119|122|232|337|350|384|1796|283",
            "with_release_type": "4|5",
            "primary_release_date.gte": yesterday.isoformat(),
            "primary_release_date.lte": future_7d.isoformat(),
            "sort_by": "popularity.desc",
            "page": 1,
        }

        # Discover TV Series
        tv_params = {
            "watch_region": Var.OTT_REGION,
            "with_watch_providers": "8|119|122|232|337|350|384|1796|283",
            "first_air_date.gte": (today - datetime.timedelta(days=3)).isoformat(),
            "first_air_date.lte": future_7d.isoformat(),
            "sort_by": "popularity.desc",
            "page": 1,
        }

        candidates = []

        # 1. Fetch Movies
        movie_res = await fetch_tmdb_json(http_client, "/discover/movie", movie_params)
        if movie_res and "results" in movie_res:
            for item in movie_res["results"][:15]:
                candidates.append((item.get("id"), "movie"))

        # 2. Fetch TV Series
        tv_res = await fetch_tmdb_json(http_client, "/discover/tv", tv_params)
        if tv_res and "results" in tv_res:
            for item in tv_res["results"][:10]:
                candidates.append((item.get("id"), "tv"))

        stats["scanned"] = len(candidates)
        if not candidates:
            logger.info("[OTT-AUTOPILOT] No candidate releases found on TMDB.")
            return stats

        for tmdb_id, media_type in candidates:
            if not tmdb_id:
                continue

            # Strict Deduplication Check in MongoDB
            is_already_posted = await db.is_ott_posted(tmdb_id, media_type)
            if is_already_posted:
                stats["skipped"] += 1
                continue

            # Fetch enriched details including IMDb ID, Videos, and Watch Providers
            endpoint = f"/{media_type}/{tmdb_id}"
            details = await fetch_tmdb_json(
                http_client,
                endpoint,
                {"append_to_response": "external_ids,videos,watch/providers"}
            )
            if not details:
                continue

            title = details.get("title") or details.get("name") or "Untitled"
            poster_path = details.get("poster_path")
            overview = details.get("overview", "").strip()
            vote_avg = details.get("vote_average", 0.0)
            genres_list = [g.get("name") for g in details.get("genres", []) if g.get("name")]
            genres_str = ", ".join(genres_list[:3]) if genres_list else "Cinema"

            release_date_raw = details.get("release_date") or details.get("first_air_date") or ""
            year_str = f" ({release_date_raw[:4]})" if len(release_date_raw) >= 4 else ""

            runtime_mins = details.get("runtime") or (details.get("episode_run_time", [0])[0] if details.get("episode_run_time") else 0)
            runtime_str = f"{runtime_mins // 60}h {runtime_mins % 60}m" if runtime_mins >= 60 else (f"{runtime_mins}m" if runtime_mins > 0 else "")

            # Extract OTT Platforms
            watch_data = details.get("watch/providers")
            platforms = extract_ott_platforms(watch_data, Var.OTT_REGION)
            if not platforms:
                # If no regional provider found, skip to maintain high relevance
                continue

            platforms_display = " • ".join(platforms[:3])

            # Extract Trailer Video
            trailer_url = None
            videos = details.get("videos", {}).get("results", [])
            for vid in videos:
                if vid.get("site") == "YouTube" and vid.get("type") in ("Trailer", "Teaser"):
                    trailer_url = f"https://youtu.be/{vid.get('key')}"
                    break

            # Extract IMDb Info
            ext_ids = details.get("external_ids", {})
            imdb_id = ext_ids.get("imdb_id")
            imdb_url = f"https://www.imdb.com/title/{imdb_id}/" if imdb_id else None

            # Audio languages
            spoken = [l.get("english_name", l.get("name", "")) for l in details.get("spoken_languages", [])]
            languages_str = ", ".join(spoken[:3]) if spoken else "Original Audio"

            # Clean & Truncate Synopsis
            if len(overview) > 350:
                overview = overview[:347].rsplit(" ", 1)[0] + "..."
            overview_quote = f"\n\n📝 *{overview}*" if overview else ""

            # Professional Post Caption
            rating_line = f"⭐ **Rating:** `{vote_avg:.1f}/10`" if vote_avg > 0 else "⭐ **Rating:** `Awaiting Reviews`"
            runtime_line = f" • ⏱️ **Runtime:** `{runtime_str}`" if runtime_str else ""

            caption = (
                f"🎬 **{title}**{year_str}\n"
                f"{rating_line}{runtime_line}\n"
                f"🎭 **Genre:** {genres_str}\n"
                f"📺 **Streaming Platform:** **{platforms_display}**\n"
                f"🔊 **Audio:** {languages_str}"
                f"{overview_quote}\n\n"
                f"⚡ *Instant streaming & direct links available on @{bot_username}*"
            )

            # Build Clean Interactive Buttons
            title_slug = urllib.parse.quote(title.strip().replace(" ", "_"))
            buttons = [
                [
                    InlineKeyboardButton("▶️ Stream / Download on Bot", url=f"https://t.me/{bot_username}?start=search_{title_slug}")
                ]
            ]
            row2 = []
            if trailer_url:
                row2.append(InlineKeyboardButton("🎬 Watch Trailer", url=trailer_url))
            if imdb_url:
                row2.append(InlineKeyboardButton("⭐ IMDb Page", url=imdb_url))
            if row2:
                buttons.append(row2)

            keyboard = InlineKeyboardMarkup(buttons)

            # Poster Image URL
            poster_url = f"https://image.tmdb.org/t/p/w780{poster_path}" if poster_path else None

            try:
                if poster_url:
                    await client.send_photo(
                        chat_id=target_channel,
                        photo=poster_url,
                        caption=caption,
                        reply_markup=keyboard
                    )
                else:
                    await client.send_message(
                        chat_id=target_channel,
                        text=caption,
                        reply_markup=keyboard,
                        disable_web_page_preview=False
                    )

                # Record in MongoDB to guarantee zero duplicate reposts
                await db.mark_ott_posted(tmdb_id, media_type, title, platforms_display)
                stats["posted"] += 1
                logger.info(f"[OTT-AUTOPILOT] Successfully posted OTT update: {title} ({platforms_display})")

                # Sleep 4 seconds between posts to strictly avoid Telegram FloodWait
                await asyncio.sleep(4)

            except FloodWait as e:
                logger.warning(f"[OTT-AUTOPILOT] FloodWait {e.value}s while posting {title}")
                await asyncio.sleep(e.value + 1)
            except Exception as e:
                logger.error(f"[OTT-AUTOPILOT] Failed to post {title}: {e}", exc_info=True)
                stats["errors"] += 1

    return stats


async def ott_scheduler_worker():
    """Background async daemon that triggers at 09:00 AM local time daily."""
    global _AUTOPILOT_RUNNING, _LAST_RUN_DATE
    if _AUTOPILOT_RUNNING:
        return
    _AUTOPILOT_RUNNING = True

    logger.info(
        f"[OTT-AUTOPILOT] Scheduler worker initialized. Scheduled daily for "
        f"{Var.OTT_SCHEDULE_HOUR:02d}:{Var.OTT_SCHEDULE_MINUTE:02d} (UTC+{Var.OTT_TIMEZONE_OFFSET})."
    )

    while True:
        try:
            if Var.OTT_AUTOPILOT:
                now_local = get_local_now()
                today_str = now_local.strftime("%Y-%m-%d")

                is_target_hour = now_local.hour == Var.OTT_SCHEDULE_HOUR
                is_target_minute = now_local.minute == Var.OTT_SCHEDULE_MINUTE

                if is_target_hour and is_target_minute and _LAST_RUN_DATE != today_str:
                    logger.info(f"[OTT-AUTOPILOT] 09:00 AM trigger activated for {today_str}. Initiating OTT scan...")
                    _LAST_RUN_DATE = today_str
                    res = await process_and_post_ott_updates(StreamBot, manual=False)
                    logger.info(f"[OTT-AUTOPILOT] Scan completed: {res}")

            await asyncio.sleep(30)
        except Exception as e:
            logger.error(f"[OTT-AUTOPILOT] Scheduler loop exception: {e}", exc_info=True)
            await asyncio.sleep(60)


# Start Scheduler on module load
asyncio.create_task(ott_scheduler_worker())


# =========================================================================
# Owner Admin Commands for OTT Autopilot
# =========================================================================

@StreamBot.on_message(filters.command(["post_ott", "scan_ott"]) & filters.private)
async def post_ott_command(client: Client, message: Message):
    if message.from_user.id != Var.OWNER_ID:
        return

    status_msg = await message.reply_text("🔍 **Scanning TMDB for new OTT releases...**", quote=True)
    res = await process_and_post_ott_updates(client, manual=True)
    
    report = (
        f"📊 **OTT Autopilot Scan Complete!**\n\n"
        f"• **Candidates Scanned:** `{res['scanned']}`\n"
        f"• **New Posts Published:** `{res['posted']}`\n"
        f"• **Already Posted (Skipped):** `{res['skipped']}`\n"
        f"• **Errors:** `{res['errors']}`\n\n"
        f"*(ℹ️ Note: If 0 items were posted, all available OTT releases have already been published. Zero duplicate posts allowed.)*"
    )
    await status_msg.edit_text(report)


@StreamBot.on_message(filters.command(["ott_status"]) & filters.private)
async def ott_status_command(client: Client, message: Message):
    if message.from_user.id != Var.OWNER_ID:
        return

    channel_id = get_target_channel()
    channel_repr = str(channel_id) if channel_id else "❌ Not configured"
    total_posted = await db.get_ott_posted_count()
    key_configured = bool(get_tmdb_key())

    now_local = get_local_now()

    text = (
        f"⚡ **OTT Autopilot System Status** ⚡\n\n"
        f"• **Autopilot Active:** `{Var.OTT_AUTOPILOT}`\n"
        f"• **Target Channel:** `{channel_repr}`\n"
        f"• **TMDB API Key:** `{'Configured ✅' if key_configured else 'Missing ✖'}`\n"
        f"• **Target Region:** `{Var.OTT_REGION}` (India)\n"
        f"• **Schedule Time:** `{Var.OTT_SCHEDULE_HOUR:02d}:{Var.OTT_SCHEDULE_MINUTE:02d}` Daily (UTC+{Var.OTT_TIMEZONE_OFFSET})\n"
        f"• **Current Local Time:** `{now_local.strftime('%Y-%m-%d %H:%M:%S')}`\n"
        f"• **Total Releases Posted to Date:** `{total_posted}`\n"
        f"• **Last Daily Run Date:** `{_LAST_RUN_DATE or 'None yet'}`\n\n"
        f"*(To trigger an immediate scan, send /post_ott)*"
    )
    await message.reply_text(text, quote=True)
