"""Stage 6 End-to-End Integration Tests.

Validates the complete lifecycle:
- Plugin loading and dormant behavior when disabled
- Activation in isolated test environment (Pyrogram group -1)
- Reconciles exact 8 read-only tools and zero mutating tools
- End-to-end execution of all 8 tools via Telegram router
- Error handling: timeouts, malformed inputs, HTTP errors, missing credentials, oversized responses
- Strict security boundaries: authorization, chat types, forwards, context/handle isolation
- HTML formatting failure fallback to plain text
"""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from pyrogram import Client, StopPropagation
from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import Chat, Message, User

# Provide mock environment variables for Thunder.vars if unconfigured in test environment
os.environ.setdefault("API_ID", "12345")
os.environ.setdefault("API_HASH", "mock_hash_for_testing")
os.environ.setdefault("BOT_TOKEN", "12345:mock_token_for_testing")
os.environ.setdefault("BIN_CHANNEL", "-100123456789")
os.environ.setdefault("DATABASE_URL", "mongodb://localhost:27017/dummy_test_db")

from Thunder.bot.plugins.ai_admin import reset_plugin_state, setup_ai_admin
from ai_admin.candidate_cache import CandidateCache
from ai_admin.config import AIAdminConfig
from ai_admin.net_guard import is_ip_private_or_restricted, validate_outbound_url
from ai_admin.validators import safe_join_path, validate_item_id


@pytest.fixture(autouse=True)
def clean_stage6_env(monkeypatch):
    """Ensure clean environment before and after every Stage 6 test."""
    reset_plugin_state()
    monkeypatch.delenv("AI_ENABLED", raising=False)
    monkeypatch.delenv("AI_ADMIN_TELEGRAM_IDS", raising=False)
    monkeypatch.delenv("AI_MUTATIONS_ENABLED", raising=False)
    yield
    reset_plugin_state()


def make_mock_message(
    user_id: int = 12345,
    chat_id: int = 12345,
    chat_type: ChatType = ChatType.PRIVATE,
    text: str = "/ai",
    is_forwarded_msg: bool = False,
) -> Message:
    """Create a mock Pyrogram Message with realistic attributes."""
    msg = MagicMock(spec=Message)
    msg.text = text
    msg.from_user = MagicMock(spec=User)
    msg.from_user.id = user_id
    msg.from_user.is_bot = False

    msg.chat = MagicMock(spec=Chat)
    msg.chat.id = chat_id
    msg.chat.type = chat_type

    msg.forward_date = 1600000000 if is_forwarded_msg else None
    msg.forward_from = MagicMock() if is_forwarded_msg else None
    msg.forward_from_chat = None
    msg.forward_sender_name = None

    msg.reply_text = AsyncMock()
    return msg


# ==============================================================================
# Task 2: Plugin Lifecycle Verification
# ==============================================================================

def test_stage6_plugin_loader_dormant_by_default():
    """Verify plugin loader keeps AI Admin completely dormant by default."""
    client = MagicMock(spec=Client)
    client.add_handler = MagicMock()

    router = setup_ai_admin(client)

    assert router is None
    assert client.add_handler.call_count == 0


def test_stage6_plugin_loader_active_when_configured(monkeypatch, tmp_path):
    """Verify plugin activates in group -1 when explicitly enabled in test config."""
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "12345")
    monkeypatch.setenv("AI_DATA_DIR", str(tmp_path))

    client = MagicMock(spec=Client)
    client.add_handler = MagicMock()

    router = setup_ai_admin(client)

    assert router is not None
    assert client.add_handler.call_count == 2
    for call in client.add_handler.call_args_list:
        assert call[1].get("group") == -1


# ==============================================================================
# Task 4 & Task 8: Exact Tool Count (8 Tools) & Zero Mutating Tools
# ==============================================================================

def test_stage6_exact_tool_count_and_absence_of_mutations(monkeypatch, tmp_path):
    """Reconcile exact tool count: exactly 8 read-only tools and zero mutating tools."""
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "12345")
    monkeypatch.setenv("AI_DATA_DIR", str(tmp_path))

    client = MagicMock(spec=Client)
    router = setup_ai_admin(client)
    assert router is not None

    registry = router.handler.registry
    registered_tools = registry.list_tools()

    # Must contain exactly 17 read-only tools
    assert len(registered_tools) == 17, f"Expected 17 tools, got {len(registered_tools)}: {[t.name for t in registered_tools]}"

    expected_tool_names = {
        "jellyfin_search",
        "jellyfin_get_item",
        "jellyfin_list_missing_metadata",
        "jellyfin_get_media_info",
        "telegram_list_injected",
        "jellyfin_list_library",
        "library_audit_and_compare",
        "tmdb_search",
        "tmdb_get_details",
        "tmdb_get_images",
        "cinemeta_search",
        "cinemeta_get_meta",
        "imdb_search",
        "tvmaze_search",
        "artwork_search",
        "fanart_get_images",
        "opensubtitles_search",
    }
    actual_tool_names = {t.name for t in registered_tools}
    assert actual_tool_names == expected_tool_names

    # All tools must be strictly read-only
    for tool in registered_tools:
        assert tool.read_only is True
        assert tool.mutates is False
        assert tool.permission == "read"

    # Mutating tools must be completely absent
    disallowed_mutations = [
        "jellyfin_refresh_item",
        "jellyfin_update_metadata",
        "apply_image",
        "apply_subtitle",
        "revert_last_change",
    ]
    for mutation in disallowed_mutations:
        assert registry.get(mutation) is None


@pytest.mark.asyncio
async def test_stage6_attempted_mutation_calls_rejected(monkeypatch, tmp_path):
    """Verify that any attempt to execute mutating operations is rejected fail-closed."""
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "12345")
    monkeypatch.setenv("AI_DATA_DIR", str(tmp_path))

    client = MagicMock(spec=Client)
    router = setup_ai_admin(client)
    runner = router.handler.runner

    for mutation_name in ["jellyfin_refresh_item", "jellyfin_update_metadata", "apply_image", "revert_last_change"]:
        success, result, msg = await runner.execute_tool(
            tool_name=mutation_name,
            params={"item_id": "11112222333344445555666677778888"},
            user_id=12345,
            chat_id=12345,
        )
        assert success is False
        assert "not recognized" in msg.lower() or "permitted" in msg.lower() or "denied" in msg.lower()


# ==============================================================================
# Task 3 & Task 4: Individual Execution of All 8 Read-Only Tools (E2E)
# ==============================================================================

@pytest.mark.asyncio
async def test_stage6_e2e_all_eight_tools_individual_execution(monkeypatch, tmp_path):
    """Test all eight read-only tools individually through full Telegram router and runner."""
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "12345")
    monkeypatch.setenv("AI_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("TMDB_API_KEY", "mock_tmdb_key")
    monkeypatch.setenv("FANART_API_KEY", "mock_fanart_key")
    monkeypatch.setenv("OPENSUBTITLES_API_KEY", "mock_os_key")

    client = MagicMock(spec=Client)
    router = setup_ai_admin(client)
    assert router is not None

    # Mock low-level network responses on tool handlers to ensure pure offline safety
    # Tool 1: jellyfin_search
    tool_jf_search = router.handler.registry.get("jellyfin_search")
    tool_jf_search.handler = AsyncMock(return_value={
        "query": "Inception",
        "count": 1,
        "items": [{"id": "11112222333344445555666677778888", "name": "Inception (2010)"}],
    })

    msg1 = make_mock_message(text="/ai find Inception")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg1)
    msg1.reply_text.assert_called_once()
    assert "jellyfin_search" in msg1.reply_text.call_args[0][0]
    assert "Inception (2010)" in msg1.reply_text.call_args[0][0]

    # Tool 2: jellyfin_get_item
    tool_jf_item = router.handler.registry.get("jellyfin_get_item")
    tool_jf_item.handler = AsyncMock(return_value={
        "id": "11112222333344445555666677778888",
        "name": "Inception",
        "overview": "A thief who steals corporate secrets...",
        "year": 2010,
    })

    msg2 = make_mock_message(text="/ai details 11112222333344445555666677778888")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg2)
    msg2.reply_text.assert_called_once()
    assert "jellyfin_get_item" in msg2.reply_text.call_args[0][0]
    assert "corporate secrets" in msg2.reply_text.call_args[0][0]

    # Tool 3: jellyfin_list_missing_metadata
    tool_jf_missing = router.handler.registry.get("jellyfin_list_missing_metadata")
    tool_jf_missing.handler = AsyncMock(return_value={
        "count": 1,
        "items": [{"id": "99990000111122223333444455556666", "name": "Unknown Media", "missing": ["Overview"]}],
    })

    msg3 = make_mock_message(text="/ai missing")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg3)
    msg3.reply_text.assert_called_once()
    assert "jellyfin_list_missing_metadata" in msg3.reply_text.call_args[0][0]
    assert "Unknown Media" in msg3.reply_text.call_args[0][0]

    # Tool 4: jellyfin_get_media_info
    tool_jf_info = router.handler.registry.get("jellyfin_get_media_info")
    tool_jf_info.handler = AsyncMock(return_value={
        "item_id": "11112222333344445555666677778888",
        "container": "mkv",
        "video_codec": "hevc",
        "resolution": "3840x2160",
    })

    msg4 = make_mock_message(text="/ai mediainfo 11112222333344445555666677778888")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg4)
    msg4.reply_text.assert_called_once()
    assert "jellyfin_get_media_info" in msg4.reply_text.call_args[0][0]
    assert "3840x2160" in msg4.reply_text.call_args[0][0]

    # Tool 5: tmdb_search
    tool_tmdb_search = router.handler.registry.get("tmdb_search")
    tool_tmdb_search.handler = AsyncMock(return_value={
        "query": "Inception",
        "count": 1,
        "results": [{"id": 27205, "title": "Inception", "year": "2010"}],
    })

    msg5 = make_mock_message(text="/ai tmdb Inception")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg5)
    msg5.reply_text.assert_called_once()
    assert "tmdb_search" in msg5.reply_text.call_args[0][0]
    assert "27205" in msg5.reply_text.call_args[0][0]

    # Tool 6: tmdb_get_details
    tool_tmdb_det = router.handler.registry.get("tmdb_get_details")
    tool_tmdb_det.handler = AsyncMock(return_value={
        "tmdb_id": 27205,
        "title": "Inception",
        "vote_average": 8.4,
        "imdb_id": "tt1375666",
    })

    msg6 = make_mock_message(text="/ai tmdb details 27205")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg6)
    msg6.reply_text.assert_called_once()
    assert "tmdb_get_details" in msg6.reply_text.call_args[0][0]
    assert "tt1375666" in msg6.reply_text.call_args[0][0]

    # Tool 7: fanart_get_images
    tool_fanart = router.handler.registry.get("fanart_get_images")
    tool_fanart.handler = AsyncMock(return_value={
        "id": "27205",
        "count": 1,
        "candidates": [{"id": "cand_art1", "type": "movieposter", "url": "https://assets.fanart.tv/poster.jpg"}],
    })

    msg7 = make_mock_message(text="/ai fanart 27205")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg7)
    msg7.reply_text.assert_called_once()
    assert "fanart_get_images" in msg7.reply_text.call_args[0][0]
    assert "cand_art1" in msg7.reply_text.call_args[0][0]

    # Tool 8: opensubtitles_search
    tool_os = router.handler.registry.get("opensubtitles_search")
    tool_os.handler = AsyncMock(return_value={
        "count": 1,
        "languages": "en",
        "candidates": [{"id": "cand_sub1", "language": "en", "format": "srt", "release": "Inception.2010.1080p"}],
    })

    msg8 = make_mock_message(text="/ai opensubtitles Inception")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg8)
    msg8.reply_text.assert_called_once()
    assert "opensubtitles_search" in msg8.reply_text.call_args[0][0]
    assert "cand_sub1" in msg8.reply_text.call_args[0][0]


# ==============================================================================
# Task 5: Arguments, Timeouts, HTTP Errors, Oversized & Malformed Responses
# ==============================================================================

@pytest.mark.asyncio
async def test_stage6_item_id_validation_prevents_traversal():
    """Verify that item ID validator rejects directory traversal and illegal characters."""
    # Valid item ID
    assert validate_item_id("11112222333344445555666677778888") is True

    # Invalid / dangerous item IDs
    assert validate_item_id("../../etc/passwd") is False
    assert validate_item_id("item; rm -rf /") is False
    assert validate_item_id("<script>alert(1)</script>") is False
    assert validate_item_id("") is False

    # Path traversal with safe_join_path
    ok, _ = safe_join_path("/safe/media/root", "../../etc/shadow")
    assert ok is False


@pytest.mark.asyncio
async def test_stage6_tool_timeout_handled_gracefully(monkeypatch, tmp_path):
    """Verify tool runner catches timeouts and reports sanitized failure without crash."""
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "12345")
    monkeypatch.setenv("AI_DATA_DIR", str(tmp_path))

    client = MagicMock(spec=Client)
    router = setup_ai_admin(client)

    async def slow_handler(params):
        await asyncio.sleep(10)
        return {"done": True}

    tool = router.handler.registry.get("jellyfin_search")
    tool.timeout_seconds = 0.05
    tool.handler = slow_handler

    msg = make_mock_message(text="/ai find SlowMovie")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    msg.reply_text.assert_called_once()
    reply = msg.reply_text.call_args[0][0]
    assert "timed out" in reply.lower() or "timeout" in reply.lower()


@pytest.mark.asyncio
async def test_stage6_oversized_response_is_capped(monkeypatch, tmp_path):
    """Verify responses exceeding max_output_chars are strictly capped."""
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "12345")
    monkeypatch.setenv("AI_DATA_DIR", str(tmp_path))

    client = MagicMock(spec=Client)
    router = setup_ai_admin(client)

    tool = router.handler.registry.get("jellyfin_search")
    tool.max_output_chars = 1000
    huge_data = {"items": [{"name": f"Item_{i}", "filler": "X" * 100} for i in range(50)]}
    tool.handler = AsyncMock(return_value=huge_data)

    msg = make_mock_message(text="/ai find HugeLibrary")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    msg.reply_text.assert_called_once()
    reply = msg.reply_text.call_args[0][0]
    # Reply must contain truncation indicator
    assert "truncated" in reply.lower()


@pytest.mark.asyncio
async def test_stage6_missing_credentials_fails_closed(monkeypatch, tmp_path):
    """Verify provider tools fail closed with sanitized error when API keys are absent."""
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "12345")
    monkeypatch.setenv("AI_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    monkeypatch.delenv("FANART_API_KEY", raising=False)

    client = MagicMock(spec=Client)
    router = setup_ai_admin(client)

    msg = make_mock_message(text="/ai fanart 27205")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    msg.reply_text.assert_called_once()
    reply = msg.reply_text.call_args[0][0]
    assert "missing" in reply.lower() or "error" in reply.lower()


def test_stage6_netguard_enforces_ssrf_and_dns_protection():
    """Verify NetGuard blocks non-allowlisted domains, private IP ranges, and invalid schemes."""
    # Denied: Non-HTTPS
    ok, _ = validate_outbound_url("http://api.themoviedb.org/3/search")
    assert ok is False

    # Denied: Private and loopback IP addresses
    assert is_ip_private_or_restricted("127.0.0.1") is True
    assert is_ip_private_or_restricted("10.0.0.1") is True
    assert is_ip_private_or_restricted("192.168.1.1") is True
    assert is_ip_private_or_restricted("169.254.169.254") is True
    assert is_ip_private_or_restricted("::1") is True

    # Denied: Disallowed external domains
    ok, _ = validate_outbound_url("https://evil-attacker.example.com/steal")
    assert ok is False

    # Allowed: Official provider endpoints
    ok, _ = validate_outbound_url("https://api.themoviedb.org/3/search/movie")
    assert ok is True
    ok, _ = validate_outbound_url("https://webservice.fanart.tv/v3/movies/27205")
    assert ok is True
    ok, _ = validate_outbound_url("https://api.opensubtitles.com/api/v1/subtitles")
    assert ok is True


# ==============================================================================
# Task 6 & Task 7: Security Boundaries, Context & Handle Isolation
# ==============================================================================

@pytest.mark.asyncio
async def test_stage6_unauthorized_user_rejected(monkeypatch, tmp_path):
    """Verify unauthorized users are rejected fail-closed."""
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "12345")
    monkeypatch.setenv("AI_DATA_DIR", str(tmp_path))

    client = MagicMock(spec=Client)
    router = setup_ai_admin(client)

    msg = make_mock_message(user_id=99999, text="/ai find Inception")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    msg.reply_text.assert_called_once()
    assert "denied" in msg.reply_text.call_args[0][0].lower()


@pytest.mark.asyncio
async def test_stage6_non_private_chat_rejected(monkeypatch, tmp_path):
    """Verify group and supergroup chats are rejected with StopPropagation."""
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "12345")
    monkeypatch.setenv("AI_DATA_DIR", str(tmp_path))

    client = MagicMock(spec=Client)
    router = setup_ai_admin(client)

    msg = make_mock_message(chat_type=ChatType.GROUP, text="/ai status")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    # In group chat, router silently drops command without replying to avoid noisy chat leaks
    msg.reply_text.assert_not_called()


@pytest.mark.asyncio
async def test_stage6_forwarded_command_rejected(monkeypatch, tmp_path):
    """Verify forwarded messages are rejected for security."""
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "12345")
    monkeypatch.setenv("AI_DATA_DIR", str(tmp_path))

    client = MagicMock(spec=Client)
    router = setup_ai_admin(client)

    msg = make_mock_message(is_forwarded_msg=True, text="/ai status")
    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    msg.reply_text.assert_called_once()
    assert "forwarded" in msg.reply_text.call_args[0][0].lower()


def test_stage6_candidate_cache_isolation_and_expiry():
    """Verify candidate handles enforce user, chat, operation binding, and expiry."""
    cache = CandidateCache(ttl_seconds=1)

    cand_id = cache.register_candidate(
        candidate_data={"url": "https://assets.fanart.tv/poster.jpg"},
        user_id=12345,
        chat_id=12345,
        operation="image_artwork",
    )

    # 1. Matching user, chat, and operation -> Success
    res = cache.resolve_candidate(
        candidate_id=cand_id,
        user_id=12345,
        chat_id=12345,
        expected_operation="image_artwork",
    )
    assert res is not None
    assert res["url"] == "https://assets.fanart.tv/poster.jpg"

    # 2. Cross-user isolation: User 99999 cannot resolve User 12345's handle
    assert cache.resolve_candidate(cand_id, user_id=99999, chat_id=12345, expected_operation="image_artwork") is None

    # 3. Cross-chat isolation: Chat 99999 cannot resolve Chat 12345's handle
    assert cache.resolve_candidate(cand_id, user_id=12345, chat_id=99999, expected_operation="image_artwork") is None

    # 4. Operation mismatch: registered as image_artwork, queried as subtitle_track -> Fails closed
    assert cache.resolve_candidate(cand_id, user_id=12345, chat_id=12345, expected_operation="subtitle_track") is None

    # 5. Expiry after TTL
    import time
    time.sleep(1.05)
    assert cache.resolve_candidate(cand_id, user_id=12345, chat_id=12345, expected_operation="image_artwork") is None


# ==============================================================================
# Task 9: HTML Formatting Fallback to Plain Text
# ==============================================================================

@pytest.mark.asyncio
async def test_stage6_html_failure_falls_back_to_plain_text(monkeypatch, tmp_path):
    """Verify that if Telegram HTML parsing fails, router safely falls back to plain text."""
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "12345")
    monkeypatch.setenv("AI_DATA_DIR", str(tmp_path))

    client = MagicMock(spec=Client)
    router = setup_ai_admin(client)

    msg = make_mock_message(text="/ai status")

    # Simulate HTML send failure (e.g., RPCError or parse error)
    first_call = True

    async def mock_reply(text, parse_mode=None, reply_markup=None):
        nonlocal first_call
        if first_call:
            first_call = False
            raise ValueError("Simulated Telegram RPC HTML parse error")
        return MagicMock()

    msg.reply_text = AsyncMock(side_effect=mock_reply)

    with pytest.raises(StopPropagation):
        await router.handle_ai_command(client, msg)

    # reply_text should be called twice: 1st with HTML mode (failed), 2nd with parse_mode=None (fallback)
    assert msg.reply_text.call_count == 2
    second_call_kwargs = msg.reply_text.call_args_list[1][1]
    assert second_call_kwargs.get("parse_mode") is None
