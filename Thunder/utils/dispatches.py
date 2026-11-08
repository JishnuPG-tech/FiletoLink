# Thunder/utils/dispatches.py
import time
from collections import deque
from typing import Dict, List, Any
from Thunder.utils.logger import logger
from Thunder.utils.human_readable import humanbytes

RECENT_DISPATCHES: deque = deque(maxlen=40)

def record_dispatch(file_name: str, file_size: str = "", stream_url: str = "") -> Dict[str, Any]:
    """Records a live conversion from the active bot session."""
    if not file_name:
        return {}
    
    entry = {
        "raw_filename": str(file_name),
        "file_size": str(file_size or ""),
        "stream_url": str(stream_url or ""),
        "timestamp": int(time.time()),
        "date": time.strftime("%d %b %Y", time.gmtime()).upper(),
    }
    RECENT_DISPATCHES.appendleft(entry)
    return entry

async def get_live_dispatches_from_sources(limit: int = 30) -> List[Dict[str, Any]]:
    """Fetches real file conversion records from MongoDB database, Telegram BIN_CHANNEL, and memory."""
    items: List[Dict[str, Any]] = []
    seen_names = set()

    # 1. Real-time dispatches from active bot memory
    for d in RECENT_DISPATCHES:
        name = d.get("raw_filename")
        if name and name not in seen_names:
            seen_names.add(name)
            items.append(d)

    # 2. Extract from MongoDB database
    try:
        from Thunder.utils.database import db
        db_records = await db.get_recent_files(limit=limit)
        for r in db_records:
            fname = r.get("file_name")
            if fname and fname not in seen_names:
                seen_names.add(fname)
                size_val = r.get("file_size", 0)
                formatted_size = humanbytes(size_val) if isinstance(size_val, (int, float)) and size_val > 0 else str(size_val or "")
                
                c_date = r.get("created_at") or r.get("last_seen_at")
                if hasattr(c_date, "strftime"):
                    date_str = c_date.strftime("%d %b %Y").upper()
                else:
                    date_str = time.strftime("%d %b %Y", time.gmtime()).upper()

                items.append({
                    "raw_filename": fname,
                    "file_size": formatted_size,
                    "stream_url": "",
                    "timestamp": int(c_date.timestamp()) if hasattr(c_date, "timestamp") else int(time.time()),
                    "date": date_str,
                })
    except Exception as e:
        logger.warning(f"Error fetching live dispatches from db: {e}")

    # 3. Extract from Telegram BIN_CHANNEL history directly if needed
    if len(items) < limit:
        try:
            from Thunder.bot import StreamBot
            from Thunder.vars import Var
            from Thunder.utils.file_properties import get_fname, get_media

            if StreamBot and getattr(StreamBot, "is_connected", False) and Var.BIN_CHANNEL:
                async for msg in StreamBot.get_chat_history(Var.BIN_CHANNEL, limit=limit * 2):
                    media = get_media(msg)
                    if media:
                        fname = get_fname(msg)
                        if fname and fname not in seen_names:
                            seen_names.add(fname)
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
