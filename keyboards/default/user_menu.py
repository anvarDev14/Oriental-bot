"""
Foydalanuvchi menyusi - Default keyboard
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Asosiy menyu
main_user_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton("🔙 Fakultetlar"),
            KeyboardButton("📞 Yordam")
        ],
        [
            KeyboardButton("ℹ️ Bot haqida"),
            KeyboardButton("⚙️ Sozlamalar")
        ]
    ],
    resize_keyboard=True
)


# Mavzular menyusi
def get_mavzu_keyboard(mavzular, page=1, total_pages=1):
    """Mavzular klaviaturasi"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    # Mavzularni qo'shish
    for mavzu, count in mavzular:
        markup.add(KeyboardButton(f"📖 {mavzu} ({count})"))

    # Sahifalash
    nav_buttons = []
    if page > 1:
        nav_buttons.append(KeyboardButton("⬅️ Oldingi"))
    if page < total_pages:
        nav_buttons.append(KeyboardButton("➡️ Keyingi"))

    if nav_buttons:
        markup.add(*nav_buttons)

    # Navigatsiya
    markup.add(
        KeyboardButton("🔙 Fakultetlar"),
        KeyboardButton("📞 Yordam")
    )

    return markup


# Darslar menyusi
def get_dars_keyboard(darslar, page=1, total_pages=1):
    """Darslar klaviaturasi"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

    # Darslarni qo'shish (har safar max 15 ta)
    for dars in darslar[:15]:
        title = dars['title'][:35]
        downloads = dars['count_download']
        markup.add(KeyboardButton(f"🎯 {title} ({downloads})"))

    # Sahifalash
    nav_buttons = []
    if page > 1:
        nav_buttons.append(KeyboardButton("⬅️ Oldingi"))
    if page < total_pages:
        nav_buttons.append(KeyboardButton("➡️ Keyingi"))

    if nav_buttons:
        markup.add(*nav_buttons)

    # Navigatsiya
    markup.add(
        KeyboardButton("🔙 Mavzularga qaytish"),
        KeyboardButton("🏠 Asosiy menyu")
    )

    return markup