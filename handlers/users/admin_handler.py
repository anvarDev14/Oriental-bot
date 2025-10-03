"""
Admin Handlers - TO'G'RI versiya
"""
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from data.config import ADMINS
from keyboards.default.admin_menu import admin_menu
from keyboards.default.confirm_menu import confirm_menu
from loader import dp, bot, dars_db, user_db
import logging

logger = logging.getLogger(__name__)


# ==================== STATES ====================
class AddCourse(StatesGroup):
    fakultet = State()
    mavzu = State()
    code = State()
    title = State()
    file = State()


class DeleteCourse(StatesGroup):
    code = State()
    confirm = State()


class AddFakultet(StatesGroup):
    name = State()


# ==================== ADMIN TEKSHIRISH ====================
def is_admin(user_id: int) -> bool:
    """Admin tekshirish"""
    return user_id in ADMINS or user_db.check_if_admin(user_id)


# ==================== FAQAT ASOSIY MENYU VA BEKOR QILISH ====================
@dp.message_handler(Text(equals=["🏠 Asosiy menyu", "❌ Bekor qilish", "/cancel"], ignore_case=True), state="*")
async def exit_to_main_menu(message: types.Message, state: FSMContext):
    """
    FAQAT asosiy menyu va bekor qilish tugmalari state dan chiqaradi
    Boshqa tugmalar oddiy ishlaydi
    """
    current_state = await state.get_state()

    if current_state:
        await state.finish()
        logger.info(f"✅ State bekor qilindi: {current_state}")

    if is_admin(message.from_user.id):
        await message.answer(
            "✅ Jarayon bekor qilindi\n\n👑 Admin panel:",
            reply_markup=admin_menu
        )
    else:
        await message.answer("✅ Bekor qilindi")


# ==================== DARS QO'SHISH ====================
@dp.message_handler(lambda m: m.text == "➕ Dars Qo'shish" and is_admin(m.from_user.id))
async def start_add_course(message: types.Message):
    """Dars qo'shishni boshlash"""
    fakultetlar = dars_db.get_all_fakultetlar()

    if not fakultetlar:
        await message.answer(
            "❌ Avval fakultet qo'shing!",
            reply_markup=admin_menu
        )
        return

    markup = InlineKeyboardMarkup(row_width=1)
    for fak in fakultetlar:
        # sqlite3.Row yoki tuple
        if isinstance(fak, tuple):
            fak_id = fak[0]
            fak_name = fak[1]
        else:
            # sqlite3.Row - index orqali
            fak_id = fak[0]
            fak_name = fak[1]

        markup.add(InlineKeyboardButton(
            f"📚 {fak_name}",
            callback_data=f"addfak_{fak_id}"
        ))

    await message.answer(
        "📚 <b>Dars qo'shish</b>\n\n"
        "Fakultetni tanlang:\n\n"
        "❌ Bekor qilish: Asosiy menyu yoki /cancel",
        reply_markup=markup,
        parse_mode="HTML"
    )
    await AddCourse.fakultet.set()


@dp.callback_query_handler(lambda c: c.data.startswith("addfak_"), state=AddCourse.fakultet)
async def select_fakultet(call: types.CallbackQuery, state: FSMContext):
    """Fakultet tanlash"""
    fak_id = int(call.data.split("_")[1])
    fakultetlar = dars_db.get_all_fakultetlar()
    fak_name = None

    for fak in fakultetlar:
        # sqlite3.Row yoki tuple
        if isinstance(fak, tuple):
            f_id = fak[0]
            f_name = fak[1]
        else:
            # sqlite3.Row - index
            f_id = fak[0]
            f_name = fak[1]

        if f_id == fak_id:
            fak_name = f_name
            break

    if not fak_name:
        await call.answer("❌ Xato")
        await state.finish()
        return

    async with state.proxy() as data:
        data['fakultet_id'] = fak_id
        data['fakultet_name'] = fak_name

    await call.message.edit_text(
        f"✅ Fakultet: <b>{fak_name}</b>\n\n"
        f"📖 Mavzu nomini kiriting:",
        parse_mode="HTML"
    )
    await AddCourse.mavzu.set()
    await call.answer()


@dp.message_handler(state=AddCourse.mavzu)
async def add_mavzu(message: types.Message, state: FSMContext):
    """Mavzu qo'shish"""
    mavzu = message.text.strip()

    if len(mavzu) < 2:
        return await message.answer("❌ Mavzu juda qisqa")

    async with state.proxy() as data:
        data['mavzu'] = mavzu

    await message.answer(
        f"✅ Mavzu: <b>{mavzu}</b>\n\n"
        f"🔢 Dars kodini kiriting:",
        parse_mode="HTML"
    )
    await AddCourse.code.set()


@dp.message_handler(state=AddCourse.code)
async def add_code(message: types.Message, state: FSMContext):
    """Kod kiriting"""
    code = message.text.strip().upper()

    if len(code) < 3:
        return await message.answer("❌ Kod kamida 3 ta belgi")

    if dars_db.search_dars_by_code(code):
        return await message.answer(f"❌ Bu kod mavjud: {code}")

    async with state.proxy() as data:
        data['code'] = code

    await message.answer(
        f"✅ Kod: <b>{code}</b>\n\n"
        f"📝 Dars nomini kiriting:",
        parse_mode="HTML"
    )
    await AddCourse.title.set()


@dp.message_handler(state=AddCourse.title)
async def add_title(message: types.Message, state: FSMContext):
    """Dars nomini kiriting"""
    title = message.text.strip()

    if len(title) < 2:
        return await message.answer("❌ Nom juda qisqa")

    async with state.proxy() as data:
        data['title'] = title
        mavzu = data.get('mavzu', '')
        code = data.get('code', '')

    await message.answer(
        f"📋 <b>Ma'lumotlar:</b>\n\n"
        f"📖 Mavzu: {mavzu}\n"
        f"🔢 Kod: {code}\n"
        f"📝 Nom: {title}\n\n"
        f"📎 Fayl yuboring:",
        parse_mode="HTML"
    )
    await AddCourse.file.set()


@dp.message_handler(content_types=['document', 'audio', 'video', 'voice', 'video_note'], state=AddCourse.file)
async def add_file(message: types.Message, state: FSMContext):
    """Fayl yuklash"""
    try:
        file_id = None
        file_name = "file"
        file_size = 0

        if message.document:
            file_id = message.document.file_id
            file_name = message.document.file_name
            file_size = message.document.file_size
        elif message.audio:
            file_id = message.audio.file_id
            file_name = message.audio.title or "audio"
            file_size = message.audio.file_size
        elif message.video:
            file_id = message.video.file_id
            file_name = "video"
            file_size = message.video.file_size
        elif message.voice:
            file_id = message.voice.file_id
            file_name = "voice"
            file_size = message.voice.file_size
        elif message.video_note:
            file_id = message.video_note.file_id
            file_name = "video_note"
            file_size = message.video_note.file_size

        async with state.proxy() as data:
            fakultet_id = data['fakultet_id']
            fakultet_name = data['fakultet_name']
            mavzu = data['mavzu']
            code = data['code']
            title = data['title']

        # Darsni qo'shish
        dars_db.add_dars(
            dars_id=fakultet_id,
            code=code,
            title=title,
            file_id=file_id,
            mavzu_name=mavzu,
            file_name=file_name,
            file_size=file_size
        )

        size_mb = file_size / (1024 * 1024) if file_size else 0

        await message.answer(
            f"✅ <b>Dars qo'shildi!</b>\n\n"
            f"📚 Fakultet: {fakultet_name}\n"
            f"📖 Mavzu: {mavzu}\n"
            f"📝 Dars: {title}\n"
            f"🔢 Kod: {code}\n"
            f"📎 Fayl: {file_name}\n"
            f"💾 Hajm: {size_mb:.2f} MB",
            reply_markup=admin_menu,
            parse_mode="HTML"
        )

        logger.info(f"➕ Dars qo'shildi: {code}")

    except Exception as e:
        logger.error(f"Xato: {e}")
        await message.answer(f"❌ Xatolik: {e}", reply_markup=admin_menu)

    await state.finish()


# ==================== DARS O'CHIRISH ====================
@dp.message_handler(lambda m: m.text == "🗑 Dars O'chirish" and is_admin(m.from_user.id))
async def start_delete_course(message: types.Message):
    """Dars o'chirishni boshlash"""
    await DeleteCourse.code.set()
    await message.answer(
        "🗑 <b>Dars o'chirish</b>\n\n"
        "🔢 Dars kodini kiriting:",
        parse_mode="HTML"
    )


@dp.message_handler(state=DeleteCourse.code)
async def confirm_delete(message: types.Message, state: FSMContext):
    """O'chirishni tasdiqlash"""
    code = message.text.strip().upper()
    dars = dars_db.search_dars_by_code(code)

    if not dars:
        return await message.answer(f"❌ Dars topilmadi: {code}")

    # sqlite3.Row yoki tuple dan dict ga o'tkazish
    if isinstance(dars, tuple):
        title = dars[3] if len(dars) > 3 else "Noma'lum"
        downloads = dars[6] if len(dars) > 6 else 0
    else:
        # sqlite3.Row - index
        title = dars[3] if len(dars) > 3 else "Noma'lum"
        downloads = dars[6] if len(dars) > 6 else 0

    # MUHIM: sqlite3.Row ni emas, faqat kerakli ma'lumotlarni saqlash
    async with state.proxy() as data:
        data['code'] = code
        data['title'] = title  # Faqat str
        data['downloads'] = downloads  # Faqat int

    await message.answer(
        f"⚠️ <b>Tasdiqlash</b>\n\n"
        f"📖 Dars: {title}\n"
        f"🔢 Kod: {code}\n"
        f"📥 Yuklanish: {downloads}\n\n"
        f"❗ Bu qaytarilmaydi!",
        reply_markup=confirm_menu,
        parse_mode="HTML"
    )
    await DeleteCourse.confirm.set()


@dp.message_handler(lambda m: m.text == "✅Tasdiqlash", state=DeleteCourse.confirm)
async def delete_confirmed(message: types.Message, state: FSMContext):
    """O'chirildi"""
    try:
        async with state.proxy() as data:
            code = data['code']
            # title va downloads ham olinadi agar kerak bo'lsa

        dars_db.delete_dars(code)

        await message.answer(
            f"✅ Dars o'chirildi!\n\n🔢 Kod: {code}",
            reply_markup=admin_menu
        )

        logger.info(f"🗑 Dars o'chirildi: {code}")

    except Exception as e:
        await message.answer(f"❌ Xato: {e}", reply_markup=admin_menu)

    await state.finish()


# ==================== FAKULTET QO'SHISH ====================
@dp.message_handler(lambda m: m.text == "➕ Fakultet Qo'shish" and is_admin(m.from_user.id))
async def start_add_fakultet(message: types.Message):
    """Fakultet qo'shish"""
    await AddFakultet.name.set()
    await message.answer("🏫 Fakultet nomini kiriting:")


@dp.message_handler(state=AddFakultet.name)
async def add_fakultet(message: types.Message, state: FSMContext):
    """Fakultet qo'shish"""
    try:
        name = message.text.strip()
        dars_db.add_fakultet(name)

        await message.answer(
            f"✅ Fakultet qo'shildi!\n\n🏫 {name}",
            reply_markup=admin_menu
        )
        logger.info(f"➕ Fakultet: {name}")
    except Exception as e:
        await message.answer(
            f"❌ Xato: {e}\n\nFakultet mavjud bo'lsa, boshqa nom kiriting",
            reply_markup=admin_menu
        )

    await state.finish()


# ==================== STATISTIKA ====================
@dp.message_handler(lambda m: m.text == "📊 Statistika" and is_admin(m.from_user.id))
async def show_simple_stats(message: types.Message):
    """Oddiy statistika"""
    try:
        total = user_db.count_users()
        daily = user_db.count_daily_users()
        active = user_db.count_active_daily_users()

        await message.answer(
            f"📊 <b>Statistika</b>\n\n"
            f"👥 Jami: {total} ta\n"
            f"📅 Bugun: +{daily} ta\n"
            f"🔥 Faol: {active} ta",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")


# handlers/admin/admin_handlers.py ga qo'shing

@dp.message_handler(lambda m: m.text == "🔍 Darslarni Ko'rish" and is_admin(m.from_user.id))
async def list_all_courses(message: types.Message):
    """Barcha darslarni ko'rish"""
    try:
        # Eng oxirgi 20 ta darsni olish
        conn = dars_db.connection
        cursor = conn.cursor()
        cursor.execute("""
            SELECT code, title, created_at, length(file_id) as file_len
            FROM Lesson 
            ORDER BY created_at DESC 
            LIMIT 20
        """)
        darslar = cursor.fetchall()
        conn.close()

        if not darslar:
            return await message.answer("❌ Darslar yo'q")

        text = "📋 <b>Oxirgi darslar:</b>\n\n"
        for idx, dars in enumerate(darslar, 1):
            code = dars[0]
            title = dars[1][:30]
            date = dars[2][:10]
            file_len = dars[3]

            status = "✅" if file_len > 50 else "❌"
            text += f"{idx}. {status} <code>{code}</code> - {title}\n"

        text += "\n❌ = Noto'g'ri file ID"

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Xato: {e}")