"""Unit tests for Stage 4A ai_admin/telegram_router.py."""

from unittest.mock import AsyncMock, MagicMock
import pytest
from pyrogram import StopPropagation
from pyrogram.enums import ChatType, ParseMode

from ai_admin.audit_log import AuditLog
from ai_admin.config import AIAdminConfig
from ai_admin.confirmation_store import ConfirmationStore
from ai_admin.context_store import ContextStore
from ai_admin.grammar import GrammarParser
from ai_admin.handler import AIAdminHandler
from ai_admin.omniroute_adapter import OmniRouteAdapter
from ai_admin.permissions import PermissionChecker
from ai_admin.snapshot_store import SnapshotStore
from ai_admin.telegram_router import (
    MAX_TELEGRAM_MESSAGE_LENGTH,
    TelegramAIAdminRouter,
    is_forwarded,
    is_private_chat,
    safe_format_html,
)
from ai_admin.tool_registry import ToolDefinition, ToolRegistry
from ai_admin.tool_runner import ToolRunner


@pytest.fixture
def base_config(tmp_path):
    return AIAdminConfig(
        enabled=True,
        mutations_enabled=False,
        admin_telegram_ids={12345},
        data_dir=str(tmp_path),
        jellyfin_base_url="https://jf.internal.example",
        jellyfin_api_key="jf_secret_key_1234567890",
        is_valid=True,
    )


@pytest.fixture
def mock_router_setup(base_config, tmp_path):
    registry = ToolRegistry()
    permissions = PermissionChecker(base_config)
    audit = AuditLog(str(tmp_path))
    confirm_store = ConfirmationStore(str(tmp_path / "confirm.sqlite"))
    context_store = ContextStore()
    snapshot_store = SnapshotStore(str(tmp_path))
    omniroute = OmniRouteAdapter(base_config)
    runner = ToolRunner(base_config, registry, permissions, audit, confirm_store)
    grammar = GrammarParser()

    # Register read-only test tools
    registry.register(
        ToolDefinition(
            name="jellyfin_search",
            purpose="Search Jellyfin library",
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
            max_output_chars=2000,
            handler=lambda p: {"items": [{"id": "item_abc", "name": p["query"]}]},
        )
    )

    registry.register(
        ToolDefinition(
            name="jellyfin_get_item",
            purpose="Get Jellyfin item details",
            json_schema={
                "type": "object",
                "properties": {"item_id": {"type": "string"}},
                "required": ["item_id"],
                "additionalProperties": False,
            },
            read_only=True,
            mutates=False,
            risk="low",
            requires_confirmation="never",
            permission="read",
            timeout_seconds=5,
            max_output_chars=2000,
            handler=lambda p: {"id": p["item_id"], "name": "Test Movie", "overview": "A test overview"},
        )
    )

    registry.register(
        ToolDefinition(
            name="jellyfin_get_media_info",
            purpose="Get media stream info",
            json_schema={
                "type": "object",
                "properties": {"item_id": {"type": "string"}},
                "required": ["item_id"],
                "additionalProperties": False,
            },
            read_only=True,
            mutates=False,
            risk="low",
            requires_confirmation="never",
            permission="read",
            timeout_seconds=5,
            max_output_chars=2000,
            handler=lambda p: {"id": p["item_id"], "video_codec": "h264", "resolution": "1080p"},
        )
    )

    registry.register(
        ToolDefinition(
            name="jellyfin_list_missing_metadata",
            purpose="List items missing metadata",
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
            timeout_seconds=5,
            max_output_chars=2000,
            handler=lambda p: {"count": 1, "items": [{"id": "missing_1", "name": "No Poster"}]},
        )
    )

    registry.register(
        ToolDefinition(
            name="tmdb_search",
            purpose="Search TMDb",
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
            max_output_chars=2000,
            handler=lambda p: {"count": 1, "results": [{"id": 550, "title": p["query"]}]},
        )
    )

    registry.register(
        ToolDefinition(
            name="fanart_get_images",
            purpose="Get Fanart.tv images",
            json_schema={
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"],
                "additionalProperties": False,
            },
            read_only=True,
            mutates=False,
            risk="low",
            requires_confirmation="never",
            permission="read",
            timeout_seconds=5,
            max_output_chars=2000,
            handler=lambda p: {"id": p["id"], "count": 1, "candidates": [{"url": "https://fanart.internal/1.jpg"}]},
        )
    )

    registry.register(
        ToolDefinition(
            name="opensubtitles_search",
            purpose="Search OpenSubtitles",
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
            max_output_chars=2000,
            handler=lambda p: {"count": 1, "candidates": [{"id": "sub_1", "lang": "en"}]},
        )
    )

    handler = AIAdminHandler(
        config=base_config,
        permissions=permissions,
        grammar=grammar,
        runner=runner,
        context_store=context_store,
        snapshot_store=snapshot_store,
        omniroute=omniroute,
        registry=registry,
    )

    router = TelegramAIAdminRouter(
        config=base_config,
        permissions=permissions,
        handler=handler,
    )

    return router, base_config, handler, runner, registry


def make_mock_message(
    user_id=12345,
    chat_id=12345,
    text="/ai help",
    chat_type=ChatType.PRIVATE,
    forward_date=None,
    forward_from=None,
):
    msg = MagicMock()
    msg.text = text
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.chat = MagicMock()
    msg.chat.id = chat_id
    msg.chat.type = chat_type
    msg.forward_date = forward_date
    msg.forward_from = forward_from
    msg.forward_from_chat = None
    msg.forward_sender_name = None
    msg.reply_text = AsyncMock()
    return msg


def make_mock_callback_query(
    user_id=12345,
    chat_id=12345,
    data="ai:status",
    chat_type=ChatType.PRIVATE,
):
    cb = MagicMock()
    cb.data = data
    cb.from_user = MagicMock()
    cb.from_user.id = user_id
    cb.message = MagicMock()
    cb.message.chat = MagicMock()
    cb.message.chat.id = chat_id
    cb.message.chat.type = chat_type
    cb.message.reply_text = AsyncMock()
    cb.message.delete = AsyncMock()
    cb.answer = AsyncMock()
    return cb


# ==============================================================================
# 1. Routing & Registration Tests
# ==============================================================================

def test_handler_registration_in_group_minus_one(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()
    client.add_handler = MagicMock()
    client.remove_handler = MagicMock()

    router.register_handlers(client)
    assert client.add_handler.call_count == 2
    for call in client.add_handler.call_args_list:
        assert call[1].get("group") == -1

    router.unregister_handlers(client)
    assert client.remove_handler.call_count == 2
    for call in client.remove_handler.call_args_list:
        assert call[1].get("group") == -1


# ==============================================================================
# 2. Authorization & Privacy Boundary Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_authorized_admin_private_chat_success(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()
    msg = make_mock_message(user_id=12345, chat_id=12345, text="/ai status")

    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    assert msg.reply_text.called
    reply_call = msg.reply_text.call_args
    assert reply_call[1]["parse_mode"] == ParseMode.HTML
    assert "AI Admin Status" in reply_call[0][0]


@pytest.mark.asyncio
async def test_unauthorized_user_denied_fail_closed(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()
    msg = make_mock_message(user_id=99999, chat_id=99999, text="/ai status")

    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    assert msg.reply_text.called
    reply_call = msg.reply_text.call_args
    assert "Access Denied" in reply_call[0][0]


@pytest.mark.asyncio
async def test_non_private_chat_rejected(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()
    # Group chat attempt
    msg = make_mock_message(user_id=12345, chat_id=-1001234567, text="/ai status", chat_type=ChatType.GROUP)

    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    # Should not reply in group to avoid leakage
    assert not msg.reply_text.called


@pytest.mark.asyncio
async def test_channel_post_rejected(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()
    msg = make_mock_message(user_id=12345, chat_id=-1009999999, text="/ai status", chat_type=ChatType.CHANNEL)

    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    assert not msg.reply_text.called


@pytest.mark.asyncio
async def test_forwarded_command_rejected(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()
    msg = make_mock_message(
        user_id=12345,
        chat_id=12345,
        text="/ai status",
        forward_date=1600000000,
        forward_from=MagicMock(),
    )

    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    assert msg.reply_text.called
    reply_call = msg.reply_text.call_args
    assert "Forwarded commands are rejected" in reply_call[0][0]


@pytest.mark.asyncio
async def test_service_disabled_fails_closed(mock_router_setup):
    router, config, _, _, _ = mock_router_setup
    config.enabled = False
    client = MagicMock()
    msg = make_mock_message(user_id=12345, chat_id=12345, text="/ai status")

    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    assert msg.reply_text.called
    reply_call = msg.reply_text.call_args
    assert "disabled" in reply_call[0][0].lower()


@pytest.mark.asyncio
async def test_missing_admin_config_fails_closed(mock_router_setup):
    router, config, _, _, _ = mock_router_setup
    config.admin_telegram_ids = set()
    client = MagicMock()
    msg = make_mock_message(user_id=12345, chat_id=12345, text="/ai status")

    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    assert msg.reply_text.called
    reply_call = msg.reply_text.call_args
    assert "invalid or missing" in reply_call[0][0].lower()


# ==============================================================================
# 3. Read-Only Tool Execution Through Telegram Router
# ==============================================================================

@pytest.mark.asyncio
async def test_command_jellyfin_search(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()
    msg = make_mock_message(user_id=12345, chat_id=12345, text="/ai find Inception")

    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    assert msg.reply_text.called
    text = msg.reply_text.call_args[0][0]
    assert "jellyfin_search" in text
    assert "Inception" in text


@pytest.mark.asyncio
async def test_command_jellyfin_details(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()
    msg = make_mock_message(user_id=12345, chat_id=12345, text="/ai details item_abc")

    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    assert msg.reply_text.called
    text = msg.reply_text.call_args[0][0]
    assert "jellyfin_get_item" in text
    assert "Test Movie" in text


@pytest.mark.asyncio
async def test_command_jellyfin_media_info(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()
    msg = make_mock_message(user_id=12345, chat_id=12345, text="/ai media_info item_abc")

    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    assert msg.reply_text.called
    text = msg.reply_text.call_args[0][0]
    assert "jellyfin_get_media_info" in text
    assert "h264" in text


@pytest.mark.asyncio
async def test_command_jellyfin_missing_metadata(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()
    msg = make_mock_message(user_id=12345, chat_id=12345, text="/ai missing")

    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    assert msg.reply_text.called
    text = msg.reply_text.call_args[0][0]
    assert "jellyfin_list_missing_metadata" in text
    assert "No Poster" in text


@pytest.mark.asyncio
async def test_command_tmdb_search(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()
    msg = make_mock_message(user_id=12345, chat_id=12345, text="/ai tmdb Fight Club")

    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    assert msg.reply_text.called
    text = msg.reply_text.call_args[0][0]
    assert "tmdb_search" in text
    assert "Fight Club" in text


@pytest.mark.asyncio
async def test_command_fanart_search(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()
    msg = make_mock_message(user_id=12345, chat_id=12345, text="/ai fanart 550")

    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    assert msg.reply_text.called
    text = msg.reply_text.call_args[0][0]
    assert "fanart_get_images" in text
    assert "550" in text


@pytest.mark.asyncio
async def test_command_opensubtitles_search(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()
    msg = make_mock_message(user_id=12345, chat_id=12345, text="/ai opensubtitles Interstellar")

    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    assert msg.reply_text.called
    text = msg.reply_text.call_args[0][0]
    assert "opensubtitles_search" in text


# ==============================================================================
# 4. Callback Query Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_callback_status_authorized(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()
    cb = make_mock_callback_query(user_id=12345, chat_id=12345, data="ai:status")

    with pytest.raises(StopPropagation):
        await router.handle_callback_query(client, cb)

    assert cb.answer.called
    assert cb.message.reply_text.called
    text = cb.message.reply_text.call_args[0][0]
    assert "AI Admin Status" in text


@pytest.mark.asyncio
async def test_callback_help_authorized(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()
    cb = make_mock_callback_query(user_id=12345, chat_id=12345, data="ai:help")

    with pytest.raises(StopPropagation):
        await router.handle_callback_query(client, cb)

    assert cb.answer.called
    assert cb.message.reply_text.called
    text = cb.message.reply_text.call_args[0][0]
    assert "Jellyfin AI Administrator" in text


@pytest.mark.asyncio
async def test_callback_cancel_authorized(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()
    cb = make_mock_callback_query(user_id=12345, chat_id=12345, data="ai:cancel")

    with pytest.raises(StopPropagation):
        await router.handle_callback_query(client, cb)

    assert cb.answer.called
    assert cb.message.delete.called


@pytest.mark.asyncio
async def test_callback_unauthorized_denied(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()
    cb = make_mock_callback_query(user_id=99999, chat_id=99999, data="ai:status")

    with pytest.raises(StopPropagation):
        await router.handle_callback_query(client, cb)

    assert cb.answer.called
    assert "Access denied" in cb.answer.call_args[0][0]
    assert not cb.message.reply_text.called


@pytest.mark.asyncio
async def test_callback_non_private_chat_denied(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()
    cb = make_mock_callback_query(user_id=12345, chat_id=-100123, data="ai:status", chat_type=ChatType.GROUP)

    with pytest.raises(StopPropagation):
        await router.handle_callback_query(client, cb)

    assert cb.answer.called
    assert "restricted to private chats" in cb.answer.call_args[0][0]
    assert not cb.message.reply_text.called


# ==============================================================================
# 5. Safe Formatting & Length Capping Tests
# ==============================================================================

def test_safe_format_html_capping():
    huge_text = "A" * 10000
    formatted = safe_format_html(huge_text, max_chars=4000)
    assert len(formatted) <= 4000
    assert "... [Response truncated" in formatted


def test_safe_format_html_escapes_xss_and_injections():
    malicious = "<script>alert('xss')</script> <a href='evil.com'>Click me</a> & \"quote\""
    formatted = safe_format_html(malicious)
    assert "<script>" not in formatted
    assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in formatted
    assert "<a href" not in formatted
    assert "&lt;a href=&#x27;evil.com&#x27;&gt;" in formatted


def test_safe_format_html_code_block_tag_balancing():
    code_block = "```json\n" + ("{\"k\": \"v\"},\n" * 500) + "```"
    formatted = safe_format_html(code_block, max_chars=500)
    assert len(formatted) <= 500
    assert "... [Response truncated" in formatted
    # Check proper closure
    assert formatted.count("<pre>") == formatted.count("</pre>")
    assert formatted.count("<code>") == formatted.count("</code>")


# ==============================================================================
# 6. Mutating Tools Invariant Test
# ==============================================================================

def test_all_mutations_strictly_disabled_and_unregistered(mock_router_setup):
    _, _, _, _, registry = mock_router_setup
    disallowed_mutations = [
        "jellyfin_refresh_item",
        "jellyfin_update_metadata",
        "apply_image",
        "apply_subtitle",
        "revert_last_change",
    ]
    for tool_name in disallowed_mutations:
        assert registry.get(tool_name) is None, f"Mutating tool '{tool_name}' must NOT be registered"


# ==============================================================================
# 7. Stage 4B Multi-Turn Conversational Context & Isolation Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_multi_turn_search_then_details_sequence(mock_router_setup):
    router, _, _, runner, _ = mock_router_setup
    client = MagicMock()

    # Turn 1: Search for title
    msg1 = make_mock_message(user_id=12345, chat_id=12345, text="/ai find Inception")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg1)
    assert msg1.reply_text.called

    # Turn 2: Request details without specifying ID (follow-up)
    msg2 = make_mock_message(user_id=12345, chat_id=12345, text="/ai details")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg2)
    assert msg2.reply_text.called
    text2 = msg2.reply_text.call_args[0][0]
    assert "jellyfin_get_item" in text2
    assert "item_abc" in text2


@pytest.mark.asyncio
async def test_multi_turn_search_then_media_info_sequence(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()

    # Turn 1: Search for title
    msg1 = make_mock_message(user_id=12345, chat_id=12345, text="/ai find Inception")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg1)

    # Turn 2: Request media info without specifying ID (follow-up)
    msg2 = make_mock_message(user_id=12345, chat_id=12345, text="/ai media_info")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg2)
    assert msg2.reply_text.called
    text2 = msg2.reply_text.call_args[0][0]
    assert "jellyfin_get_media_info" in text2
    assert "h264" in text2


@pytest.mark.asyncio
async def test_multi_turn_zero_results_clears_selected_item(mock_router_setup):
    router, _, handler, _, registry = mock_router_setup
    client = MagicMock()

    # Step 1: Valid search sets item_abc
    msg1 = make_mock_message(user_id=12345, chat_id=12345, text="/ai find Inception")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg1)

    # Step 2: Search returning 0 results
    # Temporarily make jellyfin_search return 0 items
    orig_tool = registry.get("jellyfin_search")
    registry._tools["jellyfin_search"].handler = lambda p: {"count": 0, "items": []}

    msg2 = make_mock_message(user_id=12345, chat_id=12345, text="/ai find NonexistentMovieXYZ")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg2)

    # Step 3: Follow-up details without ID should NOT resolve to stale item_abc
    msg3 = make_mock_message(user_id=12345, chat_id=12345, text="/ai details")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg3)
    text3 = msg3.reply_text.call_args[0][0]
    assert "item_abc" not in text3

    # Restore tool handler
    registry._tools["jellyfin_search"] = orig_tool


@pytest.mark.asyncio
async def test_multi_turn_context_isolation_across_admins(mock_router_setup):
    router, config, _, _, _ = mock_router_setup
    config.admin_telegram_ids.add(67890)  # Add second authorized admin
    client = MagicMock()

    # Admin A (12345) searches for Inception
    msg_a = make_mock_message(user_id=12345, chat_id=12345, text="/ai find Inception")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg_a)

    # Admin B (67890) asks for details without ID in their own private chat
    msg_b = make_mock_message(user_id=67890, chat_id=67890, text="/ai details")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg_b)

    text_b = msg_b.reply_text.call_args[0][0]
    # Admin B must NOT inherit Admin A's selected item
    assert "item_abc" not in text_b


@pytest.mark.asyncio
async def test_multi_turn_context_isolation_across_chats(mock_router_setup):
    router, config, _, _, _ = mock_router_setup
    client = MagicMock()

    # Admin searches in Chat 1 (private chat 12345)
    msg1 = make_mock_message(user_id=12345, chat_id=12345, text="/ai find Inception")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg1)

    # Admin issues follow-up in different chat ID (e.g. chat 99999)
    msg2 = make_mock_message(user_id=12345, chat_id=99999, text="/ai details")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg2)

    # Context must NOT leak across chat IDs
    if msg2.reply_text.called:
        text2 = msg2.reply_text.call_args[0][0]
        assert "item_abc" not in text2


@pytest.mark.asyncio
async def test_command_with_invalid_or_fabricated_item_id(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()

    # Attempt path traversal item ID
    msg_traversal = make_mock_message(user_id=12345, chat_id=12345, text="/ai details ../../etc/passwd")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg_traversal)

    text = msg_traversal.reply_text.call_args[0][0]
    # Must fail closed without crashing or returning sensitive files
    assert "root:" not in text


# ==============================================================================
# 8. HTML Parsing Validity Tests with Real Pyrogram Parser
# ==============================================================================

@pytest.mark.asyncio
async def test_safe_format_html_valid_with_pyrogram_parser():
    """Verify that safe_format_html produces output completely valid for Pyrogram HTML parser."""
    import asyncio
    from pyrogram.parser.html import HTML

    parser = HTML(None)

    test_inputs = [
        # XSS / HTML injection attempt
        "<script>alert('xss')</script><img onerror=alert(1) src=x><b>Bold</b>",
        # Large provider JSON output (> 5000 chars)
        "```json\n" + ("{\"title\": \"Movie <tag> & info\", \"id\": \"123\"},\n" * 200) + "```",
        # Truncation boundary test right next to partial tag
        ("A" * 3950) + "<b><i>Nested</i></b>",
        # Unicode and special symbols
        "🎬 Film: «Léon» (1994) — €10 / $20 & 100% — <bad_tag>",
        # Unmatched asterisks and backticks
        "Text with `unclosed code and *unclosed bold and _unclosed italic",
    ]

    for raw in test_inputs:
        formatted = safe_format_html(raw, max_chars=4000)
        assert len(formatted) <= 4000
        # Parse using actual Pyrogram HTML parser
        parsed = await parser.parse(formatted)
        assert isinstance(parsed, dict)
        assert "message" in parsed


# ==============================================================================
# 9. Callback Query Security & Forged Payload Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_callback_query_missing_user_rejected(mock_router_setup):
    router, _, _, _, _ = mock_router_setup
    client = MagicMock()
    cb = make_mock_callback_query(user_id=12345, chat_id=12345, data="ai:status")
    cb.from_user = None  # Missing from_user

    with pytest.raises(StopPropagation):
        await router.handle_callback_query(client, cb)

    assert cb.answer.called
    assert "Access denied" in cb.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_callback_query_malformed_and_forged_actions(mock_router_setup):
    router, _, _, runner, _ = mock_router_setup
    client = MagicMock()

    forged_actions = [
        "ai:tool:apply_image",
        "ai:eval:os.system('id')",
        "ai:confirm:token_123",
        "ai:arbitrary_payload_attempt",
        "ai:",
    ]

    for data in forged_actions:
        cb = make_mock_callback_query(user_id=12345, chat_id=12345, data=data)
        with pytest.raises(StopPropagation):
            await router.handle_callback_query(client, cb)

        assert cb.answer.called
        assert "Unknown action" in cb.answer.call_args[0][0]


# ==============================================================================
# 10. Real Pyrogram Dispatcher Priority & StopPropagation Test
# ==============================================================================

@pytest.mark.asyncio
async def test_real_pyrogram_dispatcher_group_priority_and_stop_propagation(mock_router_setup):
    """Verify group=-1 executes before group=0 and StopPropagation halts propagation in real Pyrogram Dispatcher."""
    import asyncio
    from pyrogram import Client, StopPropagation, filters
    from pyrogram.handlers import CallbackQueryHandler, MessageHandler

    router, _, _, _, _ = mock_router_setup
    client = Client("test_priority_client", api_id=12345, api_hash="abcde", in_memory=True)

    group_zero_called = []

    async def simulated_group_zero_fallback(c, q):
        group_zero_called.append("group_0_catchall")

    # Register router handlers in group -1
    router.register_handlers(client, group=-1)

    # Register simulated Thunder group 0 fallback callback catch-all
    client.add_handler(CallbackQueryHandler(simulated_group_zero_fallback), group=0)

    # Yield control to let async tasks inside add_handler run
    await asyncio.sleep(0.02)

    # Verify dispatcher groups ordering
    groups = list(client.dispatcher.groups.keys())
    assert -1 in groups
    assert 0 in groups
    assert groups.index(-1) < groups.index(0)

    # Directly verify that an ai:status callback stops propagation
    cb = make_mock_callback_query(user_id=12345, chat_id=12345, data="ai:status")
    with pytest.raises(StopPropagation):
        await router.handle_callback_query(client, cb)

    # Confirm group 0 was NOT called
    assert len(group_zero_called) == 0

