# Thunder/bot/plugins/ott_autopilot.py
"""
Daily Curated OTT Release Updates Autopilot:
- Curates exclusively famous, trending, and top-anticipated movies & series (e.g. Ramayana, Jailer 2, Godzilla Minus One, etc.).
- Strict filtering against obscure low-grade indie releases, transactional rent spam, or zero-vote filler.
- Formats:
    Upcoming: 📣 '{title}' {year} {language} {Movie/Series} Streaming {date} From {platform}
    Now Streaming: ✅ '{title}' {year} {language} {Movie/Series} Streaming Now From {platform}
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

# Major verified OTT platforms
MAJOR_OTT_PROVIDERS = {
    8: "Netflix",
    119: "Amazon Prime Video",
    122: "JioHotstar",
    232: "Zee5",
    337: "JioCinema",
    350: "Apple TV+",
    384: "SonyLIV",
    429: "ManoramaMAX",
    608: "Aha",
    613: "Sun NXT",
    614: "Simply South",
    1796: "Lionsgate Play",
}

_AUTOPILOT_RUNNING = False
_LAST_RUN_DATE: Optional[str] = None


def get_tmdb_key() -> str:
    return getattr(Var, "TMDB_API_KEY", "").strip()


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
    if provider_id and provider_id in MAJOR_OTT_PROVIDERS:
        return MAJOR_OTT_PROVIDERS[provider_id]

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
    """Extracts major subscription OTT platforms, strictly ignoring low-grade rent/buy transactions."""
    if not watch_data or not isinstance(watch_data, dict):
        return None
    results = watch_data.get("results", {})
    region_data = results.get(region) or results.get("IN") or results.get("US") or {}

    # 1. Primary: Flatrate subscription or free streaming
    for category in ("flatrate", "free", "ads"):
        items = region_data.get(category, [])
        if isinstance(items, list) and items:
            for provider in items:
                pid = provider.get("provider_id")
                pname = provider.get("provider_name", "")
                if pid in MAJOR_OTT_PROVIDERS:
                    return MAJOR_OTT_PROVIDERS[pid]
                if pname:
                    norm = normalize_provider_name(pname, pid)
                    if norm:
                        return norm

    # 2. Secondary fallback: Premier streaming stores (Apple TV+ or Amazon Prime Video)
    for category in ("rent", "buy"):
        items = region_data.get(category, [])
        if isinstance(items, list) and items:
            for provider in items:
                pid = provider.get("provider_id")
                if pid in (350, 119):
                    return MAJOR_OTT_PROVIDERS.get(pid, "Amazon Prime Video")

    return None


async def process_and_post_ott_updates(client: Client, manual: bool = False) -> Dict[str, int]:
    """Curates only famous, trending blockbusters and A-list series for broadcasting."""
    global _LAST_RUN_DATE
    target_channel = get_target_channel()
    if not target_channel:
        logger.warning("[OTT-AUTOPILOT] No target channel configured (set OTT_CHANNEL_ID or FORCE_CHANNEL_ID).")
        return {"scanned": 0, "posted": 0, "skipped": 0, "low_pop_skipped": 0, "errors": 0}

    api_key = get_tmdb_key()
    if not api_key:
        logger.warning("[OTT-AUTOPILOT] TMDB_API_KEY is not set. Autopilot scan skipped.")
        return {"scanned": 0, "posted": 0, "skipped": 0, "low_pop_skipped": 0, "errors": 0}

    now_local = get_local_now()
    today = now_local.date()
    yesterday = today - datetime.timedelta(days=10)
    future_45d = today + datetime.timedelta(days=45)

    MIN_POPULARITY_REGIONAL = float(getattr(Var, "OTT_MIN_POPULARITY_REGIONAL", 14.0))
    MIN_POPULARITY_GLOBAL = float(getattr(Var, "OTT_MIN_POPULARITY_GLOBAL", 22.0))
    DAILY_POST_LIMIT = int(getattr(Var, "OTT_DAILY_LIMIT", 8))

    stats = {"scanned": 0, "posted": 0, "skipped": 0, "low_pop_skipped": 0, "errors": 0}

    async with httpx.AsyncClient(headers={"User-Agent": "FlashFile-OTT-Bot/3.0"}) as http_client:
        candidate_pool: List[Dict[str, Any]] = []
        seen_cand = set()

        # =========================================================================
        # 1. TMDB Official Trending Feeds (High-Priority Global & National Hype)
        # =========================================================================
        trending_movie = await fetch_tmdb_json(http_client, "/trending/movie/week", {})
        if trending_movie and "results" in trending_movie:
            for item in trending_movie["results"][:20]:
                mid = item.get("id")
                if mid and (mid, "movie") not in seen_cand:
                    seen_cand.add((mid, "movie"))
                    candidate_pool.append({
                        "id": mid,
                        "type": "movie",
                        "popularity": float(item.get("popularity", 0.0)),
                        "is_trending": True,
                        "initial_title": item.get("title", ""),
                    })

        trending_tv = await fetch_tmdb_json(http_client, "/trending/tv/week", {})
        if trending_tv and "results" in trending_tv:
            for item in trending_tv["results"][:16]:
                tid = item.get("id")
                if tid and (tid, "tv") not in seen_cand:
                    seen_cand.add((tid, "tv"))
                    candidate_pool.append({
                        "id": tid,
                        "type": "tv",
                        "popularity": float(item.get("popularity", 0.0)),
                        "is_trending": True,
                        "initial_title": item.get("name", ""),
                    })

        # =========================================================================
        # 2. High-Impact Indian Cinema & Series (Malayalam, Tamil, Telugu, Hindi, Kannada)
        # =========================================================================
        indian_langs = ["hi", "ta", "te", "ml", "kn"]
        for lang in indian_langs:
            # High-popularity movies in release window
            params = {
                "watch_region": "IN",
                "with_original_language": lang,
                "primary_release_date.gte": yesterday.isoformat(),
                "primary_release_date.lte": future_45d.isoformat(),
                "sort_by": "popularity.desc",
                "page": 1,
            }
            res_m = await fetch_tmdb_json(http_client, "/discover/movie", params)
            if res_m and "results" in res_m:
                for item in res_m["results"][:6]:
                    mid = item.get("id")
                    pop = float(item.get("popularity", 0.0))
                    # Only accept items meeting popularity floor
                    if mid and (mid, "movie") not in seen_cand and pop >= MIN_POPULARITY_REGIONAL:
                        seen_cand.add((mid, "movie"))
                        candidate_pool.append({
                            "id": mid,
                            "type": "movie",
                            "popularity": pop,
                            "is_trending": False,
                            "initial_title": item.get("title", ""),
                        })

            # High-popularity series
            params_tv = {
                "watch_region": "IN",
                "with_original_language": lang,
                "first_air_date.gte": yesterday.isoformat(),
                "first_air_date.lte": future_45d.isoformat(),
                "sort_by": "popularity.desc",
                "page": 1,
            }
            res_tv = await fetch_tmdb_json(http_client, "/discover/tv", params_tv)
            if res_tv and "results" in res_tv:
                for item in res_tv["results"][:4]:
                    tid = item.get("id")
                    pop = float(item.get("popularity", 0.0))
                    if tid and (tid, "tv") not in seen_cand and pop >= (MIN_POPULARITY_REGIONAL - 2.0):
                        seen_cand.add((tid, "tv"))
                        candidate_pool.append({
                            "id": tid,
                            "type": "tv",
                            "popularity": pop,
                            "is_trending": False,
                            "initial_title": item.get("name", ""),
                        })

        stats["scanned"] = len(candidate_pool)
        if not candidate_pool:
            logger.info("[OTT-AUTOPILOT] No candidate releases found on TMDB.")
            return stats

        # =========================================================================
        # 3. Detailed Inspection, OTT Platform Verification & Fame Scoring
        # =========================================================================
        verified_announcements = []

        for cand in candidate_pool:
            tmdb_id = cand["id"]
            media_type = cand["type"]
            endpoint = f"/{media_type}/{tmdb_id}"

            details = await fetch_tmdb_json(
                http_client,
                endpoint,
                {"append_to_response": "watch/providers"}
            )
            if not details:
                continue

            # Check watch providers
            watch_data = details.get("watch/providers")
            platform = extract_primary_ott_platform(watch_data, region="IN")
            if not platform:
                continue

            title = details.get("title") or details.get("name") or cand.get("initial_title") or "Untitled"
            pop = float(details.get("popularity") or cand.get("popularity") or 0.0)
            votes = int(details.get("vote_count") or 0)
            vote_avg = float(details.get("vote_average") or 0.0)
            orig_lang = details.get("original_language", "")
            is_indian = orig_lang in ("hi", "ta", "te", "ml", "kn", "bn", "mr")

            # --- Strict Fame & Quality Filter ---
            # Exclude obscure titles with low popularity and no votes
            req_pop = MIN_POPULARITY_REGIONAL if is_indian else MIN_POPULARITY_GLOBAL
            if not cand.get("is_trending") and pop < req_pop and votes < 10:
                stats["low_pop_skipped"] += 1
                continue

            release_date_raw = details.get("release_date") or details.get("first_air_date") or ""
            year = release_date_raw[:4] if len(release_date_raw) >= 4 else str(today.year)
            language = get_language_name(orig_lang)
            media_kind = "Movie" if media_type == "movie" else "Series"

            is_now, date_str = format_release_date(release_date_raw, today)

            # Deduplication: distinct record for upcoming announcements vs streaming now
            media_key = f"{media_type}_{'now' if is_now else 'upcoming'}"
            is_already_posted = await db.is_ott_posted(tmdb_id, media_key)
            if is_already_posted:
                stats["skipped"] += 1
                continue

            # Calculate Hype & Quality Score for Ranking
            # Highest buzz & most famous releases get prioritized
            buzz_score = pop
            if cand.get("is_trending"):
                buzz_score += 40.0
            if votes >= 20:
                buzz_score += min(30.0, votes * 0.1) + (vote_avg * 2.0)
            if is_indian:
                buzz_score += 15.0  # Regional audience priority

            if is_now:
                message_text = f"✅ '{title}' {year} {language} {media_kind} Streaming Now From {platform}"
            else:
                message_text = f"📣 '{title}' {year} {language} {media_kind} Streaming {date_str} From {platform}"

            verified_announcements.append({
                "tmdb_id": tmdb_id,
                "media_key": media_key,
                "title": title,
                "platform": platform,
                "message_text": message_text,
                "score": buzz_score,
                "pop": pop,
            })

        # =========================================================================
        # 4. Sort by Buzz Score and Broadcast the Top-Tier Releases
        # =========================================================================
        verified_announcements.sort(key=lambda x: x["score"], reverse=True)

        to_post = verified_announcements[:DAILY_POST_LIMIT] if not manual else verified_announcements[:DAILY_POST_LIMIT * 2]

        for item in to_post:
            try:
                await client.send_message(
                    chat_id=target_channel,
                    text=item["message_text"],
                    disable_web_page_preview=True
                )

                # Record in database
                await db.mark_ott_posted(item["tmdb_id"], item["media_key"], item["title"], item["platform"])
                stats["posted"] += 1
                logger.info(f"[OTT-AUTOPILOT] Published Curated OTT update (Score: {item['score']:.1f}, Pop: {item['pop']:.1f}): {item['message_text']}")

                # Safe pacing between channel posts
                await asyncio.sleep(3)

            except FloodWait as e:
                logger.warning(f"[OTT-AUTOPILOT] FloodWait {e.value}s while posting {item['title']}")
                await asyncio.sleep(e.value + 1)
            except Exception as e:
                logger.error(f"[OTT-AUTOPILOT] Failed to post {item['title']}: {e}", exc_info=True)
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
        f"[OTT-AUTOPILOT] Curated Hype OTT Updates Scheduler initialized for "
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
                    logger.info(f"[OTT-AUTOPILOT] 09:00 AM trigger activated for {today_str}. Initiating curated OTT scan...")
                    _LAST_RUN_DATE = today_str
                    res = await process_and_post_ott_updates(StreamBot, manual=False)
                    logger.info(f"[OTT-AUTOPILOT] Daily curated OTT scan completed: {res}")

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
# Owner Admin Commands for Curated OTT Updates
# =========================================================================

@StreamBot.on_message(filters.command(["post_ott", "scan_ott"]) & filters.private)
async def post_ott_command(client: Client, message: Message):
    if message.from_user.id != Var.OWNER_ID:
        return

    status_msg = await message.reply_text("🔍 **Scanning TMDB for famous & trending OTT release updates...**", quote=True)
    res = await process_and_post_ott_updates(client, manual=True)

    report = (
        f"📊 **Curated OTT Updates Scan Complete!**\n\n"
        f"• **Candidates Scanned:** `{res['scanned']}`\n"
        f"• **New Hype Releases Published:** `{res['posted']}`\n"
        f"• **Already Published (Skipped):** `{res['skipped']}`\n"
        f"• **Low-Buzz / Non-Trending Skipped:** `{res.get('low_pop_skipped', 0)}`\n"
        f"• **Errors:** `{res['errors']}`\n\n"
        f"*(ℹ️ Note: Only famous, trending blockbusters and top-rated series are broadcast. Zero low-grade spam.)*"
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
        f"⚡ **Curated Hype OTT Updates Autopilot Status** ⚡\n\n"
        f"• **Autopilot Active:** `{getattr(Var, 'OTT_AUTOPILOT', True)}`\n"
        f"• **Target Channel:** `{channel_repr}`\n"
        f"• **Filter Mode:** `Trending & Blockbusters Only (High Popularity)`\n"
        f"• **Supported Media:** `Movies & TV Series`\n"
        f"• **TMDB API Key:** `{'Configured ✅' if key_configured else 'Missing (Set TMDB_API_KEY) ⚠️'}`\n"
        f"• **Target Region:** `{getattr(Var, 'OTT_REGION', 'IN')} (India)`\n"
        f"• **Schedule Time:** `{hour:02d}:{minute:02d}` Daily (UTC+{offset})\n"
        f"• **Current Local Time:** `{now_local.strftime('%Y-%m-%d %H:%M:%S')}`\n"
        f"• **Total Updates Posted to Date:** `{total_posted}`\n"
        f"• **Last Daily Run Date:** `{_LAST_RUN_DATE or 'None yet'}`\n\n"
        f"*(To trigger an immediate curated scan and post, send /post_ott)*"
    )
    await message.reply_text(text, quote=True)
