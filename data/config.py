import logging
from environs import Env

# Logging sozlamasi
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# environs kutubxonasidan foydalanish
env = Env()
env.read_env()

# .env fayl ichidan ma'lumotlarni o'qiymiz
BOT_TOKEN = env.str("BOT_TOKEN")
IP = env.str("IP", default="localhost")  # Katta harf bilan IP
ADMINS = env.list("ADMINS", subcast=int, default=[])  # Vergul bilan ajratilgan ro'yxat

def update_env_admins(admins: list):
    """ADMINS ro'yxatini .env faylida yangilash."""
    try:
        with open(".env", "r", encoding="utf-8") as file:
            lines = file.readlines()
        with open(".env", "w", encoding="utf-8") as file:
            found_admins = False
            for line in lines:
                if line.strip().startswith("ADMINS="):
                    file.write(f"ADMINS={','.join(map(str, admins))}\n")
                    found_admins = True
                else:
                    file.write(line)
            if not found_admins:
                file.write(f"ADMINS={','.join(map(str, admins))}\n")
        # Config'ni qayta yuklash
        global ADMINS
        env.read_env(override=True)  # .env faylini qayta o'qish
        ADMINS = env.list("ADMINS", subcast=int, default=[])
        logger.info(f".env updated with ADMINS: {ADMINS}")
    except FileNotFoundError:
        logger.error("Error: .env file not found")
        raise
    except PermissionError:
        logger.error("Error: No permission to write to .env file")
        raise
    except Exception as e:
        logger.error(f"Error updating .env file: {e}")
        raise

# Ma'lumotlarni konsolda chiqarish (tekshirish uchun)
logger.info(f"BOT_TOKEN: {BOT_TOKEN}")
logger.info(f"ADMINS: {ADMINS}")
logger.info(f"IP: {IP}")

# Test uchun avtomatik yangilash
update_env_admins([6369838846])  # Bot ishga tushganda ADMINS ni yangilash