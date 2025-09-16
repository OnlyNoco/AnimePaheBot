from bot import Bot 
from pyrogram import filters
from pyrogram.enums import ParseMode
from config import OWNER_ID

@Bot.on_message(filters.command("report") & filters.private)
async def report_to_admin(client, message):
  report_text = f"🚨 User Report\nFrom: {message.from_user.mention} <code>({message.from_user.id})</code>\n\nMessage: {message.text}"
  
  await client.send_message(
        chat_id=OWNER_ID,
        text=report_text,
        parse_mode=ParseMode.HTML
    )
  
  await message.reply_text("Your report already reached to OWNER, reply will be here")
  