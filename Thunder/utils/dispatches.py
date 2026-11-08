# Thunder/utils/dispatches.py
import time
from collections import deque
from typing import Dict, List, Any

# Circular buffer storing the last 40 live conversion manifests
RECENT_DISPATCHES: deque = deque(maxlen=40)

def record_dispatch(file_name: str, file_size: str = "", stream_url: str = "") -> Dict[str, Any]:
    """Records a live file-to-link conversion from the bot for the live web teleprinter."""
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

def get_dispatches() -> List[Dict[str, Any]]:
    """Returns all recent dispatches in reverse chronological order."""
    return list(RECENT_DISPATCHES)
