# Thunder/bot/plugins/subscription.py

import asyncio
import datetime
import urllib.parse
from typing import Optional

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup, Message)

from Thunder.bot import StreamBot
from Thunder.utils.database import db
from Thunder.utils.logger import logger
from Thunder.utils.messages import (
    MSG_PROOF_INSTRUCTION, MSG_SUB_APPROVED_USER, MSG_SUB_PLAN_ACTIVE,
    MSG_SUB_PLAN_FREE, MSG_SUB_REJECTED_USER, MSG_TEMP_APPROVED_USER
)
from Thunder.vars import Var

# In-memory set of users currently prompted to submit payment proof
awaiting_proof = set()


def get_upi_link(user_id: int) -> str:
    note = f"FlashFile_Sub_{user_id}"
    params = {
        "pa": Var.UPI_ID,
        "pn": Var.UPI_NAME,
        "am": str(Var.SUB_PRICE),
        "cu": "INR",
        "tn": note
    }
    return f"upi://pay?{urllib.parse.urlencode(params)}"


def get_plan_keyboard(user_id: int, file_id: Optional[str] = None) -> InlineKeyboardMarkup:
    upi_link = get_upi_link(user_id)
    buttons = [
        [
            InlineKeyboardButton(f"💳 Pay ₹{Var.SUB_PRICE} via UPI", url=upi_link)
        ],
        [
            InlineKeyboardButton("📩 Submit Payment Proof", callback_data=f"proof_{user_id}")
        ]
    ]
    if file_id:
        buttons.append([
            InlineKeyboardButton("🎟 Request 1-Time Stream Pass", callback_data=f"req_temp_{user_id}_{file_id}")
        ])
    buttons.append([
        InlineKeyboardButton("❌ Close", callback_data="close_sub")
    ])
    return InlineKeyboardMarkup(buttons)


@StreamBot.on_message(filters.command(["plan", "buy", "sub"]) & filters.private)
async def plan_command_handler(client: Client, message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "User"

    if not Var.PAYMENT_ENABLED:
        await message.reply_text(
            "⚡ **Flash File Service Status**\n\n"
            "All streaming and download links are currently **100% Free**!\n"
            "No active subscription or payment is required.",
            quote=True
        )
        return

    sub = await db.get_subscription(user_id)
    now = datetime.datetime.now(datetime.timezone.utc)

    if sub and sub.get("status") == "active" and sub.get("expires_at") and sub["expires_at"] > now:
        expires = sub["expires_at"]
        remaining = max(1, (expires - now).days)
        text = MSG_SUB_PLAN_ACTIVE.format(
            user_name=user_name,
            user_id=user_id,
            expiry_date=expires.strftime("%Y-%m-%d %H:%M UTC"),
            remaining_days=remaining
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Extend Subscription (₹10)", callback_data=f"sub_pay_{user_id}")],
            [InlineKeyboardButton("❌ Close", callback_data="close_sub")]
        ])
    else:
        text = MSG_SUB_PLAN_FREE.format(
            price=Var.SUB_PRICE,
            upi_id=Var.UPI_ID
        )
        keyboard = get_plan_keyboard(user_id)

    await message.reply_text(text, reply_markup=keyboard, quote=True)


@StreamBot.on_message(filters.command("addsub") & filters.private)
async def addsub_command_handler(client: Client, message: Message):
    sender_id = message.from_user.id
    is_owner = sender_id == Var.OWNER_ID
    is_admin = hasattr(Var, "ADMINS") and sender_id in Var.ADMINS

    if not (is_owner or is_admin):
        return

    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.reply_text("Usage: `/addsub <user_id> [days]`", quote=True)
        return

    try:
        target_id = int(parts[1])
        days = int(parts[2]) if len(parts) > 2 else Var.SUB_DURATION_DAYS
    except ValueError:
        await message.reply_text("Invalid user ID or days number.", quote=True)
        return

    doc = await db.add_subscription(target_id, days=days, plan="admin_granted")
    expiry = doc["expires_at"].strftime("%Y-%m-%d %H:%M UTC")

    await message.reply_text(
        f"✅ Subscription granted to `{target_id}` for {days} days.\n"
        f"Valid until: `{expiry}`",
        quote=True
    )

    try:
        await client.send_message(
            target_id,
            MSG_SUB_APPROVED_USER.format(expiry_date=expiry)
        )
    except Exception as e:
        logger.warning(f"Could not notify user {target_id} of granted subscription: {e}")


@StreamBot.on_message(filters.command("remsub") & filters.private)
async def remsub_command_handler(client: Client, message: Message):
    sender_id = message.from_user.id
    is_owner = sender_id == Var.OWNER_ID
    is_admin = hasattr(Var, "ADMINS") and sender_id in Var.ADMINS

    if not (is_owner or is_admin):
        return

    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.reply_text("Usage: `/remsub <user_id>`", quote=True)
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.reply_text("Invalid user ID.", quote=True)
        return

    success = await db.remove_subscription(target_id)
    if success:
        await message.reply_text(f"✅ Subscription revoked for `{target_id}`.", quote=True)
    else:
        await message.reply_text(f"Could not revoke or no active subscription found for `{target_id}`.", quote=True)


@StreamBot.on_message(filters.command("subscribers") & filters.private)
async def subscribers_command_handler(client: Client, message: Message):
    sender_id = message.from_user.id
    is_owner = sender_id == Var.OWNER_ID
    is_admin = hasattr(Var, "ADMINS") and sender_id in Var.ADMINS

    if not (is_owner or is_admin):
        return

    count = await db.get_active_subscribers_count()
    subscribers = await db.get_all_subscribers(limit=25)

    text = f"👑 **Active Subscribers:** `{count}`\n\n"
    if subscribers:
        for idx, sub in enumerate(subscribers, 1):
            exp = sub["expires_at"].strftime("%Y-%m-%d")
            text += f"{idx}. `{sub['user_id']}` — Expiry: `{exp}` ({sub.get('plan', 'monthly')})\n"
    else:
        text += "No active subscribers found."

    await message.reply_text(text, quote=True)


@StreamBot.on_callback_query(filters.regex(r"^close_sub$"))
async def close_sub_callback(client: Client, query: CallbackQuery):
    await query.answer()
    try:
        await query.message.delete()
    except Exception:
        pass


@StreamBot.on_callback_query(filters.regex(r"^sub_pay_(\d+)$"))
async def sub_pay_callback(client: Client, query: CallbackQuery):
    user_id = int(query.matches[0].group(1))
    upi_link = get_upi_link(user_id)
    text = (
        "💳 **Pay ₹10 via UPI**\n\n"
        f"**UPI ID:** `{Var.UPI_ID}`\n"
        f"**Name:** `{Var.UPI_NAME}`\n"
        f"**Amount:** `₹{Var.SUB_PRICE}`\n\n"
        "Click the button below to launch Google Pay / PhonePe / Paytm / BHIM directly:"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🚀 Open UPI App (₹{Var.SUB_PRICE})", url=upi_link)],
        [InlineKeyboardButton("📩 Submit Proof / Tx ID", callback_data=f"proof_{user_id}")],
        [InlineKeyboardButton("⬅️ Back", callback_data=f"plan_info_{user_id}")]
    ])
    await query.answer()
    try:
        await query.message.edit_text(text, reply_markup=keyboard)
    except MessageNotModified:
        pass


@StreamBot.on_callback_query(filters.regex(r"^plan_info_(\d+)$"))
async def plan_info_callback(client: Client, query: CallbackQuery):
    user_id = int(query.matches[0].group(1))
    text = MSG_SUB_PLAN_FREE.format(price=Var.SUB_PRICE, upi_id=Var.UPI_ID)
    keyboard = get_plan_keyboard(user_id)
    await query.answer()
    try:
        await query.message.edit_text(text, reply_markup=keyboard)
    except MessageNotModified:
        pass


@StreamBot.on_callback_query(filters.regex(r"^proof_(\d+)$"))
async def proof_callback(client: Client, query: CallbackQuery):
    user_id = int(query.matches[0].group(1))
    awaiting_proof.add(user_id)
    await query.answer("Please send your payment screenshot or UTR number.", show_alert=True)
    await query.message.reply_text(MSG_PROOF_INSTRUCTION, quote=True)


@StreamBot.on_callback_query(filters.regex(r"^req_temp_(\d+)_(.+)$"))
async def req_temp_callback(client: Client, query: CallbackQuery):
    user_id = int(query.matches[0].group(1))
    file_id = query.matches[0].group(2)
    user_name = query.from_user.first_name or "User"

    await query.answer("Submitting temporary stream pass request to admin...", show_alert=False)

    req_id = await db.create_sub_request(
        user_id=user_id,
        user_name=user_name,
        req_type="temp_pass",
        file_id=file_id
    )

    admin_target = Var.ADMIN_CHANNEL or Var.OWNER_ID
    if admin_target:
        admin_card = (
            "🎟 **New 1-Time Stream Pass Request**\n\n"
            f"👤 **User:** {user_name} (`{user_id}`)\n"
            f"📄 **File Unique ID:** `{file_id}`\n"
            f"🆔 **Request ID:** `{req_id}`\n\n"
            "Choose action below:"
        )
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎟 Approve Temp Pass (24h)", callback_data=f"approve_temp_{req_id}"),
                InlineKeyboardButton("👑 Approve 30-Day Sub", callback_data=f"approve_sub_{req_id}")
            ],
            [
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_sub_{req_id}")
            ]
        ])
        try:
            await client.send_message(admin_target, admin_card, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Failed to notify admin target {admin_target} of temp pass request: {e}")

    await query.message.reply_text(
        "⏳ **Request Submitted!**\n\n"
        "Your temporary pass request has been sent to the admin team for approval. "
        "You will receive a notification as soon as it is reviewed.",
        quote=True
    )


@StreamBot.on_callback_query(filters.regex(r"^approve_sub_([a-f0-9]+)$"))
async def approve_sub_callback(client: Client, query: CallbackQuery):
    admin_id = query.from_user.id
    if not (admin_id == Var.OWNER_ID or (hasattr(Var, "ADMINS") and admin_id in Var.ADMINS)):
        await query.answer("Unauthorized", show_alert=True)
        return

    req_id = query.matches[0].group(1)
    req = await db.get_sub_request(req_id)
    if not req or req.get("status") != "pending":
        await query.answer("This request has already been processed.", show_alert=True)
        return

    user_id = req["user_id"]
    doc = await db.add_subscription(user_id, days=Var.SUB_DURATION_DAYS, tx_ref=req.get("tx_ref", ""))
    await db.update_sub_request_status(req_id, "approved_sub", admin_id)

    admin_name = query.from_user.first_name or "Admin"
    expiry = doc["expires_at"].strftime("%Y-%m-%d %H:%M UTC")

    await query.answer("30-Day Monthly Subscription Approved!", show_alert=True)
    try:
        await query.message.edit_text(
            f"{query.message.text}\n\n"
            f"✅ **APPROVED (30-Day Plan)** by {admin_name} on {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M')}"
        )
    except MessageNotModified:
        pass

    try:
        await client.send_message(
            user_id,
            MSG_SUB_APPROVED_USER.format(expiry_date=expiry)
        )
    except Exception as e:
        logger.warning(f"Could not notify user {user_id} of approved subscription: {e}")


@StreamBot.on_callback_query(filters.regex(r"^approve_temp_([a-f0-9]+)$"))
async def approve_temp_callback(client: Client, query: CallbackQuery):
    admin_id = query.from_user.id
    if not (admin_id == Var.OWNER_ID or (hasattr(Var, "ADMINS") and admin_id in Var.ADMINS)):
        await query.answer("Unauthorized", show_alert=True)
        return

    req_id = query.matches[0].group(1)
    req = await db.get_sub_request(req_id)
    if not req or req.get("status") != "pending":
        await query.answer("This request has already been processed.", show_alert=True)
        return

    user_id = req["user_id"]
    file_id = req.get("file_id") or "any"
    await db.add_temp_pass(user_id, file_id, hours=24)
    await db.update_sub_request_status(req_id, "approved_temp", admin_id)

    admin_name = query.from_user.first_name or "Admin"

    await query.answer("1-Time Temporary Stream Pass Approved!", show_alert=True)
    try:
        await query.message.edit_text(
            f"{query.message.text}\n\n"
            f"🎟 **APPROVED (1-Time Pass)** by {admin_name} on {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M')}"
        )
    except MessageNotModified:
        pass

    try:
        await client.send_message(
            user_id,
            MSG_TEMP_APPROVED_USER
        )
    except Exception as e:
        logger.warning(f"Could not notify user {user_id} of approved temp pass: {e}")


@StreamBot.on_callback_query(filters.regex(r"^reject_sub_([a-f0-9]+)$"))
async def reject_sub_callback(client: Client, query: CallbackQuery):
    admin_id = query.from_user.id
    if not (admin_id == Var.OWNER_ID or (hasattr(Var, "ADMINS") and admin_id in Var.ADMINS)):
        await query.answer("Unauthorized", show_alert=True)
        return

    req_id = query.matches[0].group(1)
    req = await db.get_sub_request(req_id)
    if not req or req.get("status") != "pending":
        await query.answer("This request has already been processed.", show_alert=True)
        return

    user_id = req["user_id"]
    await db.update_sub_request_status(req_id, "rejected", admin_id)

    admin_name = query.from_user.first_name or "Admin"
    await query.answer("Request Rejected.", show_alert=True)
    try:
        await query.message.edit_text(
            f"{query.message.text}\n\n"
            f"❌ **REJECTED** by {admin_name} on {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M')}"
        )
    except MessageNotModified:
        pass

    try:
        await client.send_message(
            user_id,
            MSG_SUB_REJECTED_USER
        )
    except Exception as e:
        logger.warning(f"Could not notify user {user_id} of rejected request: {e}")


@StreamBot.on_message(filters.private & (filters.photo | filters.document | filters.text) & ~filters.command(["start", "help", "about", "plan", "buy", "sub"]))
async def proof_receiver_handler(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return

    # Check if user is actively awaiting proof or if message looks like a payment proof
    has_text_utr = False
    tx_ref = ""
    if message.text:
        text = message.text.strip()
        # Common UTR / UPI transaction references (12 digits or words like UPI, UTR, ref)
        if len(text) >= 8 and (text.isdigit() or any(k in text.lower() for k in ["utr", "upi", "txn", "ref", "paid"])):
            has_text_utr = True
            tx_ref = text

    is_photo_proof = bool(message.photo or (message.document and message.document.mime_type and "image" in message.document.mime_type))

    if user_id not in awaiting_proof and not (has_text_utr and len(tx_ref) == 12 and tx_ref.isdigit()):
        return

    awaiting_proof.discard(user_id)
    user_name = message.from_user.first_name or "User"

    photo_file_id = message.photo.file_id if message.photo else (message.document.file_id if message.document else None)
    caption_text = message.caption or tx_ref or "Payment Proof attached"

    req_id = await db.create_sub_request(
        user_id=user_id,
        user_name=user_name,
        req_type="monthly_proof",
        tx_ref=caption_text,
        proof_file_id=photo_file_id
    )

    admin_target = Var.ADMIN_CHANNEL or Var.OWNER_ID
    if admin_target:
        card_text = (
            "💰 **New Payment Proof Received**\n\n"
            f"👤 **User:** {user_name} (`{user_id}`)\n"
            f"📝 **Ref / Note:** `{caption_text}`\n"
            f"🆔 **Request ID:** `{req_id}`\n\n"
            "Review payment and choose action:"
        )
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Approve 30-Day Sub", callback_data=f"approve_sub_{req_id}"),
                InlineKeyboardButton("🎟 Approve Temp Pass", callback_data=f"approve_temp_{req_id}")
            ],
            [
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_sub_{req_id}")
            ]
        ])

        try:
            if photo_file_id:
                await client.send_photo(
                    admin_target,
                    photo=photo_file_id,
                    caption=card_text,
                    reply_markup=keyboard
                )
            else:
                await client.send_message(
                    admin_target,
                    card_text,
                    reply_markup=keyboard
                )
        except Exception as e:
            logger.error(f"Failed to forward proof to admin {admin_target}: {e}")

    await message.reply_text(
        "✅ **Payment Proof Received!**\n\n"
        "Your transaction has been submitted to admin for verification.\n"
        "Your pass will be activated as soon as it is confirmed.",
        quote=True
    )
