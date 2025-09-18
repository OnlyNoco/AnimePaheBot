import os, random
from config import START_PIC, START_MSG, ABOUT_MSG, CMD_MSG
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton 
from pyrogram.enums import ParseMode, ChatAction
from bot import Bot


#-- 🫆 start command --#
@Bot.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
  # chat action
  await client.send_chat_action(message.chat.id, ChatAction.PLAYING)
  bot_username = await client.get_me()
  # buttons 
  reply_btns = InlineKeyboardMarkup(
    [
      [
        InlineKeyboardButton("Aᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ᴄʜᴀᴛ", url=f"https://t.me/{bot_username}?startgroup=botstart")
      ]
      [
        InlineKeyboardButton("✏️ Aʙᴏᴜᴛ", callback_data="about"),
        InlineKeyboardButton("💨 Cᴏᴍᴍᴀɴᴅs", callback_data="cmd")
      ]
    ]
  )

  photo = random.choice(START_PIC)
  
  # send a photo with msg 
  await message.reply_photo(
    photo = photo,
    caption = START_MSG.format(
      mention = message.from_user.mention),
    reply_markup = reply_btns
  )
  
#-- added to group or channel --#
@Bot.on_message(filters.new_chat_members) 
async def new_chat_addded(client: Client, message: Message):
  for member in message.new_chat_members:
    if member.id == (await client.get_me()).id:
      try:
        chat = message.chat 
        perms = await client.get_chat_member(chat.id, member.id) 
        if perms.status in ['administrator', 'member']:
          await client.send_message(
            message.from_user.id,
            f"ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ ɪɴ <b>{chat.title}</b>\n"
            f"sᴛᴀᴛᴜs ◉ perms.status",
            parse_mode=ParseMode.HTML
          )
        else:
          await client.send_message(
            message.from_user.id,
            f"⎚ ᴀᴅᴅᴇᴅ ʙᴜᴛ ᴡɪᴛʜ ɴᴏ ᴘᴇʀᴍɪssɪᴏɴ",
            parse_mode=ParseMode.HTML
          )
      except Exception as e:
        await client.send_message(
          message.from_user.id,
          f"Cʜᴇᴄᴋ ᴘᴇʀᴍɪssɪᴏɴ ғᴀɪʟᴇᴅ ғᴏʀ <b>{message.chat.title}</b>\n\n <code>{e}</code>",
          parse_mode=ParseMode.HTML
        )
  
#-- Callback Queries --#
@Bot.on_callback_query()
async def callback_queries(client: Bot, query: CallbackQuery):
    #-- About --#
    if query.data == "about":
        await query.message.edit_text(
            text = ABOUT_MSG.format(mention=query.from_user.mention),
            disable_web_page_preview = True, 
            parse_mode = ParseMode.HTML,
            reply_markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("✏️ Aʙᴏᴜᴛ", callback_data="about"),
                        InlineKeyboardButton("💨 Cᴏᴍᴍᴀɴᴅs", callback_data="cmd")
                    ]
                ]
            )
        )
    
    #-- Commands --#
    elif query.data == "cmd":
        await query.message.edit_text(
            text = CMD_MSG.format(mention=query.from_user.mention),
            disable_web_page_preview = True, 
            parse_mode = ParseMode.HTML,
            reply_markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("✏️ Aʙᴏᴜᴛ", callback_data="about"),
                        InlineKeyboardButton("🔳 Bᴀᴄᴋ", callback_data="cmd")
                    ]
                ]
            )
        )
    
    #-- Back Callback --#
    elif query.data == "back":
        await query.message.edit_text(
            text = START_MSG.format(mention=query.from_user.mention),
            disable_web_page_preview = True,
            reply_markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("✏️ Aʙᴏᴜᴛ", callback_data="about"),
                        InlineKeyboardButton("💨 Cᴏᴍᴍᴀɴᴅs", callback_data="cmd")
                    ]
                ]
            )
        )