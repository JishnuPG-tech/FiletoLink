"""Unit tests for ai_admin/tool_runner.py (execution and policy enforcement)."""

import pytest
from ai_admin.audit_log import AuditLog
from ai_admin.config import AIAdminConfig
from ai_admin.confirmation_store import ConfirmationStore
from ai_admin.permissions import PermissionChecker
from ai_admin.tool_registry import ToolDefinition, ToolRegistry
from ai_admin.tool_runner import ToolRunner


@pytest.fixture
def test_setup(tmp_path):
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

    # Register a safe read tool
    registry.register(
        ToolDefinition(
            name="safe_read",
            purpose="Safe read test",
            json_schema={
                "type": "object",
                "properties": {"query": {"type": "string", "maxLength": 50}},
                "required": ["query"],
                "additionalProperties": False,
            },
            read_only=True,
            mutates=False,
            risk="low",
            requires_confirmation="never",
            permission="read",
            timeout_seconds=2,
            max_output_chars=200,
            handler=lambda p: {"echo": p["query"]},
        )
    )

    # Register a mutating tool
    registry.register(
        ToolDefinition(
            name="mutate_item",
            purpose="Mutate test",
            json_schema={
                "type": "object",
                "properties": {"item_id": {"type": "string"}},
                "required": ["item_id"],
                "additionalProperties": False,
            },
            read_only=False,
            mutates=True,
            risk="high",
            requires_confirmation="always",
            permission="write",
            timeout_seconds=2,
            max_output_chars=200,
            handler=lambda p: {"updated": p["item_id"]},
        )
    )

    runner = ToolRunner(config, registry, permissions, audit, confirm_store)
    return runner, audit, confirm_store, config


@pytest.mark.asyncio
async def test_successful_safe_tool_execution(test_setup):
    runner, audit, _, _ = test_setup
    ok, result, msg = await runner.execute_tool(
        tool_name="safe_read",
        params={"query": "test query"},
        user_id=1001,
        chat_id=1001,
    )
    assert ok is True
    assert result == {"echo": "test query"}
    assert msg == "success"

    # Verify audit record
    actions = audit.get_recent_actions(limit=5)
    assert len(actions) == 1
    assert actions[0]["tool"] == "safe_read"
    assert actions[0]["outcome"] == "success"


@pytest.mark.asyncio
async def test_unknown_tool_rejection(test_setup):
    runner, audit, _, _ = test_setup
    ok, result, msg = await runner.execute_tool(
        tool_name="execute_arbitrary_shell",
        params={"cmd": "ls"},
        user_id=1001,
        chat_id=1001,
    )
    assert ok is False
    assert "not recognized" in msg

    actions = audit.get_recent_actions(limit=5)
    assert len(actions) == 1
    assert actions[0]["outcome"] == "denied"
    assert actions[0]["error_category"] == "unknown_tool"


@pytest.mark.asyncio
async def test_schema_violation_additional_properties(test_setup):
    runner, audit, _, _ = test_setup
    # 'extra_arg' is not allowed in schema
    ok, result, msg = await runner.execute_tool(
        tool_name="safe_read",
        params={"query": "valid", "extra_arg": "malicious"},
        user_id=1001,
        chat_id=1001,
    )
    assert ok is False
    assert "Unexpected properties" in msg


@pytest.mark.asyncio
async def test_mutations_disabled_rejection(test_setup):
    runner, audit, _, config = test_setup
    config.mutations_enabled = False

    ok, result, msg = await runner.execute_tool(
        tool_name="mutate_item",
        params={"item_id": "123"},
        user_id=1001,
        chat_id=1001,
    )
    assert ok is False
    assert "read-only mode active" in msg


@pytest.mark.asyncio
async def test_confirmation_required_flow(test_setup):
    runner, audit, confirm_store, config = test_setup
    config.mutations_enabled = True

    # 1. First execution without approval_id prompts for confirmation
    ok, result, msg = await runner.execute_tool(
        tool_name="mutate_item",
        params={"item_id": "123"},
        user_id=1001,
        chat_id=1001,
    )
    assert ok is False
    assert result.get("confirmation_required") is True
    token_id = result.get("confirmation_id")
    assert token_id is not None

    # 2. Second execution with valid approval_id succeeds
    ok2, result2, msg2 = await runner.execute_tool(
        tool_name="mutate_item",
        params={"item_id": "123"},
        user_id=1001,
        chat_id=1001,
        approval_id=token_id,
    )
    assert ok2 is True
    assert result2 == {"updated": "123"}
