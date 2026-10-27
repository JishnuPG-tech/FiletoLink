"""Deterministic tool runner with policy, schema, permission, timeout, and audit enforcement."""

import asyncio
import inspect
import json
import logging
import time
import uuid
from typing import Any, Dict, Optional, Tuple

from ai_admin.audit_log import AuditLog
from ai_admin.config import AIAdminConfig
from ai_admin.confirmation_store import ConfirmationStore, compute_action_hash
from ai_admin.permissions import PermissionChecker
from ai_admin.redaction import redact_data
from ai_admin.tool_registry import ToolDefinition, ToolRegistry

logger = logging.getLogger("AIAdmin.ToolRunner")


def _validate_schema(schema: Dict[str, Any], params: Dict[str, Any]) -> Tuple[bool, str]:
    """Lightweight strict JSON schema validator for tool parameters."""
    if not isinstance(params, dict):
        return False, "Parameters must be a JSON dictionary."

    # additionalProperties check
    if schema.get("additionalProperties") is False:
        allowed = set(schema.get("properties", {}).keys())
        extra = set(params.keys()) - allowed
        if extra:
            return False, f"Unexpected properties not permitted in schema: {list(extra)}"

    # Required fields check
    for req in schema.get("required", []):
        if req not in params:
            return False, f"Missing required parameter: '{req}'"

    # Type check for properties
    props = schema.get("properties", {})
    for key, val in params.items():
        if key in props:
            expected_type = props[key].get("type")
            if expected_type == "string" and not isinstance(val, str):
                return False, f"Parameter '{key}' must be a string."
            if expected_type == "integer" and (not isinstance(val, int) or isinstance(val, bool)):
                return False, f"Parameter '{key}' must be an integer."
            if expected_type == "boolean" and not isinstance(val, bool):
                return False, f"Parameter '{key}' must be a boolean."
            if expected_type == "array" and not isinstance(val, list):
                return False, f"Parameter '{key}' must be a list."
            if expected_type == "object" and not isinstance(val, dict):
                return False, f"Parameter '{key}' must be a dictionary."

            # MaxLength check for strings
            max_len = props[key].get("maxLength")
            if max_len and isinstance(val, str) and len(val) > max_len:
                return False, f"Parameter '{key}' exceeds maximum length ({len(val)} > {max_len})."

    return True, "valid"


class ToolRunner:
    def __init__(
        self,
        config: AIAdminConfig,
        registry: ToolRegistry,
        permissions: PermissionChecker,
        audit_log: AuditLog,
        confirmation_store: ConfirmationStore,
    ):
        self.config = config
        self.registry = registry
        self.permissions = permissions
        self.audit_log = audit_log
        self.confirmation_store = confirmation_store

    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        user_id: int,
        chat_id: int,
        approval_id: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any], str]:
        """Validate, authorize, execute, cap output, and audit a tool call.

        Returns (success, result_dict, status_message).
        """
        action_id = f"act_{uuid.uuid4().hex[:16]}"
        start_time = time.time()

        # 1. Reject unknown tool
        tool = self.registry.get(tool_name)
        if not tool:
            self.audit_log.record_action(
                action_id=action_id,
                user_id=user_id,
                chat_id=chat_id,
                tool=tool_name,
                params=params,
                outcome="denied",
                error_category="unknown_tool",
            )
            return False, {}, f"Tool '{tool_name}' is not recognized or permitted."

        # 2. Schema validation
        is_schema_valid, schema_err = _validate_schema(tool.json_schema, params)
        if not is_schema_valid:
            self.audit_log.record_action(
                action_id=action_id,
                user_id=user_id,
                chat_id=chat_id,
                tool=tool_name,
                params=params,
                outcome="denied",
                error_category="schema_violation",
            )
            return False, {}, f"Schema validation error: {schema_err}"

        # 3. Permission and feature flag check
        if tool.mutates or tool.permission in ("write", "bulk"):
            allowed, reason = self.permissions.check_mutation_allowed()
            if not allowed:
                self.audit_log.record_action(
                    action_id=action_id,
                    user_id=user_id,
                    chat_id=chat_id,
                    tool=tool_name,
                    params=params,
                    outcome="denied",
                    error_category="mutations_disabled",
                )
                return False, {}, f"Operation rejected: {reason}"

        # 4. Custom tool validators
        for val_fn in tool.validators:
            try:
                if not val_fn(params):
                    self.audit_log.record_action(
                        action_id=action_id,
                        user_id=user_id,
                        chat_id=chat_id,
                        tool=tool_name,
                        params=params,
                        outcome="denied",
                        error_category="custom_validator_failed",
                    )
                    return False, {}, "Tool validator rejected the provided arguments."
            except Exception as e:
                return False, {}, f"Validation error: {e}"

        item_id = str(params.get("item_id") or "")

        # 5. Confirmation enforcement
        if tool.requires_confirmation == "always":
            if not approval_id:
                # Issue confirmation token for approval
                token_id, action_hash = self.confirmation_store.create_confirmation(
                    user_id=user_id,
                    chat_id=chat_id,
                    tool_name=tool_name,
                    params=params,
                    ttl_seconds=self.config.confirm_ttl_seconds,
                )
                self.audit_log.record_action(
                    action_id=action_id,
                    user_id=user_id,
                    chat_id=chat_id,
                    tool=tool_name,
                    item_id=item_id,
                    params=params,
                    approval_required=True,
                    approval_id=token_id,
                    outcome="pending_approval",
                )
                return False, {
                    "confirmation_required": True,
                    "confirmation_id": token_id,
                    "action_hash": action_hash,
                }, "Confirmation required prior to execution."

            # Verify and consume the confirmation token with action-hash binding
            expected_hash = compute_action_hash(tool_name, params)
            ok, payload, reason = self.confirmation_store.consume_confirmation(
                confirmation_id=approval_id,
                user_id=user_id,
                chat_id=chat_id,
                expected_action_hash=expected_hash,
            )
            if not ok:
                self.audit_log.record_action(
                    action_id=action_id,
                    user_id=user_id,
                    chat_id=chat_id,
                    tool=tool_name,
                    item_id=item_id,
                    params=params,
                    approval_required=True,
                    approval_id=approval_id,
                    outcome="denied",
                    error_category="invalid_confirmation",
                )
                return False, {}, f"Confirmation rejected: {reason}"

        # 6. Execute with strict timeout
        if not tool.handler:
            return False, {}, f"Tool '{tool_name}' has no executable implementation."

        try:
            if inspect.iscoroutinefunction(tool.handler):
                result = await asyncio.wait_for(
                    tool.handler(params),
                    timeout=tool.timeout_seconds,
                )
            else:
                result = await asyncio.to_thread(tool.handler, params)

        except asyncio.TimeoutError:
            self.audit_log.record_action(
                action_id=action_id,
                user_id=user_id,
                chat_id=chat_id,
                tool=tool_name,
                params=params,
                outcome="failed",
                error_category="timeout",
            )
            return False, {}, f"Tool execution timed out after {tool.timeout_seconds} seconds."
        except Exception as e:
            logger.error(f"[RUNNER] Exception running {tool_name}: {e}", exc_info=True)
            self.audit_log.record_action(
                action_id=action_id,
                user_id=user_id,
                chat_id=chat_id,
                tool=tool_name,
                params=params,
                outcome="failed",
                error_category=type(e).__name__,
            )
            return False, {}, f"Tool execution error: {type(e).__name__}"

        # 7. Output capping and sanitization
        clean_result = redact_data(result)
        res_json = json.dumps(clean_result)
        if len(res_json) > tool.max_output_chars:
            clean_result = {
                "_truncated": True,
                "preview": res_json[: tool.max_output_chars],
                "note": f"Output exceeded maximum size cap ({len(res_json)} > {tool.max_output_chars} chars).",
            }

        # 8. Record successful audit
        self.audit_log.record_action(
            action_id=action_id,
            user_id=user_id,
            chat_id=chat_id,
            tool=tool_name,
            params=params,
            approval_id=approval_id,
            outcome="success",
            verification_result="verified" if not tool.mutates else "pending",
        )

        return True, clean_result, "success"
