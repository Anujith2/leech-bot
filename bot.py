async def process_telegram_link(client, status_msg, user_id, user_name, url, custom_name, custom_thumb_source):
    ACTIVE_TASKS[user_id] = ACTIVE_TASKS.get(user_id, 0) + 1
    downloaded_file = None
    custom_thumb_path = None
    auto_thumb_path = None

    try:
        await status_msg.edit_text("🔍 Fetching message from Telegram channel...")
        
        # ലിങ്ക് പാസ്സ് ചെയ്ത് ചാനൽ ഐഡിയും മെസ്സേജ് ഐഡിയും കൃത്യമായി എടുക്കാൻ
        parsed_url = url.strip("/").split("/")
        msg_id = int(parsed_url[-1])
        
        if "c" in parsed_url:
            # ഇത് പ്രൈവറ്റ് ചാനൽ ലിങ്ക് ആണ് (ഉദാഹരണത്തിന്: t.me/c/123456789/123)
            c_index = parsed_url.index("c")
            chat_id = int("-100" + parsed_url[c_index + 1])
        else:
            # ഇത് പബ്ലിക് ചാനൽ ലിങ്ക് ആണ് (ഉദാഹരണത്തിന്: t.me/channelname/123)
            channel_username = parsed_url[-2]
            if channel_username.isdigit() or channel_username.startswith("-100"):
                chat_id = int(channel_username)
            else:
                chat_id = f"@{channel_username}"

        target_msg = await client.get_messages(chat_id, msg_id)

        if not target_msg or not target_msg.media:
            raise Exception("No media found in the given Telegram link or message is empty!")

        await status_msg.edit_text("📥 Downloading media from Telegram...")
        os.makedirs("downloads", exist_ok=True)

        # ഫയൽ കൃത്യമായി മുഴുവനായി ഡൗൺലോഡ് ആക്കാൻ പ്രോഗ്രസ് ഹാൻഡ്ലർ
        last_dl_update = 0
        async def dl_progress(current, total):
            nonlocal last_dl_update
            current_time = time.time()
            if current_time - last_dl_update > 3 or current == total:
                last_dl_update = current_time
                percentage = (current / total) * 100 if total > 0 else 0
                bar = get_progress_bar(percentage)
                try:
                    await status_msg.edit_text(
                        f"📥 **Downloading from Telegram...**\n\n"
                        f"{bar} `{percentage:.1f}%`\n"
                        f"📦 **Size:** `{human_bytes(current)} / {human_bytes(total)}`"
                    )
                except Exception:
                    pass

        downloaded_file = await client.download_media(
            target_msg,
            file_name="downloads/",
            progress=dl_progress
        )

        if not downloaded_file or not os.path.exists(downloaded_file):
            raise Exception("Failed to download media from Telegram link.")

        file_size = os.path.getsize(downloaded_file)
        ext = os.path.splitext(downloaded_file)[1]
        original_basename = os.path.basename(downloaded_file)

        if custom_name:
            file_title = custom_name if custom_name.endswith(ext) else custom_name + ext
            new_file_path = os.path.join("downloads", file_title)
            os.rename(downloaded_file, new_file_path)
            downloaded_file = new_file_path
        else:
            file_title = original_basename

        start_time = time.time()
        last_upload_update = 0

        def upload_progress(current, total):
            nonlocal last_upload_update
            if user_id in CANCEL_REQUESTS:
                return

            current_time = time.time()
            if current_time - last_upload_update > 3 or current == total:
                last_upload_update = current_time
                elapsed_time = current_time - start_time
                
                percentage = (current / total) * 100 if total > 0 else 0
                bar = get_progress_bar(percentage)
                
                speed = current / elapsed_time if elapsed_time > 0 else 0
                eta = (total - current) / speed if speed > 0 else 0
                
                upload_str = (
                    f"📤 **Uploading · {percentage:.1f}%**\n"
                    f"🎬 <code>{file_title}</code>\n\n"
                    f"{bar} {percentage:.1f}%\n"
                    f" ┣ 💾 **Size:** {human_bytes(current)} / {human_bytes(total)}\n"
                    f" ┣ ⚡ **Speed:** {human_bytes(speed)}/s\n"
                    f" ┗ ⏱️ **ETA:** {int(eta)}s"
                )
                try:
                    client.loop.create_task(
                        status_msg.edit_text(
                            upload_str,
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("✖️ Task Cancel", callback_data=f"cancel_dl_{user_id}")]
                            ])
                        )
                    )
                except Exception:
                    pass

        caption = (
            f"<b>{file_title}</b>\n\n"
            f"👤 <b>Task By:</b> {user_name} (`{user_id}`)\n"
            f"📦 <b>Size:</b> {human_bytes(file_size)}\n"
            f"🔗 <b>Link:</b> {url}"
        )

        valid_thumb = None
        if custom_thumb_source:
            custom_thumb_path = await download_thumbnail_from_source(client, custom_thumb_source, user_id)
            if custom_thumb_path and os.path.exists(custom_thumb_path):
                valid_thumb = custom_thumb_path

        if not valid_thumb:
            thumb = USER_THUMBNAILS.get(user_id)
            valid_thumb = thumb if thumb and os.path.exists(thumb) else None

        duration, width, height = 0, 0, 0
        if target_msg.video or target_msg.animation:
            video_obj = target_msg.video or target_msg.animation
            duration = video_obj.duration
            width = video_obj.width
            height = video_obj.height
            if not valid_thumb:
                auto_thumb_path = generate_thumbnail(downloaded_file, user_id)
                valid_thumb = auto_thumb_path

        file_mode = USER_FILE_MODES.get(user_id, "video")

        if file_mode == "document" or not (target_msg.video or target_msg.audio):
            sent_msg = await client.send_document(
                chat_id=status_msg.chat.id,
                document=downloaded_file,
                caption=caption,
                thumb=valid_thumb,
                progress=upload_progress,
                reply_to_message_id=status_msg.reply_to_message_id
            )
        elif target_msg.audio:
            sent_msg = await client.send_audio(
                chat_id=status_msg.chat.id,
                audio=downloaded_file,
                caption=caption,
                thumb=valid_thumb,
                progress=upload_progress,
                reply_to_message_id=status_msg.reply_to_message_id
            )
        else:
            sent_msg = await client.send_video(
                chat_id=status_msg.chat.id,
                video=downloaded_file,
                caption=caption,
                duration=duration,
                width=width,
                height=height,
                thumb=valid_thumb,
                progress=upload_progress,
                reply_to_message_id=status_msg.reply_to_message_id
            )

        try:
            if sent_msg:
                await sent_msg.copy(chat_id=DATABASE_CHANNEL_ID)
        except Exception as db_err:
            logging.error(f"Failed to forward to Database Channel: {db_err}")

        log_text = (
            f"📥 <b>Telegram Link Download Completed!</b>\n\n"
            f"👤 <b>User:</b> {user_name} (`{user_id}`)\n"
            f"🔗 <b>URL:</b> {url}\n"
            f"📁 <b>File:</b> {file_title}\n"
            f"📦 <b>Size:</b> {human_bytes(file_size)}"
        )
        try:
            await client.send_message(chat_id=LOG_CHANNEL_ID, text=log_text)
        except Exception as e:
            logging.error(f"Failed to send log to LOG_CHANNEL: {e}")

        if downloaded_file and os.path.exists(downloaded_file):
            os.remove(downloaded_file)
        if auto_thumb_path and os.path.exists(auto_thumb_path):
            os.remove(auto_thumb_path)
        if custom_thumb_path and os.path.exists(custom_thumb_path):
            os.remove(custom_thumb_path)

        await status_msg.delete()

    except Exception as e:
        error_msg = (
            f"⚠️ <b>Telegram Link Download Failed!</b>\n\n"
            f"<b>User:</b> {user_name} (`{user_id}`)\n"
            f"<b>URL:</b> `{url}`\n"
            f"<b>Error Details:</b> `{str(e)}`"
        )
        try:
            await client.send_message(chat_id=LOG_CHANNEL_ID, text=error_msg)
        except Exception:
            pass
        
        try:
            await status_msg.edit_text(f"❌ **Task Failed!**\n\n**Reason:** `{str(e)}`")
        except Exception:
            pass

        if downloaded_file and os.path.exists(downloaded_file):
            os.remove(downloaded_file)
        if auto_thumb_path and os.path.exists(auto_thumb_path):
            os.remove(auto_thumb_path)
        if custom_thumb_path and os.path.exists(custom_thumb_path):
            os.remove(custom_thumb_path)

    finally:
        if user_id in ACTIVE_TASKS:
            ACTIVE_TASKS[user_id] -= 1
            if ACTIVE_TASKS[user_id] <= 0:
                del ACTIVE_TASKS[user_id]
                
