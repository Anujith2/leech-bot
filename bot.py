import os
import time
import logging
import asyncio
import json
import aiohttp
import gdown
import subprocess
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
        },
        "user_settings": {}
    }

def save_data():
    data = {
        "premium_users": PREMIUM_USERS,
        "premium_codes": PREMIUM_CODES,
        "verify_settings": VERIFY_SETTINGS,
        "user_settings": USER_SETTINGS
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
USER_SETTINGS = db.get("user_settings", {})

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
    await message.reply_text("🤖 **I am Leech Bot!** Ready to help you download and manage files.", reply_markup=keyboard)

@app.on_message((filters.command("usetting") | filters.command("usettings")) & filters.group)
async def usetting_group_handler(client: Client, message: Message):
    if message.chat.id != ALLOWED_GROUP_ID:
        return
    
    user_id = str(message.from_user.id)
    if user_id not in USER_SETTINGS:
        USER_SETTINGS[user_id] = {"mode": "video", "thumb": None}
        save_data()
    
    has_thumb = "Yes ✅" if USER_SETTINGS[user_id].get("thumb") else "No ❌"
    mode_text = "🎬 Video Format" if USER_SETTINGS[user_id].get("mode") == "video" else "📁 Document Format"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Thumbnail Set: {has_thumb}", callback_data="set_thumb_info")],
        [InlineKeyboardButton(f"Mode: {mode_text}", callback_data="toggle_mode")],
        [InlineKeyboardButton("🗑️ Remove Thumbnail", callback_data="remove_thumb")]
    ])
    
    await message.reply_text(
        "⚙️ **User Personal Settings**\n\nConfigure your personal thumbnail and upload format here:",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex("^(toggle_mode|set_thumb_info|remove_thumb)$"))
async def usetting_callback(client: Client, callback_query: CallbackQuery):
    user_id = str(callback_query.from_user.id)
    if user_id not in USER_SETTINGS:
        USER_SETTINGS[user_id] = {"mode": "video", "thumb": None}
    
    data = callback_query.data
    if data == "toggle_mode":
        current_mode = USER_SETTINGS[user_id]["mode"]
        USER_SETTINGS[user_id]["mode"] = "document" if current_mode == "video" else "video"
        save_data()
        await callback_query.answer("Mode Updated!")
    elif data == "remove_thumb":
        USER_SETTINGS[user_id]["thumb"] = None
        save_data()
        await callback_query.answer("Thumbnail Removed Successfully!")
    elif data == "set_thumb_info":
        await callback_query.answer("Please send a photo in bot's private chat to set it as your custom thumbnail!", show_alert=True)
        return
    
    has_thumb = "Yes ✅" if USER_SETTINGS[user_id].get("thumb") else "No ❌"
    mode_text = "🎬 Video Format" if USER_SETTINGS[user_id].get("mode") == "video" else "📁 Document Format"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Thumbnail Set: {has_thumb}", callback_data="set_thumb_info")],
        [InlineKeyboardButton(f"Mode: {mode_text}", callback_data="toggle_mode")],
        [InlineKeyboardButton("🗑️ Remove Thumbnail", callback_data="remove_thumb")]
    ])
    
    try:
        await callback_query.message.edit_text(
            "⚙️ **User Personal Settings**\n\nConfigure your personal thumbnail and upload format here:",
            reply_markup=keyboard
        )
    except Exception:
        pass

@app.on_message(filters.photo & filters.private)
async def photo_handler(client: Client, message: Message):
    user_id = str(message.from_user.id)
    if user_id not in USER_SETTINGS:
        USER_SETTINGS[user_id] = {"mode": "video", "thumb": None}
    
    file_id = message.photo.file_id
    file_path = await client.download_media(file_id, file_name=f"thumb_{user_id}.jpg")
    USER_SETTINGS[user_id]["thumb"] = file_path
    save_data()
    await message.reply_text("✅ Custom thumbnail saved successfully! Now you can use it in groups.")

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
        args = message.text.split()
        if len(args) < 2:
            await message.reply_text("❌ Please provide a link!\nExample: `/leech <url> -n <new_name> -t <thumb_url>`")
            return
        
        url = args[1]
        custom_name = None
        custom_thumb_url = None
        
        if "-n" in args:
            try:
                n_idx = args.index("-n")
                custom_name = args[n_idx + 1]
            except Exception:
                pass
        if "-t" in args:
            try:
                t_idx = args.index("-t")
                custom_thumb_url = args[t_idx + 1]
            except Exception:
                pass

        msg = await message.reply_text("⏳ Initializing download... Please wait.")
        
        try:
            file_path = None
            if "drive.google.com" in url:
                file_path = gdown.download(url, output="downloaded_file", quiet=False, resume=True)
            else:
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
                # Fix metadata & duration issue (0:00 bug fix) using ffmpeg
                fixed_path = "fixed_" + file_path
                try:
                    cmd_ffmpeg = f"ffmpeg -i {file_path} -c copy {fixed_path} -y"
                    subprocess.run(cmd_ffmpeg, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if os.path.exists(fixed_path):
                        os.remove(file_path)
                        file_path = fixed_path
                except Exception:
                    pass

                if custom_name:
                    dir_name = os.path.dirname(file_path)
                    ext = os.path.splitext(file_path)[1]
                    new_path = os.path.join(dir_name, custom_name + ext)
                    os.rename(file_path, new_path)
                    file_path = new_path

                await msg.edit_text("📤 Uploading to Telegram...")
                
                user_info = (
                    f"\n\n👤 **Task By:** {message.from_user.first_name} (`{message.from_user.id}`)\n"
                    f"📦 **Size:** 92.41 MB\n"
                    f"🔗 **Link:** {url}"
                )

                u_id_str = str(user_id)
                u_mode = USER_SETTINGS.get(u_id_str, {}).get("mode", "video")
                u_thumb = USER_SETTINGS.get(u_id_str, {}).get("thumb")

                if custom_thumb_url:
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(custom_thumb_url) as resp:
                                if resp.status == 200:
                                    u_thumb = "custom_thumb.jpg"
                                    with open(u_thumb, "wb") as f:
                                        f.write(await resp.read())
                    except Exception:
                        pass

                if u_mode == "document":
                    await client.send_document(
                        chat_id=message.chat.id, 
                        document=file_path, 
                        thumb=u_thumb,
                        caption=f"📁 **File Uploaded Successfully!**{user_info}"
                    )
                else:
                    await client.send_video(
                        chat_id=message.chat.id, 
                        video=file_path, 
                        thumb=u_thumb,
                        caption=f"🎬 **Video Uploaded Successfully!**{user_info}"
                    )
                
                os.remove(file_path)
                if u_thumb and os.path.exists(str(u_thumb)) and "custom_thumb.jpg" in str(u_thumb):
                    os.remove(u_thumb)
                await msg.delete()
            else:
                await msg.edit_text("❌ Failed to process the file or video.")
        except Exception as e:
            await msg.edit_text(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start_web_server())
    app.run()
