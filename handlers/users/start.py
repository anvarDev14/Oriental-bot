"""
Start Handler - To'liq optimallashtirilgan
Dublikatlar yo'q, toza kod
"""
from aiogram import types
from aiogram.dispatcher.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from data.config import ADMINS, STICKERS
from keyboards.default.admin_menu import admin_menu
from keyboards.inline.fakultet import faculty_menu,FACULTY_MAPPING
from loader import dp, bot, user_db, channel_db
import asyncio
import logging

logger = logging.getLogger(__name__)


# ==================== OBUNA TEKSHIRISH ====================
async def check_channel_subscription(user_id: int, channel_id: int) -> bool:
    """Bitta kanal tekshirish"""
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.warning(f"Kanal tekshirish xatosi {channel_id}: {e}")
        return False


async def check_all_subscriptions(user_id: int) -> bool:
    """Barcha kanallar tekshirish"""
    channels = channel_db.get_all_channels()
    if not channels:
        return True

    for channel_id, _, _ in channels:
        if not await check_channel_subscription(user_id, channel_id):
            return False
    return True


async def get_unsubscribed_channels(user_id: int) -> list:
    """Obuna bo'lmagan kanallar"""
    channels = channel_db.get_all_channels()
    unsubscribed = []

    for channel_id, title, link in channels:
        if not await check_channel_subscription(user_id, channel_id):
            unsubscribed.append((link, title))

    return unsubscribed


def build_subscription_keyboard(unsubscribed: list) -> InlineKeyboardMarkup:
    """Obuna klaviaturasi"""
    markup = InlineKeyboardMarkup(row_width=1)

    for idx, (link, title) in enumerate(unsubscribed, 1):
        if link and link.startswith("https://t.me/"):
            markup.add(InlineKeyboardButton(
                f"{idx}. 📢 {title[:25]}{'...' if len(title) > 25 else ''}",
                url=link
            ))

    markup.add(InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub"))
    return markup


# ==================== RO'YXATGA OLISH ====================
async def register_user(user_id, username, first_name, last_name):
    """Foydalanuvchini ro'yxatga olish"""
    try:
        user = user_db.select_user(user_id)

        if not user:
            user_db.add_user(user_id, username, first_name, last_name)
            logger.info(f"➕ Yangi user: {user_id}")

            # Adminlarga xabar
            total = user_db.count_users()
            for admin_id in ADMINS:
                try:
                    await bot.send_sticker(admin_id, STICKERS['new_user'])
                    await bot.send_message(
                        admin_id,
                        f"🆕 <b>Yangi foydalanuvchi!</b>\n\n"
                        f"👤 {first_name or 'Nomsiz'}\n"
                        f"🆔 <code>{user_id}</code>\n"
                        f"📱 @{username or 'Yoq'}\n"
                        f"👥 Jami: {total} ta",
                        parse_mode="HTML"
                    )
                except:
                    pass
        else:
            user_db.update_user_info(user_id, username, first_name, last_name)
            user_db.update_last_active(user_id)

        return True
    except Exception as e:
        logger.error(f"Register xato: {e}")
        return False


# ==================== AVTOMATIK TEKSHIRUV ====================
async def auto_check_subscription(user_id: int, message: types.Message):
    """Avtomatik obuna tekshirish"""
    for attempt in range(60):
        await asyncio.sleep(3)

        try:
            if await check_all_subscriptions(user_id):
                await message.edit_text(
                    "✅ <b>Tabriklaymiz!</b>\n\n"
                    "🎓 Botga xush kelibsiz!\n"
                    "📚 Fakultetingizni tanlang:",
                    reply_markup=faculty_menu,
                    parse_mode="HTML"
                )
                return
        except:
            break

    # Vaqt tugadi
    try:
        await message.edit_text(
            "⏰ <b>Vaqt tugadi</b>\n\n"
            "🔄 Qaytadan /start bosing",
            parse_mode="HTML"
        )
    except:
        pass


# ==================== START HANDLER ====================
@dp.message_handler(CommandStart())
async def start_handler(message: types.Message):
    """Start buyrug'i"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    full_name = message.from_user.full_name

    # Guruhda ishlamasligi
    if message.chat.type != "private":
        await message.reply("❗ Bot faqat shaxsiy chatda ishlaydi")
        return

    # Admin tekshirish
    if user_id in ADMINS or user_db.check_if_admin(user_id):
        await message.answer(
            f"👑 <b>Admin Panel</b>\n\n"
            f"Salom, {full_name}!\n\n"
            f"📊 Statistika:\n"
            f"• Jami: {user_db.count_users()} ta\n"
            f"• Bugun: +{user_db.count_daily_users()} ta\n"
            f"• Faol: {user_db.count_active_daily_users()} ta",
            reply_markup=admin_menu,
            parse_mode="HTML"
        )
        return

    # Ro'yxatga olish
    if not await register_user(user_id, username, first_name, last_name):
        await message.answer("❌ Xatolik yuz berdi")
        return

    # Kanallar tekshirish
    channels = channel_db.get_all_channels()

    if not channels:
        # Kanallar yo'q
        await message.answer(
            f"🎓 <b>Oriental Universiteti</b>\n\n"
            f"👋 Assalomu alaykum, {full_name}!\n"
            f"📚 Fakultetingizni tanlang:",
            reply_markup=faculty_menu,
            parse_mode="HTML"
        )
        return

    # Obuna tekshirish
    if await check_all_subscriptions(user_id):
        await message.answer(
            f"✅ <b>Obuna tasdiqlandi!</b>\n\n"
            f"👋 Xush kelibsiz, {full_name}!\n"
            f"📚 Fakultetingizni tanlang:",
            reply_markup=faculty_menu,
            parse_mode="HTML"
        )
    else:
        # Obuna yo'q
        unsubscribed = await get_unsubscribed_channels(user_id)
        keyboard = build_subscription_keyboard(unsubscribed)

        msg = await message.answer(
            f"🔐 <b>Obuna bo'ling!</b>\n\n"
            f"👋 Salom, {full_name}!\n"
            f"📢 Kanallarga obuna bo'ling\n\n"
            f"🎯 Avtomatik tekshiruv boshlanadi...",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        # Avtomatik tekshiruv
        asyncio.create_task(auto_check_subscription(user_id, msg))


# ==================== OBUNA CALLBACK ====================
@dp.callback_query_handler(lambda c: c.data == "check_sub")
async def check_subscription_callback(call: types.CallbackQuery):
    """Qo'lda obuna tekshirish"""
    user_id = call.from_user.id
    full_name = call.from_user.full_name

    await call.answer("🔄 Tekshirish...")

    # Admin
    if user_id in ADMINS or user_db.check_if_admin(user_id):
        await call.message.edit_text("👑 Siz adminsiz!")
        await call.message.answer("Admin panel:", reply_markup=admin_menu)
        return

    # Ro'yxatga olish
    await register_user(
        user_id,
        call.from_user.username,
        call.from_user.first_name,
        call.from_user.last_name
    )

    # Obuna tekshirish
    if await check_all_subscriptions(user_id):
        await call.message.edit_text(
            f"🎉 <b>Zo'r!</b>\n\n"
            f"✅ Obuna tasdiqlandi!\n"
            f"👋 Xush kelibsiz, {full_name}!\n"
            f"📚 Fakultetingizni tanlang:",
            reply_markup=faculty_menu,
            parse_mode="HTML"
        )
    else:
        unsubscribed = await get_unsubscribed_channels(user_id)
        keyboard = build_subscription_keyboard(unsubscribed)

        await call.message.edit_text(
            f"❌ <b>Hali to'liq emas!</b>\n\n"
            f"⚠️ {len(unsubscribed)} ta kanal qoldi\n"
            f"👇 Qolgan kanallarga obuna bo'ling:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )