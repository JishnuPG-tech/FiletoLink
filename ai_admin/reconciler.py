"""Reconciliation engine comparing 100% ground-truth Telegram injected media against Jellyfin library."""

import aiohttp
import asyncio
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from ai_admin.jellyfin_client import JellyfinClient
from ai_admin.net_guard import validate_outbound_url
from ai_admin.providers_client import ProvidersClient

logger = logging.getLogger("AIAdmin.Reconciler")

DEFAULT_CACHE_FILE = "/data/jellyfin/file_ids.json"


def load_telegram_injected_catalog(cache_path: str = DEFAULT_CACHE_FILE) -> List[Dict[str, Any]]:
    """Load the ground-truth catalog of media injected from Telegram."""
    if not os.path.exists(cache_path):
        return []

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.warning(f"[RECONCILER] Error reading {cache_path}: {e}")
        return []

    items = []
    for key, entry in data.items():
        if not isinstance(entry, dict):
            continue

        raw_name = entry.get("file_name") or entry.get("raw_name") or entry.get("title") or ""
        strm_path = entry.get("strm_path") or ""

        items.append({
            "key": key,
            "chat_id": entry.get("chat_id"),
            "message_id": entry.get("message_id") or entry.get("msg_id"),
            "raw_name": raw_name,
            "title": entry.get("title") or raw_name,
            "clean_title": entry.get("clean_title") or entry.get("title") or raw_name,
            "year": entry.get("year"),
            "is_tv": bool(entry.get("is_tv")),
            "show_name": entry.get("show_name"),
            "season": entry.get("season"),
            "episode": entry.get("episode"),
            "strm_path": strm_path,
            "tmdb_id": entry.get("tmdb_id"),
            "imdb_id": entry.get("imdb_id"),
            "file_size": entry.get("file_size"),
            "poster_url": entry.get("poster_url"),
            "backdrop_url": entry.get("backdrop_url"),
        })
    return items


async def audit_and_compare(
    jf_client: JellyfinClient,
    cache_path: str = DEFAULT_CACHE_FILE,
) -> Dict[str, Any]:
    """Compare 100% ground-truth Telegram injected media with current Jellyfin library.
    
    Identifies:
    1. Rogue / un-injected items in Jellyfin.
    2. Duplicate series or duplicate movies.
    3. Metadata mismatches (where Jellyfin title/year diverges from Telegram file).
    4. Missing artwork (items without posters or backdrops).
    """
    injected_files = load_telegram_injected_catalog(cache_path)
    jellyfin_items = await jf_client.get_all_library_items(include_item_types="Movie,Series,Episode", limit=2000)

    # Normalize strm paths from Telegram catalog
    injected_by_strm: Dict[str, Dict[str, Any]] = {}
    injected_by_name: Dict[str, List[Dict[str, Any]]] = {}

    for inj in injected_files:
        strm = os.path.normpath(str(inj.get("strm_path") or "")).lower()
        if strm and strm.endswith(".strm"):
            injected_by_strm[strm] = inj
            base = os.path.splitext(os.path.basename(strm))[0].lower()
            injected_by_strm[base] = inj

        clean_name = re.sub(r"[^a-z0-9]+", " ", str(inj.get("clean_title") or inj.get("title") or "")).strip().lower()
        if clean_name:
            injected_by_name.setdefault(clean_name, []).append(inj)

    rogue_items = []
    duplicate_series = []
    duplicate_movies = []
    mismatches = []
    missing_artwork = []

    series_seen: Dict[str, List[Dict[str, Any]]] = {}
    movie_seen: Dict[str, List[Dict[str, Any]]] = {}

    for it in jellyfin_items:
        itype = it.get("Type")
        item_id = it.get("id")
        name = it.get("name") or "Unknown"
        path = os.path.normpath(str(it.get("path") or "")).lower()
        prov_ids = it.get("provider_ids") or {}

        # 1. Check duplicate Series
        if itype == "Series":
            norm_series = re.sub(r"[^a-z0-9]+", " ", name).strip().lower()
            series_seen.setdefault(norm_series, []).append(it)
            if not it.get("has_poster"):
                missing_artwork.append({
                    "id": item_id,
                    "title": name,
                    "type": "Series",
                    "missing": "poster",
                })
            continue

        # 2. Check Movies and Episodes
        if itype == "Movie":
            norm_movie = re.sub(r"[^a-z0-9]+", " ", name).strip().lower()
            movie_seen.setdefault(norm_movie, []).append(it)

            if not it.get("has_poster"):
                missing_artwork.append({
                    "id": item_id,
                    "title": name,
                    "type": "Movie",
                    "missing": "poster",
                })

        # Match Jellyfin item to Telegram injection
        matched_inj = injected_by_strm.get(path)
        if not matched_inj and path:
            base_fname = os.path.splitext(os.path.basename(path))[0].lower()
            matched_inj = injected_by_strm.get(base_fname)

        if not matched_inj:
            # Check name match
            norm_name = re.sub(r"[^a-z0-9]+", " ", name).strip().lower()
            name_hits = injected_by_name.get(norm_name) or []
            if name_hits:
                matched_inj = name_hits[0]

        if not matched_inj and path and path.endswith(".strm"):
            # Rogue item in Jellyfin with no Telegram injection
            rogue_items.append({
                "id": item_id,
                "title": name,
                "type": itype,
                "path": it.get("path"),
                "reason": "No corresponding Telegram injected file found",
            })
        elif matched_inj:
            # Check for title/TMDb mismatch
            inj_raw = matched_inj.get("raw_name") or ""
            inj_title = matched_inj.get("title") or ""
            inj_tmdb = matched_inj.get("tmdb_id")
            jf_tmdb = prov_ids.get("Tmdb")

            norm_jf = re.sub(r"[^a-z0-9]+", "", name.lower())
            norm_raw = re.sub(r"[^a-z0-9]+", "", inj_title.lower())

            # Divergence check
            if norm_raw and norm_jf and norm_raw not in norm_jf and norm_jf not in norm_raw:
                mismatches.append({
                    "id": item_id,
                    "jellyfin_title": name,
                    "telegram_raw_name": inj_raw,
                    "expected_title": inj_title,
                    "expected_year": matched_inj.get("year"),
                    "jellyfin_tmdb": jf_tmdb,
                    "expected_tmdb": inj_tmdb,
                    "expected_imdb": matched_inj.get("imdb_id"),
                })

    # Collect duplicate Series
    for s_name, s_list in series_seen.items():
        if len(s_list) > 1:
            duplicate_series.append({
                "series_name": s_list[0].get("name"),
                "count": len(s_list),
                "items": [{"id": x.get("id"), "path": x.get("path")} for x in s_list],
            })

    # Collect duplicate Movies
    for m_name, m_list in movie_seen.items():
        if len(m_list) > 1:
            duplicate_movies.append({
                "movie_name": m_list[0].get("name"),
                "count": len(m_list),
                "items": [{"id": x.get("id"), "path": x.get("path")} for x in m_list],
            })

    return {
        "total_telegram_injected": len(injected_files),
        "total_jellyfin_items": len(jellyfin_items),
        "rogue_items_count": len(rogue_items),
        "rogue_items": rogue_items[:20],
        "duplicate_series_count": len(duplicate_series),
        "duplicate_series": duplicate_series[:10],
        "duplicate_movies_count": len(duplicate_movies),
        "duplicate_movies": duplicate_movies[:10],
        "mismatches_count": len(mismatches),
        "mismatches": mismatches[:20],
        "missing_artwork_count": len(missing_artwork),
        "missing_artwork": missing_artwork[:20],
    }


async def apply_artwork_from_url(
    jf_client: JellyfinClient,
    item_id: str,
    image_url: str,
    image_type: str = "Primary",
) -> Dict[str, Any]:
    """Download image safely and upload directly to a Jellyfin item."""
    is_safe, reason = validate_outbound_url(image_url)
    if not is_safe:
        raise ValueError(f"Artwork URL rejected by NetGuard: {reason}")

    clean_type = "Primary" if image_type.lower() in ("poster", "primary") else "Backdrop"
    mime = "image/jpeg"

    async with aiohttp.ClientSession() as session:
        async with session.get(
            image_url,
            timeout=aiohttp.ClientTimeout(total=15.0),
            headers={"User-Agent": "Apex-ArtworkFetcher/1.0"},
        ) as resp:
            if resp.status != 200:
                raise ValueError(f"Failed to download image (HTTP {resp.status}) from {image_url}")
            content_type = resp.headers.get("Content-Type", "image/jpeg")
            if "png" in content_type:
                mime = "image/png"
            img_bytes = await resp.read()

    if len(img_bytes) < 100 or len(img_bytes) > 15 * 1024 * 1024:
        raise ValueError(f"Invalid image payload size: {len(img_bytes)} bytes")

    # Upload to Jellyfin
    await jf_client.set_item_image_bytes(item_id, clean_type, img_bytes, mime_type=mime)
    await jf_client.refresh_item(item_id, replace_all=False)
    return {"id": item_id, "image_type": clean_type, "status": "applied", "url": image_url}


async def reconcile_item(
    jf_client: JellyfinClient,
    item_id: str,
    title: Optional[str] = None,
    year: Optional[int] = None,
    tmdb_id: Optional[int] = None,
    imdb_id: Optional[str] = None,
    overview: Optional[str] = None,
    poster_url: Optional[str] = None,
    backdrop_url: Optional[str] = None,
    cache_path: str = DEFAULT_CACHE_FILE,
    raw_name: Optional[str] = None,
    cache_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Correct an item's metadata and artwork in Jellyfin and synchronize with FILE_ID_CACHE."""
    current_name = None
    current_path = None
    try:
        cur_item = await jf_client.get_item(item_id)
        if cur_item:
            current_name = cur_item.get("name")
            current_path = os.path.normpath(str(cur_item.get("path") or "")).lower()
    except Exception:
        pass

    fields: Dict[str, Any] = {}
    if title:
        fields["Name"] = title
    if year:
        fields["ProductionYear"] = int(year)
    if overview:
        fields["Overview"] = overview

    prov_ids: Dict[str, str] = {}
    if tmdb_id:
        prov_ids["Tmdb"] = str(tmdb_id)
    if imdb_id:
        prov_ids["Imdb"] = str(imdb_id)
    if prov_ids:
        fields["ProviderIds"] = prov_ids

    # 1. Update metadata in Jellyfin
    if fields:
        await jf_client.update_item_metadata(item_id, fields)

    # 2. Apply artwork if provided
    applied_art = []
    if poster_url:
        try:
            res = await apply_artwork_from_url(jf_client, item_id, poster_url, image_type="Primary")
            applied_art.append(res)
        except Exception as e:
            logger.warning(f"[RECONCILE] Failed to apply poster: {e}")

    if backdrop_url:
        try:
            res = await apply_artwork_from_url(jf_client, item_id, backdrop_url, image_type="Backdrop")
            applied_art.append(res)
        except Exception as e:
            logger.warning(f"[RECONCILE] Failed to apply backdrop: {e}")

    # 3. Synchronize FILE_ID_CACHE on disk
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            updated = False
            for key, entry in cache_data.items():
                if not isinstance(entry, dict):
                    continue
                match = False
                if cache_key and key == cache_key:
                    match = True
                elif raw_name and raw_name.lower() in str(entry.get("raw_name") or entry.get("file_name") or "").lower():
                    match = True
                elif current_path:
                    strm = os.path.normpath(str(entry.get("strm_path") or "")).lower()
                    if strm and (strm == current_path or os.path.basename(strm) == os.path.basename(current_path)):
                        match = True
                if not match and current_name and (current_name.lower() in (entry.get("title") or "").lower() or (entry.get("title") or "").lower() in current_name.lower()):
                    match = True
                if not match and title and title.lower() in (entry.get("title") or "").lower():
                    match = True
                if not match and tmdb_id and entry.get("tmdb_id") == tmdb_id:
                    match = True

                if match:
                    if title:
                        entry["title"] = title
                        entry["clean_title"] = title
                    if year:
                        entry["year"] = int(year)
                    if tmdb_id:
                        entry["tmdb_id"] = int(tmdb_id)
                    if imdb_id:
                        entry["imdb_id"] = str(imdb_id)
                    if poster_url:
                        entry["poster_url"] = poster_url
                    if backdrop_url:
                        entry["backdrop_url"] = backdrop_url
                    updated = True

            if updated:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.warning(f"[RECONCILE] Error updating {cache_path}: {e}")

    await jf_client.refresh_item(item_id, replace_all=True)
    return {
        "id": item_id,
        "title": title,
        "year": year,
        "tmdb_id": tmdb_id,
        "imdb_id": imdb_id,
        "artwork": applied_art,
        "status": "reconciled",
    }


async def cleanup_rogue_and_duplicates(
    jf_client: JellyfinClient,
    remove_rogue: bool = True,
    deduplicate_series: bool = True,
    cache_path: str = DEFAULT_CACHE_FILE,
) -> Dict[str, Any]:
    """Clean up rogue un-injected items and merge duplicate series in Jellyfin."""
    audit = await audit_and_compare(jf_client, cache_path=cache_path)

    deleted_rogue = []
    if remove_rogue:
        for r in audit.get("rogue_items", []):
            rid = r.get("id")
            if rid:
                try:
                    await jf_client.delete_item(rid)
                    deleted_rogue.append(r)
                except Exception as e:
                    logger.warning(f"[CLEANUP] Failed to delete rogue item {rid}: {e}")

    deleted_duplicate_series = []
    if deduplicate_series:
        for s in audit.get("duplicate_series", []):
            items = s.get("items") or []
            if len(items) > 1:
                # Keep the first, delete the rest
                for dup in items[1:]:
                    dup_id = dup.get("id")
                    if dup_id:
                        try:
                            await jf_client.delete_item(dup_id)
                            deleted_duplicate_series.append(dup)
                        except Exception as e:
                            logger.warning(f"[CLEANUP] Failed to delete duplicate series {dup_id}: {e}")

    # Trigger library refresh
    await jf_client.refresh_library()

    return {
        "deleted_rogue_count": len(deleted_rogue),
        "deleted_rogue_items": deleted_rogue,
        "deleted_duplicate_series_count": len(deleted_duplicate_series),
        "deleted_duplicate_series": deleted_duplicate_series,
        "status": "cleanup_complete",
    }
