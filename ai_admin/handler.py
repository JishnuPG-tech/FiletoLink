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

        # 4. Multi-Step Conversational Agent Loop
        schemas = self.registry.get_schemas_for_planner()
        history = self.context_store.get_history(user_id, chat_id)

        system_prompt = (
            "You are an intelligent, friendly, and expert Jellyfin Media Server AI Assistant.\n"
            "You have direct control to inspect and manage the Jellyfin library and query metadata/artwork providers:\n"
            "• Search Jellyfin library for movies, series, episodes (`jellyfin_search`, `jellyfin_get_item`, `jellyfin_get_media_info`, `jellyfin_list_library`).\n"
            "• Ground-Truth Telegram Files: Access all files injected from Telegram with their exact raw file names and message IDs (`telegram_list_injected`). The Telegram injected files are the 100% ground truth.\n"
            "• Library Reconciliation & Audit: Compare Telegram ground truth with Jellyfin items to detect rogue un-injected items, duplicate series, and title mismatches (`library_audit_and_compare`).\n"
            "• Automatic Fixing & Cleanup: Reconcile mismatched items (`library_fix_item`), remove rogue items / duplicate series (`library_cleanup_rogue_and_duplicates`), and apply artwork (`jellyfin_apply_artwork`).\n"
            "• Free Artwork & IMDb Providers: Search artwork & posters across providers (`artwork_search`, `imdb_search`, `cinemeta_search`, `cinemeta_get_meta`, `tvmaze_search`, `tmdb_get_images`, `fanart_get_images`).\n"
            "• Free providers like IMDb suggestions (`imdb_search`) and Cinemeta (`cinemeta_search`) require ZERO API keys, have no rate limits, and find authentic posters/thumbnails for movies and series worldwide (including Indian/regional movies like Khalifa, The Paradise, etc.).\n"
            "• Search subtitles on OpenSubtitles (`opensubtitles_search`).\n\n"
            "Workflow Guidelines:\n"
            "1. When the user asks to find a movie/series and check or fix its poster/thumbnail (e.g. Khalifa):\n"
            "   a) Query Telegram injected files (`telegram_list_injected`) to see the exact 100% true filename (e.g. 'Khalifa 2026 malayalam movie') and Jellyfin items (`jellyfin_search`).\n"
            "   b) If Jellyfin has the wrong movie/poster (e.g. Queer Khalifa), search genuine artwork via `imdb_search`, `artwork_search`, or `cinemeta_search` (e.g. query='khalifa' returns IMDb tt22797990 with Prithviraj Sukumaran, Mohanlal, and official Amazon poster).\n"
            "   c) Fix the item in Jellyfin (`library_fix_item` or `jellyfin_apply_artwork`) using the true title, year, IMDb ID, and poster URL.\n"
            "2. When the user asks about rogue movies, duplicate series, or mismatched items:\n"
            "   a) Run `library_audit_and_compare` to compare Telegram ground truth with Jellyfin.\n"
            "   b) Identify any items in Jellyfin that were not injected from Telegram (rogue), duplicate series folders, or mismatched titles.\n"
            "   c) Automatically clean them up with `library_cleanup_rogue_and_duplicates` and explain the exact changes made.\n"
            "3. If the user is just chatting or asking a general question, reply warmly, concisely, and conversationally.\n"
            "4. Format all responses using Telegram markdown (*bold*, `code`, [link](url)). Never output raw JSON unless specifically requested."
        )

        messages = [{"role": "system", "content": system_prompt}]
        for turn in history[-6:]:
            messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
        messages.append({"role": "user", "content": cleaned_text})

        max_iterations = 3
        executed_tool_results = []
        final_reply = ""

        for iteration in range(max_iterations):
            planned_ok, tool_calls, reply_or_err = await self.omniroute.chat_or_plan(
                messages=messages,
                tool_schemas=schemas,
                timeout_seconds=self.config.omniroute_timeout_seconds,
            )

            if not planned_ok:
                final_reply = f"⚠️ Could not process instruction ({reply_or_err})."
                break

            # If model produced conversational response without calling any tools
            if not tool_calls:
                final_reply = reply_or_err or "I didn't detect any specific action needed."
                break

            # Execute tool calls
            tool_outputs = []
            for call in tool_calls:
                ok, res, msg = await self.runner.execute_tool(
                    tool_name=call["name"],
                    params=call.get("params", {}),
                    user_id=user_id,
                    chat_id=chat_id,
                )
                tool_outputs.append({"tool": call["name"], "success": ok, "result": res, "message": msg})
                executed_tool_results.append({"tool": call["name"], "success": ok, "result": res, "message": msg})

                if ok and isinstance(res, dict) and "items" in res and res["items"]:
                    items_list = res["items"]
                    self.context_store.set_selected_item(user_id, chat_id, items_list[0].get("id"), items_list[0].get("name"))
                    self.context_store.set_search_results(user_id, chat_id, items_list)

            # Append assistant's turn with tool_calls
            assistant_msg = {
                "role": "assistant",
                "content": reply_or_err or None,
                "tool_calls": [
                    {
                        "id": f"call_{iteration}_{i}",
                        "type": "function",
                        "function": {
                            "name": c["name"],
                            "arguments": json.dumps(c.get("params", {}))
                        }
                    }
                    for i, c in enumerate(tool_calls)
                ]
            }
            messages.append(assistant_msg)

            # Append tool outputs
            for i, tout in enumerate(tool_outputs):
                call_id = f"call_{iteration}_{i}"
                clean_res = json.dumps(tout["result"], default=str)
                if len(clean_res) > 3000:
                    clean_res = clean_res[:3000] + "... [truncated]"
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": tout["tool"],
                    "content": clean_res,
                })

        if not final_reply and executed_tool_results:
            synth_ok, synthesized = await self.omniroute.synthesize_response(
                instruction=cleaned_text,
                context_history=history,
                tool_results=executed_tool_results,
            )
            final_reply = synthesized if (synth_ok and synthesized) else f"✅ Completed {len(executed_tool_results)} action(s)."

        # Save turn to history
        self.context_store.add_turn(user_id, chat_id, "user", cleaned_text)
        self.context_store.add_turn(user_id, chat_id, "assistant", final_reply)

        return True, final_reply
