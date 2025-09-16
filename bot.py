from aiohttp import web
from plugins import web_server

from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
from datetime import datetime
import pyrogram.utils
pyrogram.utils.MIN_CHANNEL_ID = -1009147483647

from config import API_HASH, API_ID, LOGGER, BOT_TOKEN, WORKER, PORT


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=API_ID,
            plugins={
                "root": "plugins"
            },
            workers=WORKER,
            bot_token=BOT_TOKEN
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()
        
        try:
            self.set_parse_mode(ParseMode.HTML)
            # here is the vars 
            bot_name = usr_bot_me.first_name or "Name Not Defined!"
            bot_username = usr_bot_me.username or "Username Not Defined!"
            self.LOGGER(__name__).info(f"Bot Running..!\n\nCreated by \nhttps://t.me/OnlyNoco")
            self.LOGGER(__name__).info("Bot Detailes: \n\n")
            self.LOGGER(__name__).info(f"Bot Name: {bot_name}")
            self.LOGGER(__name__).info(f"Bot Username: {bot_username}")
            
        except Exception as e:
            self.LOGGER(__name__).warning(f"Error during bot startup: {e}")
            sys.exit()

        #web-response
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")