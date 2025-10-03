# loader.py
"""
Bot komponentlarini yuklash
"""
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from data.config import BOT_TOKEN
from utils.db_api.user import UserDatabase
from utils.db_api.courses import CourseDatabase
from utils.db_api.channel import ChannelDB
import logging

logger = logging.getLogger(__name__)

# Bot va Dispatcher
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Databaselar
user_db = UserDatabase("main.db")
dars_db = CourseDatabase("main.db")
channel_db = ChannelDB("main.db")

logger.info("✅ Bot komponentlari yuklandi")

