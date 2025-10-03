"""
Bekor qilish - Default keyboard
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

cancel_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("❌ Bekor qilish")]
    ],
    resize_keyboard=True
)