# app.py
"""
Bot - asosiy fayl
"""
from aiogram import executor
from loader import dp, user_db, dars_db, channel_db
import logging

logger = logging.getLogger(__name__)


async def on_startup(dispatcher):
    """Bot ishga tushganda"""
    logger.info("🚀 Bot ishga tushmoqda...")
    
    try:
        # Jadvalarni yaratish
        user_db.create_table()
        dars_db.create_tables()
        logger.info("✅ Jadvallar tayyor")
    except Exception as e:
        logger.error(f"❌ Database xatosi: {e}")
    
    # DEFAULT FAKULTETLARNI QO'SHISH
    logger.info("📚 Default fakultetlarni tekshirish...")
    
    default_fakultetlar = [
        "Dasturiy injiniring",
        "Kompyuter injiniring",
        "Iqtisodiyot",
        "Menejment (talim)",
        "Menejment",
        "Tarix",
        "Psixologiya",
        "Moliyaviy nazorat",
        "Raqamli iqtisodiyot",
        "Lingvistika (Ingliz)",
        "Lingvistika (Arab)",
        "Sport faoliyati",
        "Talim nazariyasi",
        "Pedagogika"
    ]
    
    added_count = 0
    for fakultet_name in default_fakultetlar:
        try:
            existing = dars_db.get_fakultet_by_name(fakultet_name)
            if not existing:
                dars_db.add_fakultet(fakultet_name)
                added_count += 1
                logger.info(f"➕ Default fakultet: {fakultet_name}")
        except Exception:
            pass
    
    if added_count > 0:
        logger.info(f"✅ {added_count} ta default fakultet qo'shildi")
    else:
        logger.info("✅ Barcha default fakultetlar mavjud")
    
    # Handlerlarni import qilish
    try:
        # IMPORT QO'SHISH - Bu yerda handlers yuklash
        import handlers.users.start
        import handlers.users.main_handlers
        import handlers.admin.admin_handlers
        
        logger.info("✅ Handlerlar yuklandi")
    except ImportError as e:
        logger.error(f"⚠️ Handler import xatosi: {e}")
        logger.error("handlers/admin/__init__.py faylini tekshiring!")
    
    logger.info("🎉 Bot tayyor!")


async def on_shutdown(dispatcher):
    """Bot to'xtaganda"""
    logger.info("⏹ Bot to'xtatilmoqda...")
    channel_db.close()
    logger.info("👋 Bot to'xtatildi")


if __name__ == '__main__':
    executor.start_polling(
        dp,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True
    )
