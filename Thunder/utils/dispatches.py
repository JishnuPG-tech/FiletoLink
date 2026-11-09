# Thunder/utils/dispatches.py
import re
import time
from collections import deque
from typing import Dict, List, Any
from Thunder.utils.logger import logger
from Thunder.utils.human_readable import humanbytes

RECENT_DISPATCHES: deque = deque(maxlen=40)

# Aggressive Unicode emoji & pictograph pattern
EMOJI_PATTERN = re.compile(
    "["
    "\U00010000-\U0010ffff"
    "\u200d"
    "\ufe0f"
    "\u20e3"
    "\u2600-\u27bf"
    "\u2300-\u23ff"
    "\u2b50-\u2b55"
    "]+",
    flags=re.UNICODE
)

def purge_emoji(text: str) -> str:
    """Removes all Unicode emojis, pictographs, symbols, and surrogate artifacts."""
    if not text:
        return ""
    cleaned = EMOJI_PATTERN.sub("", str(text))
    cleaned = re.sub(r"[\ud800-\udfff]", "", cleaned)
    cleaned = re.sub(r"^[\s\-_~•·|/\\#@!?,:;+=]+", "", cleaned)
    cleaned = re.sub(r"[\s\-_~•·|/\\#@!?,:;+=]+$", "", cleaned)
    return cleaned.strip()

def extract_canonical_key(raw: str) -> str:
    """Extracts a normalized canonical title key for deduplicating identical movies/series."""
    cleaned = purge_emoji(raw)
    cleaned = re.sub(r"\.(mkv|mp4|avi|webm|mov|ts|m4v|flac)$", "", cleaned, flags=re.I)
    cleaned = re.sub(r"[@#][\w_]+|t\.me/[\w_]+|https?://\S+|www\.\S+", " ", cleaned)
    cleaned = re.sub(r"\[.*?\]|\{.*?\}", " ", cleaned)
    cleaned = re.sub(r"\((?!\d{4}\)).*?\)", " ", cleaned)
    cleaned = re.sub(r"[\._\-]+", " ", cleaned).strip()

    tv_match = re.search(r"\b(s\d{1,2}|season\s*\d+|episode\s*\d+|e\d{1,2})\b", cleaned, flags=re.I)
    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", cleaned)

    if tv_match:
        base = cleaned[:tv_match.start()].strip()
    elif year_match:
        base = cleaned[:year_match.start()].strip()
    else:
        cut_match = re.search(
            r"\b(2160p|4k|1080p|720p|480p|bluray|brrip|web[\s\-]?dl|webrip|hdrip|dvd|x264|x265|hevc|aac|truehd|atmos|remux|multi|ita|eng|hindi|tamil|malayalam|telugu|kannada)\b",
            cleaned,
            flags=re.I
        )
        if cut_match:
            base = cleaned[:cut_match.start()].strip()
        else:
            base = cleaned

    key = re.sub(r"[^a-zA-Z0-9]+", "", base).lower()
    return key or cleaned.lower()

def record_dispatch(file_name: str, file_size: str = "", stream_url: str = "") -> Dict[str, Any]:
    """Records a live conversion from the active bot session (purging emojis)."""
    clean_name = purge_emoji(file_name)
    if not clean_name:
        return {}
    
    entry = {
        "raw_filename": clean_name,
        "file_size": str(file_size or ""),
        "stream_url": str(stream_url or ""),
        "timestamp": int(time.time()),
        "date": time.strftime("%d %b %Y", time.gmtime()).upper(),
    }
    RECENT_DISPATCHES.appendleft(entry)
    return entry

async def get_live_dispatches_from_sources(limit: int = 30) -> List[Dict[str, Any]]:
    """Fetches real file conversion records, purges all emojis, and guarantees 100% unique movie/series items."""
    items: List[Dict[str, Any]] = []
    seen_keys = set()

    # 1. Real-time dispatches from active bot memory
    for d in RECENT_DISPATCHES:
        name = purge_emoji(d.get("raw_filename", ""))
        key = extract_canonical_key(name)
        if name and key and key not in seen_keys:
            seen_keys.add(key)
            items.append({**d, "raw_filename": name})
            if len(items) >= limit:
                return items

    # 2. Extract from MongoDB database with a wide scan (limit * 4) to deduplicate into limit unique items
    try:
        from Thunder.utils.database import db
        db_records = await db.get_recent_files(limit=limit * 4)
        for r in db_records:
            raw_fname = r.get("file_name") or r.get("raw_filename") or r.get("name") or r.get("title") or ""
            fname = purge_emoji(raw_fname)
            key = extract_canonical_key(fname)
            if fname and key and key not in seen_keys:
                seen_keys.add(key)
                size_val = r.get("file_size", 0)
                formatted_size = humanbytes(size_val) if isinstance(size_val, (int, float)) and size_val > 0 else str(size_val or "")
                
                c_date = r.get("created_at") or r.get("last_seen_at")
                if hasattr(c_date, "strftime"):
                    date_str = c_date.strftime("%d %b %Y").upper()
                elif hasattr(r.get("_id"), "generation_time"):
                    date_str = r["_id"].generation_time.strftime("%d %b %Y").upper()
                else:
                    date_str = time.strftime("%d %b %Y", time.gmtime()).upper()

                items.append({
                    "raw_filename": fname,
                    "file_size": formatted_size,
                    "stream_url": "",
                    "timestamp": int(c_date.timestamp()) if hasattr(c_date, "timestamp") else int(time.time()),
                    "date": date_str,
                })
                if len(items) >= limit:
                    break

        # 2b. Extract from OTT channel posts collection if more items needed
        if len(items) < limit:
            try:
                ott_cursor = db.ott_posts_col.find({}).sort("_id", -1).limit(limit * 2)
                async for ott in ott_cursor:
                    title = ott.get("title", "")
                    if title:
                        fname = purge_emoji(title)
                        key = extract_canonical_key(fname)
                        if fname and key and key not in seen_keys:
                            seen_keys.add(key)
                            p_date = ott.get("posted_at")
                            if hasattr(p_date, "strftime"):
                                date_str = p_date.strftime("%d %b %Y").upper()
                            elif hasattr(ott.get("_id"), "generation_time"):
                                date_str = ott["_id"].generation_time.strftime("%d %b %Y").upper()
                            else:
                                date_str = "TODAY"
                            platform = ott.get("platform") or "OTT 4K Release"
                            items.append({
                                "raw_filename": fname,
                                "file_size": platform,
                                "stream_url": "",
                                "timestamp": int(p_date.timestamp()) if hasattr(p_date, "timestamp") else int(time.time()),
                                "date": date_str,
                            })
                            if len(items) >= limit:
                                break
            except Exception as e_ott:
                logger.warning(f"Error fetching live dispatches from ott_posts_col: {e_ott}")
    except Exception as e:
        logger.warning(f"Error fetching live dispatches from db: {e}")

    # 3. Extract from Telegram BIN_CHANNEL history directly if needed
    if len(items) < limit:
        try:
            from Thunder.bot import StreamBot
            from Thunder.vars import Var
            from Thunder.utils.file_properties import get_fname, get_media

            if StreamBot and getattr(StreamBot, "is_connected", False) and Var.BIN_CHANNEL:
                async for msg in StreamBot.get_chat_history(Var.BIN_CHANNEL, limit=limit * 4):
                    media = get_media(msg)
                    if media:
                        raw_fname = get_fname(msg)
                        fname = purge_emoji(raw_fname)
                        key = extract_canonical_key(fname)
                        if fname and key and key not in seen_keys:
                            seen_keys.add(key)
                            s_bytes = getattr(media, "file_size", 0) or 0
                            items.append({
                                "raw_filename": fname,
                                "file_size": humanbytes(s_bytes) if s_bytes else "",
                                "stream_url": "",
                                "timestamp": int(msg.date.timestamp()) if msg.date else int(time.time()),
                                "date": msg.date.strftime("%d %b %Y").upper() if msg.date else "TODAY",
                            })
                            if len(items) >= limit:
                                break
        except Exception as e:
            logger.warning(f"Error fetching from BIN_CHANNEL history: {e}")

    return items[:limit]

def get_dispatches() -> List[Dict[str, Any]]:
    return list(RECENT_DISPATCHES)
