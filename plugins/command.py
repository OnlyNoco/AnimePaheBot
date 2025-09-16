from plugins.main import *  
import os
import re
import asyncio
import tempfile
from bot import Bot
from pyrogram import filters
from pyrogram.types import Message
from config import LOGGER
from plugins.progress import progress_bar
import time

logger = LOGGER("search_command")



# Initialize downloader
downloader = AnimepaheDownloader(debug=True)


@Bot.on_message(filters.command("search"))
async def search_command(client, message: Message):
    """Handle /search command with anime name and episode range"""
    try:
        # Parse command arguments
        command_text = message.text.split(maxsplit=1)
        if len(command_text) < 2:
            await message.reply_text(
                "❌ **Usage:** `/search <anime_name> <episodes>`\n\n"
                "Examples:\n"
                "• `/search horimiya 1-2`\n" 
                "• `/search attack on titan 5`\n"
                "• `/search naruto 1,3,5-8`"
            )
            return

        # Extract anime name and episodes
        args = command_text[1].strip()
        
        # Find the last word that looks like episode numbers
        words = args.split()
        if len(words) < 2:
            await message.reply_text("❌ Please specify both anime name and episode numbers!")
            return
            
        # Assume last word is episode specification
        episode_str = words[-1]
        anime_name = ' '.join(words[:-1])
        
        # Validate episode format
        episodes = parse_episode_range(episode_str)
        if not episodes:
            await message.reply_text("❌ Invalid episode format! Use formats like: 1, 1-5, or 1,3,5-8")
            return

        # Send initial message
        status_msg = await message.reply_text(f"🔍 Searching for **{anime_name}**...")

        # Search for anime
        results = await asyncio.to_thread(downloader.search_anime, anime_name)
        if not results:
            await status_msg.edit_text(f"❌ No anime found for: **{anime_name}**")
            return

        # Use first result (most relevant)
        selected_anime = results[0]
        session_id = selected_anime['session']
        anime_title = selected_anime['title']
        
        await status_msg.edit_text(
            f"✅ Found: **{anime_title}**\n"
            f"📺 Episodes: {selected_anime['episodes']}\n"
            f"📅 Year: {selected_anime['year']}\n"
            f"📊 Score: {selected_anime['score']}\n\n"
            f"🔄 Getting episodes list..."
        )

        # Get all episodes for this anime
        all_episodes = []
        page = 1
        while True:
            episode_data = await asyncio.to_thread(downloader.get_episodes, session_id, page)
            all_episodes.extend(episode_data['episodes'])
            
            if page >= episode_data['last_page']:
                break
            page += 1

        if not all_episodes:
            await status_msg.edit_text(f"❌ No episodes found for **{anime_title}**")
            return

        # Find episodes to download
        episodes_to_download = []
        available_episodes = [ep['episode'] for ep in all_episodes]
        
        for ep_num in episodes:
            for ep in all_episodes:
                if ep['episode'] == ep_num:
                    episodes_to_download.append(ep)
                    break

        if not episodes_to_download:
            await status_msg.edit_text(
                f"❌ Requested episodes {episodes} not found!\n"
                f"📺 Available episodes: {min(available_episodes)}-{max(available_episodes)}"
            )
            return

        await status_msg.edit_text(
            f"✅ Found {len(episodes_to_download)} episode(s) to download\n"
            f"📺 Episodes: {[ep['episode'] for ep in episodes_to_download]}\n\n"
            f"⬬ Starting downloads..."
        )

        # Download episodes
        for i, ep in enumerate(episodes_to_download):
            episode_num = ep['episode']
            episode_session = ep['session']
            
            try:
                await status_msg.edit_text(
                    f"📥 Processing Episode {episode_num} ({i+1}/{len(episodes_to_download)})\n"
                    f"🔄 Getting download links..."
                )

                # Get download links
                download_links = await asyncio.to_thread(downloader.get_download_links, session_id, episode_session)
                if not download_links:
                    await message.reply_text(f"❌ No download links found for episode {episode_num}")
                    continue

                # Use first available link (usually highest quality)
                selected_link = download_links[0]
                
                await status_msg.edit_text(
                    f"📥 Processing Episode {episode_num} ({i+1}/{len(episodes_to_download)})\n"
                    f"🎥 Quality: {selected_link['text']}\n"
                    f"🔓 Bypassing protection..."
                )

                # Get direct download URL
                direct_url = await asyncio.to_thread(downloader.get_direct_download_url, selected_link['url'])
                if not direct_url:
                    await message.reply_text(f"❌ Failed to get direct download URL for episode {episode_num}")
                    continue

                # Create filename
                quality_match = re.search(r'\b\d{3,4}p\b', selected_link['text'])
                quality = quality_match.group() if quality_match else 'unknown'
                
                audio_type = "Dub" if 'eng' in selected_link['text'].lower() else "Sub"
                
                # Sanitize anime title for filename
                safe_title = re.sub(r'[<>:"/\\|?*]', '', anime_title)
                filename = f"[{audio_type}] [{safe_title}] [EP {episode_num}] [{quality}].mp4"
                start_time = time.time()
                
                # Create temp download path
                temp_dir = tempfile.mkdtemp()
                output_path = os.path.join(temp_dir, filename)

                '''# Track download progress (simplified to avoid async issues in callback)
                def progress_callback(progress, downloaded, total):
                    # Simple progress tracking - avoid async operations in callback
                    if progress % 20 < 1:  # Log every 20%
                        logger.info(f"Download progress: {progress:.1f}%")'''

                await status_msg.edit_text(
                    f"📥 Downloading Episode {episode_num} ({i+1}/{len(episodes_to_download)})\n"
                    f"🎥 Quality: {selected_link['text']}\n"
                    f"📊 Starting download..."
                )

                # Download file in background thread
                download_success = await asyncio.to_thread(
                    downloader.download_file, 
                    direct_url, 
                    output_path, 
                    lambda downloaded, total: asyncio.run_coroutine_threadsafe(
                      progress_bar(downloaded, total, start_time, status_msg, f"Downloading Episode {episode_num}"),
                      asyncio.get_event_loop()
                    )
                )
                
                if download_success:
                    # Upload to Telegram
                    await status_msg.edit_text(
                        f"📤 Uploading Episode {episode_num} to Telegram...\n"
                        f"📁 File: {filename}"
                    )
                    
                    try:
                        # Send the video file
                        await message.reply_document(
                            document=output_path,
                            file_name=filename,
                            progress=progress_bar,
                            progress_args=(start_time, status_msg, f"Uploading Episode {episode_num}")
                        )
                        
                        # Clean up temp file
                        os.remove(output_path)
                        os.rmdir(temp_dir)
                        
                    except Exception as upload_error:
                        logger.error(f"Upload error: {upload_error}")
                        await message.reply_text(f"❌ Failed to upload episode {episode_num}: {str(upload_error)}")
                        # Clean up on error
                        if os.path.exists(output_path):
                            os.remove(output_path)
                            os.rmdir(temp_dir)
                        
                else:
                    await message.reply_text(f"❌ Failed to download episode {episode_num}")
                    # Clean up on error
                    if os.path.exists(output_path):
                        os.remove(output_path)
                        os.rmdir(temp_dir)

            except Exception as e:
                logger.error(f"Error processing episode {episode_num}: {e}")
                await message.reply_text(f"❌ Error processing episode {episode_num}: {str(e)}")

        # Final status update
        await status_msg.edit_text(
            f"✅ **Download Complete!**\n"
            f"📺 Anime: {anime_title}\n"
            f"📊 Processed: {len(episodes_to_download)} episode(s)\n"
            f"🎯 Episodes: {[ep['episode'] for ep in episodes_to_download]}"
        )

    except Exception as e:
        logger.error(f"Error in search command: {e}")
        await message.reply_text(f"❌ An error occurred: {str(e)}")
        