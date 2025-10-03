"""
Admin panel - Default keyboard
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton("➕ Dars Qo'shish"),
            KeyboardButton("🗑 Dars O'chirish")
        ],
        [
            KeyboardButton("➕ Fakultet Qo'shish"),
            KeyboardButton("🗑 Fakultet O'chirish")
        ],
        [
            KeyboardButton("📊 Statistika"),
            KeyboardButton("📣 Reklama")
        ],
        [
            KeyboardButton("👤 Admin Qo'shish"),
            KeyboardButton("🗑 Admin O'chirish")
        ],
        [
            KeyboardButton("📋 Adminlar Ro'yxati"),
            KeyboardButton("📢 Kanallar")
        ],
        [
            KeyboardButton("🏠 Asosiy menyu")
        ]
    ],
    resize_keyboard=True
)
