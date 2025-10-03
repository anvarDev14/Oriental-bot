# keyboards/inline/admin_actions.py
"""
Admin harakatlari - Inline keyboard
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_fakultet_keyboard(fakultetlar):
    """Fakultet tanlash - Admin"""
    markup = InlineKeyboardMarkup(row_width=1)

    for fak in fakultetlar:
        markup.add(InlineKeyboardButton(
            f"📚 {fak['name']}",
            callback_data=f"addfak_{fak['id']}"
        ))

    markup.add(InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"))
    return markup


def get_confirm_keyboard():
    """Tasdiqlash - Inline"""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ Ha", callback_data="confirm_yes"),
        InlineKeyboardButton("❌ Yo'q", callback_data="confirm_no")
    )
    return markup

