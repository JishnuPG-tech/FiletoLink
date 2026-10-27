"""Jellyfin Media Server API client for AI Admin with strict bounds, redaction, and error handling."""

import aiohttp
import asyncio
import inspect
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from ai_admin.redaction import redact_data, redact_text, register_secret_string
from ai_admin.validators import validate_item_id

logger = logging.getLogger("AIAdmin.JellyfinClient")

# Response payload size cap (512 KB) to prevent memory exhaustion
MAX_RESPONSE_BYTES = 512 * 1024


class JellyfinError(Exception):
    """Base exception for Jellyfin client operations."""
    pass


class JellyfinAuthError(JellyfinError):
    """Raised when Jellyfin credentials are missing or invalid."""
    pass


class JellyfinNotFoundError(JellyfinError):
    """Raised when a requested media item does not exist."""
    pass


class JellyfinClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8096",
        api_key: str = "",
        timeout_seconds: float = 10.0,
    ):
        self.base_url = (base_url or "http://127.0.0.1:8096").rstrip("/")
        self.api_key = (api_key or "").strip()
        self.timeout_seconds = timeout_seconds

        if self.api_key:
            register_secret_string(self.api_key)

    def _get_auth_headers(self) -> Dict[str, str]:
        """Build MediaBrowser Authorization header without leaking key in unredacted state."""
        key = self.api_key
        if not key:
            # Fallback to APEX_JELLYFIN_API_KEY env if set
            key = os.environ.get("APEX_JELLYFIN_API_KEY", "").strip()

        if not key:
            # Try reading from Jellyfin DB on disk if accessible
            for db in (
                "/opt/jellyfin-local/data/data/jellyfin.db",
                "/data/jellyfin/data/data/jellyfin.db",
            ):
                if os.path.exists(db):
                    try:
                        import sqlite3
                        with sqlite3.connect(db, timeout=2) as conn:
                            cur = conn.cursor()
                            cur.execute("PRAGMA table_info('api_keys')")
                            cols = [r[1] for r in cur.fetchall()]
                            if "AccessToken" in cols:
                                if "IsActive" in cols:
                                    cur.execute("SELECT AccessToken FROM api_keys WHERE IsActive IS NOT 0 ORDER BY DateCreated DESC LIMIT 1")
                                else:
                                    cur.execute("SELECT AccessToken FROM api_keys ORDER BY DateCreated DESC LIMIT 1")
                                row = cur.fetchone()
                                if row and row[0]:
                                    key = str(row[0]).strip()
                                    register_secret_string(key)
                                    break
                    except Exception:
                        pass

        if not key:
            raise JellyfinAuthError("No Jellyfin API key available (JELLYFIN_API_KEY not configured).")

        return {
            "Authorization": (
                'MediaBrowser Client="AIAdmin", Device="ApexServer", '
                'DeviceId="ai-admin", Version="1.0.0", '
                f'Token="{key}"'
            ),
            "Accept": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Any:
        """Execute HTTP request against Jellyfin API with timeout and payload capping."""
        url = f"{self.base_url}{path}"
        headers = self._get_auth_headers()

        close_session = False
        if session is None:
            session = aiohttp.ClientSession()
            close_session = True

        try:
            async with session.request(
                method=method,
                url=url,
                params=params,
                json=json_body,
                headers=headers,
                allow_redirects=False,
                timeout=aiohttp.ClientTimeout(
                    total=self.timeout_seconds,
                    connect=min(3.0, self.timeout_seconds),
                    sock_read=self.timeout_seconds,
                ),
            ) as resp:
                if resp.status in (301, 302, 303, 307, 308):
                    raise JellyfinError(f"Unexpected redirect from Jellyfin server (HTTP {resp.status}).")
                if resp.status in (401, 403):
                    raise JellyfinAuthError("Jellyfin authentication failed (HTTP 401/403).")
                if resp.status == 404:
                    raise JellyfinNotFoundError(f"Requested resource not found on Jellyfin (HTTP 404): {path}")
                if resp.status >= 400:
                    raise JellyfinError(f"Jellyfin API error (HTTP {resp.status})")

                chunks = []
                total_bytes = 0
                read_fn = getattr(getattr(resp, "content", None), "read", None)
                if read_fn and inspect.iscoroutinefunction(read_fn):
                    while True:
                        chunk = await read_fn(64 * 1024)
                        if not chunk:
                            break
                        total_bytes += len(chunk)
                        if total_bytes > MAX_RESPONSE_BYTES:
                            raise JellyfinError(
                                f"Jellyfin response exceeded maximum size limit ({total_bytes} > {MAX_RESPONSE_BYTES} bytes)."
                            )
                        chunks.append(chunk)
                    raw_body = b"".join(chunks)
                else:
                    raw_body = await resp.read()
                    if len(raw_body) > MAX_RESPONSE_BYTES:
                        raise JellyfinError(
                            f"Jellyfin response exceeded maximum size limit ({len(raw_body)} > {MAX_RESPONSE_BYTES} bytes)."
                        )

                if not raw_body:
                    return {}

                try:
                    data = json.loads(raw_body.decode("utf-8", errors="replace"))
                except Exception as e:
                    raise JellyfinError(f"Malformed JSON response from Jellyfin: {type(e).__name__}")

                return data

        except asyncio.TimeoutError:
            raise JellyfinError(f"Jellyfin request timed out after {self.timeout_seconds}s.")
        except aiohttp.ClientError as exc:
            clean_err = redact_text(str(exc))
            raise JellyfinError(f"Jellyfin connection error: {clean_err}")
        finally:
            if close_session:
                await session.close()

    async def search_items(
        self,
        query: str,
        item_types: Optional[str] = "Movie,Series,Episode",
        limit: int = 20,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> List[Dict[str, Any]]:
        """Search items in Jellyfin library with bounded results."""
        clean_query = (query or "").strip()
        if not clean_query:
            return []

        bounded_limit = max(1, min(limit, 50))
        params = {
            "searchTerm": clean_query,
            "IncludeItemTypes": item_types or "Movie,Series,Episode",
            "Recursive": "true",
            "Fields": "Overview,ProductionYear,ProviderIds,Genres,OfficialRating,CommunityRating,ImageTags",
            "Limit": str(bounded_limit),
        }

        data = await self._request("GET", "/Items", params=params, session=session)
        items = data.get("Items") or []

        results = []
        for it in items:
            image_tags = it.get("ImageTags") or {}
            results.append({
                "id": it.get("Id"),
                "name": it.get("Name"),
                "type": it.get("Type"),
                "year": it.get("ProductionYear"),
                "overview": (it.get("Overview") or "")[:200] + ("..." if len(it.get("Overview") or "") > 200 else ""),
                "genres": it.get("Genres") or [],
                "provider_ids": it.get("ProviderIds") or {},
                "has_primary_image": "Primary" in image_tags,
                "has_backdrop": bool(it.get("BackdropImageTags")),
            })
        return results

    async def get_item(
        self,
        item_id: str,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        """Fetch complete item details for a specific Jellyfin item ID."""
        if not validate_item_id(item_id):
            raise ValueError(f"Invalid item_id format: '{item_id}'")

        data = await self._request("GET", f"/Items/{item_id}", session=session)
        if not data:
            raise JellyfinNotFoundError(f"Item '{item_id}' not found.")

        image_tags = data.get("ImageTags") or {}
        backdrop_tags = data.get("BackdropImageTags") or []

        return {
            "id": data.get("Id"),
            "name": data.get("Name"),
            "original_title": data.get("OriginalTitle"),
            "type": data.get("Type"),
            "year": data.get("ProductionYear"),
            "overview": data.get("Overview"),
            "tagline": data.get("Taglines", [None])[0] if data.get("Taglines") else None,
            "genres": data.get("Genres") or [],
            "studios": [s.get("Name") for s in data.get("Studios") or [] if isinstance(s, dict)],
            "provider_ids": data.get("ProviderIds") or {},
            "community_rating": data.get("CommunityRating"),
            "official_rating": data.get("OfficialRating"),
            "has_primary_image": "Primary" in image_tags,
            "has_backdrop": len(backdrop_tags) > 0,
            "backdrop_count": len(backdrop_tags),
            "media_sources_count": len(data.get("MediaSources") or []),
            "path_basename": os.path.basename(str(data.get("Path") or "")),
        }

    async def list_missing_metadata(
        self,
        filter_types: Optional[List[str]] = None,
        limit: int = 30,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> List[Dict[str, Any]]:
        """Identify media items in library that are missing critical metadata or artwork."""
        bounded_limit = max(1, min(limit, 50))
        params = {
            "IncludeItemTypes": "Movie,Series",
            "Recursive": "true",
            "Fields": "Overview,ProviderIds,ImageTags,BackdropImageTags,Genres",
            "Limit": "200",  # Sample pool
        }

        data = await self._request("GET", "/Items", params=params, session=session)
        items = data.get("Items") or []

        wanted_filters = set(filter_types or ["overview", "poster", "backdrop", "provider_id"])
        missing_items = []

        for it in items:
            image_tags = it.get("ImageTags") or {}
            backdrop_tags = it.get("BackdropImageTags") or []
            prov_ids = it.get("ProviderIds") or {}
            overview = (it.get("Overview") or "").strip()

            missing = []
            if "overview" in wanted_filters and not overview:
                missing.append("overview")
            if "poster" in wanted_filters and "Primary" not in image_tags:
                missing.append("primary_image")
            if "backdrop" in wanted_filters and not backdrop_tags:
                missing.append("backdrop")
            if "provider_id" in wanted_filters and not (prov_ids.get("Tmdb") or prov_ids.get("Imdb")):
                missing.append("provider_ids")

            if missing:
                missing_items.append({
                    "id": it.get("Id"),
                    "name": it.get("Name"),
                    "type": it.get("Type"),
                    "year": it.get("ProductionYear"),
                    "missing": missing,
                })
                if len(missing_items) >= bounded_limit:
                    break

        return missing_items

    async def get_media_info(
        self,
        item_id: str,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        """Fetch media stream specifications (codecs, resolution, audio tracks, subtitles)."""
        if not validate_item_id(item_id):
            raise ValueError(f"Invalid item_id format: '{item_id}'")

        params = {"Fields": "MediaStreams,MediaSources,Container,Path"}
        data = await self._request("GET", f"/Items/{item_id}", params=params, session=session)
        if not data:
            raise JellyfinNotFoundError(f"Item '{item_id}' not found.")

        media_streams = data.get("MediaStreams") or []
        video_streams = []
        audio_streams = []
        subtitle_streams = []

        for s in media_streams:
            stype = str(s.get("Type") or "").lower()
            if stype == "video":
                video_streams.append({
                    "index": s.get("Index"),
                    "codec": s.get("Codec"),
                    "profile": s.get("Profile"),
                    "width": s.get("Width"),
                    "height": s.get("Height"),
                    "aspect_ratio": s.get("AspectRatio"),
                    "bit_depth": s.get("BitDepth"),
                    "frame_rate": s.get("AverageFrameRate") or s.get("RealFrameRate"),
                })
            elif stype == "audio":
                audio_streams.append({
                    "index": s.get("Index"),
                    "codec": s.get("Codec"),
                    "language": s.get("Language"),
                    "title": s.get("Title"),
                    "channels": s.get("Channels"),
                    "bitrate": s.get("BitRate"),
                    "is_default": s.get("IsDefault", False),
                })
            elif stype == "subtitle":
                subtitle_streams.append({
                    "index": s.get("Index"),
                    "codec": s.get("Codec"),
                    "language": s.get("Language"),
                    "title": s.get("Title"),
                    "is_external": s.get("IsExternal", False),
                    "is_forced": s.get("IsForced", False),
                    "is_default": s.get("IsDefault", False),
                })

        sources = data.get("MediaSources") or []
        container = data.get("Container")
        if not container and sources:
            container = sources[0].get("Container")

        return {
            "id": data.get("Id"),
            "name": data.get("Name"),
            "type": data.get("Type"),
            "container": container,
            "video": video_streams,
            "audio": audio_streams,
            "subtitles": subtitle_streams,
            "total_video_tracks": len(video_streams),
            "total_audio_tracks": len(audio_streams),
            "total_subtitle_tracks": len(subtitle_streams),
        }
