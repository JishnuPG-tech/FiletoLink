# Thunder/bot/plugins/ott_autopilot.py
"""
Daily OTT Release Updates Autopilot:
- Posts concise, clean OTT release updates directly to the channel.
- Formats:
    Upcoming: 📣 '{title}' {year} {language} Movie Streaming {date} From {platform}
    Now Streaming: ✅ '{title}' {year} {language} Movie Streaming Now From {platform}
- No posters, no synopsis, no rating cards, no buttons - pure clean text announcements.
- Deduplication via MongoDB: never reposts duplicate announcements.
- Admin commands: /post_ott (manual scan), /ott_status (status & stats).
"""

import asyncio
import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message

from Thunder.bot import StreamBot
from Thunder.utils.database import db
from Thunder.utils.logger import logger
from Thunder.vars import Var

TMDB_BASE = "https://api.themoviedb.org/3"
DEFAULT_TMDB_KEY = "c189b870db5d1a87c1cb51cae8bfa178"

LANGUAGE_MAP = {
    "ml": "Malayalam",
    "ta": "Tamil",
    "te": "Telugu",
    "hi": "Hindi",
    "kn": "Kannada",
    "en": "English",
    "bn": "Bengali",
    "mr": "Marathi",
    "pa": "Punjabi",
    "gu": "Gujarati",
    "ko": "Korean",
    "ja": "Japanese",
    "es": "Spanish",
    "fr": "French",
}

_AUTOPILOT_RUNNING = False
_LAST_RUN_DATE: Optional[str] = None


def get_tmdb_key() -> str:
    return getattr(Var, "TMDB_API_KEY", "").strip() or DEFAULT_TMDB_KEY


def get_target_channel() -> Optional[int]:
    return getattr(Var, "OTT_CHANNEL_ID", None) or getattr(Var, "FORCE_CHANNEL_ID", None)


def get_local_now() -> datetime.datetime:
    offset = getattr(Var, "OTT_TIMEZONE_OFFSET", 5.5)
    tz = datetime.timezone(datetime.timedelta(hours=offset))
    return datetime.datetime.now(tz)


def get_language_name(code: str) -> str:
    if not code:
        return "Cinema"
    code_lower = code.lower().strip()
    return LANGUAGE_MAP.get(code_lower, code.capitalize())


def normalize_provider_name(provider_name: str, provider_id: Optional[int] = None) -> str:
    name_clean = provider_name.strip()
    name_lower = name_clean.lower()

    if "hotstar" in name_lower or provider_id == 122:
        return "JioHotstar"
    if "prime" in name_lower or "amazon" in name_lower or provider_id == 119:
        return "Amazon Prime Video"
    if "netflix" in name_lower or provider_id == 8:
        return "Netflix"
    if "zee5" in name_lower or "zee" in name_lower or provider_id == 232:
        return "Zee5"
    if "sonyliv" in name_lower or "sony" in name_lower or provider_id == 384:
        return "SonyLIV"
    if "jiocinema" in name_lower or "jio" in name_lower or provider_id == 337:
        return "JioCinema"
    if "apple" in name_lower or provider_id == 350:
        return "Apple TV+"
    if "manorama" in name_lower or provider_id == 429:
        return "ManoramaMAX"
    if "aha" in name_lower or provider_id == 608:
        return "Aha"
    if "sun nxt" in name_lower or "sunnxt" in name_lower or provider_id == 613:
        return "Sun NXT"
    if "simply south" in name_lower or provider_id == 614:
        return "Simply South"
    if "lionsgate" in name_lower or provider_id == 1796:
        return "Lionsgate Play"

    return name_clean


def format_release_date(release_date_str: str, today: datetime.date) -> Tuple[bool, str]:
    """
    Returns (is_now, formatted_date_string)
    e.g. (True, "Now")
    or   (False, "November 6th")
    """
    if not release_date_str:
        return True, "Now"
    try:
        rdate = datetime.datetime.strptime(release_date_str[:10], "%Y-%m-%d").date()
    except Exception:
        return True, "Now"

    if rdate <= today:
        return True, "Now"

    day = rdate.day
    if 11 <= day <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    month_name = rdate.strftime("%B")
    return False, f"{month_name} {day}{suffix}"


async def fetch_tmdb_json(client: httpx.AsyncClient, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    api_key = get_tmdb_key()
    if not api_key:
        return None
    full_params = {"api_key": api_key, **params}
    url = f"{TMDB_BASE}{endpoint}"
    try:
        resp = await client.get(url, params=full_params, timeout=14.0)
        if resp.status_code == 200:
            return resp.json()
        logger.debug(f"[OTT-AUTOPILOT] TMDB {endpoint} returned status {resp.status_code}")
        return None
    except Exception as e:
        logger.debug(f"[OTT-AUTOPILOT] TMDB error for {endpoint}: {e}")
        return None


def extract_primary_ott_platform(watch_data: Optional[Dict[str, Any]], region: str = "IN") -> Optional[str]:
    if not watch_data or not isinstance(watch_data, dict):
        return None
    results = watch_data.get("results", {})
    region_data = results.get(region) or results.get("IN") or results.get("US") or {}

    for category in ("flatrate", "free", "ads", "rent", "buy"):
        items = region_data.get(category, [])
        if isinstance(items, list) and items:
            provider = items[0]
            pid = provider.get("provider_id")
            pname = provider.get("provider_name", "")
            if pname:
                return normalize_provider_name(pname, pid)

    return None


async def process_and_post_ott_updates(client: Client, manual: bool = False) -> Dict[str, int]:
    global _LAST_RUN_DATE
    target_channel = get_target_channel()
    if not target_channel:
        logger.warning("[OTT-AUTOPILOT] No target channel configured (set OTT_CHANNEL_ID or FORCE_CHANNEL_ID).")
        return {"scanned": 0, "posted": 0, "skipped": 0, "errors": 0}

    now_local = get_local_now()
    today = now_local.date()
    yesterday = today - datetime.timedelta(days=7)
    future_30d = today + datetime.timedelta(days=35)

    stats = {"scanned": 0, "posted": 0, "skipped": 0, "errors": 0}

    async with httpx.AsyncClient(headers={"User-Agent": "FlashFile-OTT-Bot/2.0"}) as http_client:
        candidate_ids = []
        seen_cand = set()

        # Multi-query strategy to catch Malayalam, Tamil, Telugu, Hindi and Pan-India OTT titles
        query_configs = [
            # 1. Malayalam OTT releases
            {"with_original_language": "ml", "sort_by": "popularity.desc"},
            # 2. Tamil OTT releases
            {"with_original_language": "ta", "sort_by": "popularity.desc"},
            # 3. Telugu OTT releases
            {"with_original_language": "te", "sort_by": "popularity.desc"},
            # 4. Hindi OTT releases
            {"with_original_language": "hi", "sort_by": "popularity.desc"},
            # 5. General India Major OTT streaming
            {
                "region": "IN",
                "watch_region": "IN",
                "with_watch_providers": "8|119|122|232|337|384|429|608|613",
                "sort_by": "popularity.desc",
            },
        ]

        for q in query_configs:
            params = {
                "watch_region": "IN",
                "primary_release_date.gte": yesterday.isoformat(),
                "primary_release_date.lte": future_30d.isoformat(),
                "page": 1,
                **q,
            }
            res = await fetch_tmdb_json(http_client, "/discover/movie", params)
            if res and "results" in res:
                for item in res["results"][:12]:
                    mid = item.get("id")
                    if mid and (mid, "movie") not in seen_cand:
                        seen_cand.add((mid, "movie"))
                        candidate_ids.append((mid, "movie"))

        stats["scanned"] = len(candidate_ids)
        if not candidate_ids:
            logger.info("[OTT-AUTOPILOT] No candidate releases found on TMDB.")
            return stats

        for tmdb_id, media_type in candidate_ids:
            endpoint = f"/{media_type}/{tmdb_id}"
            details = await fetch_tmdb_json(
                http_client,
                endpoint,
                {"append_to_response": "watch/providers"}
            )
            if not details:
                continue

            # Extract platform
            watch_data = details.get("watch/providers")
            platform = extract_primary_ott_platform(watch_data, region="IN")
            if not platform:
                continue

            title = details.get("title") or details.get("name") or "Untitled"
            release_date_raw = details.get("release_date") or details.get("first_air_date") or ""
            year = release_date_raw[:4] if len(release_date_raw) >= 4 else str(today.year)
            orig_lang = details.get("original_language", "")
            language = get_language_name(orig_lang)
            media_kind = "Movie" if media_type == "movie" else "Series"

            is_now, date_str = format_release_date(release_date_raw, today)

            # Deduplication: distinct record for upcoming announcements vs streaming now
            media_key = f"{media_type}_{'now' if is_now else 'upcoming'}"

            is_already_posted = await db.is_ott_posted(tmdb_id, media_key)
            if is_already_posted:
                stats["skipped"] += 1
                continue

            # Format the exact announcement message requested by the user
            if is_now:
                message_text = f"✅ '{title}' {year} {language} {media_kind} Streaming Now From {platform}"
            else:
                message_text = f"📣 '{title}' {year} {language} {media_kind} Streaming {date_str} From {platform}"

            try:
                # Post pure clean text message with no other additions
                await client.send_message(
                    chat_id=target_channel,
                    text=message_text,
                    disable_web_page_preview=True
                )

                # Record in database
                await db.mark_ott_posted(tmdb_id, media_key, title, platform)
                stats["posted"] += 1
                logger.info(f"[OTT-AUTOPILOT] Published OTT update: {message_text}")

                # Rate limiting between posts to prevent Telegram FloodWait
                await asyncio.sleep(3)

            except FloodWait as e:
                logger.warning(f"[OTT-AUTOPILOT] FloodWait {e.value}s while posting {title}")
                await asyncio.sleep(e.value + 1)
            except Exception as e:
                logger.error(f"[OTT-AUTOPILOT] Failed to post {title}: {e}", exc_info=True)
                stats["errors"] += 1

    return stats


async def ott_scheduler_worker():
    """Background async daemon that triggers daily at 09:00 AM local time."""
    global _AUTOPILOT_RUNNING, _LAST_RUN_DATE
    if _AUTOPILOT_RUNNING:
        return
    _AUTOPILOT_RUNNING = True

    hour = getattr(Var, "OTT_SCHEDULE_HOUR", 9)
    minute = getattr(Var, "OTT_SCHEDULE_MINUTE", 0)
    offset = getattr(Var, "OTT_TIMEZONE_OFFSET", 5.5)

    logger.info(
        f"[OTT-AUTOPILOT] Clean OTT Updates Scheduler worker initialized for "
        f"{hour:02d}:{minute:02d} daily (UTC+{offset})."
    )

    while True:
        try:
            if getattr(Var, "OTT_AUTOPILOT", True):
                now_local = get_local_now()
                today_str = now_local.strftime("%Y-%m-%d")

                is_target_hour = now_local.hour == hour
                is_target_minute = now_local.minute == minute

                if is_target_hour and is_target_minute and _LAST_RUN_DATE != today_str:
                    logger.info(f"[OTT-AUTOPILOT] 09:00 AM trigger activated for {today_str}. Initiating clean OTT scan...")
                    _LAST_RUN_DATE = today_str
                    res = await process_and_post_ott_updates(StreamBot, manual=False)
                    logger.info(f"[OTT-AUTOPILOT] Daily clean OTT scan completed: {res}")

            await asyncio.sleep(30)
        except Exception as e:
            logger.error(f"[OTT-AUTOPILOT] Scheduler loop exception: {e}", exc_info=True)
            await asyncio.sleep(60)


# Start Scheduler safely on module load or active loop
try:
    loop = asyncio.get_running_loop()
    loop.create_task(ott_scheduler_worker())
except RuntimeError:
    pass


# =========================================================================
# Owner Admin Commands for Clean OTT Updates
# =========================================================================

@StreamBot.on_message(filters.command(["post_ott", "scan_ott"]) & filters.private)
async def post_ott_command(client: Client, message: Message):
    if message.from_user.id != Var.OWNER_ID:
        return

    status_msg = await message.reply_text("🔍 **Scanning TMDB for new OTT release updates...**", quote=True)
    res = await process_and_post_ott_updates(client, manual=True)

    report = (
        f"📊 **OTT Updates Scan Complete!**\n\n"
        f"• **Candidates Scanned:** `{res['scanned']}`\n"
        f"• **New Updates Published:** `{res['posted']}`\n"
        f"• **Already Posted (Skipped):** `{res['skipped']}`\n"
        f"• **Errors:** `{res['errors']}`\n\n"
        f"*(ℹ️ Note: If 0 items were posted, all current announcements have already been published. Zero duplicate messages allowed.)*"
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
    hour = getattr(Var, "OTT_SCHEDULE_HOUR", 9)
    minute = getattr(Var, "OTT_SCHEDULE_MINUTE", 0)
    offset = getattr(Var, "OTT_TIMEZONE_OFFSET", 5.5)

    text = (
        f"⚡ **Clean OTT Updates Autopilot Status** ⚡\n\n"
        f"• **Autopilot Active:** `{getattr(Var, 'OTT_AUTOPILOT', True)}`\n"
        f"• **Target Channel:** `{channel_repr}`\n"
        f"• **TMDB API Key:** `{'Configured ✅' if key_configured else 'Using Default Key ✅'}`\n"
        f"• **Target Region:** `{getattr(Var, 'OTT_REGION', 'IN')} (India)`\n"
        f"• **Schedule Time:** `{hour:02d}:{minute:02d}` Daily (UTC+{offset})\n"
        f"• **Current Local Time:** `{now_local.strftime('%Y-%m-%d %H:%M:%S')}`\n"
        f"• **Total Updates Posted to Date:** `{total_posted}`\n"
        f"• **Last Daily Run Date:** `{_LAST_RUN_DATE or 'None yet'}`\n\n"
        f"*(To trigger an immediate scan and post, send /post_ott)*"
    )
    await message.reply_text(text, quote=True)
