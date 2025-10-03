"""
Yordam - Inline keyboard
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_support_keyboard():
    """Yordam keyboard"""
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📞 Admin", url="https://t.me/anvarcode"),
        InlineKeyboardButton("📢 Kanal", url="https://t.me/anvarDev1423"),
        InlineKeyboardButton("💬 Guruh", url="https://t.me/oriental_talabalarii")
    )
    return markup