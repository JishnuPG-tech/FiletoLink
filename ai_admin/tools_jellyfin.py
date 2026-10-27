"""Stage 2 Jellyfin tools implementation: active read-only tools and disabled mutation definitions."""

import logging
from typing import Any, Dict, List, Optional

from ai_admin.jellyfin_client import JellyfinClient
from ai_admin.mutation_contracts import MUTATION_CONTRACTS
from ai_admin.reconciler import (
    apply_artwork_from_url,
    audit_and_compare,
    cleanup_rogue_and_duplicates,
    load_telegram_injected_catalog,
    reconcile_item,
)
from ai_admin.tool_registry import ToolDefinition, ToolRegistry
from ai_admin.validators import validate_item_id

logger = logging.getLogger("AIAdmin.ToolsJellyfin")


# ==============================================================================
# 1. Read-Only Tool Handlers
# ==============================================================================

def make_jellyfin_search_handler(client: JellyfinClient):
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "")
        item_types = params.get("item_types", "Movie,Series,Episode")
        limit = params.get("limit", 20)
        items = await client.search_items(query=query, item_types=item_types, limit=limit)
        return {
            "query": query,
            "count": len(items),
            "items": items,
        }
    return handler


def make_jellyfin_get_item_handler(client: JellyfinClient):
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        item_id = params.get("item_id", "")
        item = await client.get_item(item_id=item_id)
        return item
    return handler


def make_jellyfin_list_missing_metadata_handler(client: JellyfinClient):
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        filter_types = params.get("filter_types")
        limit = params.get("limit", 30)
        items = await client.list_missing_metadata(filter_types=filter_types, limit=limit)
        return {
            "count": len(items),
            "items": items,
        }
    return handler


def make_jellyfin_get_media_info_handler(client: JellyfinClient):
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        item_id = params.get("item_id", "")
        info = await client.get_media_info(item_id=item_id)
        return info
    return handler


def make_telegram_list_injected_handler():
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        query = (params.get("query") or "").strip().lower()
        filter_type = params.get("filter_type")
        items = load_telegram_injected_catalog()

        if query:
            items = [
                it for it in items
                if query in (it.get("raw_name") or "").lower()
                or query in (it.get("title") or "").lower()
                or query in (it.get("show_name") or "").lower()
            ]

        if filter_type == "movie":
            items = [it for it in items if not it.get("is_tv")]
        elif filter_type == "tv":
            items = [it for it in items if it.get("is_tv")]

        return {
            "count": len(items),
            "items": items[:params.get("limit", 50)],
        }
    return handler


def make_jellyfin_list_library_handler(client: JellyfinClient):
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        item_types = params.get("item_types", "Movie,Series")
        limit = params.get("limit", 100)
        items = await client.get_all_library_items(include_item_types=item_types, limit=limit)
        return {
            "count": len(items),
            "items": items,
        }
    return handler


def make_library_audit_and_compare_handler(client: JellyfinClient):
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        audit = await audit_and_compare(jf_client=client)
        return audit
    return handler


def make_library_fix_item_handler(client: JellyfinClient):
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        item_id = params.get("item_id", "")
        title = params.get("title")
        year = params.get("year")
        tmdb_id = params.get("tmdb_id")
        imdb_id = params.get("imdb_id")
        overview = params.get("overview")
        poster_url = params.get("poster_url")
        backdrop_url = params.get("backdrop_url")

        res = await reconcile_item(
            jf_client=client,
            item_id=item_id,
            title=title,
            year=year,
            tmdb_id=tmdb_id,
            imdb_id=imdb_id,
            overview=overview,
            poster_url=poster_url,
            backdrop_url=backdrop_url,
        )
        return res
    return handler


def make_library_cleanup_rogue_and_duplicates_handler(client: JellyfinClient):
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        remove_rogue = params.get("remove_rogue", True)
        deduplicate_series = params.get("deduplicate_series", True)
        res = await cleanup_rogue_and_duplicates(
            jf_client=client,
            remove_rogue=remove_rogue,
            deduplicate_series=deduplicate_series,
        )
        return res
    return handler


def make_jellyfin_apply_artwork_handler(client: JellyfinClient):
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        item_id = params.get("item_id", "")
        image_url = params.get("image_url", "")
        image_type = params.get("image_type", "Primary")
        res = await apply_artwork_from_url(
            jf_client=client,
            item_id=item_id,
            image_url=image_url,
            image_type=image_type,
        )
        return res
    return handler


# ==============================================================================
# 2. Disabled Mutation Placeholders (Fail-closed)
# ==============================================================================

async def disabled_mutation_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    """Strict fail-closed stub for disabled mutating operations."""
    raise PermissionError("Mutating operations are disabled in Stage 2.")


# ==============================================================================
# 3. Tool Definitions & Registration
# ==============================================================================

def get_jellyfin_read_tool_definitions(client: JellyfinClient) -> List[ToolDefinition]:
    """Build tool definitions for active read-only Jellyfin tools."""
    return [
        ToolDefinition(
            name="jellyfin_search",
            purpose="Search Jellyfin media library for movies, series, or episodes by title.",
            json_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "maxLength": 100},
                    "item_types": {"type": "string", "maxLength": 50},
                    "limit": {"type": "integer"},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            read_only=True,
            mutates=False,
            risk="low",
            requires_confirmation="never",
            permission="read",
            timeout_seconds=15,
            max_output_chars=4000,
            handler=make_jellyfin_search_handler(client),
        ),
        ToolDefinition(
            name="jellyfin_get_item",
            purpose="Get full metadata details for a specific media item by its Jellyfin item ID.",
            json_schema={
                "type": "object",
                "properties": {
                    "item_id": {"type": "string", "maxLength": 64},
                },
                "required": ["item_id"],
                "additionalProperties": False,
            },
            read_only=True,
            mutates=False,
            risk="low",
            requires_confirmation="never",
            permission="read",
            timeout_seconds=10,
            max_output_chars=4000,
            handler=make_jellyfin_get_item_handler(client),
            validators=[lambda p: validate_item_id(p.get("item_id", ""))],
        ),
        ToolDefinition(
            name="jellyfin_list_missing_metadata",
            purpose="List library items that are missing posters, backdrops, overviews, or provider IDs.",
            json_schema={
                "type": "object",
                "properties": {
                    "filter_types": {"type": "array"},
                    "limit": {"type": "integer"},
                },
                "additionalProperties": False,
            },
            read_only=True,
            mutates=False,
            risk="low",
            requires_confirmation="never",
            permission="read",
            timeout_seconds=20,
            max_output_chars=4000,
            handler=make_jellyfin_list_missing_metadata_handler(client),
        ),
        ToolDefinition(
            name="jellyfin_get_media_info",
            purpose="Inspect technical media streams, video codec/resolution, audio tracks, and subtitles.",
            json_schema={
                "type": "object",
                "properties": {
                    "item_id": {"type": "string", "maxLength": 64},
                },
                "required": ["item_id"],
                "additionalProperties": False,
            },
            read_only=True,
            mutates=False,
            risk="low",
            requires_confirmation="never",
            permission="read",
            timeout_seconds=10,
            max_output_chars=4000,
            handler=make_jellyfin_get_media_info_handler(client),
            validators=[lambda p: validate_item_id(p.get("item_id", ""))],
        ),
        ToolDefinition(
            name="telegram_list_injected",
            purpose="List raw media files injected from Telegram, with original file names, message IDs, and parsed details.",
            json_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "maxLength": 100},
                    "filter_type": {"type": "string", "maxLength": 10},
                    "limit": {"type": "integer"},
                },
                "additionalProperties": False,
            },
            read_only=True,
            mutates=False,
            risk="low",
            requires_confirmation="never",
            permission="read",
            timeout_seconds=10,
            max_output_chars=4000,
            handler=make_telegram_list_injected_handler(),
        ),
        ToolDefinition(
            name="jellyfin_list_library",
            purpose="List all media items currently in Jellyfin library, with item IDs, titles, and paths.",
            json_schema={
                "type": "object",
                "properties": {
                    "item_types": {"type": "string", "maxLength": 50},
                    "limit": {"type": "integer"},
                },
                "additionalProperties": False,
            },
            read_only=True,
            mutates=False,
            risk="low",
            requires_confirmation="never",
            permission="read",
            timeout_seconds=20,
            max_output_chars=4000,
            handler=make_jellyfin_list_library_handler(client),
        ),
        ToolDefinition(
            name="library_audit_and_compare",
            purpose="Compare Telegram injected files (the 100% ground truth) with Jellyfin items to detect rogue movies, duplicate series, and mismatches.",
            json_schema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            read_only=True,
            mutates=False,
            risk="low",
            requires_confirmation="never",
            permission="read",
            timeout_seconds=30,
            max_output_chars=4000,
            handler=make_library_audit_and_compare_handler(client),
        ),
    ]


def get_jellyfin_active_mutation_definitions(client: JellyfinClient) -> List[ToolDefinition]:
    """Tool definitions for active mutating operations when AI_MUTATIONS_ENABLED=true."""
    return [
        ToolDefinition(
            name="library_fix_item",
            purpose="Correct title, year, TMDb ID, IMDb ID, or authentic artwork for a Jellyfin item and update cache.",
            json_schema={
                "type": "object",
                "properties": {
                    "item_id": {"type": "string", "maxLength": 64},
                    "title": {"type": "string", "maxLength": 100},
                    "year": {"type": "integer"},
                    "tmdb_id": {"type": "integer"},
                    "imdb_id": {"type": "string", "maxLength": 20},
                    "overview": {"type": "string", "maxLength": 1000},
                    "poster_url": {"type": "string", "maxLength": 300},
                    "backdrop_url": {"type": "string", "maxLength": 300},
                },
                "required": ["item_id"],
                "additionalProperties": False,
            },
            read_only=False,
            mutates=True,
            risk="medium",
            requires_confirmation="never",
            permission="write",
            timeout_seconds=30,
            max_output_chars=4000,
            handler=make_library_fix_item_handler(client),
            validators=[lambda p: validate_item_id(p.get("item_id", ""))],
        ),
        ToolDefinition(
            name="library_cleanup_rogue_and_duplicates",
            purpose="Delete rogue un-injected items and merge/clean duplicate series in Jellyfin.",
            json_schema={
                "type": "object",
                "properties": {
                    "remove_rogue": {"type": "boolean"},
                    "deduplicate_series": {"type": "boolean"},
                },
                "additionalProperties": False,
            },
            read_only=False,
            mutates=True,
            risk="medium",
            requires_confirmation="never",
            permission="write",
            timeout_seconds=30,
            max_output_chars=4000,
            handler=make_library_cleanup_rogue_and_duplicates_handler(client),
        ),
        ToolDefinition(
            name="jellyfin_apply_artwork",
            purpose="Download and apply authentic poster or backdrop image from URL to a Jellyfin item.",
            json_schema={
                "type": "object",
                "properties": {
                    "item_id": {"type": "string", "maxLength": 64},
                    "image_url": {"type": "string", "maxLength": 300},
                    "image_type": {"type": "string", "maxLength": 20},
                },
                "required": ["item_id", "image_url"],
                "additionalProperties": False,
            },
            read_only=False,
            mutates=True,
            risk="medium",
            requires_confirmation="never",
            permission="write",
            timeout_seconds=25,
            max_output_chars=4000,
            handler=make_jellyfin_apply_artwork_handler(client),
            validators=[lambda p: validate_item_id(p.get("item_id", ""))],
        ),
    ]


def get_disabled_mutation_definitions() -> List[ToolDefinition]:
    """Tool definitions for mutating operations - kept explicitly disabled in Stage 2."""
    return [
        ToolDefinition(
            name="jellyfin_refresh_item",
            purpose="Queue a metadata and artwork refresh for a specific Jellyfin item.",
            json_schema={
                "type": "object",
                "properties": {
                    "item_id": {"type": "string", "maxLength": 64},
                    "refresh_images": {"type": "boolean"},
                },
                "required": ["item_id"],
                "additionalProperties": False,
            },
            read_only=False,
            mutates=True,
            risk="medium",
            requires_confirmation="always",
            permission="write",
            timeout_seconds=15,
            max_output_chars=4000,
            handler=disabled_mutation_handler,
            validators=[lambda p: validate_item_id(p.get("item_id", ""))],
        ),
        ToolDefinition(
            name="jellyfin_update_metadata",
            purpose="Update title, overview, genres, or provider IDs for a Jellyfin item.",
            json_schema={
                "type": "object",
                "properties": {
                    "item_id": {"type": "string", "maxLength": 64},
                    "fields": {"type": "object"},
                },
                "required": ["item_id", "fields"],
                "additionalProperties": False,
            },
            read_only=False,
            mutates=True,
            risk="medium",
            requires_confirmation="always",
            permission="write",
            timeout_seconds=15,
            max_output_chars=4000,
            handler=disabled_mutation_handler,
            validators=[lambda p: validate_item_id(p.get("item_id", ""))],
        ),
        ToolDefinition(
            name="apply_image",
            purpose="Download and apply approved artwork candidate to a Jellyfin item.",
            json_schema={
                "type": "object",
                "properties": {
                    "item_id": {"type": "string", "maxLength": 64},
                    "candidate_id": {"type": "string", "maxLength": 64},
                    "image_type": {"type": "string", "maxLength": 30},
                },
                "required": ["item_id", "candidate_id", "image_type"],
                "additionalProperties": False,
            },
            read_only=False,
            mutates=True,
            risk="medium",
            requires_confirmation="always",
            permission="write",
            timeout_seconds=20,
            max_output_chars=4000,
            handler=disabled_mutation_handler,
            validators=[lambda p: validate_item_id(p.get("item_id", ""))],
        ),
        ToolDefinition(
            name="apply_subtitle",
            purpose="Download and place approved subtitle candidate next to media stream.",
            json_schema={
                "type": "object",
                "properties": {
                    "item_id": {"type": "string", "maxLength": 64},
                    "candidate_id": {"type": "string", "maxLength": 64},
                    "language": {"type": "string", "maxLength": 10},
                },
                "required": ["item_id", "candidate_id", "language"],
                "additionalProperties": False,
            },
            read_only=False,
            mutates=True,
            risk="medium",
            requires_confirmation="always",
            permission="write",
            timeout_seconds=20,
            max_output_chars=4000,
            handler=disabled_mutation_handler,
            validators=[lambda p: validate_item_id(p.get("item_id", ""))],
        ),
        ToolDefinition(
            name="revert_last_change",
            purpose="Rollback previous modification using snapshot reference.",
            json_schema={
                "type": "object",
                "properties": {
                    "snapshot_id": {"type": "string", "maxLength": 64},
                    "item_id": {"type": "string", "maxLength": 64},
                },
                "additionalProperties": False,
            },
            read_only=False,
            mutates=True,
            risk="high",
            requires_confirmation="always",
            permission="write",
            timeout_seconds=15,
            max_output_chars=4000,
            handler=disabled_mutation_handler,
        ),
    ]


def register_jellyfin_tools(registry: ToolRegistry, client: JellyfinClient, register_mutations: bool = False) -> None:
    """Register Jellyfin tools into ToolRegistry. Mutations remain unregistered unless explicitly enabled."""
    for tool_def in get_jellyfin_read_tool_definitions(client):
        registry.register(tool_def)

    if register_mutations:
        for tool_def in get_disabled_mutation_definitions():
            registry.register(tool_def)
