from config import OWNER_ID, ANIME_POST_TEMPLATE, MAX_CAPTION_LENGTH
from pyrogram import filters 
from pyrogram.errors import ChatAdminRequired, ChatWriteForbidden
from pyrogram.enums import ParseMode
from bot import Bot
from plugins.anilist import get_anilist_info 
from database.database import * 
from plugins.episode_process import process_episodes 
import json
import asyncio

# divider sticker 
sticker_id = "CAACAgUAAxkBAAIOaGjLukYTKq7AP4KWwOnR2ZVvP-pZAALwDwACqihhVjrVtQeszRWVNgQ" 



@Bot.on_message(filters.document & filters.private & filters.user(OWNER_ID))
async def handle_json(client, message):
    try:
        file_path = await message.download()
        if not file_path.endswith(".json"):
            await message.reply("<code>SEND VALID JSON FILE</code>", parse_mode=ParseMode.HTML)
            return

        # Load JSON
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract JSON data
        first_key = next(iter(data))
        anime_info = data[first_key]

        anime_title = anime_info["anime_title"]
        poster_url = anime_info["poster_url"]
        year = anime_info["year"]
        anime_type = anime_info["type"]
        status = anime_info["status"]
        total_episodes = anime_info["total_episodes"]
        episodes = anime_info["episodes"] 
        
        await asyncio.sleep(5) # 5 sec rest 

        # Get AniList data
        anilist_data = get_anilist_info(anime_title)
        if not anilist_data:
            await message.reply("❌ Anime not found on AniList")
            return

        # Genres text with emojis
        genres_text = ", ".join(anilist_data["genres"])

        # Compose caption
        caption = ANIME_POST_TEMPLATE.format(
            title_local=anime_title,
            title_eng=anilist_data['anime_title_eng'],
            genres=genres_text,
            anime_type=anime_type,
            average_score=anilist_data['averageScore'],
            status=status,
            first_aired=anilist_data['first_aired'],
            last_aired=anilist_data['last_aired'],
            duration=anilist_data['duration'],
            episodes=total_episodes,
            description=anilist_data['description']
        )

        # Truncate caption if too long for Telegram
        if len(caption) > MAX_CAPTION_LENGTH:
            caption = caption[:MAX_CAPTION_LENGTH - 3] + "..."

        # get channel id from mongodb 
        post_channel_id = get_channel_id() 
        await asyncio.sleep(5) # 5 sec rest 
        if post_channel_id: 
          # Send post with AniList cover as thumbnail
          await client.send_photo(
            chat_id=post_channel_id,
            photo=anilist_data['anime_cover_url'],
            caption=caption, 
            parse_mode=ParseMode.HTML
          ) 
        else: 
          await message.reply_text(f"POST CHANNEL ID ERROR!")
        await asyncio.sleep(5) # 5 sec rest  
        
        
        await client.send_sticker(
          chat_id=post_channel_id,
          sticker=sticker_id
        ) 
        
        # callback for episode processing main oart of this bot 
        await process_episodes(
          client=client,
          anime_info=anime_info,
          anilist_data=anilist_data,
          post_channel_id=post_channel_id
        )
        
        

    except Exception as e:
        await message.reply(f"❌ Error: {e}") 
  
  
  


@Bot.on_message(filters.command("setchannel") & filters.user(OWNER_ID))
async def set_channel(client, message):
    if len(message.command) < 2:
        await message.reply("⚠️ Usage: <code>/setchannel -1001234567890</code>")
        return

    try:
        channel_id = int(message.command[1])

        # Test permission
        try:
            test_msg = await client.send_message(channel_id, "🔄 Testing permissions...")
            await test_msg.delete()
        except (ChatAdminRequired, ChatWriteForbidden):
            await message.reply("❌ Bot has no permission to post in that channel.")
            return

        # Save instantly
        save_channel_id(channel_id)

        await message.reply(f"✅ Channel ID saved: <code>{channel_id}</code>")

    except Exception as e:
        await message.reply(f"❌ Error: {e}") 
        



@Bot.on_message(filters.command("getchannel") & filters.user(OWNER_ID))
async def get_channel(client, message):
    channel_id = get_channel_id()
    if channel_id:
        await message.reply(f"📌 Current channel ID: <code>{channel_id}</code>")
    else:
        await message.reply("⚠️ No channel has been set yet.")