"""
Main Handlers - Fakultet va dars tanlash (Sahifalash bilan)
"""
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from data.config import ADMINS, STICKERS
from keyboards.inline.fakultet import faculty_menu, FACULTY_MAPPING
from keyboards.default.admin_menu import admin_menu
from loader import dp, bot, dars_db, user_db
import logging

logger = logging.getLogger(__name__)

# Sahifalash uchun ma'lumotlarni saqlash
user_pagination = {}  # {user_id: {'darslar': [], 'page': 0, 'mavzu': '', 'faculty': ''}}

DARS_PER_PAGE = 10  # Har sahifada 10 ta dars


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

    # Sahifalash ma'lumotlarini saqlash
    user_pagination[message.from_user.id] = {
        'darslar': darslar,
        'page': 0,
        'mavzu': mavzu_name,
        'faculty': faculty
    }

    await show_darslar_page(message, message.from_user.id)


# ==================== DARSLARNI SAHIFALAB KO'RSATISH ====================
async def show_darslar_page(message, user_id):
    """Darslarni sahifalab ko'rsatish"""
    if user_id not in user_pagination:
        await message.answer("❌ Xato. Qaytadan mavzu tanlang.")
        return

    data = user_pagination[user_id]
    darslar = data['darslar']
    page = data['page']
    mavzu_name = data['mavzu']
    faculty_name = data['faculty']

    # Darslarni aqlli saralash (raqamli tartib)
    def natural_sort_key(dars):
        """Raqamlarni to'g'ri saralash uchun"""
        import re
        title = dars['title']
        # Raqamlarni topish va int ga aylantirish
        parts = re.split(r'(\d+)', title)
        return [int(part) if part.isdigit() else part.lower() for part in parts]

    darslar_sorted = sorted(darslar, key=natural_sort_key)

    total_pages = (len(darslar_sorted) + DARS_PER_PAGE - 1) // DARS_PER_PAGE
    start_idx = page * DARS_PER_PAGE
    end_idx = start_idx + DARS_PER_PAGE
    current_darslar = darslar_sorted[start_idx:end_idx]

    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    # Darslarni 2 ustunda vertikal tartibda qo'shish
    for idx, dars in enumerate(current_darslar):
        dars_number = start_idx + idx + 1
        button_text = f"{dars_number}"

        # Har bir qatorda 2 ta tugma
        if idx % 2 == 0:
            if idx + 1 < len(current_darslar):
                # Juft indeks - yangi qator boshlanadi
                next_number = start_idx + idx + 2
                markup.row(
                    KeyboardButton(button_text),
                    KeyboardButton(f"{next_number}")
                )
            else:
                # Oxirgi toq element
                markup.row(KeyboardButton(button_text))

    # Navigatsiya tugmalari
    if page > 0 and page < total_pages - 1:
        # Ikkala tugma ham bor
        markup.row(
            KeyboardButton("⬅️ Oldingi"),
            KeyboardButton("Keyingi ➡️")
        )
    elif page > 0:
        # Faqat oldingi
        markup.row(KeyboardButton("⬅️ Oldingi"))
    elif page < total_pages - 1:
        # Faqat keyingi
        markup.row(KeyboardButton("Keyingi ➡️"))

    # Asosiy tugmalar
    markup.row(
        KeyboardButton("🔙 Mavzular"),
        KeyboardButton("🏠 Menu")
    )

    # Darslar ro'yxatini matn sifatida
    dars_list = ""
    for idx, dars in enumerate(current_darslar):
        dars_number = start_idx + idx + 1
        title = dars['title'][:40]
        downloads = dars['count_download']
        dars_list += f"{dars_number}. {title} ({downloads}📥)\n"

    text = (
        f"📚 <b>{faculty_name}</b>\n"
        f"📖 <b>{mavzu_name}</b>\n\n"
        f"{dars_list}\n"
        f"📊 Jami: {len(darslar_sorted)} ta | Sahifa: {page + 1}/{total_pages}"
    )

    await message.answer(text, reply_markup=markup, parse_mode="HTML")


# ==================== SAHIFA NAVIGATSIYA ====================
@dp.message_handler(lambda m: m.text in ["⬅️ Oldingi", "Keyingi ➡️", ""])
async def navigate_pages(message: types.Message):
    """Sahifalar bo'yicha navigatsiya"""
    if message.text == "":
        return

    user_id = message.from_user.id

    if user_id not in user_pagination:
        await message.answer("❌ Xato. Qaytadan mavzu tanlang.")
        return

    data = user_pagination[user_id]
    total_pages = (len(data['darslar']) + DARS_PER_PAGE - 1) // DARS_PER_PAGE

    if message.text == "Keyingi ➡️":
        if data['page'] < total_pages - 1:
            data['page'] += 1
    elif message.text == "⬅️ Oldingi":
        if data['page'] > 0:
            data['page'] -= 1

    await show_darslar_page(message, user_id)


# ==================== DARS RAQAMI ORQALI TANLASH ====================
@dp.message_handler(lambda m: m.text and m.text.isdigit())
async def select_dars_by_number(message: types.Message):
    """Raqam orqali dars tanlash"""
    user_id = message.from_user.id

    if user_id not in user_pagination:
        return

    dars_number = int(message.text)
    data = user_pagination[user_id]

    # Darslarni saralash (xuddi ko'rsatilgandek)
    import re
    def natural_sort_key(dars):
        title = dars['title']
        parts = re.split(r'(\d+)', title)
        return [int(part) if part.isdigit() else part.lower() for part in parts]

    darslar = sorted(data['darslar'], key=natural_sort_key)

    # Dars indeksini hisoblash
    dars_index = dars_number - 1

    if dars_index < 0 or dars_index >= len(darslar):
        await message.answer("❌ Noto'g'ri raqam")
        return

    selected_dars = darslar[dars_index]
    selected = dars_db.search_dars_by_code(selected_dars['code'])

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


# ==================== DARS TANLASH ====================
@dp.message_handler(lambda m: m.text and m.text.startswith("🎯 "))
async def select_dars(message: types.Message):
    """Dars yuklash"""
    # Dars nomini olish
    dars_text = message.text[2:].strip()
    dars_title = dars_text.split(" (")[0].strip() if " (" in dars_text else dars_text.strip()

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

    # Darsni topish - yangilangan qidiruv
    all_darslar = dars_db.get_dars_by_fakultet(fakultet_id)
    selected = None

    # Avval to'liq nom bo'yicha qidirish
    for dars in all_darslar:
        if dars['title'] == dars_title:
            selected = dars_db.search_dars_by_code(dars['code'])
            break

    # Agar topilmasa, qisqartirilgan nom bo'yicha qidirish
    if not selected:
        for dars in all_darslar:
            # Dars nomini 50 belgigacha qisqartirish (klaviaturadagi kabi)
            short_title = dars['title'][:50]
            if short_title == dars_title or dars['title'].startswith(dars_title):
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
    # Sahifalash ma'lumotlarini tozalash
    if message.from_user.id in user_pagination:
        del user_pagination[message.from_user.id]

    await message.answer(
        "🎓 Fakultetingizni tanlang:",
        reply_markup=faculty_menu
    )


@dp.message_handler(text="🔙 Mavzular")
async def back_to_mavzular(message: types.Message):
    """Mavzularga qaytish"""
    # Sahifalash ma'lumotlarini tozalash
    if message.from_user.id in user_pagination:
        del user_pagination[message.from_user.id]

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


@dp.message_handler(text="🏠 Menu")
async def main_menu_short(message: types.Message):
    """Asosiy menyu (qisqa)"""
    # Sahifalash ma'lumotlarini tozalash
    if message.from_user.id in user_pagination:
        del user_pagination[message.from_user.id]

    if message.from_user.id in ADMINS or user_db.check_if_admin(message.from_user.id):
        await message.answer("👑 Admin panel:", reply_markup=admin_menu)
    else:
        await message.answer("🎓 Fakultetingizni tanlang:", reply_markup=faculty_menu)


@dp.message_handler(text="🏠 Asosiy menyu")
async def main_menu(message: types.Message):
    """Asosiy menyu"""
    # Sahifalash ma'lumotlarini tozalash
    if message.from_user.id in user_pagination:
        del user_pagination[message.from_user.id]

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