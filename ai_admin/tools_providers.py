"""Stage 3 External provider read-only tools: TMDb, Fanart.tv, and OpenSubtitles."""

import logging
from typing import Any, Dict, List

from ai_admin.providers_client import ProvidersClient
from ai_admin.tool_registry import ToolDefinition, ToolRegistry

logger = logging.getLogger("AIAdmin.ToolsProviders")


# ==============================================================================
# Tool Handlers
# ==============================================================================

def make_tmdb_search_handler(client: ProvidersClient):
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "")
        media_type = params.get("media_type", "movie")
        year = params.get("year")
        language = params.get("language")
        limit = params.get("limit", 10)

        hits = await client.tmdb_search(
            query=query,
            media_type=media_type,
            year=year,
            language=language,
            limit=limit,
        )
        return {
            "query": query,
            "media_type": media_type,
            "count": len(hits),
            "results": hits,
        }
    return handler


def make_tmdb_get_details_handler(client: ProvidersClient):
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        tmdb_id = params.get("tmdb_id")
        media_type = params.get("media_type", "movie")
        details = await client.tmdb_get_details(tmdb_id=tmdb_id, media_type=media_type)
        return details
    return handler


def make_fanart_get_images_handler(client: ProvidersClient):
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        id_str = str(params.get("id", ""))
        media_type = params.get("media_type", "movie")
        limit = params.get("limit", 15)

        candidates = await client.fanart_get_images(
            id_str=id_str,
            media_type=media_type,
            limit=limit,
        )
        return {
            "id": id_str,
            "media_type": media_type,
            "count": len(candidates),
            "candidates": candidates,
        }
    return handler


def make_opensubtitles_search_handler(client: ProvidersClient):
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query")
        imdb_id = params.get("imdb_id")
        tmdb_id = params.get("tmdb_id")
        languages = params.get("languages", "en")
        season = params.get("season")
        episode = params.get("episode")
        limit = params.get("limit", 10)

        candidates = await client.opensubtitles_search(
            query=query,
            imdb_id=imdb_id,
            tmdb_id=tmdb_id,
            languages=languages,
            season=season,
            episode=episode,
            limit=limit,
        )
        return {
            "count": len(candidates),
            "languages": languages,
            "candidates": candidates,
        }
    return handler


def make_tmdb_get_images_handler(client: ProvidersClient):
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        tmdb_id = params.get("tmdb_id")
        media_type = params.get("media_type", "movie")
        limit = params.get("limit", 20)
        candidates = await client.tmdb_get_images(
            tmdb_id=tmdb_id,
            media_type=media_type,
            limit=limit,
        )
        return {
            "tmdb_id": tmdb_id,
            "media_type": media_type,
            "count": len(candidates),
            "candidates": candidates,
        }
    return handler


def make_cinemeta_search_handler(client: ProvidersClient):
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "")
        media_type = params.get("media_type", "movie")
        limit = params.get("limit", 10)
        results = await client.cinemeta_search(
            query=query,
            media_type=media_type,
            limit=limit,
        )
        return {
            "query": query,
            "media_type": media_type,
            "count": len(results),
            "results": results,
            "provider": "cinemeta (IMDb)",
        }
    return handler


def make_cinemeta_get_meta_handler(client: ProvidersClient):
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        imdb_id = params.get("imdb_id", "")
        media_type = params.get("media_type", "movie")
        details = await client.cinemeta_get_meta(
            imdb_id=imdb_id,
            media_type=media_type,
        )
        return details
    return handler


def make_tvmaze_search_handler(client: ProvidersClient):
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "")
        limit = params.get("limit", 10)
        results = await client.tvmaze_search(
            query=query,
            limit=limit,
        )
        return {
            "query": query,
            "count": len(results),
            "results": results,
            "provider": "tvmaze",
        }
    return handler


def make_artwork_search_handler(client: ProvidersClient):
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query")
        imdb_id = params.get("imdb_id")
        tmdb_id = params.get("tmdb_id")
        media_type = params.get("media_type", "movie")
        limit = params.get("limit", 15)
        candidates = await client.artwork_search(
            query=query,
            imdb_id=imdb_id,
            tmdb_id=tmdb_id,
            media_type=media_type,
            limit=limit,
        )
        return {
            "query": query,
            "imdb_id": imdb_id,
            "tmdb_id": tmdb_id,
            "count": len(candidates),
            "candidates": candidates,
        }
    return handler


# ==============================================================================
# Tool Definitions
# ==============================================================================

def get_provider_read_tool_definitions(client: ProvidersClient) -> List[ToolDefinition]:
    """Build tool definitions for active read-only provider tools."""
    return [
        ToolDefinition(
            name="tmdb_search",
            purpose="Search The Movie Database (TMDb) for movies or TV shows by title, year, and language.",
            json_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "maxLength": 100},
                    "media_type": {"type": "string", "maxLength": 10},
                    "year": {"type": "integer"},
                    "language": {"type": "string", "maxLength": 10},
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
            handler=make_tmdb_search_handler(client),
        ),
        ToolDefinition(
            name="tmdb_get_details",
            purpose="Fetch complete metadata, external IMDb IDs, genres, and ratings from TMDb.",
            json_schema={
                "type": "object",
                "properties": {
                    "tmdb_id": {"type": "integer"},
                    "media_type": {"type": "string", "maxLength": 10},
                },
                "required": ["tmdb_id"],
                "additionalProperties": False,
            },
            read_only=True,
            mutates=False,
            risk="low",
            requires_confirmation="never",
            permission="read",
            timeout_seconds=15,
            max_output_chars=4000,
            handler=make_tmdb_get_details_handler(client),
        ),
        ToolDefinition(
            name="tmdb_get_images",
            purpose="Fetch all official posters, backdrops, and logos from TMDb by tmdb_id.",
            json_schema={
                "type": "object",
                "properties": {
                    "tmdb_id": {"type": "integer"},
                    "media_type": {"type": "string", "maxLength": 10},
                    "limit": {"type": "integer"},
                },
                "required": ["tmdb_id"],
                "additionalProperties": False,
            },
            read_only=True,
            mutates=False,
            risk="low",
            requires_confirmation="never",
            permission="read",
            timeout_seconds=15,
            max_output_chars=4000,
            handler=make_tmdb_get_images_handler(client),
        ),
        ToolDefinition(
            name="cinemeta_search",
            purpose="Search Stremio Cinemeta catalog (free, no API key required) for movies or series to get IMDb posters.",
            json_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "maxLength": 100},
                    "media_type": {"type": "string", "maxLength": 10},
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
            handler=make_cinemeta_search_handler(client),
        ),
        ToolDefinition(
            name="cinemeta_get_meta",
            purpose="Fetch high-resolution poster and background from Cinemeta (free, no API key required) by IMDb ID.",
            json_schema={
                "type": "object",
                "properties": {
                    "imdb_id": {"type": "string", "maxLength": 20},
                    "media_type": {"type": "string", "maxLength": 10},
                },
                "required": ["imdb_id"],
                "additionalProperties": False,
            },
            read_only=True,
            mutates=False,
            risk="low",
            requires_confirmation="never",
            permission="read",
            timeout_seconds=15,
            max_output_chars=4000,
            handler=make_cinemeta_get_meta_handler(client),
        ),
        ToolDefinition(
            name="tvmaze_search",
            purpose="Search TVmaze for TV shows and official artwork (free, no API key required).",
            json_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "maxLength": 100},
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
            handler=make_tvmaze_search_handler(client),
        ),
        ToolDefinition(
            name="artwork_search",
            purpose="Search posters and backdrops across multiple free and configured providers (TMDb, Cinemeta, TVmaze, Fanart.tv) with automatic fallback.",
            json_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "maxLength": 100},
                    "imdb_id": {"type": "string", "maxLength": 20},
                    "tmdb_id": {"type": "integer"},
                    "media_type": {"type": "string", "maxLength": 10},
                    "limit": {"type": "integer"},
                },
                "additionalProperties": False,
            },
            read_only=True,
            mutates=False,
            risk="low",
            requires_confirmation="never",
            permission="read",
            timeout_seconds=15,
            max_output_chars=4000,
            handler=make_artwork_search_handler(client),
        ),
        ToolDefinition(
            name="fanart_get_images",
            purpose="Query Fanart.tv for high-resolution posters, clearlogos, banners, and backdrops.",
            json_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "maxLength": 32},
                    "media_type": {"type": "string", "maxLength": 10},
                    "limit": {"type": "integer"},
                },
                "required": ["id"],
                "additionalProperties": False,
            },
            read_only=True,
            mutates=False,
            risk="low",
            requires_confirmation="never",
            permission="read",
            timeout_seconds=15,
            max_output_chars=4000,
            handler=make_fanart_get_images_handler(client),
        ),
        ToolDefinition(
            name="opensubtitles_search",
            purpose="Search OpenSubtitles for subtitle candidates matching a movie or TV episode.",
            json_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "maxLength": 100},
                    "imdb_id": {"type": "string", "maxLength": 20},
                    "tmdb_id": {"type": "integer"},
                    "languages": {"type": "string", "maxLength": 30},
                    "season": {"type": "integer"},
                    "episode": {"type": "integer"},
                    "limit": {"type": "integer"},
                },
                "additionalProperties": False,
            },
            read_only=True,
            mutates=False,
            risk="low",
            requires_confirmation="never",
            permission="read",
            timeout_seconds=15,
            max_output_chars=4000,
            handler=make_opensubtitles_search_handler(client),
        ),
    ]


def register_provider_tools(registry: ToolRegistry, client: ProvidersClient) -> None:
    """Register external provider read-only tools into ToolRegistry."""
    for tool_def in get_provider_read_tool_definitions(client):
        registry.register(tool_def)
