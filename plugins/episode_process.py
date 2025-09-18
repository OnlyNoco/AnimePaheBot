import aiohttp
import os
import time
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from config import DB_CHANNEL, BOT_USERNAME, EPISODE_POST_TEMPLATE, FILENAME_TEMPLATE
from database.database import get_channel_id
from plugins.progressbar import progress_bar

sticker_id = "CAACAgUAAxkBAAIOaGjLukYTKq7AP4KWwOnR2ZVvP-pZAALwDwACqihhVjrVtQeszRWVNgQ" 

async def process_episodes(client, anime_info, anilist_data, post_channel_id):
    episodes = anime_info["episodes"]
    anime_title = anime_info["anime_title"] 
    poster_url = anime_info["poster_url"]
    cover_url = anilist_data['anime_cover_url'] 
    
    # Determine season number
    season = 1
    if "Season" in anime_title:
        try:
            season = int(anime_title.split("Season")[1].split()[0])
        except:
            season = 1

    # Loop through episodes
    for ep_num in sorted(episodes.keys(), key=lambda x: int(x)):
        ep_files = episodes[ep_num]

        # Filter only Sub/Dub (English only)
        filtered_files = []
        for f in ep_files:
            lower = f["quality"].lower()
            if "eng" in lower:
                f["type"] = "Dub"
                filtered_files.append(f)
            elif not any(lang in lower for lang in ["kor","spa","fra","ger","chi"]):
                f["type"] = "Sub"
                filtered_files.append(f)

        # Order: Sub first, then Dub
        filtered_files.sort(key=lambda x: 0 if x["type"]=="Sub" else 1)
        buttons = []

        for file in filtered_files:
            q_text = file["quality"].split("路")[-1].split("BD")[0].strip()
            display_text = f"{q_text} - {file['type']}"

            # Dynamic filename using config template
            file_name = FILENAME_TEMPLATE.format(
                season=season,
                episode=ep_num,
                title=anime_title,
                type=file['type'],
                quality=q_text
            )
            tmp_path = f"/tmp/{file_name}"
            download_success = False

            # Progress message
            progress_msg = await client.send_message(post_channel_id, f"⏳ Starting download Ep {ep_num} - {display_text}")

            # Download with progress
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(file["direct_url"]) as resp:
                        if resp.status == 200:
                            total_size = int(resp.headers.get('content-length', 0))
                            current = 0
                            start_time = time.time()
                            with open(tmp_path, "wb") as f_out:
                                async for chunk in resp.content.iter_chunked(1024*64):
                                    f_out.write(chunk)
                                    current += len(chunk)
                                    await progress_bar(current, total_size, start_time, progress_msg, "Downloading")
                            download_success = True
            except:
                download_success = False

            if not download_success:
                tmp_path = "/assist/failed.mp4"

            # Upload to DB_CHANNEL with progress and thumbnail
            start_time = time.time()
            db_msg = await client.send_document(
                chat_id=DB_CHANNEL,
                document=tmp_path, 
                thumbnail=poster_url,
                progress=progress_bar,
                progress_args=(start_time, progress_msg, "Uploading")
            )

            if download_success:
                os.remove(tmp_path)

            msg_id = db_msg.message_id
            base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
            link = f"https://t.me/{BOT_USERNAME}?start={base64_string}"
            buttons.append([InlineKeyboardButton(display_text, url=link)])

            await progress_msg.delete()
            await asyncio.sleep(2)

        audio_type = "Japanese + English[Sub]" if all(f["type"]=="Sub" for f in filtered_files) else "Dual"

        ep_caption = EPISODE_POST_TEMPLATE.format(
            anime_title=anime_title,
            episode=ep_num,
            season=season,
            audio=audio_type
        )

        post_channel_id = get_channel_id()
        if post_channel_id:
            await client.send_photo(
                chat_id=post_channel_id,
                photo=poster_url,
                caption=ep_caption,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            await client.send_message(chat_id=post_channel_id, text="POST CHANNEL ID ERROR!")
       
        await client.send_sticker(chat_id=post_channel_id, sticker=sticker_id)
        await asyncio.sleep(30)