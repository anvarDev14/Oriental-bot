"""
Main Handlers - Fakultet va dars tanlash
"""
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from data.config import ADMINS, STICKERS
from keyboards.inline.fakultet import faculty_menu, FACULTY_MAPPING
from keyboards.default.admin_menu import admin_menu
from loader import dp, bot, dars_db, user_db
import logging

logger = logging.getLogger(__name__)


# ==================== FAKULTET TANLASH ====================
@dp.callback_query_handler(lambda c: c.data.startswith("faculty_"))
async def select_faculty(call: types.CallbackQuery):
    """Fakultet tanlash"""
    await call.answer()

    if call.data == "faculty_back":
        await call.message.edit_text(
            "🎓 Fakultetingizni tanlang:",
            reply_markup=faculty_menu
        )
        return

    faculty_name = FACULTY_MAPPING.get(call.data)
    if not faculty_name:
        await call.message.answer("❌ Xato")
        return

    # Fakultetni saqlash
    user_db.update_faculty(call.from_user.id, faculty_name)

    # Fakultet ID topish
    fakultetlar = dars_db.get_all_fakultetlar()
    fakultet_id = None

    for fak in fakultetlar:
        if fak['name'] == faculty_name:
            fakultet_id = fak['id']
            break

    if not fakultet_id:
        await call.message.answer(
            "❌ Fakultet topilmadi\n📝 Admin qo'shishi kerak"
        )
        return

    # Mavzularni ko'rsatish
    await show_mavzular(call.message, fakultet_id, faculty_name, edit=True)


# ==================== MAVZULARNI KO'RSATISH ====================
async def show_mavzular(message, fakultet_id, faculty_name, edit=False):
    """Mavzular ro'yxati"""
    darslar = dars_db.get_dars_by_fakultet(fakultet_id)

    if not darslar:
        text = f"📚 <b>{faculty_name}</b>\n\n❌ Hozircha darslar yo'q"
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("🔙 Fakultetlar"))

        if edit:
            await message.edit_text(text, parse_mode="HTML")
            await message.answer("Asosiy menyu:", reply_markup=markup)
        else:
            await message.answer(text, reply_markup=markup, parse_mode="HTML")
        return

    # Mavzularga guruhlash
    mavzular = {}
    for dars in darslar:
        mavzu = dars['mavzu_name'] or "Boshqa"

        if mavzu not in mavzular:
            mavzular[mavzu] = []
        mavzular[mavzu].append(dars)

    # Klaviatura
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    for mavzu in sorted(mavzular.keys()):
        count = len(mavzular[mavzu])
        markup.add(KeyboardButton(f"📖 {mavzu} ({count})"))

    markup.add(
        KeyboardButton("🔙 Fakultetlar"),
        KeyboardButton("📞 Yordam")
    )

    text = (
        f"📚 <b>{faculty_name}</b>\n\n"
        f"📖 Mavzuni tanlang:\n\n"
        f"📊 Jami: {len(darslar)} ta dars"
    )

    if edit:
        await message.edit_text("✅ Fakultet tanlandi!")
        await message.answer(text, reply_markup=markup, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=markup, parse_mode="HTML")


# ==================== MAVZU TANLASH ====================
@dp.message_handler(lambda m: m.text and m.text.startswith("📖 "))
async def select_mavzu(message: types.Message):
    """Mavzu tanlash"""
    # Mavzu nomini olish
    mavzu_text = message.text[2:].strip()
    mavzu_name = mavzu_text.split(" (")[0] if " (" in mavzu_text else mavzu_text

    # Fakultetni olish
    faculty = user_db.get_user_faculty(message.from_user.id)
    if not faculty:
        await message.answer("❌ Avval fakultetni tanlang", reply_markup=faculty_menu)
        return

    # Fakultet ID
    fakultetlar = dars_db.get_all_fakultetlar()
    fakultet_id = None
    for fak in fakultetlar:
        if fak['name'] == faculty:
            fakultet_id = fak['id']
            break

    if not fakultet_id:
        await message.answer("❌ Xato")
        return

    # Mavzu bo'yicha darslar
    if mavzu_name == "Boshqa":
        all_darslar = dars_db.get_dars_by_fakultet(fakultet_id)
        darslar = [d for d in all_darslar if not d['mavzu_name']]
    else:
        darslar = dars_db.get_dars_by_mavzu(fakultet_id, mavzu_name)

    if not darslar:
        await message.answer("❌ Darslar topilmadi")
        return

    await show_darslar(message, darslar, mavzu_name, faculty)


# ==================== DARSLARNI KO'RSATISH ====================
async def show_darslar(message, darslar, mavzu_name, faculty_name):
    """Darslar ro'yxati"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

    # Darslarni qo'shish
    for dars in darslar[:20]:  # Max 20 ta
        title = dars['title'][:35]
        downloads = dars['count_download']
        markup.add(KeyboardButton(f"🎯 {title} ({downloads})"))

    markup.add(
        KeyboardButton("🔙 Mavzularga qaytish"),
        KeyboardButton("🏠 Asosiy menyu")
    )

    text = (
        f"📚 <b>{faculty_name}</b>\n"
        f"📖 <b>{mavzu_name}</b>\n\n"
        f"Darsni tanlang:\n\n"
        f"📊 Jami: {len(darslar)} ta"
    )

    await message.answer(text, reply_markup=markup, parse_mode="HTML")


# ==================== DARS TANLASH ====================
@dp.message_handler(lambda m: m.text and m.text.startswith("🎯 "))
async def select_dars(message: types.Message):
    """Dars yuklash"""
    # Dars nomini olish
    dars_text = message.text[2:].strip()
    dars_title = dars_text.split(" (")[0] if " (" in dars_text else dars_text

    # Fakultet
    faculty = user_db.get_user_faculty(message.from_user.id)
    if not faculty:
        await message.answer("❌ Avval fakultetni tanlang")
        return

    # Fakultet ID
    fakultetlar = dars_db.get_all_fakultetlar()
    fakultet_id = None
    for fak in fakultetlar:
        if fak['name'] == faculty:
            fakultet_id = fak['id']
            break

    # Darsni topish
    all_darslar = dars_db.get_dars_by_fakultet(fakultet_id)
    selected = None

    for dars in all_darslar:
        if dars['title'].startswith(dars_title[:20]):
            selected = dars_db.search_dars_by_code(dars['code'])
            break

    if not selected:
        await message.answer("❌ Dars topilmadi")
        return

    # Faylni yuborish
    try:
        await message.answer_document(
            document=selected['file_id'],
            caption=(
                f"📚 <b>{selected['title']}</b>\n\n"
                f"🔢 Kod: <code>{selected['code']}</code>\n"
                f"📥 Yuklanish: {selected['count_download'] + 1}\n"
                f"📅 {selected['created_at'][:10]}"
            ),
            parse_mode="HTML"
        )

        # Statistika
        dars_db.update_download_count(selected['code'])
        user_db.increment_downloads(message.from_user.id)
        user_db.update_last_active(message.from_user.id)

        logger.info(f"📥 Download: {selected['code']} by {message.from_user.id}")

    except Exception as e:
        logger.error(f"Fayl yuborish xatosi: {e}")
        await message.answer(f"❌ Xatolik: {e}")


# ==================== NAVIGATSIYA ====================
@dp.message_handler(text="🔙 Fakultetlar")
async def back_to_faculties(message: types.Message):
    """Fakultetlarga qaytish"""
    await message.answer(
        "🎓 Fakultetingizni tanlang:",
        reply_markup=faculty_menu
    )


@dp.message_handler(text="🔙 Mavzularga qaytish")
async def back_to_mavzular(message: types.Message):
    """Mavzularga qaytish"""
    faculty = user_db.get_user_faculty(message.from_user.id)
    if not faculty:
        await message.answer("❌ Xato", reply_markup=faculty_menu)
        return

    fakultetlar = dars_db.get_all_fakultetlar()
    fakultet_id = None
    for fak in fakultetlar:
        if fak['name'] == faculty:
            fakultet_id = fak['id']
            break

    if fakultet_id:
        await show_mavzular(message, fakultet_id, faculty)
    else:
        await message.answer("❌ Xato", reply_markup=faculty_menu)


@dp.message_handler(text="🏠 Asosiy menyu")
async def main_menu(message: types.Message):
    """Asosiy menyu"""
    if message.from_user.id in ADMINS or user_db.check_if_admin(message.from_user.id):
        await message.answer("👑 Admin panel:", reply_markup=admin_menu)
    else:
        await message.answer("🎓 Fakultetingizni tanlang:", reply_markup=faculty_menu)


@dp.message_handler(text="📞 Yordam")
async def support(message: types.Message):
    """Yordam"""
    await message.answer(
        "📞 <b>Yordam</b>\n\n"
        "📧 @anvarDev1423 \n"
        "📱 @anvarcode\n\n"
        "🔰 Savol-javoblar uchun admin bilan bog'laning",
        parse_mode="HTML"
    )