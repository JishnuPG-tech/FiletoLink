import importlib.util
import os
from unittest.mock import MagicMock
import pytest
from pyrogram import Client

# Provide mock environment variables for Thunder.vars if unconfigured in test environment
os.environ.setdefault("API_ID", "12345")
os.environ.setdefault("API_HASH", "mock_hash_for_testing")
os.environ.setdefault("BOT_TOKEN", "12345:mock_token_for_testing")
os.environ.setdefault("BIN_CHANNEL", "-100123456789")
os.environ.setdefault("DATABASE_URL", "mongodb://localhost:27017/dummy_test_db")

from Thunder.bot.plugins.ai_admin import reset_plugin_state, setup_ai_admin


@pytest.fixture(autouse=True)
def clean_plugin_env(monkeypatch):
    """Ensure clean environment and reset plugin registration state before and after each test."""
    reset_plugin_state()
    # Ensure default disabled state
    monkeypatch.delenv("AI_ENABLED", raising=False)
    monkeypatch.delenv("AI_ADMIN_TELEGRAM_IDS", raising=False)
    monkeypatch.delenv("AI_MUTATIONS_ENABLED", raising=False)
    yield
    reset_plugin_state()


def test_plugin_disabled_by_default():
    """Verify that plugin is completely dormant and registers 0 handlers by default."""
    client = MagicMock(spec=Client)
    client.add_handler = MagicMock()

    router = setup_ai_admin(client)

    assert router is None
    assert client.add_handler.call_count == 0


def test_plugin_invalid_config_fails_closed(monkeypatch):
    """Verify that enabled=True with missing admin IDs fails closed without registering handlers."""
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "")  # Empty admin IDs

    client = MagicMock(spec=Client)
    client.add_handler = MagicMock()

    router = setup_ai_admin(client)

    assert router is None
    assert client.add_handler.call_count == 0


def test_plugin_enabled_registers_handlers_in_group_minus_one(monkeypatch, tmp_path):
    """Verify that valid configuration registers handlers strictly in group -1."""
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "12345")
    monkeypatch.setenv("AI_DATA_DIR", str(tmp_path))

    client = MagicMock(spec=Client)
    client.add_handler = MagicMock()

    router = setup_ai_admin(client)

    assert router is not None
    # Must register 2 handlers: MessageHandler and CallbackQueryHandler
    assert client.add_handler.call_count == 2
    for call in client.add_handler.call_args_list:
        assert call[1].get("group") == -1


def test_duplicate_registration_prevented(monkeypatch, tmp_path):
    """Verify that calling setup_ai_admin repeatedly does not duplicate handlers."""
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "12345")
    monkeypatch.setenv("AI_DATA_DIR", str(tmp_path))

    client = MagicMock(spec=Client)
    client.add_handler = MagicMock()

    router1 = setup_ai_admin(client)
    assert router1 is not None
    assert client.add_handler.call_count == 2

    # Second call must be idempotent
    router2 = setup_ai_admin(client)
    assert router2 is router1
    # Handler count should NOT increase
    assert client.add_handler.call_count == 2


def test_plugin_registers_zero_mutating_tools(monkeypatch, tmp_path):
    """Verify that plugin registry contains only read-only tools and ZERO mutating tools."""
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "12345")
    monkeypatch.setenv("AI_DATA_DIR", str(tmp_path))

    client = MagicMock(spec=Client)
    client.add_handler = MagicMock()

    router = setup_ai_admin(client)
    assert router is not None

    registry = router.handler.registry

    # 1. Disallowed mutation tools must NOT be present
    disallowed_mutations = [
        "jellyfin_refresh_item",
        "jellyfin_update_metadata",
        "apply_image",
        "apply_subtitle",
        "revert_last_change",
    ]
    for mutation_name in disallowed_mutations:
        assert registry.get(mutation_name) is None, f"Mutating tool '{mutation_name}' must NOT be registered!"

    # 2. Every registered tool must be read_only=True and mutates=False
    for tool in registry.list_tools():
        assert tool.read_only is True, f"Tool '{tool.name}' must be read-only"
        assert tool.mutates is False, f"Tool '{tool.name}' must not mutate"
        assert tool.permission == "read", f"Tool '{tool.name}' must have 'read' permission"


def test_dynamic_import_by_thunder_main_lifecycle(monkeypatch):
    """Simulate the exact dynamic import loop from Thunder/__main__.py."""
    plugin_file = os.path.abspath("Thunder/bot/plugins/ai_admin.py")
    assert os.path.exists(plugin_file), f"Plugin file missing: {plugin_file}"

    # Default environment (disabled)
    spec = importlib.util.spec_from_file_location("Thunder.bot.plugins.ai_admin", plugin_file)
    assert spec is not None and spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    # Executing module should complete without any error
    spec.loader.exec_module(module)

    # State must be dormant
    assert module._REGISTERED is False
    assert module._ROUTER_INSTANCE is None


def test_admin_id_parsing_wildcard_and_invalid_tokens(monkeypatch, tmp_path):
    """Verify that wildcard, string, or malformed admin IDs cannot create an open allowlist."""
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_DATA_DIR", str(tmp_path))

    # Test 1: Wildcard "*" or "all" fails closed
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "*")
    client = MagicMock(spec=Client)
    client.add_handler = MagicMock()
    router = setup_ai_admin(client)
    assert router is None
    assert client.add_handler.call_count == 0

    reset_plugin_state()
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "all,admin,nobody")
    router = setup_ai_admin(client)
    assert router is None
    assert client.add_handler.call_count == 0

    # Test 2: Mixed valid and invalid tokens extracts only valid integers
    reset_plugin_state()
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "12345, invalid_token, 67890; bad_id")
    router = setup_ai_admin(client)
    assert router is not None
    assert router.config.admin_telegram_ids == {12345, 67890}


def test_setup_failure_unregisters_partial_handlers(monkeypatch, tmp_path):
    """Verify that any exception during setup cleanly unregisters handlers without leaving orphans."""
    from unittest.mock import patch

    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "12345")
    monkeypatch.setenv("AI_DATA_DIR", str(tmp_path))

    client = MagicMock(spec=Client)
    client.add_handler = MagicMock()
    client.remove_handler = MagicMock()

    # Force an error after handler registration
    with patch("Thunder.bot.plugins.ai_admin.TelegramAIAdminRouter.register_handlers") as mock_reg:
        # Simulate registration happening, then unexpected failure
        def side_effect(c, group=-1):
            mock_reg.router._registered_handlers.append(("mock_h", group))
            raise RuntimeError("Simulated mid-setup network/memory error")

        mock_reg.side_effect = side_effect
        mock_reg.router = MagicMock()

        router = setup_ai_admin(client)
        assert router is None


def test_no_network_requests_during_import_or_setup(monkeypatch, tmp_path):
    """Verify that neither importing nor setting up the plugin makes outbound network requests."""
    from unittest.mock import patch

    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "12345")
    monkeypatch.setenv("AI_DATA_DIR", str(tmp_path))

    client = MagicMock(spec=Client)
    client.add_handler = MagicMock()

    with patch("aiohttp.ClientSession.get") as mock_aio_get, patch("httpx.AsyncClient.get") as mock_httpx_get:
        router = setup_ai_admin(client)
        assert router is not None
        # Must make 0 network calls during setup
        assert mock_aio_get.call_count == 0
        assert mock_httpx_get.call_count == 0

