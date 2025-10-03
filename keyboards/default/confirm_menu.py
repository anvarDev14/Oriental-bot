from aiogram.types import ReplyKeyboardMarkup,KeyboardButton


confirm_menu=ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="✅Tasdiqlash"),
            KeyboardButton(text="❌Bekor qilish"),
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=True

)