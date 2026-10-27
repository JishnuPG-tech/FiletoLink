"""Unit tests for ai_admin/grammar.py and ai_admin/handler.py."""

import pytest
from ai_admin.audit_log import AuditLog
from ai_admin.config import AIAdminConfig
from ai_admin.confirmation_store import ConfirmationStore
from ai_admin.context_store import ContextStore
from ai_admin.grammar import GrammarParser
from ai_admin.handler import AIAdminHandler
from ai_admin.omniroute_adapter import OmniRouteAdapter
from ai_admin.permissions import PermissionChecker
from ai_admin.snapshot_store import SnapshotStore
from ai_admin.tool_registry import ToolDefinition, ToolRegistry
from ai_admin.tool_runner import ToolRunner


def test_grammar_parsing_commands():
    grammar = GrammarParser()

    assert grammar.parse("status") == ("status", {})
    assert grammar.parse("reset") == ("reset", {})
    assert grammar.parse("undo") == ("undo", {})
    assert grammar.parse("find Inception") == ("search_library_items", {"query": "Inception"})
    assert grammar.parse("search 'The Dark Knight'") == ("search_library_items", {"query": "The Dark Knight"})
    assert grammar.parse("details item_123") == ("get_item_details", {"item_id": "item_123"})
    assert grammar.parse("images item_123") == ("get_item_images", {"item_id": "item_123"})
    assert grammar.parse("subtitles item_123") == ("get_item_subtitles", {"item_id": "item_123"})

    # Contextual follow-up
    assert grammar.parse("show images", selected_item_id="item_focus") == ("get_item_images", {"item_id": "item_focus"})
    assert grammar.parse("random natural language query") is None


@pytest.fixture
def handler_setup(tmp_path):
    config = AIAdminConfig(
        enabled=True,
        mutations_enabled=False,
        admin_telegram_ids={1001},
        data_dir=str(tmp_path),
    )
    registry = ToolRegistry()
    permissions = PermissionChecker(config)
    audit = AuditLog(str(tmp_path))
    confirm_store = ConfirmationStore(str(tmp_path / "confirm.sqlite"))
    context_store = ContextStore()
    snapshot_store = SnapshotStore(str(tmp_path))
    omniroute = OmniRouteAdapter(config)
    runner = ToolRunner(config, registry, permissions, audit, confirm_store)
    grammar = GrammarParser()

    # Register mock echo_health tool
    registry.register(
        ToolDefinition(
            name="search_library_items",
            purpose="Search items",
            json_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
                "additionalProperties": False,
            },
            read_only=True,
            mutates=False,
            risk="low",
            requires_confirmation="never",
            permission="read",
            timeout_seconds=5,
            max_output_chars=500,
            handler=lambda p: [{"id": "1", "name": p["query"]}],
        )
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
    return handler, context_store


@pytest.mark.asyncio
async def test_handler_unauthorized_user_rejected_before_tool(handler_setup):
    handler, _ = handler_setup
    handled, response = await handler.handle_message(
        user_id=9999,  # Unauthorized
        chat_id=9999,
        text="find Inception",
    )
    assert handled is False
    assert "Access denied" in response


@pytest.mark.asyncio
async def test_handler_help_and_status(handler_setup):
    handler, _ = handler_setup

    # Help
    h1, r1 = await handler.handle_message(user_id=1001, chat_id=1001, text="/ai")
    assert h1 is True
    assert "Jellyfin AI Administrator" in r1

    # Status
    h2, r2 = await handler.handle_message(user_id=1001, chat_id=1001, text="status")
    assert h2 is True
    assert "AI Admin Status" in r2


@pytest.mark.asyncio
async def test_handler_grammar_dispatch(handler_setup):
    handler, _ = handler_setup
    handled, response = await handler.handle_message(
        user_id=1001,
        chat_id=1001,
        text="find Inception",
    )
    assert handled is True
    assert "search_library_items" in response
    assert "Inception" in response
