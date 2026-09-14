import os
import time
import logging
import asyncio
import json
import aiohttp
import gdown
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import UserNotParticipant
from aiohttp import web

# Logging Setup
logging.basicConfig(level=logging.INFO)

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

DATABASE_CHANNEL_ID = int(os.environ.get("DATABASE_CHANNEL_ID", "-1004396122384"))
LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", "-1004441596603"))
ALLOWED_GROUP_ID = int(os.environ.get("ALLOWED_GROUP_ID", "0"))
FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", "-100XXXXXXXXXX") 
FORCE_SUB_LINK = "https://t.me/+jE68aN-rzNQ2OTZl"

ADMIN_ID = 1727225499
ADMIN_USERNAME = "anujith1238"

app = Client("LeechBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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
            "1": {"status": True, "shortener": "", "api": "", "tutorial": "", "time": "24 Hours"},
            "2": {"status": False, "shortener": "", "api": "", "tutorial": "", "time": "24 Hours"},
            "3": {"status": False, "shortener": "", "api": "", "tutorial": "", "time": "24 Hours"},
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
    "1": {"status": True, "shortener": "", "api": "", "tutorial": "", "time": "24 Hours"},
    "2": {"status": False, "shortener": "", "api": "", "tutorial": "", "time": "24 Hours"},
    "3": {"status": False, "shortener": "", "api": "", "tutorial": "", "time": "24 Hours"},
})

ADMIN_STATES = {}

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
    except Exception:
        return True 

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id
    if not await check_force_sub(client, user_id):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Update Channel", url=FORCE_SUB_LINK)],
            [InlineKeyboardButton("🔄 Try Again", url=f"https://t.me/{client.me.username}?start=start")]
        ])
        await message.reply_text("⚠️ **Access Denied!** Please join our update channel first.", reply_markup=keyboard)
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Admin Contact", url=f"https://t.me/{ADMIN_USERNAME}")],
        [InlineKeyboardButton("📢 Leech Group Join Now", url=FORCE_SUB_LINK)]
    ])
    await message.reply_text("🤖 **I am Leech Bot!** Ready to help you download files and videos.", reply_markup=keyboard)

@app.on_message(filters.command("plans") & filters.private)
async def plans_handler(client: Client, message: Message):
    plans_text = (
        "<b>- AVAILABLE PLANS ❤️ -</b>\n\n"
        "• <b>08rs</b> - 1 Day\n"
        "• <b>15rs</b> - 3 Days\n"
        "• <b>30rs</b> - 1 Week\n"
        "• <b>70rs</b> - 1 Month\n\n"
        "✨ <b>UPI ID -</b> <code>vijayalakshmik8825@ybl</code>\n\n"
        "💢 <b>MUST SEND SCREENSHOT AFTER PAYMENT</b>"
    )
    await message.reply_text(plans_text)

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
            "You don't have an active plan yet. Send `/plans` to check available plans or contact the admin using the button below.",
            reply_markup=keyboard
        )

@app.on_message(filters.command("customize") & filters.private)
async def customize_handler(client: Client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏰ FIRST TOKEN VERIFICATION", callback_data="custom_verify_1")],
        [InlineKeyboardButton("⏰ SECOND TOKEN VERIFICATION", callback_data="custom_verify_2")],
        [InlineKeyboardButton("⏰ THIRD TOKEN VERIFICATION", callback_data="custom_verify_3")]
    ])
    await message.reply_text("<b>TOKEN VERIFICATION SETTINGS:</b>", reply_markup=keyboard)

@app.on_callback_query(filters.regex("^custom_"))
async def custom_callback_handler(client: Client, callback_query: CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("❌ Unauthorized!", show_alert=True)
        return
    
    data = callback_query.data
    if data.startswith("custom_verify_"):
        v_num = data.split("_")[-1]
        v_data = VERIFY_SETTINGS[v_num]
        status_icon = "✅" if v_data["status"] else "❌"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 FIRST VERIFY SHORTENER", callback_data=f"set_short_{v_num}")],
            [InlineKeyboardButton("🍿 FIRST VERIFY TUTORIAL", callback_data=f"set_tutor_{v_num}")],
            [InlineKeyboardButton("⏳ FIRST VERIFY TIME", callback_data=f"set_time_{v_num}")],
            [InlineKeyboardButton(f"🔒 FIRST VERIFY - {status_icon}", callback_data=f"toggle_v_{v_num}")],
            [InlineKeyboardButton("« BACK", callback_data="custom_main")]
        ])
        await callback_query.message.edit_text(f"⏰ **FIRST TOKEN VERIFICATION:**", reply_markup=keyboard)
        
    elif data == "custom_main" or data == "custom_back":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⏰ FIRST TOKEN VERIFICATION", callback_data="custom_verify_1")],
            [InlineKeyboardButton("⏰ SECOND TOKEN VERIFICATION", callback_data="custom_verify_2")],
            [InlineKeyboardButton("⏰ THIRD TOKEN VERIFICATION", callback_data="custom_verify_3")]
        ])
        await callback_query.message.edit_text("<b>TOKEN VERIFICATION SETTINGS:</b>", reply_markup=keyboard)
        
    elif data.startswith("set_short_"):
        v_num = data.split("_")[-1]
        ADMIN_STATES[ADMIN_ID] = {"action": "waiting_shortener", "v_num": v_num}
        await callback_query.message.reply_text(
            "SEND ME A SHORTLINK URL...\n\nFORMAT :\nhttps://vjlink.online - ❌\nvjlink.online - ✅\n\n/cancel - CANCEL THIS PROCESS."
        )
        await callback_query.answer()
        
    elif data.startswith("set_tutor_"):
        v_num = data.split("_")[-1]
        ADMIN_STATES[ADMIN_ID] = {"action": "waiting_tutorial", "v_num": v_num}
        await callback_query.message.reply_text(
            "SEND ME A TUTORIAL LINK...\n\n/cancel - CANCEL THIS PROCESS."
        )
        await callback_query.answer()

    elif data.startswith("set_time_"):
        v_num = data.split("_")[-1]
        ADMIN_STATES[ADMIN_ID] = {"action": "waiting_time", "v_num": v_num}
        await callback_query.message.reply_text(
            "SEND ME A TIME IN LIKE THIS - 1h or 15m\n\n/cancel - CANCEL THIS PROCESS."
        )
        await callback_query.answer()

    elif data.startswith("toggle_v_"):
        v_num = data.split("_")[-1]
        VERIFY_SETTINGS[v_num]["status"] = not VERIFY_SETTINGS[v_num]["status"]
        save_data()
        await callback_query.answer("Status Updated!")
        v_data = VERIFY_SETTINGS[v_num]
        status_icon = "✅" if v_data["status"] else "❌"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 FIRST VERIFY SHORTENER", callback_data=f"set_short_{v_num}")],
            [InlineKeyboardButton("🍿 FIRST VERIFY TUTORIAL", callback_data=f"set_tutor_{v_num}")],
            [InlineKeyboardButton("⏳ FIRST VERIFY TIME", callback_data=f"set_time_{v_num}")],
            [InlineKeyboardButton(f"🔒 FIRST VERIFY - {status_icon}", callback_data=f"toggle_v_{v_num}")],
            [InlineKeyboardButton("« BACK", callback_data="custom_main")]
        ])
        await callback_query.message.edit_text(f"⏰ **FIRST TOKEN VERIFICATION:**", reply_markup=keyboard)

@app.on_message(filters.private & filters.user(ADMIN_ID))
async def admin_text_input_handler(client: Client, message: Message):
    if message.text == "/cancel":
        if ADMIN_ID in ADMIN_STATES:
            del ADMIN_STATES[ADMIN_ID]
            await message.reply_text("❌ Process Cancelled.")
        return

    if ADMIN_ID in ADMIN_STATES:
        state = ADMIN_STATES[ADMIN_ID]
        v_num = state["v_num"]
        
        if state["action"] == "waiting_shortener":
            shortener_site = message.text.strip()
            ADMIN_STATES[ADMIN_ID] = {"action": "waiting_api", "v_num": v_num, "shortener": shortener_site}
            await message.reply_text("SEND ME SHORTLINK API...")
            return
            
        elif state["action"] == "waiting_api":
            api_key = message.text.strip()
            shortener_site = state["shortener"]
            
            VERIFY_SETTINGS[v_num]["shortener"] = shortener_site
            VERIFY_SETTINGS[v_num]["api"] = api_key
            save_data()
            
            del ADMIN_STATES[ADMIN_ID]
            await message.reply_text("SUCCESSFULLY SET SHORTLINK ✅")
            return

        elif state["action"] == "waiting_tutorial":
            tutor_link = message.text.strip()
            VERIFY_SETTINGS[v_num]["tutorial"] = tutor_link
            save_data()
            
            del ADMIN_STATES[ADMIN_ID]
            await message.reply_text("SUCCESSFULLY SET TUTORIAL LINK ✅")
            return

        elif state["action"] == "waiting_time":
            time_val = message.text.strip()
            VERIFY_SETTINGS[v_num]["time"] = time_val
            save_data()
            
            del ADMIN_STATES[ADMIN_ID]
            await message.reply_text(f"SUCCESSFULLY SET VERIFY TIME - {time_val} ✅")
            return

@app.on_message((filters.command("leech") | filters.command("v")) & filters.group)
async def restricted_group_handler(client: Client, message: Message):
    if message.chat.id != ALLOWED_GROUP_ID:
        return

    user_id = message.from_user.id
    if not await check_force_sub(client, user_id):
        await message.reply_text("⚠️ Please join the update channel first.")
        return
    
    cmd = message.command[0]
    if cmd == "leech":
        if len(message.command) < 2:
            await message.reply_text("❌ Please provide a link!\nExample: `/leech https://...`")
            return
        
        url = message.command[1]
        msg = await message.reply_text("⏳ Processing your leech request...")
        
        try:
            file_path = None
            if "drive.google.com" in url:
                file_path = gdown.download(url, output="downloaded_file", quiet=False, resume=True)
            else:
                # Direct video file / web link download support using aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            file_path = "downloaded_video.mp4"
                            with open(file_path, "wb") as f:
                                while True:
                                    chunk = await resp.content.read(1024)
                                    if not chunk:
                                        break
                                    f.write(chunk)
                        else:
                            await msg.edit_text("❌ Failed to download from the given link.")
                            return

            if file_path and os.path.exists(file_path):
                await msg.edit_text("📤 Uploading to Telegram...")
                # Send as video if it's a video file or document
                if file_path.endswith((".mp4", ".mkv", ".avi", ".mov")):
                    await client.send_video(chat_id=message.chat.id, video=file_path)
                else:
                    await client.send_document(chat_id=message.chat.id, document=file_path)
                os.remove(file_path)
                await msg.delete()
            else:
                await msg.edit_text("❌ Failed to process the file or video.")
        except Exception as e:
            await msg.edit_text(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start_web_server())
    app.run()
