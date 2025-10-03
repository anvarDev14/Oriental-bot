"""
Config - Optimallashtirilgan konfiguratsiya
"""
import logging
from environs import Env

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

env = Env()
env.read_env()

# Asosiy sozlamalar
BOT_TOKEN = env.str("BOT_TOKEN")
ADMINS = env.list("ADMINS", subcast=int, default=[])

STICKERS = {
    'welcome': None,  # Hozircha o'chirib qo'yamiz
    'success': None,
    'deleted': None,
    'statistics': None,
    'download': None,
    'new_user': None,
    'error': None
}

logger.info(f"✅ Bot token yuklandi")
logger.info(f"👑 Adminlar: {len(ADMINS)} ta")
logger.info(f"🎨 Stikerlar: {len(STICKERS)} ta")