"""Request handler and dispatcher for AI Admin (isolated logic)."""

import json
from typing import Any, Dict, Optional, Tuple

from ai_admin.config import AIAdminConfig
from ai_admin.context_store import ContextStore
from ai_admin.grammar import GrammarParser
from ai_admin.omniroute_adapter import OmniRouteAdapter
from ai_admin.permissions import PermissionChecker
from ai_admin.snapshot_store import SnapshotStore
from ai_admin.tool_registry import ToolRegistry
from ai_admin.tool_runner import ToolRunner


class AIAdminHandler:
    def __init__(
        self,
        config: AIAdminConfig,
        permissions: PermissionChecker,
        grammar: GrammarParser,
        runner: ToolRunner,
        context_store: ContextStore,
        snapshot_store: SnapshotStore,
        omniroute: OmniRouteAdapter,
        registry: ToolRegistry,
    ):
        self.config = config
        self.permissions = permissions
        self.grammar = grammar
        self.runner = runner
        self.context_store = context_store
        self.snapshot_store = snapshot_store
        self.omniroute = omniroute
        self.registry = registry

    async def handle_message(
        self,
        user_id: Optional[int],
        chat_id: Optional[int],
        text: str,
        is_channel: bool = False,
        is_anonymous_admin: bool = False,
    ) -> Tuple[bool, str]:
        """Process incoming instruction.

        Returns (is_handled, response_text).
        """
        # 1. Authorize
        auth_ok, reason = self.permissions.check_authorization(
            user_id=user_id,
            chat_id=chat_id,
            is_channel=is_channel,
            is_anonymous_admin=is_anonymous_admin,
        )
        if not auth_ok:
            return False, reason

        cleaned_text = (text or "").strip()
        if not cleaned_text or cleaned_text.lower() in ("/ai", "help"):
            return True, (
                "🤖 *Jellyfin AI Administrator*\n\n"
                "Commands:\n"
                "• `find <title>` — Search library items\n"
                "• `details <item_id>` — Show item metadata\n"
                "• `images <item_id>` — Inspect current artwork\n"
                "• `subtitles <item_id>` — Inspect subtitle streams\n"
                "• `status` — View service status and feature flags\n"
                "• `undo` — Revert the last applied modification\n"
                "• `reset` — Clear conversation context\n"
            )

        # 2. Check administrative subcommands
        lower = cleaned_text.lower()
        if lower in ("status", "/ai status"):
            mode = self.omniroute.get_capability_mode()
            return True, (
                "⚙️ *AI Admin Status*\n"
                f"• Enabled: `{self.config.enabled}`\n"
                f"• Mutations: `{self.config.mutations_enabled}`\n"
                f"• Planner Mode: `{mode}`\n"
                f"• Config Valid: `{self.config.is_valid}`\n"
            )

        if lower in ("reset", "/ai reset"):
            self.context_store.clear(user_id, chat_id)
            return True, "✅ Conversation context has been reset."

        if lower in ("undo", "/ai undo"):
            latest = self.snapshot_store.get_latest_snapshot(user_id, chat_id)
            if not latest:
                return True, "ℹ️ No recent actions available to undo."
            snap_id, meta, blob = latest
            return True, f"ℹ️ Undo target identified: {meta.get('action', 'mutation')} (Snapshot `{snap_id}`)."

        # 3. Deterministic grammar resolution
        selected_id, _ = self.context_store.get_selected_item(user_id, chat_id)
        grammar_match = self.grammar.parse(cleaned_text, selected_item_id=selected_id)

        if grammar_match:
            tool_name, params = grammar_match
            # Resolve legacy aliases if direct tool name is not registered
            if not self.registry.get(tool_name):
                if tool_name == "search_library_items" and self.registry.get("jellyfin_search"):
                    tool_name = "jellyfin_search"
                elif tool_name == "get_item_details" and self.registry.get("jellyfin_get_item"):
                    tool_name = "jellyfin_get_item"
                elif tool_name == "get_item_images" and self.registry.get("fanart_get_images"):
                    tool_name = "fanart_get_images"
                    params = {"id": params.get("item_id", "")}
                elif tool_name == "get_item_subtitles" and self.registry.get("opensubtitles_search"):
                    tool_name = "opensubtitles_search"
                    params = {"query": params.get("item_id", "")}

            success, result, msg = await self.runner.execute_tool(
                tool_name=tool_name,
                params=params,
                user_id=user_id,
                chat_id=chat_id,
            )
            if success:
                # Store contextual selection if an item was returned
                if isinstance(result, dict):
                    if "id" in result and isinstance(result["id"], str):
                        self.context_store.set_selected_item(user_id, chat_id, result["id"], result.get("name", ""))
                    elif result.get("items") is not None:
                        items_list = result.get("items") or []
                        if len(items_list) == 1 and isinstance(items_list[0], dict) and "id" in items_list[0]:
                            self.context_store.set_selected_item(user_id, chat_id, items_list[0]["id"], items_list[0].get("name", ""))
                            self.context_store.set_search_results(user_id, chat_id, items_list)
                        else:
                            # 0 items or multiple ambiguous items: clear focused selection to avoid stale target reuse
                            self.context_store.set_selected_item(user_id, chat_id, None, None)
                            if items_list:
                                self.context_store.set_search_results(user_id, chat_id, items_list)

                return True, f"✅ *{tool_name}*\n```json\n{json.dumps(result, indent=2)}\n```"
            return True, f"⚠️ {msg}"

        # 4. Conversational LLM Planner resolution (if available)
        schemas = self.registry.get_schemas_for_planner()
        history = self.context_store.get_history(user_id, chat_id)
        planned_ok, tool_calls, reply_or_err = await self.omniroute.chat_or_plan(
            instruction=cleaned_text,
            context_history=history,
            tool_schemas=schemas,
        )

        if not planned_ok:
            return True, f"⚠️ Could not resolve instruction ({reply_or_err})."

        # Direct conversational response (no tools needed)
        if not tool_calls:
            fallback_msg = reply_or_err or "I didn't detect any specific action needed."
            self.context_store.add_turn(user_id, chat_id, "user", cleaned_text)
            self.context_store.add_turn(user_id, chat_id, "assistant", fallback_msg)
            return True, fallback_msg

        results = []
        for call in tool_calls:
            ok, res, msg = await self.runner.execute_tool(
                tool_name=call["name"],
                params=call.get("params", {}),
                user_id=user_id,
                chat_id=chat_id,
            )
            results.append({"tool": call["name"], "success": ok, "result": res, "message": msg})
            if ok and isinstance(res, dict) and "items" in res and res["items"]:
                items_list = res["items"]
                self.context_store.set_selected_item(user_id, chat_id, items_list[0].get("id"), items_list[0].get("name"))
                self.context_store.set_search_results(user_id, chat_id, items_list)

        # Synthesize conversational response from tool outputs
        synth_ok, synthesized_reply = await self.omniroute.synthesize_response(
            instruction=cleaned_text,
            context_history=history,
            tool_results=results,
        )

        final_reply = synthesized_reply if (synth_ok and synthesized_reply) else f"✅ Executed {len(results)} action(s):\n```json\n{json.dumps(results, indent=2)}\n```"

        # Save turn to history
        self.context_store.add_turn(user_id, chat_id, "user", cleaned_text)
        self.context_store.add_turn(user_id, chat_id, "assistant", final_reply)

        return True, final_reply
