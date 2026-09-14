import os
import time
import logging
import asyncio
import json
import aiohttp
import subprocess
import gdown
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import UserNotParticipant
import yt_dlp
from aiohttp import web

# Logging Setup
logging.basicConfig(level=logging.INFO)

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Channel IDs
DATABASE_CHANNEL_ID = int(os.environ.get("DATABASE_CHANNEL_ID", "-1004396122384"))
LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", "-1004441596603"))

# ബോട്ട് പ്രവർത്തിക്കാൻ അനുവാദമുള്ള ഒരേയൊരു ഗ്രൂപ്പിന്റെ ID മാത്രം ഇവിടെ നൽകുക
ALLOWED_GROUP_ID = int(os.environ.get("ALLOWED_GROUP_ID", "0"))

# Force Subscribe Channel/Group ID or Username
FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", "-100XXXXXXXXXX") 
FORCE_SUB_LINK = "https://t.me/+jE68aN-rzNQ2OTZl"

ADMIN_ID = 1727225499
ADMIN_USERNAME = "anujith1238"

app = Client("LeechBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

USER_THUMBNAILS = {}
WAITING_FOR_THUMB = set()
USER_YTDL_LINKS = {}
USER_FILE_MODES = {}

# Persistent Database files for data storage
DB_FILE = "database.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "premium_users": {},
        "premium_codes": {},
        "verify_settings": {
            "1": {"status": True, "shortener": "", "api": "", "tutorial": "", "time": 24},
            "2": {"status": False, "shortener": "", "api": "", "tutorial": "", "time": 24},
            "3": {"status": False, "shortener": "", "api": "", "tutorial": "", "time": 24},
        }
    }

def save_data():
    data = {
        "premium_users": PREMIUM_USERS,
        "premium_codes": PREMIUM_CODES,
        "verify_settings": VERIFY_SETTINGS
    }
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()
PREMIUM_USERS = db.get("premium_users", {})
PREMIUM_CODES = db.get("premium_codes", {})
VERIFY_SETTINGS = db.get("verify_settings", {
    "1": {"status": True, "shortener": "", "api": "", "tutorial": "", "time": 24},
    "2": {"status": False, "shortener": "", "api": "", "tutorial": "", "time": 24},
    "3": {"status": False, "shortener": "", "api": "", "tutorial": "", "time": 24},
})

ACTIVE_TASKS = {}
USER_TASK_LIMIT = 2
CANCEL_REQUESTS = set()

async def web_handler(request):
    return web.Response(text="Bot is Live! 🚀")

async def start_web_server():
    web_app = web.Application()
    web_app.add_routes([web.get("/", web_handler)])
    runner = web.AppRunner(web_app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Web server started on port {port}")

def human_bytes(size):
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.2f} {units[i]}"

def get_progress_bar(percentage):
    completed = int(percentage / 10)
    remaining = 10 - completed
    return "█" * completed + "░" * remaining

# Check if user is premium
def is_premium(user_id):
    if user_id == ADMIN_ID:
        return True
    if str(user_id) in PREMIUM_USERS:
        if PREMIUM_USERS[str(user_id)] > time.time():
            return True
        else:
            del PREMIUM_USERS[str(user_id)]
            save_data()
    return False

# Force Subscribe Check Function
async def check_force_sub(client, user_id):
    if not FORCE_SUB_CHANNEL or FORCE_SUB_CHANNEL == "-100XXXXXXXXXX":
        return True 
    try:
        user = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        if user.status in ["banned", "left"]:
            return False
        return True
    except UserNotParticipant:
        return False
    except Exception as e:
        logging.error(f"Force Sub Check Error: {e}")
        return True 

# 1. Start Command (Private Chat)
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    user = message.from_user
    user_id = user.id if user else 0
    
    if not await check_force_sub(client, user_id):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Update Channel / Group", url=FORCE_SUB_LINK)],
            [InlineKeyboardButton("🔄 Try Again", url=f"https://t.me/{client.me.username}?start=start")]
        ])
        await message.reply_text(
            "⚠️ **Access Denied!**\n\n"
            "You must join our update group/channel in order to use this bot. "
            "Please join using the button below and try again.",
            reply_markup=keyboard
        )
        return

    user_name = user.first_name if user else "Unknown"
    username = f"@{user.username}" if user and user.username else "No Username"

    if user and not user.is_bot:
        log_msg = (
            f"👤 <b>New User Started Bot!</b>\n\n"
            f"<b>Name:</b> {user_name}\n"
            f"<b>User ID:</b> <code>{user_id}</code>\n"
            f"<b>Username:</b> {username}"
        )
        try:
            await client.send_message(chat_id=LOG_CHANNEL_ID, text=log_msg)
        except Exception as e:
            logging.error(f"Failed to send start log to LOG_CHANNEL: {e}")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Admin Contact", url=f"https://t.me/{ADMIN_USERNAME}")],
        [InlineKeyboardButton("📢 Leech Group Join Now", url=FORCE_SUB_LINK)]
    ])
    await message.reply_text(
        "🤖 **I am Leech Bot!**\n"
        "Ready to help you download and manage files from Telegram, Google Drive, M3U8, and Direct/CDN Links.",
        reply_markup=keyboard
    )

# 2. Plans Command (/plans)
@app.on_message(filters.command("plans") & filters.private)
async def plans_handler(client: Client, message: Message):
    plans_text = (
        "<b>- ᴀᴠᴀɪʟᴀʙʟᴇ ᴘʟᴀɴs ❤️ -</b>\n\n"
        "• <b>08rs</b> - 1 day\n"
        "• <b>15rs</b> - 3 day\n"
        "• <b>30rs</b> - 1 ᴡᴇᴇᴋ\n"
        "• <b>70rs</b> - 1 ᴍᴏɴᴛʜs\n\n"
        "🎁 <b>ᴘʀᴇᴍɪᴜᴍ ғᴇᴀᴛᴜʀᴇs</b> 🎁\n\n"
        "○ ɴᴏ ɴᴇᴇᴅ to ᴠᴇʀɪғʏ\n"
        "○ ɴᴏ ɴᴇᴇᴅ ᴛᴏ ᴏᴘᴇɴ ʟɪɴᴋ\n"
        "○ ᴅɪʀᴇᴄᴛ ғɪʟᴇs\n\n"
        "✨ <b>ᴜᴘɪ ɪᴅ -</b> <code>vijayalakshmik8825@ybl</code>\n\n"
        "ᴄʟɪᴄᴋ ᴛᴏ ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴀᴄᴛɪᴠᴇ ᴘʟᴀɴ /myplan\n\n"
        "💢 <b>ᴍᴜsᴛ sᴇɴᴅ sᴄʀᴇᴇnsʜᴏᴛ ᴀғᴛᴇʀ ᴘᴀʏᴍᴇɴᴛ</b>\n\n"
        "‼️ <b>ᴀғᴛᴇʀ sᴇɴᴅɪɴɢ ᴀ sᴄʀᴇᴇnsʜᴏᴛ ᴘʟᴇᴀsᴇ ɢɪᴠᴇ ᴜs sᴏᴍᴇ ᴛɪᴍᴇ ᴛᴏ ᴀᴅᴅ ʏᴏᴜ ɪɴ ᴛʜᴇ ᴘʀᴇᴍɪᴜᴍ</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Contact Admin", url=f"https://t.me/{ADMIN_USERNAME}")]
    ])
    await message.reply_text(plans_text, reply_markup=keyboard)

# 3. My Plan Command (/myplan)
@app.on_message(filters.command("myplan") & filters.private)
async def myplan_handler(client: Client, message: Message):
    user_id = message.from_user.id
    
    if is_premium(user_id):
        if user_id == ADMIN_ID:
            await message.reply_text("👑 **You are the Bot Admin!** You have unlimited access.")
        else:
            expire_timestamp = PREMIUM_USERS.get(str(user_id))
            remaining_time = expire_timestamp - time.time()
            days_left = int(remaining_time // (24 * 3600))
            hours_left = int((remaining_time % (24 * 3600)) // 3600)
            
            await message.reply_text(
                f"✅ **Your Plan is Active!**\n\n"
                f"⏳ **Time Remaining:** `{days_left} Days and {hours_left} Hours`\n"
                f"Enjoy your premium features!"
            )
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👤 Contact Admin to Buy Plan", url=f"https://t.me/{ADMIN_USERNAME}")]
        ])
        await message.reply_text(
            "❌ **You do not have an active plan!**\n\n"
            " ഇതുവരെ നിങ്ങൾ പ്ലാൻ സജീവമായിട്ടില്ല. പ്ലാനുകൾ കാണാൻ `/plans` എന്ന് അയക്കുക അല്ലെങ്കിൽ താഴെയുള്ള ബട്ടൺ വഴി അഡ്മിനെ ബന്ധപ്പെടുക.",
            reply_markup=keyboard
        )

# 4. Customize Verification Command (/customize) - Admin Only
@app.on_message(filters.command("customize") & filters.private)
async def customize_handler(client: Client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏰ FIRST VERIFICATION", callback_data="custom_verify_1")],
        [InlineKeyboardButton("⏰ SECOND VERIFICATION", callback_data="custom_verify_2")],
        [InlineKeyboardButton("⏰ THIRD VERIFICATION", callback_data="custom_verify_3")],
        [InlineKeyboardButton("« BACK", callback_data="custom_back")]
    ])
    
    text = (
        "<b>TOKEN VERIFICATION:</b>\n\n"
        "TOKEN VERIFICATION: A SYSTEM REQUIRING USERS TO WATCH ADS OR SOLVE CAPTCHAS ON EXTERNAL SITES TO UNLOCK BOT ACCESS FOR TIME THAT BOT OWNER SET AND ALSO ALLOWING BOT OWNERS TO EARN MONEY WHENEVER A USER CLICKS."
    )
    await message.reply_text(text, reply_markup=keyboard)

@app.on_callback_query(filters.regex("^custom_"))
async def custom_callback_handler(client: Client, callback_query: CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("❌ You are not authorized!", show_alert=True)
        return
    
    data = callback_query.data
    if data in ["custom_verify_1", "custom_verify_2", "custom_verify_3"]:
        v_num = data.split("_")[-1]
        v_data = VERIFY_SETTINGS[v_num]
        status_icon = "✅" if v_data["status"] else "❌"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 FIRST VERIFY SHORTNER", callback_data=f"set_short_{v_num}")],
            [InlineKeyboardButton("🍿 FIRST VERIFY TUTORIAL", callback_data=f"set_tutor_{v_num}")],
            [InlineKeyboardButton(f"⏳ FIRST VERIFY TIME ({v_data['time']}h)", callback_data=f"set_time_{v_num}")],
            [InlineKeyboardButton(f"🔒 FIRST VERIFY - {status_icon}", callback_data=f"toggle_v_{v_num}")],
            [InlineKeyboardButton("« BACK", callback_data="custom_main")]
        ])
        await callback_query.message.edit_text(f"⏰ **TOKEN VERIFICATION {v_num}:**", reply_markup=keyboard)
    elif data in ["custom_main", "custom_back"]:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⏰ FIRST VERIFICATION", callback_data="custom_verify_1")],
            [InlineKeyboardButton("⏰ SECOND VERIFICATION", callback_data="custom_verify_2")],
            [InlineKeyboardButton("⏰ THIRD VERIFICATION", callback_data="custom_verify_3")],
            [InlineKeyboardButton("« BACK", callback_data="custom_back")]
        ])
        text = (
            "<b>TOKEN VERIFICATION:</b>\n\n"
            "TOKEN VERIFICATION: A SYSTEM REQUIRING USERS TO WATCH ADS OR SOLVE CAPTCHAS ON EXTERNAL SITES TO UNLOCK BOT ACCESS FOR TIME THAT BOT OWNER SET AND ALSO ALLOWING BOT OWNERS TO EARN MONEY WHENEVER A USER CLICKS."
        )
        await callback_query.message.edit_text(text, reply_markup=keyboard)

# 5. Create Premium Code Command (/createcode days uses)
@app.on_message(filters.command("createcode") & filters.private)
async def create_code_handler(client: Client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    if len(message.command) < 3:
        await message.reply_text(
            "⚠️ **Usage:**\n`/createcode days users`\n\n"
            "✏️ **Example:**\n`/createcode 30 50`"
        )
        return
    
    try:
        days = int(message.command[1])
        max_uses = int(message.command[2])
        
        import random
        import string
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        code = f"ANUJITH-{code}"
        
        PREMIUM_CODES[code] = {
            "days": days,
            "max_uses": max_uses,
            "used_by": []
        }
        save_data()
        
        await message.reply_text(
            f"✅ **Premium Code Created Successfully!**\n\n"
            f"🔑 **Code:** `<code>{code}</code>`\n"
            f"⏳ **Validity:** `{days} Days`\n"
            f"👥 **Max Uses:** `{max_uses}`"
        )
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# 6. Redeem Premium Code Command (/redeem code)
@app.on_message(filters.command("redeem") & filters.private)
async def redeem_code_handler(client: Client, message: Message):
    user_id = message.from_user.id
    
    if len(message.command) < 2:
        await message.reply_text(
            "⚠️ **Usage:**\n`/redeem CODE`\n\n"
            "⚠️ **Example:**\n`/redeem ANUJITH-XXXXXX`"
        )
        return
    
    code = message.command[1].strip()
    
    if code not in PREMIUM_CODES:
        await message.reply_text("❌ **Invalid or Expired Code!** Please check the code and try again.")
        return
    
    code_data = PREMIUM_CODES[code]
    
    if user_id in code_data["used_by"]:
        await message.reply_text("⚠️ **You have already used this code!**")
        return
    
    if len(code_data["used_by"]) >= code_data["max_uses"]:
        await message.reply_text("❌ **This code has reached its maximum usage limit!**")
        del PREMIUM_CODES[code]
        save_data()
        return
    
    days = code_data["days"]
    expire_seconds = days * 24 * 60 * 60
    
    current_time = time.time()
    if str(user_id) in PREMIUM_USERS and PREMIUM_USERS[str(user_id)] > current_time:
        PREMIUM_USERS[str(user_id)] += expire_seconds
    else:
        PREMIUM_USERS[str(user_id)] = current_time + expire_seconds
        
    code_data["used_by"].append(user_id)
    save_data()
    
    await message.reply_text(
        f"🎉 **Congratulations!**\n\n"
        f"Successfully redeemed premium for `{days} Days`! Enjoy your features."
    )

# 7. Admin Commands: Add Premium Directly (/addpremium user_id days)
@app.on_message(filters.command("addpremium") & filters.private)
async def add_premium_handler(client: Client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    if len(message.command) < 3:
        await message.reply_text("❌ Usage: `/addpremium user_id days`\nExample: `/addpremium 123456789 28`")
        return
    
    try:
        target_user_id = int(message.command[1])
        days = int(message.command[2])
        
        expire_seconds = days * 24 * 60 * 60
        expire_time = time.time() + expire_seconds
        PREMIUM_USERS[str(target_user_id)] = expire_time
        save_data()
        
        await message.reply_text(f"✅ Successfully added premium status to user `{target_user_id}` for `{days}` days!")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# 8. Admin Commands: Remove Premium (/rmpremium user_id)
@app.on_message(filters.command("rmpremium") & filters.private)
async def remove_premium_handler(client: Client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: `/rmpremium user_id`")
        return
    
    try:
        target_user_id = str(message.command[1])
        if target_user_id in PREMIUM_USERS:
            del PREMIUM_USERS[target_user_id]
            save_data()
            await message.reply_text(f"✅ Successfully removed premium status from user `{target_user_id}`!")
        else:
            await message.reply_text("⚠️ This user is not in the premium list.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# 9. Group Commands - ബോട്ട് അനുവദിച്ച നിർദ്ദിഷ്ട ഗ്രൂപ്പിൽ മാത്രം വർക്ക് ചെയ്യും
@app.on_message((filters.command("leech") | filters.command("v") | filters.command("ytdl") | filters.command("yt")) & filters.group)
async def restricted_group_handler(client: Client, message: Message):
    if message.chat.id != ALLOWED_GROUP_ID:
        return

    user_id = message.from_user.id
    
    if not await check_force_sub(client, user_id):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Update Channel / Group", url=FORCE_SUB_LINK)]
        ])
        await message.reply_text(
            f"⚠️ Hey {message.from_user.first_name},\n\n"
            "You haven't joined our update group/channel yet! "
            "Please join using the button below to use this bot.",
            reply_markup=keyboard
        )
        return
    
    cmd = message.command[0]
    if cmd == "leech":
        if len(message.command) < 2:
            await message.reply_text("❌ Please provide a link!\nExample: `/leech https://...`")
            return
        raw_text = message.text.split(" ", 1)[1]
        await message.reply_text(f"⏳ Processing your leech request for: `{raw_text}`")
    elif cmd == "v":
        if len(message.command) < 2:
            await message.reply_text("❌ Please provide a link to bypass!\nExample: `/v https://...`")
            return
        await message.reply_text("⏳ Processing bypass request...")
    elif cmd in ["ytdl", "yt"]:
        if len(message.command) < 2:
            await message.reply_text("❌ Please provide a YouTube link!\nExample: `/ytdl https://...`")
            return
        await message.reply_text("⏳ Processing YouTube download request...")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start_web_server())
    logging.info("Bot Starting...")
    app.run()
