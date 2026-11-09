# Thunder/utils/messages.py

# =====================================================================================
# ====== ERROR MESSAGES ======
# =====================================================================================

# ------ General Errors ------
MSG_ERROR_GENERIC = "⚠️ **Oops!** Something went wrong. Please try again. If the issue persists, contact support."
MSG_ERROR_USER_INFO = "❗ **User Not Found:** Couldn't find user. Please check the ID or Username."

# ------ User Input & Validation Errors ------
MSG_INVALID_USER_ID = "❌ **Invalid User ID:** Please provide a numeric user ID."
MSG_ERROR_START_BOT = "⚠️ You need to start the bot in private first to use this command.\n👉 [Click here]({invite_link}) to start a private chat."
MSG_ERROR_REPLY_FILE = "⚠️ Please use the /link command in reply to a file."
MSG_ERROR_NO_FILE = "⚠️ The message you're replying to does not contain any file."
MSG_ERROR_INVALID_NUMBER = "⚠️ **Invalid number specified.**"
MSG_ERROR_NUMBER_RANGE = "⚠️ **Please specify a number between 1 and {max_files}.**"
MSG_ERROR_DM_FAILED = "⚠️ I couldn't send you a Direct Message. Please start the bot first."

# ------ File & Media Errors ------
MSG_ERROR_PROCESSING_MEDIA = "⚠️ **Oops!** Something went wrong while processing your media. Please try again. If the issue persists, contact support."

# ------ Admin Action Errors (Ban, Auth, etc.) ------
MSG_AUTHORIZE_FAILED = (
    "❌ **Authorization Failed:** "
    "Could not authorize user `{user_id}`."
)
MSG_DEAUTHORIZE_FAILED = (
    "❌ **Deauthorization Failed:** "
    "User `{user_id}` was not authorized or an error occurred."
)
MSG_TOKEN_FAILED = (
    "⚠️ **Token Activation Failed!**\n\n"
    "> ❗ Reason: {reason}\n\n"
    "🔑 Please check your token or contact support."
)
MSG_SHELL_ERROR = """**❌ Shell Command Error ❌**
<pre>{error}</pre>"""

# ------ System & Bot Errors ------
MSG_ERROR_NOT_ADMIN = "⚠️ **Admin Required:** I need admin privileges to work here."
MSG_DC_INVALID_USAGE = "🤔 **Invalid Usage:** Please reply to a user's message or a media file to get DC info."
MSG_DC_ANON_ERROR = "😥 **Cannot Get Your DC Info:** Unable to identify you. This command might not work for anonymous users."
MSG_DC_FILE_ERROR = "⚙️ **Error Getting File DC Info:** Could not fetch details. File might be inaccessible."
MSG_STATS_ERROR = "❌ **Stats Error:** Could not retrieve system statistics."
MSG_STATUS_ERROR = "❌ **Status Error:** Could not retrieve system status."
MSG_DB_ERROR = "❌ **Database Error:** Could not retrieve user count."
MSG_CRITICAL_ERROR = (
    "🚨 **Critical Media Processing Error** 🚨\n\n"
    "> ⚠️ Details:\n```\n{error}\n```\n\n"
    "Please investigate immediately! (ID: {error_id})"
)

# =====================================================================================
# ====== ADMIN MESSAGES ======
# =====================================================================================

# ------ Ban/Unban ------
MSG_DECORATOR_BANNED = "You are currently banned and cannot use this bot.\nReason: {reason}\nBanned on: {ban_time}"
MSG_BAN_USAGE = "⚠️ **Usage:** /ban [user_id] [reason]"
MSG_CANNOT_BAN_OWNER = "❌ **Cannot ban an owner.**"
MSG_ADMIN_USER_BANNED = "✅ **User {user_id} has been banned."
MSG_BAN_REASON_SUFFIX = "\n📝 **Reason:** {reason}"
MSG_ADMIN_NO_BAN_REASON = "No reason provided"
MSG_USER_BANNED_NOTIFICATION = "🚫 **You have been banned from using this bot.**"
MSG_UNBAN_USAGE = "⚠️ **Usage:** /unban <user_id>"
MSG_ADMIN_USER_UNBANNED = "✅ **User {user_id} has been unbanned."
MSG_USER_UNBANNED_NOTIFICATION = "🎉 **You have been unbanned from using this bot.**"
MSG_USER_NOT_IN_BAN_LIST = "ℹ️ **User {user_id} was not found in the ban list."
MSG_CHANNEL_BANNED = "✅ **Channel {channel_id} has been banned.**"
MSG_CHANNEL_BANNED_REASON_SUFFIX = "\n📝 **Reason:** {reason}"
MSG_CHANNEL_UNBANNED = "✅ **Channel {channel_id} has been unbanned.**"
MSG_CHANNEL_NOT_BANNED = "ℹ️ **Channel {channel_id} was not found in the ban list.**"

# ------ Token & Authorization ------
MSG_AUTHORIZE_USAGE = "🔑 **Usage:** `/authorize <user_id>`"
MSG_DEAUTHORIZE_USAGE = "🔒 **Usage:** `/deauthorize <user_id>`"
MSG_AUTHORIZE_SUCCESS = (
    "✅ **User Authorized!**\n\n"
    "> 👤 User ID: `{user_id}`\n"
    "> 🔑 Access: Permanent"
)
MSG_DEAUTHORIZE_SUCCESS = (
    "✅ **User Deauthorized!**\n\n"
    "> 👤 User ID: `{user_id}`\n"
    "> 🔒 Access: Revoked"
)
MSG_TOKEN_ACTIVATED = "✅ Token successfully activated!\n\n⏳ This token is valid for {duration_hours} hours."
MSG_TOKEN_INVALID = "🚫 **Expired or Invalid Token.** Please click the button below to activate your access token."
MSG_NO_AUTH_USERS = "ℹ️ **No Authorized Users Found:** The list is currently empty."
MSG_AUTH_USER_INFO = """{i}. 👤: {display_name}
   • User ID: `{user_id}`
   • Authorized by: `{authorized_by}`
   • Date: `{auth_time}`\n\n"""
MSG_ADMIN_AUTH_LIST_HEADER = "🔐 **Authorized Users List**\n\n"

# ------ Shell Commands ------
MSG_SHELL_USAGE = (
    "<b>Usage:</b>\n"
    "/shell <command>\n\n"
    "<b>Example:</b>\n"
    "/shell ls -l"
)
MSG_SHELL_EXECUTING = "Executing Command... ⚙️\n<pre>{command}</pre>"
MSG_SHELL_OUTPUT = """**Shell Command Output:**
<pre>{output}</pre>"""
MSG_SHELL_OUTPUT_STDOUT = "<b>[stdout]:</b>\n<pre>{output}</pre>"
MSG_SHELL_OUTPUT_STDERR = "<b>[stderr]:</b>\n<pre>{error}</pre>"
MSG_SHELL_NO_OUTPUT = "✅ <b>Command Executed:</b> No output."

# ------ Admin View & Control ------

MSG_WORKLOAD_ITEM = "   {bot_name}: {load}\n"
MSG_ADMIN_RESTART_DONE = "✅ **Restart Successful!**"
MSG_RESTARTING = "♻️ **Updating and Restarting Bot...**\n\n> ⏳ Please wait a moment."
MSG_LOG_FILE_CAPTION = "📄 **System Logs**"

MSG_LOG_FILE_EMPTY = "ℹ️ **Log File Empty:** No data found in the log file."
MSG_LOG_FILE_MISSING = "⚠️ **Log File Missing:** Could not find the log file."

# =====================================================================================
# ====== BUTTON TEXTS (User-facing) ======
# =====================================================================================

MSG_BUTTON_STREAM_NOW = "▶️ Stream Online"
MSG_BUTTON_DOWNLOAD = "📥 Fast Download"
MSG_BUTTON_GET_HELP = "📖 Get Help"
MSG_BUTTON_CANCEL_BROADCAST = "🛑 Cancel Broadcast"
MSG_BUTTON_VIEW_PROFILE = "👤 View User Profile"
MSG_BUTTON_ABOUT = "ℹ️ About Bot"
MSG_BUTTON_JOIN_CHANNEL = "📢 Join {channel_title}"
MSG_BUTTON_GITHUB = "🛠️ GitHub"
MSG_BUTTON_START_CHAT = "📩 Start Chat"
MSG_BUTTON_CLOSE = "✖ Close"


# =====================================================================================
# ====== COMMAND RESPONSES (User-facing) ======
# =====================================================================================

MSG_WELCOME = (
    "👋 **Welcome, {user_name}!**\n\n"
    "I'm **FlashFile** ⚡\n"
    "I convert your Telegram files into direct high-speed download links (for Chrome, IDM, or any browser) and provide instant 4K streaming.\n\n"
    "**How to use:**\n"
    "> 1. Send or forward any file to me to get instant download & stream links.\n"
    "> 2. In groups, reply to a file with `/link`.\n\n"
    "📢 **Updates Channel:** @flashfilez\n"
    "🛠️ **Developer:** @JishnuPG-tech\n\n"
    "» Use `/help` for all commands & pro tips.\n\n"
    "Send or forward a file to begin!"
)

MSG_HELP = (
    "📖 **FlashFile Help Guide**\n\n"
    "Convert any Telegram file into a direct high-speed download link for Chrome or any browser, with instant 4K streaming:\n\n"
    "**Private Chat:**\n"
    "> 1. Send or forward **any file** (document, video, audio, zip, photo up to 4 GB).\n"
    "> 2. I'll instantly reply with your high-speed direct download link & stream link!\n\n"
    "**Using in Groups:**\n"
    "> • Reply to any file with `/link`.\n"
    "> • **Batch Mode:** Reply to the **first** file with `/link <number>` (e.g., `/link 5` up to {max_files} files).\n"
    "> • Bot needs administrator rights in the group to function.\n\n"
    "**Channel & Developer:**\n"
    "> • Updates Channel: https://t.me/flashfilez\n"
    "> • Developer GitHub: https://github.com/JishnuPG-tech\n\n"
    "**Available Commands:**\n"
    "> `/start` - Welcome message & quick start information.\n"
    "> `/help` - Shows this help message.\n"
    "> `/link <num>` - (Groups) Generate direct links.\n"
    "> `/about` - Learn about FlashFile features and updates.\n"
    "> `/ping` - Check responsiveness and online status.\n"
    "> `/dc` - View Telegram DC datacenter information.\n\n"
    "**Pro Tips:**\n"
    "> • Paste the download link into Chrome, Brave, IDM, or 1DM for max speed multi-threaded downloads.\n"
    "> • All direct links support 100% pause and resume via HTTP 206.\n"
    "> • Tap 'Stream Online' to watch immediately in VLC or MX Player without saving to phone storage."
)

MSG_ABOUT = (
    "⚡ **About FlashFile**\n\n"
    "FlashFile converts any Telegram file into a direct high-speed HTTP link for Chrome, IDM, or any browser, plus instant 4K streaming in VLC and MX Player.\n\n"
    "**Key Capabilities:**\n"
    "> 📥 **1-Click Browser Downloads:** Full wire-speed download on Chrome, Brave, IDM, and 1DM.\n"
    "> ▶️ **Instant 4K Streaming:** Watch directly in VLC, MX Player, or built-in web cinema.\n"
    "> ⚡ **HTTP 206 Resumption:** 100% pause & resume if connection drops.\n"
    "> 📁 **Universal File Support:** MKV, MP4, documents, zip archives, and lossless audio up to 4 GB.\n"
    "> ☁️ **RAM Direct Stream:** Zero phone storage used for temporary video files.\n\n"
    "**Project Links:**\n"
    "> 📢 Channel: https://t.me/flashfilez\n"
    "> 🛠️ Developer: https://github.com/JishnuPG-tech\n"
    "> 🤖 Bot: @flashfilezbot\n\n"
    "Share @flashfilezbot with friends for lightning-fast downloads!"
)

# ------ Ping ------
MSG_PING_START = "🛰️ **Pinging...** Please wait."
MSG_PING_RESPONSE = (
    "⚡ **Pong! Bot is Online!**\n\n"
    "> ⏱️ **Ping:** {time_taken_ms:.2f} ms\n"
    "> 🤖 **Bot Status:** `Active`"
)

# ------ DC Info ------
MSG_DC_USER_INFO = (
    "📍 **Information**\n"
    "> 👤 **User:** [{user_name}](tg://user?id={user_id})\n"
    "> 🆔 **User ID:** `{user_id}`\n"
    "> 🌍 **DC ID:** `{dc_id}`"
)

MSG_DC_FILE_INFO = (
    "🗂️ **File Information**\n"
    ">`{file_name}`\n"
    "💾 **File Size:** `{file_size}`\n"
    "📁 **File Type:** `{file_type}`\n"
    "🌍 **DC ID:** `{dc_id}`"
)

MSG_DC_UNKNOWN = "Unknown"

# ------ File Link Generation ------
MSG_DM_SINGLE_PREFIX = "📬 **From {chat_title}**\n"
MSG_LINKS = (
    "⚡ **FlashFile**\n\n"
    "> **File:** `{file_name}`\n"
    "> **Size:** `{file_size}`\n\n"
    "🔗 **Direct Download Link:**\n"
    "`{download_link}`\n\n"
    "▶️ **Instant Stream Link:**\n"
    "`{stream_link}`\n\n"
    "• High-Speed Resumable • Chrome, IDM & VLC Ready\n"
    "• Powered by @flashfilezbot"
)

# =====================================================================================
# ====== USER NOTIFICATIONS ======
# =====================================================================================

MSG_NEW_USER = (
    "👤 **New User Alert**\n"
    "> 👤 **Name:** [{first_name}](tg://user?id={user_id})\n"
    "> 🆔 **User ID:** `{user_id}`\n\n"
)
MSG_COMMUNITY_CHANNEL = "📢 **{channel_title}:** 🔒 Join this channel to use the bot."

# =====================================================================================
# ====== PROCESSING MESSAGES ======
# =====================================================================================

# ------ General File Processing ------
MSG_PROCESSING_REQUEST = "⏳ **Processing your request...**"
MSG_PROCESSING_FILE = "⏳ **Processing your file...**"
MSG_NEW_FILE_REQUEST = (
    "> 👤 **Source:** [{source_info}](tg://user?id={id_})\n"
    "> 🆔 **ID:** `{id_}`\n\n"
    "🚀 **Download:** `{online_link}`\n\n"
    "🖥️ **Stream:** `{stream_link}`"
)

# ------ Batch Processing ------
MSG_PROCESSING_BATCH = "♻️ **Processing Batch {batch_number}/{total_batches}** ({file_count} files)"
MSG_PROCESSING_STATUS = "📊 **Processing Files:** {processed}/{total} complete, {failed} failed"
MSG_BATCH_LINKS_READY = "🔗 Here are your {count} download links:"
MSG_DM_BATCH_PREFIX = "📬 **Batch Links from {chat_title}**\n"
MSG_PROCESSING_RESULT = "✅ **Process Complete:** {processed}/{total} files processed successfully, {failed} failed"

# =====================================================================================
# ====== BROADCAST MESSAGES ======
# =====================================================================================

MSG_BROADCAST_START = "📣 **Starting Broadcast...**\n\n> ⏳ Please wait for completion."
MSG_BROADCAST_COMPLETE = (
    "📢 **Broadcast Completed Successfully!** 📢\n\n"
    "⏱️ **Duration:** `{elapsed_time}`\n"
    "👥 **Total Users:** `{total_users}`\n"
    "✅ **Successful Deliveries:** `{successes}`\n"
    "❌ **Failed Deliveries:** `{failures}`\n"
    "🗑️ **Accounts Removed (Blocked/Deactivated):** `{deleted_accounts}`\n"
)
MSG_BROADCAST_CANCEL = "🛑 **Cancelling Broadcast:** `{broadcast_id}`\n\n> ⏳ Stopping operations..."
MSG_INVALID_BROADCAST_CMD = "Please reply to the message you want to broadcast."
MSG_BROADCAST_USAGE = (
    "📣 **Broadcast Command Usage:**\n\n"
    "`/broadcast` - Broadcast to all users\n"
    "`/broadcast authorized` - Broadcast to authorized users only\n"
    "`/broadcast regular` - Broadcast to regular (non-authorized) users only\n\n"
    "**Note:** Reply to the message you want to broadcast."
)

# =====================================================================================
# ====== PERMISSION MESSAGES ======
# =====================================================================================

MSG_ERROR_UNAUTHORIZED = "You are not authorized to view this information."
MSG_ERROR_BROADCAST_RESTART = "Please use the /broadcast command to start a new broadcast."
MSG_ERROR_BROADCAST_INSTRUCTION = "To start a new broadcast, use the /broadcast command and reply to the message you want to broadcast."
MSG_ERROR_CALLBACK_UNSUPPORTED = "This button is not active or no longer supported."

# =====================================================================================
# ====== RATE LIMITING MESSAGES ======
# =====================================================================================

MSG_RATE_LIMIT_QUEUE_PRIORITY = (
    "⚡ You're in the **Priority Queue!**\n\n"
    "> ⏳ **Estimated Wait:** `~{wait_estimate} minute{s}`\n"
    "> 🚀 **Status:** In Queue"
)

MSG_RATE_LIMIT_QUEUE_REGULAR = (
    "⏳ **Rate Limit Reached!**\n\n"
    "> ⌛ **Estimated Wait:** `~{wait_estimate} minute{s1}`\n"
    "> 📊 **Limit:** `{max_requests} files per {time_window} minute{s2}`\n"
    "> 🔄 **Status:** In Queue"
)

MSG_RATE_LIMIT_QUEUE_FULL = (
    "⚠️ **Service Busy!** The processing queue is currently full.\n\n"
    "> 🕒 **Please try again in:** `~{wait_estimate} minute{s}`\n"
    "> 💡 **Tip:** Try again later when system load decreases"
)


# =====================================================================================
# ====== FILE TYPE DESCRIPTIONS ======
# =====================================================================================
MSG_FILE_TYPE_DOCUMENT = "📄 Document"
MSG_FILE_TYPE_PHOTO = "🖼️ Photo"
MSG_FILE_TYPE_VIDEO = "🎬 Video"
MSG_FILE_TYPE_AUDIO = "🎵 Audio"
MSG_FILE_TYPE_VOICE = "🎤 Voice Message"
MSG_FILE_TYPE_STICKER = "🎨 Sticker"
MSG_FILE_TYPE_ANIMATION = "🎞️ Animation (GIF)"
MSG_FILE_TYPE_VIDEO_NOTE = "📹 Video Note"
MSG_FILE_TYPE_UNKNOWN = "❓ Unknown File Type"

# =====================================================================================
# ====== SYSTEM & STATUS MESSAGES ======
# =====================================================================================

MSG_SYSTEM_STATUS = (
    "✅ **System Status:** Operational\n\n"
    "> 🕒 **Uptime:** `{uptime}`\n"
    "> 🤖 **Bot Instances:** `{active_bots}`\n"
    "> 📊 **Total Workload:** `{total_workload}`\n\n"
    "📜 **Workload Distribution:**\n\n"
    "{workload_items}\n"
    "> ♻️ **Version:** `{version}`"
)

# ------ Speedtest Messages ------
MSG_SPEEDTEST_INIT = "🚀 **Running Speed Test...**"
MSG_SPEEDTEST_ERROR = "❌ **Speed Test Failed!**\n\n> Unable to complete the speed test. Please try again later."
MSG_SPEEDTEST_RESULT = (
    "⚡ **Speed Test Results**\n\n"
    "**SPEEDTEST INFO:**\n"
    "> **Download:** `{download_mbps} Mbps` (`{download_bps}/s`)\n"
    "> **Upload:** `{upload_mbps} Mbps` (`{upload_bps}/s`)\n"
    "> **Ping:** `{ping} ms`\n"
    "> **Timestamp:** `{timestamp}`\n"
    "> **Data Sent:** `{bytes_sent}`\n"
    "> **Data Received:** `{bytes_received}`\n\n"
    "**SERVER INFO:**\n"
    "> **Name:** `{server_name}`\n"
    "> **Country:** `{server_country}`\n"
    "> **Sponsor:** `{server_sponsor}`\n"
    "> **Latency:** `{server_latency} ms`\n"
    "> **Coordinates:** `{server_lat}, {server_lon}`\n\n"
    "**CLIENT DETAILS:**\n"
    "> **IP:** `{client_ip}`\n"
    "> **Coordinates:** `{client_lat}, {client_lon}`\n"
    "> **ISP:** `{client_isp}`\n"
    "> **ISP Rating:** `{client_isprating}`\n"
    "> **Country:** `{client_country}`"
)
MSG_SYSTEM_STATS = (
    "📊 **System Statistics**\n\n"
    "> System Uptime: {sys_uptime}\n"
    "> Bot Uptime: {bot_uptime}\n\n"
    "⚙️ **Performance:**\n"
    "> CPU: {cpu_percent}%\n"
    "> CPU Core: {cpu_cores}\n"
    "> Frequency: {cpu_freq} GHz\n\n"
    "💾 **RAM**\n"
    "> Total: {ram_total}\n"
    "> Used: {ram_used}\n"
    "> Free: {ram_free}\n\n"
    "💽 **Storage:**\n"
    "> Disk: `{disk_percent}%`\n"
    "> Total: `{total}`\n"
    "> Used: `{used}`\n"
    "> Free: `{free}`\n\n"
    "📶 **Network:**\n"
    "> 🔺 Upload: `{upload}`\n"
    "> 🔻 Download: `{download}`\n"
)

MSG_DB_STATS = "📊 **Database Statistics**\n\n> 👥 **Total Users:** `{total_users}`"

# Payment & Subscription Messages
MSG_SUB_PLAN_ACTIVE = (
    "👑 **FlashFile Premium Active**\n\n"
    "👤 **Account:** `{user_name}` (`{user_id}`)\n"
    "📅 **Valid Until:** `{expiry_date}`\n"
    "⏳ **Remaining:** `{remaining_days} days`\n"
    "⚡ **Tier:** `30-Day Monthly Pass (Unlimited)`\n\n"
    "✨ You have unlimited streaming & high-speed direct downloads!"
)

MSG_SUB_PLAN_FREE = (
    "⚡ **FlashFile Premium Access**\n\n"
    "Unlock unlimited ultra-fast streaming & direct download links:\n\n"
    "💳 **Monthly Pass:** `₹{price} / 30 Days`\n"
    "✨ Unlimited high-speed streaming links\n"
    "⚡ Pure Google Pay UPI integration\n"
    "📱 Compatible with VLC, MX Player, and Web\n"
    "🎟 Optional 1-time file passes available\n\n"
    "🔗 **UPI ID:** `{upi_id}`"
)

MSG_PAYWALL_GATE = (
    "🔒 **FlashFile Premium Access Required**\n\n"
    "Direct streaming links for this bot require an active pass:\n\n"
    "💎 **Monthly Pass:** `₹{price} / 30 Days` (Unlimited)\n"
    "🎟 **1-Time Pass:** Request temporary access for this file\n\n"
    "📲 **Pay via UPI:** `{upi_id}`\n"
    "*(Supports Google Pay, PhonePe, Paytm, BHIM)*"
)

MSG_PROOF_INSTRUCTION = (
    "📩 **Submit Payment Proof**\n\n"
    "Please send your **Transaction ID / UTR Number** or reply to this message with a **screenshot of your payment**.\n\n"
    "Admin will verify and activate your pass within minutes."
)

MSG_SUB_APPROVED_USER = (
    "🎉 **Subscription Activated!**\n\n"
    "Your **30-Day Monthly Pass** is now active!\n"
    "📅 **Valid Until:** `{expiry_date}`\n\n"
    "You can now send any video or document to generate instant stream and download links. Enjoy!"
)

MSG_TEMP_APPROVED_USER = (
    "🎟 **Temporary Stream Pass Approved!**\n\n"
    "You have been granted a **1-time temporary stream pass** (valid for 24 hours).\n\n"
    "Send or forward your file again to generate your link!"
)

MSG_SUB_REJECTED_USER = (
    "❌ **Access Request Not Approved**\n\n"
    "Your payment proof or pass request could not be verified by admin.\n"
    "If this is an error or you need help, please reach out to admin."
)
