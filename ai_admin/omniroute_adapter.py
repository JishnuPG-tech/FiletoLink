"""OmniRoute adapter with capability probe, response limits, and error classification."""

import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from ai_admin.config import AIAdminConfig
from ai_admin.redaction import redact_text

logger = logging.getLogger("AIAdmin.OmniRoute")


class OmniRouteAdapter:
    def __init__(self, config: AIAdminConfig, session: Optional[aiohttp.ClientSession] = None):
        self.config = config
        self._external_session = session
        self._capability_mode: str = "grammar_only"  # native_tools | json_mode | grammar_only
        self._probed: bool = False

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._external_session and not self._external_session.closed:
            return self._external_session
        return aiohttp.ClientSession()

    def get_capability_mode(self) -> str:
        return self._capability_mode

    async def probe_capability(self) -> str:
        """Probe the configured models in fallback order to classify tool support mode.

        Returns one of: 'native_tools', 'json_mode', 'grammar_only'.
        """
        if not (self.config.omniroute_api_url and self.config.omniroute_api_key):
            self._capability_mode = "grammar_only"
            self._probed = True
            return self._capability_mode

        models_to_try = self.config.ai_models or ([self.config.ai_model] if self.config.ai_model else [])

        for model in models_to_try:
            probe_payload = {
                "model": model,
                "max_tokens": 100,
                "temperature": 0,
                "messages": [{"role": "user", "content": "Run echo_health with message 'ping'"}],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "echo_health",
                            "description": "Probe health",
                            "parameters": {
                                "type": "object",
                                "properties": {"message": {"type": "string"}},
                                "required": ["message"],
                                "additionalProperties": False,
                            },
                        },
                    }
                ],
            }

            try:
                status, data, err = await self._send_request(probe_payload, timeout_seconds=10)
                if status == 200 and isinstance(data, dict):
                    msg = ((data.get("choices") or [{}])[0].get("message") or {})
                    tool_calls = msg.get("tool_calls")
                    if tool_calls and isinstance(tool_calls, list) and len(tool_calls) > 0:
                        self._capability_mode = "native_tools"
                        self._probed = True
                        return self._capability_mode

                    content = (msg.get("content") or "").strip()
                    if "echo_health" in content and ("{" in content):
                        self._capability_mode = "json_mode"
                        self._probed = True
                        return self._capability_mode
                elif status in (401, 403):
                    break
            except Exception as e:
                logger.warning(f"[OMNIROUTE-PROBE] Probe failed for {model}: {e}")

        self._capability_mode = "grammar_only"
        self._probed = True
        return self._capability_mode

    async def chat_or_plan(
        self,
        instruction: Optional[str] = None,
        context_history: Optional[List[Dict[str, str]]] = None,
        tool_schemas: Optional[List[Dict[str, Any]]] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        timeout_seconds: int = 30,
    ) -> Tuple[bool, List[Dict[str, Any]], str]:
        """Send instruction or pre-built messages to OmniRoute.
        Returns:
            (success, tool_calls_list, conversational_content_or_error)
            - If tool_calls_list is non-empty: tools need to be executed.
            - If tool_calls_list is empty and success is True: conversational response is in the third element.
            - If success is False: error message is in the third element.
        """
        if not (self.config.omniroute_api_url and self.config.omniroute_api_key):
            return False, [], "OmniRoute configuration is missing (OMNIROUTE_API_KEY / OMNIROUTE_API_URL)."

        if messages is None:
            system_prompt = (
                "You are an intelligent, helpful, and friendly Jellyfin Media Server AI Assistant.\n"
                "You have access to tools to inspect and manage the Jellyfin library and query metadata/artwork providers (TMDB, Fanart.tv, OpenSubtitles).\n"
                "If the user asks to find, check, compare, or fix posters, thumbnails, subtitles, or metadata, use the appropriate tools.\n"
                "If the user greets you or asks general questions that do not require tool operations, answer conversationally and helpfully.\n"
                "Format your answers with clean Telegram markdown (*bold*, `code`, [link](url))."
            )
            built_messages = [{"role": "system", "content": system_prompt}]
            if context_history:
                for turn in context_history[-8:]:
                    built_messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
            if instruction:
                built_messages.append({"role": "user", "content": instruction})
            messages = built_messages

        models_to_try = self.config.ai_models or ([self.config.ai_model] if self.config.ai_model else [])
        last_err = ""

        for model in models_to_try:
            payload = {
                "model": model,
                "temperature": 0.3,
                "max_tokens": self.config.ai_max_tokens,
                "messages": messages,
            }
            if tool_schemas:
                payload["tools"] = tool_schemas

            logger.info(f"[OMNIROUTE-CHAT] Attempting model '{model}'...")
            status, data, err_msg = await self._send_request(payload, timeout_seconds=timeout_seconds)

            if status in (401, 403):
                return False, [], err_msg

            if status != 200 or not isinstance(data, dict):
                last_err = err_msg
                logger.warning(f"[OMNIROUTE-CHAT-FAILOVER] Model '{model}' failed ({status}: {err_msg}). Trying fallback...")
                continue

            choices = data.get("choices") or []
            if not choices:
                last_err = f"Model '{model}' returned an empty choice list."
                logger.warning(f"[OMNIROUTE-CHAT-FAILOVER] {last_err}. Trying fallback...")
                continue

            msg = choices[0].get("message") or {}
            raw_tool_calls = msg.get("tool_calls") or []

            parsed_calls = []
            for call in raw_tool_calls:
                func = call.get("function") or {}
                name = func.get("name")
                args_str = func.get("arguments") or "{}"
                try:
                    args = json.loads(args_str) if isinstance(args_str, str) else args_str
                except Exception:
                    args = {}
                if name:
                    parsed_calls.append({"name": name, "params": args})

            content = (msg.get("content") or "").strip()
            return True, parsed_calls, content

        return False, [], last_err or "All configured AI models failed to respond."

    async def synthesize_response(
        self,
        instruction: str,
        context_history: List[Dict[str, str]],
        tool_results: List[Dict[str, Any]],
        timeout_seconds: int = 25,
    ) -> Tuple[bool, str]:
        """Synthesize tool execution results into a natural, conversational response."""
        if not (self.config.omniroute_api_url and self.config.omniroute_api_key):
            return False, ""

        system_prompt = (
            "You are an intelligent, friendly Jellyfin Media Server AI Assistant.\n"
            "Explain the results of the operations conversationally to the user.\n"
            "Highlight key findings (e.g. movie/series title, current artwork/thumbnail status, matching poster candidates).\n"
            "If new posters or subtitles were found, describe them clearly and ask if the user wants to apply any of them.\n"
            "Be concise, engaging, and clear. Format with Telegram markdown (*bold*, `code`)."
        )

        compact_results = json.dumps(tool_results, default=str)
        if len(compact_results) > 6000:
            compact_results = compact_results[:6000] + "... [truncated]"

        user_content = (
            f"User Instruction: {instruction}\n\n"
            f"Tool Results:\n{compact_results}\n\n"
            "Give a natural, friendly, and helpful response summarizing what you found and any next actions."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        models_to_try = self.config.ai_models or ([self.config.ai_model] if self.config.ai_model else [])
        for model in models_to_try:
            payload = {
                "model": model,
                "temperature": 0.4,
                "max_tokens": self.config.ai_max_tokens,
                "messages": messages,
            }
            try:
                status, data, err_msg = await self._send_request(payload, timeout_seconds=timeout_seconds)
                if status == 200 and isinstance(data, dict):
                    choices = data.get("choices") or []
                    if choices:
                        content = ((choices[0].get("message") or {}).get("content") or "").strip()
                        if content:
                            return True, content
                elif status in (401, 403):
                    break
            except Exception as e:
                logger.warning(f"[OMNIROUTE-SYNTH] Synthesis failed on {model}: {e}")

        return False, ""

    async def plan_action(
        self,
        instruction: str,
        context_history: List[Dict[str, str]],
        tool_schemas: List[Dict[str, Any]],
        timeout_seconds: int = 30,
    ) -> Tuple[bool, List[Dict[str, Any]], str]:
        """Send instruction to OmniRoute and return structured tool calls.
        Attempts models in fallback order if rate-limited (HTTP 429), errored, or timed out.

        Returns (success, tool_calls_list, error_or_reason).
        """
        ok, tool_calls, content_or_err = await self.chat_or_plan(
            instruction=instruction,
            context_history=context_history,
            tool_schemas=tool_schemas,
            timeout_seconds=timeout_seconds,
        )
        if not ok:
            return False, [], content_or_err
        return True, tool_calls, "success"

    async def _send_request(
        self,
        payload: Dict[str, Any],
        timeout_seconds: int = 30,
        max_response_bytes: int = 100 * 1024,
    ) -> Tuple[int, Optional[Dict[str, Any]], str]:
        """Low-level request dispatcher with timeout, status error classification, and size caps."""
        url = f"{self.config.omniroute_api_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.omniroute_api_key}",
            "Content-Type": "application/json",
        }

        session = await self._get_session()
        is_temp_session = (session != self._external_session)

        try:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout_seconds)) as resp:
                status = resp.status
                if status == 401 or status == 403:
                    return status, None, "Authentication failed with OmniRoute: verify OMNIROUTE_API_KEY."
                if status == 429:
                    retry_after = resp.headers.get("Retry-After", "unknown")
                    return status, None, f"OmniRoute rate limit exceeded (Retry-After: {retry_after})."
                if status != 200:
                    raw_body = await resp.text()
                    clean_body = redact_text(raw_body[:200])
                    return status, None, f"OmniRoute returned error HTTP {status}: {clean_body}"

                # Enforce response byte limit
                content_bytes = await resp.read()
                if len(content_bytes) > max_response_bytes:
                    return 500, None, f"OmniRoute response exceeded size cap ({len(content_bytes)} bytes)."

                try:
                    data = json.loads(content_bytes.decode("utf-8"))
                    return 200, data, "ok"
                except Exception as json_err:
                    return 500, None, f"Malformed JSON from OmniRoute: {json_err}"

        except asyncio.TimeoutError:
            return 504, None, f"OmniRoute request timed out after {timeout_seconds} seconds."
        except Exception as e:
            return 500, None, f"Network error contacting OmniRoute: {type(e).__name__}"
        finally:
            if is_temp_session:
                await session.close()
