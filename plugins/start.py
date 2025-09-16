import os, random
from config import START_PIC, START_MSG, ABOUT_MSG, CMD_MSG
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton 
from pyrogram.enums import ParseMode
from bot import Bot


#-- 🫆 start command --#
@Bot.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
  # chat action
  await client.send_chat_action(message.chat.id, ChatAction.PLAYING)
  
  # buttons 
  reply_btns = InlineKeyboardMarkup(
    [
      [
        InlineKeyboardButton("✏️ About Me", callback_data="about"),
        InlineKeyboardButton("💨 Commands", callback_data="cmd")
      ]
    ]
  )

  photo = random.choice(START_PIC)
  
  # send a photo with msg 
  await message.reply_photo(
    photo = photo,
    caption = START_MSG.format(
      first = message.from_user.first_name,
      last = message.from_user.last_name,
      username = "Mr.Ghost Kun" if not message.from_user.username else "@" + message.from_user.username,
      mention = message.from_user.mention,
      id = message.from_user.id,
    ),
    reply_markup = reply_btns
  )
  
  
  
#-- Callback Queries --#
@Bot.on_callback_query()
async def callback_queries(client: Bot, query: CallbackQuery):
    #-- About --#
    if query.data == "about":
        await query.message.edit_text(
            text = ABOUT_MSG.format(query.from_user.mention,
            disable_web_page_preview = True, 
            parse_mode = ParseMode.HTML,
            reply_markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("💨 Commands", callback_data="cmd"),
                        InlineKeyboardButton("◀️ Back", callback_data="back")
                    ]
                ]
            )
        )
    
    #-- Commands --#
    elif query.data == "cmd":
        await query.message.edit_text(
            text = CMD_MSG.format(query.from_user.mention,
            disable_web_page_preview = True, 
            parse_mode = ParseMode.HTML,
            reply_markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("✏️ About Me", callback_data="about"),
                        InlineKeyboardButton("◀️ Back", callback_data="back")
                    ]
                ]
            )
        )
    
    #-- Back Callback --#
    elif query.data == "back":
        await query.message.edit_text(
            text = START_MSG.format(query.from_user.mention,
            disable_web_page_preview = True,
            reply_markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("✏️ About Me", callback_data="about"),
                        InlineKeyboardButton("💨 Commands", callback_data="cmd")
                    ]
                ]
            )
        )