# Thunder/bot/plugins/ai_admin.py
"""Dedicated read-only AI Administrator plugin for StreamBot.

Integrates TelegramAIAdminRouter into Pyrogram handler group -1.
Features:
- Disabled by default (dormant unless AI_ENABLED=true).
- Fails closed on missing or invalid administrator configuration.
- Strict read-only tools only (zero mutating tools registered).
- Thread-safe and idempotent (guards against duplicate handler registration).
- Private admin chat authorization and safe HTML formatting.
"""

import logging
import os
from typing import Optional

from pyrogram import Client

from ai_admin.audit_log import AuditLog
from ai_admin.config import AIAdminConfig
from ai_admin.confirmation_store import ConfirmationStore
from ai_admin.context_store import ContextStore
from ai_admin.grammar import GrammarParser
from ai_admin.handler import AIAdminHandler
from ai_admin.jellyfin_client import JellyfinClient
from ai_admin.omniroute_adapter import OmniRouteAdapter
from ai_admin.permissions import PermissionChecker
from ai_admin.providers_client import ProvidersClient
from ai_admin.snapshot_store import SnapshotStore
from ai_admin.telegram_router import TelegramAIAdminRouter
from ai_admin.tool_registry import ToolRegistry
from ai_admin.tool_runner import ToolRunner
from ai_admin.tools_jellyfin import get_jellyfin_read_tool_definitions
from ai_admin.tools_providers import get_provider_read_tool_definitions

logger = logging.getLogger("Thunder.Plugin.AIAdmin")

_REGISTERED = False
_REGISTERED_CLIENT_IDS = set()
_ROUTER_INSTANCE: Optional[TelegramAIAdminRouter] = None


def get_stream_bot() -> Optional[Client]:
    """Safely obtain primary StreamBot instance if Telegram environment is configured."""
    try:
        from Thunder.bot import StreamBot
        return StreamBot
    except Exception as e:
        logger.debug(f"StreamBot unavailable or unconfigured: {e}")
        return None


def setup_ai_admin(client: Optional[Client] = None) -> Optional[TelegramAIAdminRouter]:
    """Initialize and register AI Admin router if enabled and valid.

    Idempotent: protects against duplicate handler registration.
    Supports multiple Pyrogram clients (e.g. StreamBot and tg_app).
    Fails closed if disabled, unconfigured, or invalid.
    """
    global _REGISTERED, _REGISTERED_CLIENT_IDS, _ROUTER_INSTANCE

    target_client = client or get_stream_bot()

    if _ROUTER_INSTANCE is not None:
        if target_client is not None and id(target_client) not in _REGISTERED_CLIENT_IDS:
            try:
                _ROUTER_INSTANCE.register_handlers(target_client, group=-1)
                _REGISTERED_CLIENT_IDS.add(id(target_client))
                logger.info("Registered AI Admin handlers on additional Pyrogram client.")
            except Exception as e:
                logger.debug(f"Could not register handlers on client: {e}")
        return _ROUTER_INSTANCE

    config = AIAdminConfig.from_env()

    # 1. Disabled by default
    if not config.enabled:
        logger.info("AI Administrator is disabled (AI_ENABLED=false). Plugin remains dormant.")
        return None

    # 2. Validation check (fail closed)
    if not config.is_valid or not config.admin_telegram_ids:
        logger.warning(
            f"AI Administrator configuration is invalid ({config.validation_error}). "
            "Failing closed without registering handlers."
        )
        return None

    target_client = client or get_stream_bot()
    if target_client is None:
        logger.warning("No Telegram client available to register AI Admin handlers. Failing closed.")
        return None

    try:
        # 3. Build isolated read-only dependencies
        permissions = PermissionChecker(config)
        audit_log = AuditLog(data_dir=config.data_dir)
        confirm_store = ConfirmationStore(db_path=os.path.join(config.data_dir, "confirmations.sqlite"))
        context_store = ContextStore(ttl_seconds=config.context_ttl_seconds)
        snapshot_store = SnapshotStore(data_dir=config.data_dir)
        omniroute = OmniRouteAdapter(config)
        grammar = GrammarParser()

        # 4. Strict read-only tool registry (ZERO mutating tools registered)
        registry = ToolRegistry()
        jf_client = JellyfinClient(
            base_url=config.jellyfin_base_url,
            api_key=config.jellyfin_api_key,
        )
        for tool_def in get_jellyfin_read_tool_definitions(jf_client):
            registry.register(tool_def)

        prov_client = ProvidersClient(
            tmdb_api_key=os.environ.get("TMDB_API_KEY", ""),
            fanart_api_key=os.environ.get("FANART_API_KEY", ""),
            opensubtitles_api_key=os.environ.get("OPENSUBTITLES_API_KEY", ""),
        )
        for tool_def in get_provider_read_tool_definitions(prov_client):
            registry.register(tool_def)

        runner = ToolRunner(
            config=config,
            registry=registry,
            permissions=permissions,
            audit_log=audit_log,
            confirmation_store=confirm_store,
        )

        handler = AIAdminHandler(
            config=config,
            permissions=permissions,
            grammar=grammar,
            runner=runner,
            context_store=context_store,
            snapshot_store=snapshot_store,
            omniroute=omniroute,
            registry=registry,
        )

        router = TelegramAIAdminRouter(
            config=config,
            permissions=permissions,
            handler=handler,
        )

        # 5. Register handlers in Pyrogram group -1
        router.register_handlers(target_client, group=-1)
        _REGISTERED_CLIENT_IDS.add(id(target_client))

        _REGISTERED = True
        _ROUTER_INSTANCE = router
        logger.info("AI Administrator read-only plugin initialized successfully in Pyrogram group=-1.")
        return router

    except Exception as e:
        logger.error(f"Failed to initialize AI Admin plugin: {e}", exc_info=True)
        if "router" in locals() and target_client is not None:
            try:
                router.unregister_handlers(target_client)
            except Exception:
                pass
        return None


def reset_plugin_state() -> None:
    """Testing helper to reset registration state between test runs."""
    global _REGISTERED, _REGISTERED_CLIENT_IDS, _ROUTER_INSTANCE
    _REGISTERED = False
    _REGISTERED_CLIENT_IDS.clear()
    _ROUTER_INSTANCE = None


# Trigger setup on module load if bot is available (standard Pyrogram plugin lifecycle)
setup_ai_admin()
