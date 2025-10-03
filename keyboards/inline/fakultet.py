# ==================== INLINE KEYBOARDS ====================

# keyboards/inline/fakultet.py
"""
Fakultet tanlash - Inline keyboard
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Fakultet mapping
FACULTY_MAPPING = {
    "faculty_dasturiy": "Dasturiy injiniring",
    "faculty_kompyuter": "Kompyuter injiniring",
    "faculty_iqtisod": "Iqtisodiyot",
    "faculty_menejment1": "Menejment (talim)",
    "faculty_menejment2": "Menejment",
    "faculty_tarix": "Tarix",
    "faculty_psixologiya": "Psixologiya",
    "faculty_moliya": "Moliyaviy nazorat",
    "faculty_raqamli": "Raqamli iqtisodiyot",
    "faculty_ingliz": "Lingvistika (Ingliz)",
    "faculty_arab": "Lingvistika (Arab)",
    "faculty_sport": "Sport faoliyati",
    "faculty_talim": "Talim nazariyasi",
    "faculty_pedagogika": "Pedagogika"
}

# Fakultet menu
faculty_menu = InlineKeyboardMarkup(row_width=2)
faculty_menu.add(
    InlineKeyboardButton("💻 Dasturiy injiniring", callback_data="faculty_dasturiy"),
    InlineKeyboardButton("⚙️ Kompyuter injiniring", callback_data="faculty_kompyuter"),
    InlineKeyboardButton("📈 Iqtisodiyot", callback_data="faculty_iqtisod"),
    InlineKeyboardButton("📊 Menejment (talim)", callback_data="faculty_menejment1"),
    InlineKeyboardButton("🎯 Menejment", callback_data="faculty_menejment2"),
    InlineKeyboardButton("📜 Tarix", callback_data="faculty_tarix"),
    InlineKeyboardButton("🧠 Psixologiya", callback_data="faculty_psixologiya"),
    InlineKeyboardButton("💰 Moliyaviy nazorat", callback_data="faculty_moliya"),
    InlineKeyboardButton("📱 Raqamli iqtisodiyot", callback_data="faculty_raqamli"),
    InlineKeyboardButton("🇬🇧 Lingvistika (Ingliz)", callback_data="faculty_ingliz"),
    InlineKeyboardButton("🇸🇦 Lingvistika (Arab)", callback_data="faculty_arab"),
    InlineKeyboardButton("⚽ Sport faoliyati", callback_data="faculty_sport"),
    InlineKeyboardButton("📚 Talim nazariyasi", callback_data="faculty_talim"),
    InlineKeyboardButton("🎓 Pedagogika", callback_data="faculty_pedagogika")
)
