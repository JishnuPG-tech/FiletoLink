"""External provider HTTP client for TMDb, Fanart.tv, and OpenSubtitles with SSRF guards and bounds."""

import aiohttp
import asyncio
import inspect
import json
import logging
import os
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

from ai_admin.candidate_cache import CandidateCache
from ai_admin.net_guard import validate_outbound_url
from ai_admin.redaction import redact_data, redact_text, register_secret_string

logger = logging.getLogger("AIAdmin.ProvidersClient")

# Max response size for external metadata (256 KB)
MAX_PROVIDER_RESPONSE_BYTES = 256 * 1024


class ProviderError(Exception):
    """Base error for external metadata providers."""
    pass


class ProviderAuthError(ProviderError):
    """Raised on missing or invalid provider credentials."""
    pass


class ProviderRateLimitError(ProviderError):
    """Raised when an external provider issues HTTP 429."""
    pass


class ProviderNotFoundError(ProviderError):
    """Raised when the requested external resource does not exist."""
    pass


class ProviderSecurityError(ProviderError):
    """Raised when an outbound URL violates SSRF or domain security policies."""
    pass


class ProvidersClient:
    def __init__(
        self,
        candidate_cache: Optional[CandidateCache] = None,
        tmdb_api_key: Optional[str] = None,
        fanart_api_key: Optional[str] = None,
        opensubtitles_api_key: Optional[str] = None,
        timeout_seconds: float = 10.0,
    ):
        self.candidate_cache = candidate_cache or CandidateCache()
        self.timeout_seconds = timeout_seconds

        # Resolve credentials with env fallbacks (zero hardcoded secrets)
        self.tmdb_key = (
            tmdb_api_key
            or os.environ.get("TMDB_API_KEY")
            or os.environ.get("APEX_TMDB_API_KEY")
            or ""
        ).strip()

        self.fanart_key = (
            fanart_api_key
            or os.environ.get("FANART_API_KEY")
            or os.environ.get("APEX_FANART_API_KEY")
            or ""
        ).strip()

        self.os_key = (
            opensubtitles_api_key
            or os.environ.get("OPENSUBTITLES_API_KEY")
            or os.environ.get("APEX_OPENSUBTITLES_API_KEY")
            or ""
        ).strip()

        # Register secrets for automatic scrubbing
        if self.tmdb_key:
            register_secret_string(self.tmdb_key)
        if self.fanart_key:
            register_secret_string(self.fanart_key)
        if self.os_key:
            register_secret_string(self.os_key)

    async def _safe_get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Any:
        """SSRF-guarded, redirect-checked, size-capped HTTP GET for external APIs."""
        # 1. SSRF & domain policy check
        is_safe, sec_reason = validate_outbound_url(url)
        if not is_safe:
            raise ProviderSecurityError(f"Outbound network request blocked by NetGuard: {sec_reason}")

        close_session = False
        if session is None:
            session = aiohttp.ClientSession()
            close_session = True

        try:
            async with session.get(
                url=url,
                params=params,
                headers=headers,
                allow_redirects=False,
                timeout=aiohttp.ClientTimeout(
                    total=self.timeout_seconds,
                    connect=min(3.0, self.timeout_seconds),
                    sock_read=self.timeout_seconds,
                ),
            ) as resp:
                if resp.status in (301, 302, 303, 307, 308):
                    raise ProviderSecurityError(f"Unexpected redirect from provider (HTTP {resp.status}).")

                if resp.status == 429:
                    raise ProviderRateLimitError("External provider rate limit exceeded (HTTP 429).")

                if resp.status in (401, 403):
                    raise ProviderAuthError(f"Provider authentication failed (HTTP {resp.status}).")

                if resp.status == 404:
                    raise ProviderNotFoundError("Resource not found on external provider (HTTP 404).")

                if resp.status >= 400:
                    raise ProviderError(f"Provider returned HTTP error {resp.status}.")

                # Stream-read chunks to cap incoming response size
                chunks = []
                total_bytes = 0
                read_fn = getattr(getattr(resp, "content", None), "read", None)
                if read_fn and inspect.iscoroutinefunction(read_fn):
                    while True:
                        chunk = await read_fn(32 * 1024)
                        if not chunk:
                            break
                        total_bytes += len(chunk)
                        if total_bytes > MAX_PROVIDER_RESPONSE_BYTES:
                            raise ProviderError(
                                f"Provider response exceeded maximum size limit ({total_bytes} > {MAX_PROVIDER_RESPONSE_BYTES} bytes)."
                            )
                        chunks.append(chunk)
                    raw_body = b"".join(chunks)
                else:
                    raw_body = await resp.read()
                    if len(raw_body) > MAX_PROVIDER_RESPONSE_BYTES:
                        raise ProviderError(
                            f"Provider response exceeded maximum size limit ({len(raw_body)} > {MAX_PROVIDER_RESPONSE_BYTES} bytes)."
                        )

                if not raw_body:
                    return {}

                try:
                    data = json.loads(raw_body.decode("utf-8", errors="replace"))
                except Exception as e:
                    raise ProviderError(f"Malformed JSON from provider: {type(e).__name__}")

                return data

        except asyncio.TimeoutError:
            raise ProviderError(f"Provider request timed out after {self.timeout_seconds}s.")
        except aiohttp.ClientError as exc:
            clean_err = redact_text(str(exc))
            raise ProviderError(f"Provider connection error: {clean_err}")
        finally:
            if close_session:
                await session.close()

    # ==========================================================================
    # 1. TMDb
    # ==========================================================================

    async def tmdb_search(
        self,
        query: str,
        media_type: str = "movie",
        year: Optional[int] = None,
        language: Optional[str] = None,
        limit: int = 10,
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> List[Dict[str, Any]]:
        """Search TMDb for movie or TV titles with bounded output and candidate artwork handles."""
        clean_query = (query or "").strip()
        if not clean_query:
            return []

        if not self.tmdb_key:
            raise ProviderAuthError("TMDb API key not configured (TMDB_API_KEY).")

        clean_type = media_type.lower() if media_type in ("movie", "tv", "multi") else "movie"
        bounded_limit = max(1, min(limit, 20))

        url = f"https://api.themoviedb.org/3/search/{clean_type}"
        params: Dict[str, Any] = {
            "api_key": self.tmdb_key,
            "query": clean_query,
            "include_adult": "false",
        }
        if year:
            if clean_type == "tv":
                params["first_air_date_year"] = str(year)
            else:
                params["year"] = str(year)
        if language:
            params["language"] = language[:10]

        data = await self._safe_get(url, params=params, session=session)
        hits = data.get("results") or []

        results = []
        for hit in hits[:bounded_limit]:
            title = hit.get("title") or hit.get("name") or "Unknown"
            orig_title = hit.get("original_title") or hit.get("original_name")
            release_date = hit.get("release_date") or hit.get("first_air_date") or ""
            parsed_year = int(release_date[:4]) if len(release_date) >= 4 and release_date[:4].isdigit() else None
            overview = (hit.get("overview") or "").strip()
            poster_path = hit.get("poster_path")
            backdrop_path = hit.get("backdrop_path")

            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            backdrop_url = f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else None

            poster_cand = None
            if poster_url:
                poster_cand = self.candidate_cache.register_candidate(
                    {
                        "provider": "themoviedb.org",
                        "raw_url": poster_url,
                        "image_type": "poster",
                        "target_id": str(hit.get("id")),
                    },
                    user_id=user_id,
                    chat_id=chat_id,
                    operation="image_artwork",
                )

            results.append({
                "tmdb_id": hit.get("id"),
                "media_type": hit.get("media_type") or clean_type,
                "title": title,
                "original_title": orig_title,
                "year": parsed_year,
                "overview": overview[:200] + ("..." if len(overview) > 200 else ""),
                "original_language": hit.get("original_language"),
                "vote_average": hit.get("vote_average"),
                "has_poster": bool(poster_path),
                "poster_url": poster_url,
                "poster_candidate_id": poster_cand,
                "has_backdrop": bool(backdrop_path),
                "backdrop_url": backdrop_url,
            })
        return results

    async def tmdb_get_details(
        self,
        tmdb_id: int,
        media_type: str = "movie",
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        """Fetch full details and external IDs for a TMDb item."""
        if not isinstance(tmdb_id, int) or tmdb_id <= 0:
            raise ValueError(f"Invalid tmdb_id: {tmdb_id}")

        if not self.tmdb_key:
            raise ProviderAuthError("TMDb API key not configured (TMDB_API_KEY).")

        clean_type = "tv" if str(media_type).lower() == "tv" else "movie"
        url = f"https://api.themoviedb.org/3/{clean_type}/{tmdb_id}"
        params = {
            "api_key": self.tmdb_key,
            "append_to_response": "external_ids",
        }

        data = await self._safe_get(url, params=params, session=session)
        ext_ids = data.get("external_ids") or {}

        title = data.get("title") or data.get("name") or "Unknown"
        release_date = data.get("release_date") or data.get("first_air_date") or ""
        parsed_year = int(release_date[:4]) if len(release_date) >= 4 and release_date[:4].isdigit() else None

        return {
            "tmdb_id": data.get("id"),
            "imdb_id": ext_ids.get("imdb_id"),
            "media_type": clean_type,
            "title": title,
            "original_title": data.get("original_title") or data.get("original_name"),
            "year": parsed_year,
            "overview": data.get("overview"),
            "tagline": data.get("tagline"),
            "genres": [g.get("name") for g in data.get("genres") or [] if isinstance(g, dict)],
            "vote_average": data.get("vote_average"),
            "runtime_minutes": data.get("runtime") or (data.get("episode_run_time", [None])[0] if data.get("episode_run_time") else None),
            "status": data.get("status"),
            "has_poster": bool(data.get("poster_path")),
            "has_backdrop": bool(data.get("backdrop_path")),
        }

    async def tmdb_get_images(
        self,
        tmdb_id: int,
        media_type: str = "movie",
        limit: int = 20,
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch all official posters, backdrops, and logos from TMDb."""
        if not isinstance(tmdb_id, int) or tmdb_id <= 0:
            raise ValueError(f"Invalid tmdb_id: {tmdb_id}")

        if not self.tmdb_key:
            raise ProviderAuthError("TMDb API key not configured (TMDB_API_KEY).")

        clean_type = "tv" if str(media_type).lower() in ("tv", "series") else "movie"
        url = f"https://api.themoviedb.org/3/{clean_type}/{tmdb_id}/images"
        params = {"api_key": self.tmdb_key}

        data = await self._safe_get(url, params=params, session=session)
        bounded_limit = max(1, min(limit, 40))
        candidates = []

        categories = [
            ("posters", "poster"),
            ("backdrops", "backdrop"),
            ("logos", "clearlogo"),
        ]

        for cat_key, canonical_type in categories:
            items = data.get(cat_key) or []
            for item in items:
                if not isinstance(item, dict):
                    continue
                file_path = item.get("file_path")
                if not file_path:
                    continue
                raw_url = f"https://image.tmdb.org/t/p/original{file_path}"
                preview_url = f"https://image.tmdb.org/t/p/w500{file_path}"
                cand_id = self.candidate_cache.register_candidate(
                    {
                        "provider": "themoviedb.org",
                        "raw_url": raw_url,
                        "image_type": canonical_type,
                        "target_id": str(tmdb_id),
                    },
                    user_id=user_id,
                    chat_id=chat_id,
                    operation="image_artwork",
                )
                candidates.append({
                    "candidate_id": cand_id,
                    "image_type": canonical_type,
                    "preview_url": preview_url,
                    "full_url": raw_url,
                    "width": item.get("width"),
                    "height": item.get("height"),
                    "vote_average": item.get("vote_average"),
                    "provider": "themoviedb.org",
                })
                if len(candidates) >= bounded_limit:
                    break
            if len(candidates) >= bounded_limit:
                break

        return candidates

    # ==========================================================================
    # 2. Free Stremio Cinemeta (No API Key Required)
    # ==========================================================================

    async def cinemeta_search(
        self,
        query: str,
        media_type: str = "movie",
        limit: int = 10,
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> List[Dict[str, Any]]:
        """Search Stremio Cinemeta catalog (free, no API key required). Returns IMDb items with posters."""
        clean_query = (query or "").strip()
        if not clean_query:
            return []

        clean_type = "series" if str(media_type).lower() in ("tv", "series") else "movie"
        encoded_query = urllib.parse.quote(clean_query)
        url = f"https://v3-cinemeta.strem.io/catalog/{clean_type}/top/search={encoded_query}.json"

        data = await self._safe_get(url, session=session)
        metas = data.get("metas") or []
        bounded_limit = max(1, min(limit, 20))
        results = []

        for m in metas[:bounded_limit]:
            imdb_id = m.get("imdb_id") or m.get("id") or ""
            name = m.get("name") or "Unknown"
            year = m.get("year")
            poster_url = m.get("poster")
            cand_id = None
            if poster_url:
                cand_id = self.candidate_cache.register_candidate(
                    {
                        "provider": "cinemeta",
                        "raw_url": poster_url,
                        "image_type": "poster",
                        "target_id": imdb_id or name,
                    },
                    user_id=user_id,
                    chat_id=chat_id,
                    operation="image_artwork",
                )

            results.append({
                "imdb_id": imdb_id,
                "title": name,
                "year": year,
                "media_type": clean_type,
                "poster_url": poster_url,
                "candidate_id": cand_id,
                "description": (m.get("description") or "")[:200],
                "provider": "cinemeta (IMDb)",
            })
        return results

    async def cinemeta_get_meta(
        self,
        imdb_id: str,
        media_type: str = "movie",
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        """Fetch detailed metadata and high-res artwork from Cinemeta (free, no API key)."""
        clean_id = (imdb_id or "").strip()
        if not clean_id or not clean_id.startswith("tt"):
            raise ValueError(f"Invalid IMDb ID: {imdb_id}. Must start with 'tt'.")

        clean_type = "series" if str(media_type).lower() in ("tv", "series") else "movie"
        url = f"https://v3-cinemeta.strem.io/meta/{clean_type}/{clean_id}.json"

        data = await self._safe_get(url, session=session)
        meta = data.get("meta") or {}

        poster_url = meta.get("poster")
        background_url = meta.get("background")
        logo_url = meta.get("logo")

        poster_cand = None
        if poster_url:
            poster_cand = self.candidate_cache.register_candidate(
                {"provider": "cinemeta", "raw_url": poster_url, "image_type": "poster", "target_id": clean_id},
                user_id=user_id,
                chat_id=chat_id,
                operation="image_artwork",
            )

        backdrop_cand = None
        if background_url:
            backdrop_cand = self.candidate_cache.register_candidate(
                {"provider": "cinemeta", "raw_url": background_url, "image_type": "backdrop", "target_id": clean_id},
                user_id=user_id,
                chat_id=chat_id,
                operation="image_artwork",
            )

        return {
            "imdb_id": clean_id,
            "title": meta.get("name") or "Unknown",
            "year": meta.get("year"),
            "media_type": clean_type,
            "description": meta.get("description"),
            "genres": meta.get("genres") or [],
            "imdb_rating": meta.get("imdbRating"),
            "poster_url": poster_url,
            "poster_candidate_id": poster_cand,
            "background_url": background_url,
            "background_candidate_id": backdrop_cand,
            "logo_url": logo_url,
            "provider": "cinemeta (IMDb)",
        }

    # ==========================================================================
    # 3. Free TVmaze (No API Key Required)
    # ==========================================================================

    async def tvmaze_search(
        self,
        query: str,
        limit: int = 10,
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> List[Dict[str, Any]]:
        """Search TVmaze for TV shows and official artwork (free, no API key)."""
        clean_query = (query or "").strip()
        if not clean_query:
            return []

        encoded_query = urllib.parse.quote(clean_query)
        url = f"https://api.tvmaze.com/search/shows?q={encoded_query}"

        data = await self._safe_get(url, session=session)
        bounded_limit = max(1, min(limit, 20))
        results = []

        if isinstance(data, list):
            for item in data[:bounded_limit]:
                show = item.get("show") or {}
                image = show.get("image") or {}
                poster_url = image.get("original") or image.get("medium")
                cand_id = None
                if poster_url:
                    cand_id = self.candidate_cache.register_candidate(
                        {
                            "provider": "tvmaze",
                            "raw_url": poster_url,
                            "image_type": "poster",
                            "target_id": str(show.get("id")),
                        },
                        user_id=user_id,
                        chat_id=chat_id,
                        operation="image_artwork",
                    )

                results.append({
                    "show_id": show.get("id"),
                    "title": show.get("name") or "Unknown",
                    "premiered": show.get("premiered"),
                    "genres": show.get("genres") or [],
                    "rating": (show.get("rating") or {}).get("average"),
                    "poster_url": poster_url,
                    "candidate_id": cand_id,
                    "summary": (show.get("summary") or "")[:200],
                    "provider": "tvmaze",
                })
        return results

    # ==========================================================================
    # 4. Unified Artwork Search (Multi-Provider Fallback)
    # ==========================================================================

    async def artwork_search(
        self,
        query: Optional[str] = None,
        imdb_id: Optional[str] = None,
        tmdb_id: Optional[int] = None,
        media_type: str = "movie",
        limit: int = 15,
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> List[Dict[str, Any]]:
        """Multi-provider artwork search across TMDb, Cinemeta, TVmaze, and Fanart.tv.
        Guarantees posters & backdrops are found even if an API key is missing.
        """
        candidates: List[Dict[str, Any]] = []
        bounded_limit = max(1, min(limit, 30))

        # 1. Try TMDb images if tmdb_id or query is available and tmdb_key is configured
        if self.tmdb_key:
            target_tmdb_id = tmdb_id
            if not target_tmdb_id and query:
                try:
                    hits = await self.tmdb_search(
                        query=query,
                        media_type=media_type,
                        limit=3,
                        user_id=user_id,
                        chat_id=chat_id,
                        session=session,
                    )
                    if hits:
                        target_tmdb_id = hits[0].get("tmdb_id")
                        if hits[0].get("poster_url"):
                            candidates.append({
                                "candidate_id": hits[0].get("poster_candidate_id"),
                                "image_type": "poster",
                                "preview_url": hits[0].get("poster_url"),
                                "title": hits[0].get("title"),
                                "provider": "themoviedb.org",
                            })
                except Exception as e:
                    logger.debug(f"[ARTWORK-SEARCH] TMDb search skipped: {e}")

            if target_tmdb_id:
                try:
                    tmdb_imgs = await self.tmdb_get_images(
                        tmdb_id=target_tmdb_id,
                        media_type=media_type,
                        limit=bounded_limit,
                        user_id=user_id,
                        chat_id=chat_id,
                        session=session,
                    )
                    candidates.extend(tmdb_imgs)
                except Exception as e:
                    logger.debug(f"[ARTWORK-SEARCH] TMDb get_images skipped: {e}")

        # 2. Try Cinemeta (Free, no key needed) if IMDb ID or query is available
        if len(candidates) < bounded_limit:
            if imdb_id and imdb_id.startswith("tt"):
                try:
                    meta = await self.cinemeta_get_meta(
                        imdb_id=imdb_id,
                        media_type=media_type,
                        user_id=user_id,
                        chat_id=chat_id,
                        session=session,
                    )
                    if meta.get("poster_url"):
                        candidates.append({
                            "candidate_id": meta.get("poster_candidate_id"),
                            "image_type": "poster",
                            "preview_url": meta.get("poster_url"),
                            "title": meta.get("title"),
                            "provider": "cinemeta (IMDb)",
                        })
                    if meta.get("background_url"):
                        candidates.append({
                            "candidate_id": meta.get("background_candidate_id"),
                            "image_type": "backdrop",
                            "preview_url": meta.get("background_url"),
                            "title": meta.get("title"),
                            "provider": "cinemeta (IMDb)",
                        })
                except Exception as e:
                    logger.debug(f"[ARTWORK-SEARCH] Cinemeta get_meta skipped: {e}")

            if len(candidates) < bounded_limit and query:
                try:
                    c_hits = await self.cinemeta_search(
                        query=query,
                        media_type=media_type,
                        limit=5,
                        user_id=user_id,
                        chat_id=chat_id,
                        session=session,
                    )
                    for ch in c_hits:
                        if ch.get("poster_url"):
                            candidates.append({
                                "candidate_id": ch.get("candidate_id"),
                                "image_type": "poster",
                                "preview_url": ch.get("poster_url"),
                                "title": ch.get("title"),
                                "provider": "cinemeta (IMDb)",
                            })
                except Exception as e:
                    logger.debug(f"[ARTWORK-SEARCH] Cinemeta search skipped: {e}")

        # 3. Try TVmaze if TV series and query is provided (Free, no key needed)
        if len(candidates) < bounded_limit and media_type in ("tv", "series") and query:
            try:
                tv_hits = await self.tvmaze_search(
                    query=query,
                    limit=5,
                    user_id=user_id,
                    chat_id=chat_id,
                    session=session,
                )
                for th in tv_hits:
                    if th.get("poster_url"):
                        candidates.append({
                            "candidate_id": th.get("candidate_id"),
                            "image_type": "poster",
                            "preview_url": th.get("poster_url"),
                            "title": th.get("title"),
                            "provider": "tvmaze",
                        })
            except Exception as e:
                logger.debug(f"[ARTWORK-SEARCH] TVmaze search skipped: {e}")

        # 4. Try Fanart.tv if fanart_key is configured
        if len(candidates) < bounded_limit and self.fanart_key:
            lookup_id = imdb_id or (str(tmdb_id) if tmdb_id else None)
            if lookup_id:
                try:
                    f_imgs = await self.fanart_get_images(
                        id_str=lookup_id,
                        media_type=media_type,
                        limit=bounded_limit,
                        user_id=user_id,
                        chat_id=chat_id,
                        session=session,
                    )
                    candidates.extend(f_imgs)
                except Exception as e:
                    logger.debug(f"[ARTWORK-SEARCH] Fanart lookup skipped: {e}")

        # Deduplicate candidates by preview_url
        seen_urls = set()
        deduped = []
        for cand in candidates:
            url = cand.get("preview_url") or cand.get("full_url")
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            deduped.append(cand)
            if len(deduped) >= bounded_limit:
                break

        return deduped

    # ==========================================================================
    # 5. Fanart.tv
    # ==========================================================================

    async def fanart_get_images(
        self,
        id_str: str,
        media_type: str = "movie",
        limit: int = 15,
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve available artwork metadata from Fanart.tv with candidate handle mapping."""
        clean_id = (id_str or "").strip()
        if not clean_id:
            raise ValueError("Missing id for Fanart lookup.")

        if not self.fanart_key:
            raise ProviderAuthError("Fanart.tv API key not configured (FANART_API_KEY).")

        clean_type = "tv" if media_type.lower() == "tv" else "movies"
        url = f"https://webservice.fanart.tv/v3/{clean_type}/{clean_id}"
        params = {"api_key": self.fanart_key}

        data = await self._safe_get(url, params=params, session=session)

        bounded_limit = max(1, min(limit, 30))
        candidates = []

        # Categories mapping
        type_mapping = {
            "movieposter": "poster",
            "tvposter": "poster",
            "moviebackground": "backdrop",
            "showbackground": "backdrop",
            "hdmovielogo": "clearlogo",
            "hdtvlogo": "clearlogo",
            "clearlogo": "clearlogo",
            "moviethumb": "thumb",
            "tvthumb": "thumb",
            "moviebanner": "banner",
            "tvbanner": "banner",
        }

        for cat_key, items in data.items():
            if not isinstance(items, list):
                continue
            canonical_type = type_mapping.get(cat_key.lower())
            if not canonical_type:
                continue

            for item in items:
                if not isinstance(item, dict):
                    continue
                raw_url = item.get("url")
                if not raw_url:
                    continue

                # Register raw URL into candidate cache, returning opaque candidate_id bound to user/chat
                cand_id = self.candidate_cache.register_candidate(
                    {
                        "provider": "fanart.tv",
                        "raw_url": raw_url,
                        "image_type": canonical_type,
                        "target_id": clean_id,
                    },
                    user_id=user_id,
                    chat_id=chat_id,
                    operation="image_artwork",
                )

                candidates.append({
                    "candidate_id": cand_id,
                    "image_type": canonical_type,
                    "lang": item.get("lang") or "00",
                    "likes": int(item.get("likes") or 0),
                    "provider": "fanart.tv",
                })
                if len(candidates) >= bounded_limit:
                    break
            if len(candidates) >= bounded_limit:
                break

        return candidates

    # ==========================================================================
    # 3. OpenSubtitles
    # ==========================================================================

    async def opensubtitles_search(
        self,
        query: Optional[str] = None,
        imdb_id: Optional[str] = None,
        tmdb_id: Optional[int] = None,
        languages: Optional[str] = "en",
        season: Optional[int] = None,
        episode: Optional[int] = None,
        limit: int = 10,
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> List[Dict[str, Any]]:
        """Search subtitle metadata on OpenSubtitles with candidate handle mapping."""
        bounded_limit = max(1, min(limit, 20))

        # Check if official API key is available
        if self.os_key:
            url = "https://api.opensubtitles.com/api/v1/subtitles"
            headers = {
                "Api-Key": self.os_key,
                "User-Agent": "Apex-AIAdmin v1.0",
                "Accept": "application/json",
            }
            params: Dict[str, Any] = {}
            if imdb_id and imdb_id.startswith("tt"):
                try:
                    params["imdb_id"] = int(imdb_id.replace("tt", ""))
                except ValueError:
                    params["query"] = imdb_id
            elif tmdb_id:
                params["tmdb_id"] = str(tmdb_id)
            elif query:
                params["query"] = query.strip()
            else:
                return []

            if season is not None and episode is not None:
                params["type"] = "episode"
                params["season_number"] = str(season)
                params["episode_number"] = str(episode)

            if languages:
                params["languages"] = languages.strip().lower()

            data = await self._safe_get(url, params=params, headers=headers, session=session)
            items = data.get("data") or []

            results = []
            for item in items[:bounded_limit]:
                attrs = item.get("attributes") or {}
                files = attrs.get("files") or []
                raw_lang = attrs.get("language") or "en"
                release = attrs.get("release") or attrs.get("feature_details", {}).get("title") or "Unknown"

                for f in files:
                    fid = f.get("file_id")
                    if not fid:
                        continue
                    # Download URL registered securely into candidate cache
                    dl_url = f"https://api.opensubtitles.com/api/v1/download/{fid}"
                    cand_id = self.candidate_cache.register_candidate(
                        {
                            "provider": "opensubtitles.com",
                            "download_url": dl_url,
                            "file_id": fid,
                            "language": raw_lang,
                            "file_name": f.get("file_name") or f"{release}.srt",
                        },
                        user_id=user_id,
                        chat_id=chat_id,
                        operation="subtitle_track",
                    )

                    results.append({
                        "candidate_id": cand_id,
                        "language": raw_lang,
                        "release_name": release[:150],
                        "file_name": (f.get("file_name") or f"{release}.srt")[:100],
                        "format": "srt",
                        "downloads": attrs.get("download_count") or 0,
                        "provider": "opensubtitles.com",
                    })
                    if len(results) >= bounded_limit:
                        break
            return results

        # Fallback to public Stremio OpenSubtitles endpoint if no API key
        if imdb_id and imdb_id.startswith("tt"):
            if season is not None and episode is not None:
                url = f"https://opensubtitles-v3.strem.io/subtitles/series/{imdb_id}:{season}:{episode}.json"
            else:
                url = f"https://opensubtitles-v3.strem.io/subtitles/movie/{imdb_id}.json"
        else:
            raise ProviderAuthError("OpenSubtitles API key not configured (OPENSUBTITLES_API_KEY).")

        data = await self._safe_get(url, session=session)
        sub_list = data.get("subtitles") or []

        results = []
        for s in sub_list[:bounded_limit]:
            sub_url = s.get("url")
            if not sub_url:
                continue
            cand_id = self.candidate_cache.register_candidate(
                {
                    "provider": "stremio-opensubtitles",
                    "download_url": sub_url,
                    "language": s.get("lang") or "en",
                },
                user_id=user_id,
                chat_id=chat_id,
                operation="subtitle_track",
            )
            results.append({
                "candidate_id": cand_id,
                "language": s.get("lang") or "en",
                "release_name": (s.get("id") or "stremio-sub")[:150],
                "format": "srt",
                "provider": "stremio-opensubtitles",
            })
        return results
