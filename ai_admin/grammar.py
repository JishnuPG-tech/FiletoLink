"""Deterministic command grammar parser (no-LLM fallback)."""

import re
from typing import Any, Dict, Optional, Tuple


class GrammarParser:
    """Parses standard administrator instructions deterministically without an LLM."""

    # Patterns
    _STATUS_RE = re.compile(r"^status\b", re.IGNORECASE)
    _RESET_RE = re.compile(r"^reset\b", re.IGNORECASE)
    _UNDO_RE = re.compile(r"^undo\b", re.IGNORECASE)

    _FIND_RE = re.compile(r"^(?:find|search|lookup)\s+(?:item\s+)?(.+)", re.IGNORECASE)
    _DETAILS_RE = re.compile(r"^(?:details|info|show\s+details)\s*([a-zA-Z0-9_\-]*)$", re.IGNORECASE)
    _MEDIA_INFO_RE = re.compile(r"^(?:media_info|mediainfo|stream_info)\s*([a-zA-Z0-9_\-]*)$", re.IGNORECASE)
    _MISSING_RE = re.compile(r"^(?:missing|missing_metadata|list_missing)\b", re.IGNORECASE)
    _TMDB_DETAILS_RE = re.compile(r"^tmdb\s+details\s+([0-9]+)$", re.IGNORECASE)
    _TMDB_RE = re.compile(r"^tmdb(?:\s+search)?\s+(.+)$", re.IGNORECASE)
    _FANART_RE = re.compile(r"^fanart\s+([a-zA-Z0-9_\-]+)$", re.IGNORECASE)
    _OPENSUBTITLES_RE = re.compile(r"^(?:opensubtitles|os)(?:\s+search)?\s+(.+)$", re.IGNORECASE)
    _IMAGES_RE = re.compile(r"^(?:images|posters|show\s+images|artwork)\s*([a-zA-Z0-9_\-]*)$", re.IGNORECASE)
    _SUBTITLES_RE = re.compile(r"^(?:subtitles|subs|show\s+subtitles)\s*([a-zA-Z0-9_\-]*)$", re.IGNORECASE)

    def parse(self, text: str, selected_item_id: Optional[str] = None) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Parse text instruction into (tool_name, params) or return None if unparseable."""
        if not text or not isinstance(text, str):
            return None

        cleaned = text.strip()
        if not cleaned:
            return None

        # 1. Management commands
        if self._STATUS_RE.match(cleaned):
            return "status", {}
        if self._RESET_RE.match(cleaned):
            return "reset", {}
        if self._UNDO_RE.match(cleaned):
            return "undo", {}

        # 2. Search library items
        m_find = self._FIND_RE.match(cleaned)
        if m_find:
            query = m_find.group(1).strip()
            # Strip quotes if present
            query = query.strip("'\"")
            return "search_library_items", {"query": query}

        # 3. Details
        m_det = self._DETAILS_RE.match(cleaned)
        if m_det:
            item_id = m_det.group(1).strip() or selected_item_id
            if item_id:
                return "get_item_details", {"item_id": item_id}

        # 4. Media info
        m_media = self._MEDIA_INFO_RE.match(cleaned)
        if m_media:
            item_id = m_media.group(1).strip() or selected_item_id
            if item_id:
                return "jellyfin_get_media_info", {"item_id": item_id}

        # 5. Missing metadata
        if self._MISSING_RE.match(cleaned):
            return "jellyfin_list_missing_metadata", {}

        # 6. TMDb Details
        m_tmdb_det = self._TMDB_DETAILS_RE.match(cleaned)
        if m_tmdb_det:
            return "tmdb_get_details", {"tmdb_id": int(m_tmdb_det.group(1).strip())}

        # 7. TMDb Search
        m_tmdb = self._TMDB_RE.match(cleaned)
        if m_tmdb:
            return "tmdb_search", {"query": m_tmdb.group(1).strip().strip("'\"")}

        # 8. Fanart
        m_fanart = self._FANART_RE.match(cleaned)
        if m_fanart:
            return "fanart_get_images", {"id": m_fanart.group(1).strip()}

        # 9. OpenSubtitles
        m_os = self._OPENSUBTITLES_RE.match(cleaned)
        if m_os:
            return "opensubtitles_search", {"query": m_os.group(1).strip().strip("'\"")}

        # 10. Images
        m_img = self._IMAGES_RE.match(cleaned)
        if m_img:
            item_id = m_img.group(1).strip() or selected_item_id
            if item_id:
                return "get_item_images", {"item_id": item_id}

        # 11. Subtitles
        m_sub = self._SUBTITLES_RE.match(cleaned)
        if m_sub:
            item_id = m_sub.group(1).strip() or selected_item_id
            if item_id:
                return "get_item_subtitles", {"item_id": item_id}

        return None
