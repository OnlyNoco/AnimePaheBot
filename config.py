import os, random
import base64
import logging 
from logging.handlers import RotatingFileHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN", "0")
API_ID = int(os.environ.get("API_ID", "26254064"))
API_HASH = os.environ.get("API_HASH", "72541d6610ae7730e6135af9423b319c")
WORKER = int(os.environ.get("WORKER", "4"))
OWNER_ID = int(os.environ.get("OWNER_ID", "5296584067"))
PORT = os.environ.get("PORT", "8080") 
DB_CHANNEL = os.environ.get("DB_CHANNEL", "-1002689479503")
DB_URL = os.environ.get("DB_URL", "mongodb+srv://abidabdullahcloud:abidabdullah1425@cluster0.3ebwbfh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.environ.get("DB_NAME", "ANIME_CRISP")
START_MSG = os.environ.get("START_MSG", "<blockquote>Hello {mention}</blockquote>\n\n<b>I 'm a bot who can steal videos from youtube and give it to you but i am exoecting rewards from you! :)</b>")
ABOUT_MSG = os.environ.get("ABOUT_MSG", "<b><blockquote>About us</blockquote></b>\n\nCreator: <a href='https://t.me/OnlyNoco'></a>\nPortfolio: <a href='href='https://onlynoco.vercel.app'></a>\n\n <blockquote>Channels,</blockquote>\n<blockquote><a href='https://t.me/HeavenlySubs'>Donghua</a>\n<a href='https://t.me/+O7PeEMZOAoMzYzVl'>Hentai</a></blockquote>")
CMD_MSG = os.environ.get("CMD_MSG", "<blockquote>/start - to check bot alive or dead!\n/help - to get help from bot usuages\n/report - to report issue to admin")
START_PIC = os.environ.get("START_PIC", "https://envs.sh/bjb.mp4 https://envs.sh/bjP.mp4 https://envs.sh/bjw.mp4 https://envs.sh/bj0.mp4 https://envs.sh/bjS.mp4 https://envs.sh/bjW.mp4 https://envs.sh/bjB.mp4 https://envs.sh/bjI.mp4 https://envs.sh/bjn.mp4 https://envs.sh/bjT.mp4 https://envs.sh/bjZ.mp4 https://envs.sh/bjL.mp4 https://envs.sh/bj5.mp4 https://envs.sh/bjY.mp4 https://envs.sh/bjC.mp4").split(" ")
FLOOD_WAIT = int(os.environ.get("FLOOD_WAIT", "10")) # in seconds

BOT_USERNAME = "Goddo_YatoBot"

# Caption template html support
ANIME_POST_TEMPLATE = """
{title_eng}

‣ Genres : {genres}
‣ Type : {anime_type}
‣ Average Rating : {average_score}%
‣ Status : {status}
‣ First aired : {first_aired}
‣ Last aired : {last_aired}
‣ Runtime : {duration} minutes
‣ No of episodes : {episodes}

‣ Synopsis : {description}

(Source: AniList)
""" 


EPISODE_POST_TEMPLATE = """<b><i>{anime_title}</i></b>
◐ Episode: {episode}
◐ Season: {season}
◑ Audio: {audio}""" 

FILENAME_TEMPLATE = "[S{season:02}EP{episode}] {title} [{type}] [{quality}].mp4"

# Max caption length for Telegram
MAX_CAPTION_LENGTH = 1000


# LOGGER SETUP
LOG_FILE_NAME = "onlynoco.txt"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
loggiing = "LTEwMDIxOTcyNzk1NDI="