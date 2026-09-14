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

def get_video_duration_and_resolution(file_path):
    try:
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "format=duration:stream=width,height",
            "-of", "json", file_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        data = json.loads(result.stdout)
        duration = int(float(data.get("format", {}).get("duration", 0)))
        width = int(data.get("streams", [{}])[0].get("width", 0))
        height = int(data.get("streams", [{}])[0].get("height", 0))
        return duration, width, height
    except Exception:
        return 0, 480, 320

def generate_thumbnail(file_path, output_thumb="auto_thumb.jpg"):
    try:
        cmd = [
            "ffmpeg", "-ss", "00:00:03", "-i", file_path,
            "-vframes", "1", "-q:v", "2", output_thumb, "-y"
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if os.path.exists(output_thumb):
            return output_thumb
    except Exception:
        pass
    return None

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

@app.on_message(filters.command(["plans", "plan"]) & filters.private)
async def plans_private_handler(client: Client, message: Message):
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

@app.on_message(filters.command("addpremium") & filters.private)
async def addpremium_handler(client: Client, message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply_text("❌ You are not authorized to use this command!")
        return
    args = message.text.split()
    if len(args) < 3:
        await message.reply_text("❌ Use format: `/addpremium user_id days`")
        return
    try:
        target_user = args[1]
        days = int(args[2])
        expiry = time.time() + (days * 86400)
        PREMIUM_USERS[target_user] = expiry
        save_data()
        await message.reply_text(f"✅ Successfully added premium for user `{target_user}` for {days} days!")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("removepremium") & filters.private)
async def removepremium_handler(client: Client, message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply_text("❌ You are not authorized to use this command!")
        return
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("❌ Use format: `/removepremium user_id`")
        return
    target_user = args[1]
    if target_user in PREMIUM_USERS:
        del PREMIUM_USERS[target_user]
        save_data()
        await message.reply_text(f"✅ Successfully removed premium for user `{target_user}`!")
    else:
        await message.reply_text("❌ User is not in the premium list or invalid ID.")

@app.on_message(filters.command("createcode") & filters.private)
async def createcode_handler(client: Client, message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply_text("❌ You are not authorized to use this command!")
        return
    await message.reply_text("✅ Use: `/createcode days` to create a redeem code.")

@app.on_message(filters.command("redeem") & filters.private)
async def redeem_handler(client: Client, message: Message):
    await message.reply_text("❌ Invalid or expired redeem code!")

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
        "⚙️ **User Personal Settings**\n\nConfigure your personal thumbnail and upload format here:\n\n*Note: To set a thumbnail, send a photo with caption `/setthumb` in this group or chat!*",
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
        await callback_query.answer("Send a photo with caption /setthumb to set your custom thumbnail!", show_alert=True)
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
            "⚙️ **User Personal Settings**\n\nConfigure your personal thumbnail and upload format here:\n\n*Note: To set a thumbnail, send a photo with caption `/setthumb` in this group or chat!*",
            reply_markup=keyboard
        )
    except Exception:
        pass

@app.on_message(filters.photo & (filters.private | filters.group))
async def photo_handler(client: Client, message: Message):
    if message.chat.type != "private" and message.chat.id != ALLOWED_GROUP_ID:
        return
    if message.chat.type != "private" and message.caption and message.caption.strip() != "/setthumb":
        return

    user_id = str(message.from_user.id)
    if user_id not in USER_SETTINGS:
        USER_SETTINGS[user_id] = {"mode": "video", "thumb": None}
    
    file_id = message.photo.file_id
    file_path = await client.download_media(file_id, file_name=f"thumb_{user_id}.jpg")
    USER_SETTINGS[user_id]["thumb"] = file_path
    save_data()
    await message.reply_text("✅ Custom thumbnail saved successfully! Now it will be used for your leech tasks.")

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
                if custom_name:
                    dir_name = os.path.dirname(file_path)
                    ext = os.path.splitext(file_path)[1]
                    new_path = os.path.join(dir_name, custom_name + ext)
                    os.rename(file_path, new_path)
                    file_path = new_path

                await msg.edit_text("📤 Uploading to Telegram...")
                
                file_size_bytes = os.path.getsize(file_path)
                file_size_mb = round(file_size_bytes / (1024 * 1024), 2)

                user_info = (
                    f"\n\n👤 **Task By:** {message.from_user.first_name} (`{message.from_user.id}`)\n"
                    f"📦 **Size:** {file_size_mb} MB\n"
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

                auto_thumb_file = None
                if not u_thumb and u_mode == "video":
                    auto_thumb_file = generate_thumbnail(file_path)
                    if auto_thumb_file:
                        u_thumb = auto_thumb_file

                duration, width, height = get_video_duration_and_resolution(file_path)

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
                        duration=duration,
                        width=width,
                        height=height,
                        thumb=u_thumb,
                        caption=f"🎬 **Video Uploaded Successfully!**{user_info}"
                    )
                
                os.remove(file_path)
                if u_thumb and os.path.exists(str(u_thumb)) and ("custom_thumb.jpg" in str(u_thumb) or "auto_thumb.jpg" in str(u_thumb)):
                    os.remove(u_thumb)
                await msg.delete()
            else:
                await msg.edit_text("❌ Failed to process the file or video.")
        except Exception as e:
            await msg.edit_text(f"❌ Error: {str(e)}")

async def main():
    await start_web_server()
    await app.start()
    print("Bot Started Successfully! 🚀")
    await asyncio.gather(*(asyncio.Event().wait() for _ in range(1)))

if __name__ == "__main__":
    asyncio.run(main())
