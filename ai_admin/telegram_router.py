"""Stage 4A Telegram Router for AI Administrator.

Registers isolated, private-admin Telegram handlers for /ai commands
and ai:* callback queries in Pyrogram group -1.
Ensures zero collisions with existing bot plugins (group 0 catch-all),
strict authorization, HTML escaping, and length capping <= 4000 chars.
"""

import aiohttp
import asyncio
import html
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from pyrogram import Client, StopPropagation, filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from ai_admin.config import AIAdminConfig
from ai_admin.handler import AIAdminHandler
from ai_admin.permissions import PermissionChecker

logger = logging.getLogger("AIAdmin.TelegramRouter")

MAX_TELEGRAM_MESSAGE_LENGTH = 4000

import time

_DEDUP_CACHE: Dict[Tuple[int, int], float] = {}
_DEDUP_LOCK = asyncio.Lock()


async def should_process_message(chat_id: Any, message_id: Any) -> bool:
    """Check if (chat_id, message_id) is new and claim processing rights.

    Prevents duplicate bot replies caused by concurrent MTProto & Webhook delivery
    or Telegram Bot API webhook delivery retries.
    """
    if chat_id is None or message_id is None:
        return True

    try:
        c_id = int(chat_id)
        m_id = int(message_id)
    except (ValueError, TypeError):
        return True

    key = (c_id, m_id)
    now = time.time()

    async with _DEDUP_LOCK:
        expired = [k for k, ts in _DEDUP_CACHE.items() if now - ts > 120]
        for k in expired:
            _DEDUP_CACHE.pop(k, None)

        if key in _DEDUP_CACHE:
            logger.info(f"[AI-DEDUP] Dropping duplicate delivery for chat={chat_id} msg={message_id}")
            return False

        _DEDUP_CACHE[key] = now
        return True


def clear_dedup_cache() -> None:
    """Clear in-memory deduplication cache (useful for testing)."""
    _DEDUP_CACHE.clear()


def is_ai_update(data: Dict[str, Any]) -> bool:
    """Fast check whether an update should be intercepted by AI Admin."""
    if not isinstance(data, dict):
        return False
    cb = data.get("callback_query")
    if cb and str(cb.get("data") or "").startswith("ai:"):
        return True
    msg = data.get("message")
    if msg and isinstance(msg, dict):
        text = (msg.get("text") or "").strip()
        if not text:
            return False
        if text.startswith("/ai"):
            return True
        chat_type = str((msg.get("chat") or {}).get("type", "")).lower()
        if chat_type == "private" and not text.startswith("/"):
            return True
    return False


def is_private_chat(chat_obj: Any) -> bool:
    """Verify whether a chat object represents a private 1-on-1 chat."""
    if not chat_obj:
        return False
    c_type = getattr(chat_obj, "type", None)
    if c_type is None:
        return False
    val = getattr(c_type, "value", c_type)
    return str(val).lower() == "private"


def is_forwarded(message: Any) -> bool:
    """Detect whether a message was forwarded."""
    if not message:
        return False
    return bool(
        getattr(message, "forward_date", None)
        or getattr(message, "forward_from", None)
        or getattr(message, "forward_from_chat", None)
        or getattr(message, "forward_sender_name", None)
    )


def safe_format_html(text: str, max_chars: int = MAX_TELEGRAM_MESSAGE_LENGTH) -> str:
    """Format text into safe Telegram HTML with dynamic escaping and length capping.
    
    Protects against tag injection from untrusted media titles or provider data.
    """
    if not text:
        return ""

    # Parse fenced code blocks first: ```json ... ```
    code_block_pattern = re.compile(r"```(?:[a-zA-Z0-9_\-]+)?\n?(.*?)```", re.DOTALL)
    parts = []
    last_idx = 0

    for m in code_block_pattern.finditer(text):
        # Text before code block
        pre_text = text[last_idx:m.start()]
        if pre_text:
            parts.append(_format_inline_markdown_to_html(pre_text))
        
        # Code block contents: strictly escape HTML
        code_content = html.escape(m.group(1), quote=True)
        parts.append(f"<pre><code>{code_content}</code></pre>")
        last_idx = m.end()

    # Trailing text after last code block
    if last_idx < len(text):
        parts.append(_format_inline_markdown_to_html(text[last_idx:]))

    rendered = "".join(parts)

    # Cap length strictly <= max_chars
    if len(rendered) > max_chars:
        suffix = "\n\n<i>... [Response truncated to stay within message limit]</i>"
        reserve = len(suffix) + 30
        allowed_len = max(20, max_chars - reserve)
        
        while allowed_len > 0:
            truncated = rendered[:allowed_len]
            balanced = _balance_html_tags(truncated)
            candidate = balanced + suffix
            if len(candidate) <= max_chars:
                rendered = candidate
                break
            allowed_len -= 5
        else:
            # Fallback if max_chars is extremely small
            rendered = suffix[:max_chars]

    return rendered


def _format_inline_markdown_to_html(raw: str) -> str:
    """Escape raw text and convert basic inline markdown (*bold*, `code`) safely."""
    # First, escape all HTML entities so raw untrusted input cannot inject tags
    escaped = html.escape(raw, quote=True)

    # Convert `inline code`
    escaped = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", escaped)

    # Convert *bold* (avoiding double asterisks or edge cases)
    escaped = re.sub(r"\*([^*\n]+)\*", r"<b>\1</b>", escaped)

    return escaped


def _balance_html_tags(text: str) -> str:
    """Close any unclosed standard tags (<pre>, <code>, <b>, <i>) and strip partial tags."""
    if not text:
        return ""

    # Strip any trailing incomplete tag (e.g. "something <pr" or "something </")
    last_lt = text.rfind("<")
    last_gt = text.rfind(">")
    if last_lt > last_gt:
        text = text[:last_lt]

    # Strip any trailing incomplete HTML entity (e.g. "something &qu")
    last_amp = text.rfind("&")
    last_semi = text.rfind(";")
    if last_amp > last_semi and last_amp >= len(text) - 10:
        text = text[:last_amp]

    open_tags = []
    tag_regex = re.compile(r"<\s*(/)?\s*(b|i|code|pre)\s*>", re.IGNORECASE)
    
    for match in tag_regex.finditer(text):
        is_closing = bool(match.group(1))
        tag_name = match.group(2).lower()
        if is_closing:
            if open_tags and open_tags[-1] == tag_name:
                open_tags.pop()
        else:
            open_tags.append(tag_name)

    # Append closing tags in reverse order
    closers = "".join(f"</{t}>" for t in reversed(open_tags))
    return text + closers


class TelegramAIAdminRouter:
    """Pyrogram handler router for AI Admin operations."""

    def __init__(
        self,
        config: AIAdminConfig,
        permissions: PermissionChecker,
        handler: AIAdminHandler,
    ):
        self.config = config
        self.permissions = permissions
        self.handler = handler
        self._registered_handlers: List[Tuple[Any, int]] = []

    def register_handlers(self, client: Client, group: int = -1) -> None:
        """Register /ai command, private conversational chat, and ai:* callback query handlers in group -1."""
        cmd_filter = filters.command(["ai"]) | (
            filters.private & filters.text & ~filters.command(["start", "help", "stream", "login", "restart", "cancel", "status_bot"])
        )
        cmd_h = MessageHandler(self.handle_ai_command, filters=cmd_filter)
        cb_h = CallbackQueryHandler(self.handle_callback_query, filters=filters.regex(r"^ai:"))

        client.add_handler(cmd_h, group=group)
        client.add_handler(cb_h, group=group)

        self._registered_handlers.append((cmd_h, group))
        self._registered_handlers.append((cb_h, group))
        logger.info(f"Registered AI Admin handlers in Pyrogram group={group}")

    def unregister_handlers(self, client: Client) -> None:
        """Remove previously registered handlers from client."""
        for h, grp in self._registered_handlers:
            try:
                client.remove_handler(h, group=grp)
            except Exception as e:
                logger.debug(f"Error removing handler {h} from group {grp}: {e}")
        self._registered_handlers.clear()

    async def handle_ai_command(self, client: Client, message: Message) -> None:
        """Handle incoming /ai commands and private conversational messages in group -1."""
        try:
            # 1. Config enabled check
            if not self.config.enabled:
                if is_private_chat(getattr(message, "chat", None)):
                    await message.reply_text(
                        "⚠️ <b>AI Administrator is currently disabled.</b>",
                        parse_mode=ParseMode.HTML,
                    )
                raise StopPropagation

            # 2. Config validity check
            if not self.config.is_valid or not self.config.admin_telegram_ids:
                if is_private_chat(getattr(message, "chat", None)):
                    await message.reply_text(
                        "⚠️ <b>AI Administrator configuration is invalid or missing admin IDs.</b>",
                        parse_mode=ParseMode.HTML,
                    )
                raise StopPropagation

            # 3. Private chat constraint: reject group, channel, supergroup
            if not is_private_chat(getattr(message, "chat", None)):
                logger.warning(
                    f"Rejected /ai command from non-private chat id={getattr(message.chat, 'id', None)} "
                    f"type={getattr(message.chat, 'type', None)}"
                )
                raise StopPropagation

            # 4. Reject forwarded commands
            if is_forwarded(message):
                logger.warning(
                    f"Rejected forwarded /ai command from user={getattr(message.from_user, 'id', None)}"
                )
                await message.reply_text(
                    "⚠️ <b>Forwarded commands are rejected for security.</b>",
                    parse_mode=ParseMode.HTML,
                )
                raise StopPropagation

            # 5. Authorization check
            user_id = message.from_user.id if message.from_user else None
            chat_id = message.chat.id if message.chat else None
            auth_ok, reason = self.permissions.check_authorization(
                user_id=user_id,
                chat_id=chat_id,
                is_channel=False,
                is_anonymous_admin=False,
            )
            if not auth_ok:
                logger.warning(f"Unauthorized /ai attempt by user={user_id} in chat={chat_id}: {reason}")
                await message.reply_text(
                    "⛔ <b>Access Denied:</b> You are not authorized to use the AI Administrator.",
                    parse_mode=ParseMode.HTML,
                )
                raise StopPropagation

            # Deduplication: prevent duplicate replies from concurrent MTProto and Webhook delivery
            msg_id = getattr(message, "id", None)
            if not isinstance(msg_id, int):
                msg_id = getattr(message, "message_id", None)
            if isinstance(msg_id, int):
                if not await should_process_message(chat_id, msg_id):
                    raise StopPropagation

            # 6. Parse command instruction
            raw_text = getattr(message, "text", "") or ""
            if raw_text.startswith("/ai"):
                parts = raw_text.split(maxsplit=1)
                instruction = parts[1].strip() if len(parts) > 1 else ""
            else:
                instruction = raw_text.strip()

            # 7. Execute via isolated AIAdminHandler
            handled, response = await self.handler.handle_message(
                user_id=user_id,
                chat_id=chat_id,
                text=instruction,
                is_channel=False,
                is_anonymous_admin=False,
            )

            # 8. Format safely and send
            formatted_html = safe_format_html(response)
            
            # Optional quick action buttons for status / help
            reply_markup = None
            if not instruction or instruction.lower() in ("help", "status"):
                reply_markup = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("⚙️ Status", callback_data="ai:status"),
                        InlineKeyboardButton("❓ Help", callback_data="ai:help"),
                    ]
                ])

            # 8. Format safely and send with fallback
            await self._send_safe_reply(message, response, reply_markup=reply_markup)
            raise StopPropagation

        except StopPropagation:
            raise
        except Exception as e:
            logger.error(f"Error handling /ai command: {e}", exc_info=True)
            raise StopPropagation

    async def _send_safe_reply(self, target_msg: Message, text: str, reply_markup: Optional[Any] = None) -> None:
        """Send message in HTML mode, falling back safely to plain text if parsing fails."""
        formatted_html = safe_format_html(text)
        try:
            await target_msg.reply_text(
                formatted_html,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
            )
        except Exception as e:
            logger.warning(f"HTML reply failed ({e}), falling back to plain text")
            clean_plain = (text or "")[:MAX_TELEGRAM_MESSAGE_LENGTH]
            await target_msg.reply_text(
                clean_plain,
                parse_mode=None,
                reply_markup=reply_markup,
            )

    async def handle_callback_query(self, client: Client, callback_query: CallbackQuery) -> None:
        """Handle incoming ai:* callback queries in group -1."""
        try:
            # 1. Config checks
            if not self.config.enabled or not self.config.is_valid:
                await callback_query.answer("AI Administrator is disabled or unconfigured.", show_alert=True)
                raise StopPropagation

            # 2. Private chat check
            msg = getattr(callback_query, "message", None)
            if msg and not is_private_chat(getattr(msg, "chat", None)):
                await callback_query.answer("AI Admin actions are restricted to private chats.", show_alert=True)
                raise StopPropagation

            # 3. Authorization check
            user_id = callback_query.from_user.id if callback_query.from_user else None
            chat_id = msg.chat.id if msg and msg.chat else user_id
            auth_ok, reason = self.permissions.check_authorization(
                user_id=user_id,
                chat_id=chat_id,
                is_channel=False,
                is_anonymous_admin=False,
            )
            if not auth_ok:
                await callback_query.answer("⛔ Access denied: unauthorized administrator.", show_alert=True)
                raise StopPropagation

            # 4. Dispatch callback action
            data = getattr(callback_query, "data", "") or ""
            action = data[3:] if data.startswith("ai:") else data

            if action == "status":
                handled, response = await self.handler.handle_message(
                    user_id=user_id,
                    chat_id=chat_id,
                    text="status",
                )
                await callback_query.answer()
                if msg:
                    await self._send_safe_reply(msg, response)

            elif action == "help":
                handled, response = await self.handler.handle_message(
                    user_id=user_id,
                    chat_id=chat_id,
                    text="",
                )
                await callback_query.answer()
                if msg:
                    await self._send_safe_reply(msg, response)

            elif action.startswith("item:"):
                item_id = action.split(":", 1)[1]
                handled, response = await self.handler.handle_message(
                    user_id=user_id,
                    chat_id=chat_id,
                    text=f"details {item_id}",
                )
                await callback_query.answer()
                if msg:
                    await self._send_safe_reply(msg, response)

            elif action == "cancel":
                await callback_query.answer("Operation cancelled.")
                if msg:
                    try:
                        await msg.delete()
                    except Exception:
                        pass
            else:
                await callback_query.answer(f"Unknown action: {action[:20]}", show_alert=True)

            raise StopPropagation

        except StopPropagation:
            raise
        except Exception as e:
            logger.error(f"Error handling callback query: {e}", exc_info=True)
            raise StopPropagation


async def handle_webhook_update(
    data: Dict[str, Any],
    bot_token: Optional[str] = None,
    client: Optional[Client] = None,
) -> bool:
    """Process incoming Telegram Bot API webhook update dict for AI Admin commands and callbacks.

    Returns True if update was an AI Admin command/callback and handled.
    Returns False if update was unrelated (allowing standard streaming/media ingestion).
    """
    if not isinstance(data, dict):
        return False

    message_dict = data.get("message")
    callback_dict = data.get("callback_query")

    if not message_dict and not callback_dict:
        return False

    config = AIAdminConfig.from_env()

    async def _send_reply(chat_id: int, text: str, reply_markup: Optional[Dict[str, Any]] = None):
        if client and getattr(client, "is_connected", False):
            try:
                await client.send_message(chat_id, text, parse_mode=ParseMode.HTML)
                return
            except Exception:
                pass

        token = (
            bot_token
            or os.environ.get("TELEGRAM_BOT_TOKEN")
            or os.environ.get("TG_BOT_TOKEN")
            or os.environ.get("BOT_TOKEN")
        )
        if token:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=5.0),
                    ) as resp:
                        pass
            except Exception as e:
                logger.warning(f"[AI-ADMIN] Failed to send webhook reply: {e}")

    # 1. Message (/ai command or private conversational message)
    if message_dict:
        raw_text = (message_dict.get("text") or "").strip()
        if not raw_text:
            return False

        chat = message_dict.get("chat") or {}
        chat_id = chat.get("id")
        chat_type = chat.get("type", "")
        from_user = message_dict.get("from") or {}
        user_id = from_user.get("id")

        is_ai_command = raw_text.startswith("/ai")
        # Ignore other slash commands (e.g. /start, /stream) so default bot plugins handle them
        if raw_text.startswith("/") and not is_ai_command:
            return False

        # In non-private chats, only explicit /ai commands are processed
        if not is_ai_command and chat_type != "private":
            return False

        # Config enabled check
        if not config.enabled:
            if chat_type == "private" and chat_id and is_ai_command:
                await _send_reply(
                    chat_id,
                    "⚠️ <b>AI Administrator is currently disabled (AI_ENABLED=false).</b>\n\n"
                    "To enable, set <code>AI_ENABLED=true</code> in your Hugging Face Space variables.",
                )
            return is_ai_command

        # Config validity check
        if not config.is_valid or not config.admin_telegram_ids:
            if chat_type == "private" and chat_id and is_ai_command:
                await _send_reply(
                    chat_id,
                    f"⚠️ <b>AI Administrator configuration is invalid:</b> {config.validation_error or 'Missing admin IDs'}\n\n"
                    "Set <code>AI_ADMIN_TELEGRAM_IDS</code> to your Telegram User ID in your Space variables.",
                )
            return is_ai_command

        # Private chat only
        if chat_type != "private":
            logger.warning(f"[AI-ADMIN] Rejected /ai from non-private chat id={chat_id} type={chat_type}")
            return True

        # Check forwarded
        if bool(
            message_dict.get("forward_date")
            or message_dict.get("forward_from")
            or message_dict.get("forward_from_chat")
        ):
            if chat_id:
                await _send_reply(chat_id, "⚠️ <b>Forwarded commands are rejected for security.</b>")
            return True

        # Check authorization
        permissions = PermissionChecker(config)
        auth_ok, reason = permissions.check_authorization(
            user_id=user_id,
            chat_id=chat_id,
            is_channel=False,
            is_anonymous_admin=False,
        )
        if not auth_ok:
            if is_ai_command:
                logger.warning(f"[AI-ADMIN] Unauthorized /ai attempt by user={user_id} in chat={chat_id}: {reason}")
                if chat_id:
                    await _send_reply(
                        chat_id,
                        "⛔ <b>Access Denied:</b> You are not authorized to use the AI Administrator.\n\n"
                        f"Your Telegram User ID is <code>{user_id}</code>. Add this ID to <code>AI_ADMIN_TELEGRAM_IDS</code> in your Space variables.",
                    )
            return is_ai_command

        if is_ai_command:
            parts = raw_text.split(maxsplit=1)
            instruction = parts[1].strip() if len(parts) > 1 else ""
        else:
            instruction = raw_text.strip()

        # Deduplication check: drop duplicate webhook delivery or messages already processed by MTProto
        msg_id = message_dict.get("message_id")
        if isinstance(msg_id, int):
            if not await should_process_message(chat_id, msg_id):
                return True

        from Thunder.bot.plugins.ai_admin import setup_ai_admin
        router = setup_ai_admin(client)
        if not router:
            if chat_id:
                await _send_reply(chat_id, "⚠️ <b>AI Administrator router could not be initialized.</b>")
            return True

        handled, response = await router.handler.handle_message(
            user_id=user_id,
            chat_id=chat_id,
            text=instruction,
            is_channel=False,
            is_anonymous_admin=False,
        )

        formatted_html = safe_format_html(response)
        reply_markup = None
        if not instruction or instruction.lower() in ("help", "status"):
            reply_markup = {
                "inline_keyboard": [
                    [
                        {"text": "⚙️ Status", "callback_data": "ai:status"},
                        {"text": "❓ Help", "callback_data": "ai:help"},
                    ]
                ]
            }

        await _send_reply(chat_id, formatted_html, reply_markup=reply_markup)
        return True

    # 2. Callback query (ai:* callback)
    if callback_dict:
        data_str = (callback_dict.get("data") or "").strip()
        if not data_str.startswith("ai:"):
            return False

        cb_id = callback_dict.get("id")
        from_user = callback_dict.get("from") or {}
        user_id = from_user.get("id")
        msg = callback_dict.get("message") or {}
        chat = msg.get("chat") or {}
        chat_id = chat.get("id") or user_id

        token = (
            bot_token
            or os.environ.get("TELEGRAM_BOT_TOKEN")
            or os.environ.get("TG_BOT_TOKEN")
            or os.environ.get("BOT_TOKEN")
        )

        async def _answer_cb(text: str = "", show_alert: bool = False):
            if token and cb_id:
                try:
                    async with aiohttp.ClientSession() as session:
                        await session.post(
                            f"https://api.telegram.org/bot{token}/answerCallbackQuery",
                            json={"callback_query_id": cb_id, "text": text, "show_alert": show_alert},
                            timeout=aiohttp.ClientTimeout(total=3.0),
                        )
                except Exception:
                    pass

        if not config.enabled or not config.is_valid:
            await _answer_cb("AI Administrator is disabled or unconfigured.", show_alert=True)
            return True

        permissions = PermissionChecker(config)
        auth_ok, reason = permissions.check_authorization(user_id=user_id, chat_id=chat_id)
        if not auth_ok:
            await _answer_cb("⛔ Access denied: unauthorized administrator.", show_alert=True)
            return True

        action = data_str[3:]
        from Thunder.bot.plugins.ai_admin import setup_ai_admin
        router = setup_ai_admin(client)
        if not router:
            await _answer_cb("Router unavailable.", show_alert=True)
            return True

        if action == "status":
            _, response = await router.handler.handle_message(user_id=user_id, chat_id=chat_id, text="status")
            await _answer_cb()
            if chat_id:
                await _send_reply(chat_id, safe_format_html(response))
        elif action == "help":
            _, response = await router.handler.handle_message(user_id=user_id, chat_id=chat_id, text="")
            await _answer_cb()
            if chat_id:
                await _send_reply(chat_id, safe_format_html(response))
        elif action.startswith("item:"):
            item_id = action.split(":", 1)[1]
            _, response = await router.handler.handle_message(
                user_id=user_id, chat_id=chat_id, text=f"details {item_id}"
            )
            await _answer_cb()
            if chat_id:
                await _send_reply(chat_id, safe_format_html(response))
        elif action == "cancel":
            await _answer_cb("Operation cancelled.")
        else:
            await _answer_cb(f"Unknown action: {action[:20]}", show_alert=True)

        return True
