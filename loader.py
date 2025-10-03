# loader.py

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from data.config import BOT_TOKEN
from utils.db_api.user import UserDatabase
from utils.db_api.courses import CourseDatabase
from utils.db_api.channel import ChannelDB
import logging
import os

logger = logging.getLogger(__name__)

# Bot va Dispatcher
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Database path - /tmp papkasida (har doim yozish mumkin)
DB_PATH = "/tmp/main.db"

# Yoki URI mode ishlatish
# DB_PATH = "file:main.db?mode=memory&cache=shared"

# Databaselar
user_db = UserDatabase(DB_PATH)
dars_db = CourseDatabase(DB_PATH)
channel_db = ChannelDB(DB_PATH)

logger.info("✅ Bot komponentlari yuklandi")