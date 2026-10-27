"""Stage 2 Jellyfin tools implementation: active read-only tools and disabled mutation definitions."""

import logging
from typing import Any, Dict, List, Optional

from ai_admin.jellyfin_client import JellyfinClient
from ai_admin.mutation_contracts import MUTATION_CONTRACTS
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
