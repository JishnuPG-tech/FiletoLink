# Thunder/bot/plugins/batch.py
"""Dedicated /batch & /b Command Handler:
- Converts multiple files, TV series episodes, or collections into a single organized card.
- Supports 3 flexible usage modes:
  1. Link Range: /batch <start_message_link> <end_message_link>
     (e.g., /batch https://t.me/c/1234567890/10 https://t.me/c/1234567890/25)
  2. Reply to File: Reply to a media file with /batch <count>
     (e.g., reply with /batch 10)
  3. Interactive Guide: Send /batch alone for clear usage instructions.
- Enforces strict channel subscription and rate limit checks.
- Generates a compact series card with numbered 1-tap episode stream buttons.
"""

import asyncio
import io
import re
from typing import Any, Dict, List, Optional, Tuple

from pyrogram import Client, enums, filters
from pyrogram.errors import (
    ChannelPrivate,
    ChatAdminRequired,
    FloodWait,
    MessageNotModified,
    RPCError,
)
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from Thunder.bot import StreamBot
from Thunder.bot.plugins.stream import process_single, validate_request_common
from Thunder.utils.bot_utils import reply_user_err
from Thunder.utils.logger import logger
from Thunder.utils.rate_limiter import handle_rate_limited_request
from Thunder.vars import Var

LINK_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?t(?:elegram)?\.me/(?:c/(\d+)|([a-zA-Z0-9_]+))/(\d+)"
)


def parse_telegram_link(url: str) -> Optional[Tuple[Any, int]]:
    match = LINK_REGEX.search(url.strip())
    if not match:
        return None
    raw_channel_id, username, msg_id = match.groups()
    if raw_channel_id:
        chat_id: Any = int(f"-100{raw_channel_id}")
    else:
        chat_id = username
    return chat_id, int(msg_id)


def build_progress_bar(completed: int, total: int, length: int = 10) -> str:
    if total <= 0:
        return "░" * length
    fraction = min(max(completed / total, 0.0), 1.0)
    filled = int(fraction * length)
    return "▓" * filled + "░" * (length - filled)


@StreamBot.on_message(filters.command(["batch", "b"]))
async def batch_command_handler(bot: Client, msg: Message, **kwargs):
    async def _actual_batch_handler(client: Client, message: Message, **handler_kwargs):
        # 1. Common Validation (Banned, Token, Strict Force Channel Check)
        shortener_val = await validate_request_common(client, message)
        if shortener_val is None:
            return

        text = message.text.strip() if message.text else ""
        parts = text.split()

        target_chat: Any = None
        start_id: int = 0
        end_id: int = 0

        # Mode 1: Check for 2 Telegram message links in the text
        links_found = LINK_REGEX.findall(text)
        if len(links_found) >= 2:
            parsed1 = parse_telegram_link(parts[1]) if len(parts) > 1 else None
            parsed2 = parse_telegram_link(parts[2]) if len(parts) > 2 else None

            if not (parsed1 and parsed2):
                matches = list(LINK_REGEX.finditer(text))
                if len(matches) >= 2:
                    parsed1 = parse_telegram_link(matches[0].group(0))
                    parsed2 = parse_telegram_link(matches[1].group(0))

            if not (parsed1 and parsed2):
                return await reply_user_err(
                    message,
                    "⚠️ **Invalid Links!** Please provide 2 valid Telegram message links."
                )

            chat1, mid1 = parsed1
            chat2, mid2 = parsed2

            if str(chat1).lower() != str(chat2).lower():
                return await reply_user_err(
                    message,
                    "⚠️ **Error:** Both message links must belong to the **same channel or group**."
                )

            target_chat = chat1
            start_id = min(mid1, mid2)
            end_id = max(mid1, mid2)

        # Mode 2: Reply to a media message with /batch <count>
        elif message.reply_to_message:
            ref = message.reply_to_message
            target_chat = message.chat.id
            start_id = ref.id
            count = 5
            if len(parts) > 1:
                try:
                    count = int(parts[1])
                except ValueError:
                    return await reply_user_err(
                        message,
                        "⚠️ **Invalid Count:** Usage: Reply with `/batch <number>` (e.g. `/batch 8`)."
                    )

            if count < 1:
                return await reply_user_err(message, "⚠️ Batch count must be at least 1.")

            end_id = start_id + count - 1

        # Mode 3: Interactive Help / Instructions
        else:
            help_text = (
                "📦 **Batch & Series Link Generator** 📦\n\n"
                "Convert an entire season, web series, or batch of files into a **single organized card**!\n\n"
                "**How to use:**\n\n"
                "1️⃣ **Method 1: Two Message Links (Any Channel):**\n"
                "Send `/batch <start_link> <end_link>`\n"
                "*Example:*\n"
                "`/batch https://t.me/c/1234567890/10 https://t.me/c/1234567890/18`\n\n"
                "2️⃣ **Method 2: Reply to First File:**\n"
                "Reply to any video or file with `/batch <count>`\n"
                "*Example:*\n"
                "Reply with `/batch 10` to process 10 files in a row.\n\n"
                f"*(⚡ Maximum limit: {Var.MAX_BATCH_FILES} files per batch)*"
            )
            return await message.reply_text(help_text, quote=True, disable_web_page_preview=True)

        # Validate range & count
        total_requested = end_id - start_id + 1
        if total_requested > Var.MAX_BATCH_FILES:
            return await reply_user_err(
                message,
                f"⚠️ **Batch Limit Exceeded!**\n"
                f"You requested `{total_requested}` messages. The maximum allowed limit is `{Var.MAX_BATCH_FILES}` files."
            )

        status_msg = await message.reply_text(
            f"⏳ **Initializing Batch:** Fetching {total_requested} messages from `{target_chat}`...",
            quote=True
        )

        all_ids = list(range(start_id, end_id + 1))
        batch_results: List[Dict[str, Any]] = []
        failed_count = 0

        # Process in chunks of 10 to prevent message limit issues
        CHUNK_SIZE = 10
        total_chunks = (len(all_ids) + CHUNK_SIZE - 1) // CHUNK_SIZE

        for chunk_idx in range(total_chunks):
            chunk_ids = all_ids[chunk_idx * CHUNK_SIZE : (chunk_idx + 1) * CHUNK_SIZE]

            try:
                try:
                    messages = await client.get_messages(target_chat, chunk_ids)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    messages = await client.get_messages(target_chat, chunk_ids)
            except (ChannelPrivate, ChatAdminRequired):
                return await status_msg.edit_text(
                    "❌ **Access Denied:** The bot cannot access this private channel.\n"
                    "Please make sure @flashfilezbot is added to the channel as an **Administrator**!"
                )
            except Exception as e:
                logger.error(f"Error fetching batch messages: {e}", exc_info=True)
                messages = []

            if not messages:
                failed_count += len(chunk_ids)
                continue

            for m in messages:
                if m and (m.document or m.video or m.audio):
                    try:
                        links = await process_single(
                            client,
                            message,
                            m,
                            None,
                            shortener_val,
                            original_request_msg=message
                        )
                        if links:
                            batch_results.append({
                                "name": links.get("media_name", "File"),
                                "size": links.get("media_size", "N/A"),
                                "stream": links.get("stream_link", ""),
                                "online": links.get("online_link", ""),
                            })
                        else:
                            failed_count += 1
                    except Exception as e:
                        logger.error(f"Error processing batch item {m.id}: {e}", exc_info=True)
                        failed_count += 1
                else:
                    failed_count += 1

            # Update progress
            progress_pct = int(((chunk_idx + 1) / total_chunks) * 100)
            bar = build_progress_bar(chunk_idx + 1, total_chunks, length=8)
            try:
                await status_msg.edit_text(
                    f"⏳ **Processing Batch:** `{len(batch_results)}/{total_requested}` files ready\n"
                    f"`[{bar}]` {progress_pct}%"
                )
            except (MessageNotModified, FloodWait):
                pass

        if not batch_results:
            return await status_msg.edit_text(
                "❌ **Batch Empty:** No valid media files (video/audio/document) were found in the specified range."
            )

        # Build Clean Compilation Card
        total_files = len(batch_results)
        first_title = batch_results[0]["name"]

        # Clean title for collection card
        cleaned_title = re.sub(r"[._]", " ", first_title)
        if len(cleaned_title) > 35:
            cleaned_title = cleaned_title[:32] + "..."

        caption = (
            f"📦 **Batch Collection Ready!**\n\n"
            f"📂 **Collection:** `{cleaned_title}`\n"
            f"📊 **Total Files:** `{total_files}` | ✖️ **Skipped:** `{failed_count}`\n\n"
            f"⚡ **Tap an episode below to stream or download:**"
        )

        # Build Interactive Grid Buttons (3 buttons per row)
        grid_buttons = []
        row = []
        for idx, item in enumerate(batch_results, 1):
            btn_label = f"🎬 Ep {idx:02d}" if total_files > 4 else f"🎬 File {idx}"
            row.append(InlineKeyboardButton(btn_label, url=item["stream"]))
            if len(row) == 3:
                grid_buttons.append(row)
                row = []
        if row:
            grid_buttons.append(row)

        # Bottom row for first download link
        if batch_results:
            grid_buttons.append([
                InlineKeyboardButton("📥 Download File 01", url=batch_results[0]["online"])
            ])

        keyboard = InlineKeyboardMarkup(grid_buttons)

        # Edit status message into final collection card
        try:
            await status_msg.edit_text(
                caption,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Error displaying batch card: {e}", exc_info=True)
            await message.reply_text(caption, reply_markup=keyboard, quote=True)

        # If more than 5 files, send a clean text summary document of all links
        if total_files >= 5:
            links_dump = (
                f"FlashFilez Batch Stream Links\n"
                f"Collection: {cleaned_title}\n"
                f"Total Files: {total_files}\n"
                f"----------------------------------------\n\n"
            )
            for idx, item in enumerate(batch_results, 1):
                links_dump += f"{idx:02d}. {item['name']} ({item['size']})\n"
                links_dump += f"   Stream: {item['stream']}\n"
                links_dump += f"   Direct: {item['online']}\n\n"

            file_bytes = io.BytesIO(links_dump.encode("utf-8"))
            file_bytes.name = f"Batch_{total_files}_Links.txt"
            try:
                await message.reply_document(
                    document=file_bytes,
                    caption=f"📋 Complete text list for all `{total_files}` links.",
                    quote=True
                )
            except Exception as e:
                logger.warning(f"Could not send batch links file: {e}")

    await handle_rate_limited_request(bot, msg, _actual_batch_handler, **kwargs)
