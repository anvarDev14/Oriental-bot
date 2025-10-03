# handlers/users/middleware.py
from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import MessageNotModified, BotBlocked, ChatNotFound, UserDeactivated
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from data.config import ADMINS
from loader import bot, user_db, channel_db, dp
import logging

logger = logging.getLogger(__name__)


class SubscriptionMiddleware(BaseMiddleware):
    """Obuna majburiy middleware - State support bilan"""

    # Cache uchun
    _subscription_cache = {}
    _cache_duration = 30  # 30 soniya

    # Obuna shart bo'lmagan buyruqlar
    ALLOWED_COMMANDS = {'/start', '/help', '/admin', '/cancel'}
    ALLOWED_CALLBACKS = {
        'check_subscription',
        'faculty_back',
        'no_action',
        'invalid_channel'
    }




    async def on_pre_process_update(self, update: types.Update, data: dict):
        """Har bir yangilanish oldidan bajariladi"""
        try:
            # Foydalanuvchi ma'lumotlarini olish
            user_info = self._extract_user_info(update)
            if not user_info:
                return

            user_id, chat_id, message = user_info

            # Admin tekshiruvi
            if await self._is_admin(user_id):
                return

            # Shaxsiy chat tekshiruvi
            if message.chat.type != "private":
                await self._handle_group_chat(message, update)
                raise CancelHandler()

            # STATE tekshiruvi - ENG MUHIM!
            if await self._is_in_state(user_id, chat_id):
                return  # State da bo'lsa obuna tekshirmaslik

            # Ruxsat berilgan buyruqlar
            if await self._is_allowed_action(update, user_id, chat_id):
                return

            # Obuna tekshiruvi
            if not await self._check_subscription(user_id):
                await self._handle_unsubscribed_user(user_id, message, update)
                raise CancelHandler()

        except CancelHandler:
            raise
        except Exception as e:
            logger.error(f"Middleware xatolik: {e}")
            return  # Xatolik bo'lsa, davom etish

    async def _is_in_state(self, user_id: int, chat_id: int) -> bool:
        """Foydalanuvchi state da ekanligini tekshirish"""
        try:
            state = dp.current_state(chat=chat_id, user=user_id)
            current_state = await state.get_state()

            if current_state:
                logger.info(f"State mavjud: {current_state} (user: {user_id}), middleware skip")
                return True

            return False
        except Exception as e:
            logger.error(f"State tekshirish xatolik: {e}")
            return False

    def _extract_user_info(self, update: types.Update):
        """Update dan foydalanuvchi ma'lumotlarini ajratib olish"""
        user_id = None
        chat_id = None
        message = None

        if update.message:
            user_id = update.message.from_user.id
            chat_id = update.message.chat.id
            message = update.message
        elif update.callback_query and update.callback_query.message:
            user_id = update.callback_query.from_user.id
            chat_id = update.callback_query.message.chat.id
            message = update.callback_query.message
        else:
            return None

        if not all([user_id, chat_id, message]):
            return None

        return user_id, chat_id, message

    async def _is_admin(self, user_id: int) -> bool:
        """Admin tekshiruvi"""
        try:
            # Config adminlar
            if isinstance(ADMINS, list) and user_id in ADMINS:
                return True

            # Database adminlar
            if user_db and user_db.check_if_admin(user_id):
                return True

            return False
        except Exception as e:
            logger.error(f"Admin tekshirish xatolik: {e}")
            return False

    async def _is_allowed_action(self, update: types.Update, user_id: int, chat_id: int) -> bool:
        """Ruxsat berilgan harakat tekshiruvi"""
        try:
            # Buyruq tekshiruvi
            if update.message and update.message.text:
                text = update.message.text.strip()
                command = text.split()[0].lower()

                if command in self.ALLOWED_COMMANDS:
                    return True

                # Admin panel tugmalari
                admin_buttons = [
                    "➕ Dars Qo'shish",
                    "🗑 Dars O'chirish",
                    "➕ Fakultet Qo'shish",
                    "🗑 Fakultet O'chirish",
                    "📊 Statistika",
                    "🔙 Admin menyu",
                    "📣 Reklama",
                    "📢 Kanallar",
                    "👤 Admin Qo'shish",
                    "🗑 Admin O'chirish",
                    "📋 Adminlar Ro'yxati",
                    "✅Tasdiqlash",
                    "❌Bekor qilish"
                ]

                if text in admin_buttons:
                    # Admin ekanligini tekshirish
                    if await self._is_admin(user_id):
                        return True

            # Callback tekshiruvi
            if update.callback_query and update.callback_query.data:
                callback_data = update.callback_query.data

                # To'g'ridan-to'g'ri ruxsat berilgan
                if callback_data in self.ALLOWED_CALLBACKS:
                    return True

                # Prefiks bo'yicha ruxsat berish
                allowed_prefixes = [
                    'add_course_',
                    'del_fakultet_',
                    'fakultetdel_',
                ]

                for prefix in allowed_prefixes:
                    if callback_data.startswith(prefix):
                        if await self._is_admin(user_id):
                            return True

            return False
        except Exception as e:
            logger.error(f"Ruxsat tekshirish xatolik: {e}")
            return False

    async def _check_subscription(self, user_id: int) -> bool:
        """Obuna holatini tekshirish"""
        try:
            # Cache dan tekshirish
            import time
            current_time = time.time()

            if user_id in self._subscription_cache:
                cache_data = self._subscription_cache[user_id]
                if current_time - cache_data['timestamp'] < self._cache_duration:
                    return cache_data['subscribed']

            # Database dan kanallarni olish
            if not channel_db:
                return True

            channels = channel_db.get_all_channels()
            if not channels:
                return True

            # Har bir kanalga obuna tekshirish
            for channel_id, _, _ in channels:
                if not await self._check_single_channel(user_id, channel_id):
                    # Cache ga saqlash
                    self._subscription_cache[user_id] = {
                        'subscribed': False,
                        'timestamp': current_time
                    }
                    return False

            # Barcha kanallarga obuna
            self._subscription_cache[user_id] = {
                'subscribed': True,
                'timestamp': current_time
            }
            return True

        except Exception as e:
            logger.error(f"Obuna tekshirish xatolik: {e}")
            return True  # Xatolik bo'lsa ruxsat berish

    async def _check_single_channel(self, user_id: int, channel_id: int) -> bool:
        """Bitta kanalga obuna tekshirish"""
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            return member.status in ["member", "administrator", "creator"]
        except Exception as e:
            logger.warning(f"Kanal {channel_id} tekshirish xatolik: {e}")
            return False

    async def _get_unsubscribed_channels(self, user_id: int) -> list:
        """Obuna bo'lmagan kanallar ro'yxati"""
        try:
            if not channel_db:
                return []

            channels = channel_db.get_all_channels()
            if not channels:
                return []

            unsubscribed = []
            for channel_id, title, link in channels:
                if not await self._check_single_channel(user_id, channel_id):
                    unsubscribed.append((link, title))

            return unsubscribed
        except Exception as e:
            logger.error(f"Obuna bo'lmagan kanallar xatolik: {e}")
            return []

    def _build_subscription_keyboard(self, unsubscribed_channels: list) -> InlineKeyboardMarkup:
        """Obuna klaviaturasini yaratish"""
        markup = InlineKeyboardMarkup(row_width=1)

        if not unsubscribed_channels:
            return markup

        for index, (invite_link, title) in enumerate(unsubscribed_channels, start=1):
            if invite_link and invite_link.startswith("https://t.me/"):
                # Nom uzunligini cheklash
                display_title = title[:25] + "..." if len(title) > 25 else title
                markup.add(InlineKeyboardButton(
                    f"{index}. 📢 {display_title}",
                    url=invite_link
                ))
            else:
                markup.add(InlineKeyboardButton(
                    f"{index}. ❌ Noto'g'ri havola",
                    callback_data="no_action"
                ))

        # Tekshirish tugmasi
        markup.add(InlineKeyboardButton(
            "✅ Obuna bo'ldim, tekshirish",
            callback_data="check_subscription"
        ))

        return markup

    async def _handle_group_chat(self, message: types.Message, update: types.Update):
        """Guruh chatda bo'lganda ishlov berish"""
        try:
            if update.message and update.message.chat.type != "channel":
                await message.reply(
                    "🤖 <b>Bot faqat shaxsiy chatda ishlaydi!</b>\n"
                    "📩 Menga shaxsiy xabar yuboring.",
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Guruh javob xatolik: {e}")

    async def _handle_unsubscribed_user(self, user_id: int, message: types.Message, update: types.Update):
        """Obuna bo'lmagan foydalanuvchini boshqarish"""
        try:
            unsubscribed = await self._get_unsubscribed_channels(user_id)

            if not unsubscribed:
                logger.warning("Obuna kanallar yo'q, lekin middleware ishlayabdi")
                return

            text = (
                "🔐 <b>Botdan foydalanish uchun obuna bo'ling!</b>\n\n"
                f"📢 {len(unsubscribed)} ta kanalga obuna bo'lishingiz kerak.\n"
                "👇 Quyidagi kanallarga obuna bo'ling:\n\n"
                "⚡ <i>Obuna bo'lgandan keyin \"✅ Obuna bo'ldim\" tugmasini bosing!</i>"
            )

            markup = self._build_subscription_keyboard(unsubscribed)

            if update.callback_query:
                # Callback query uchun
                await self._edit_or_send_message(message, text, markup)
            else:
                # Oddiy message uchun
                await self._send_subscription_message(message, text, markup)

        except Exception as e:
            logger.error(f"Obuna xabar yuborish xatolik: {e}")

    async def _edit_or_send_message(self, message: types.Message, text: str, markup: InlineKeyboardMarkup):
        """Xabarni edit qilish yoki yangi yuborish"""
        try:
            if (message.text != text or
                    not message.reply_markup or
                    str(message.reply_markup) != str(markup)):
                await message.edit_text(text, reply_markup=markup, parse_mode="HTML")
        except MessageNotModified:
            pass  # Xabar bir xil
        except Exception as e:
            logger.warning(f"Edit xatolik: {e}")
            try:
                await message.answer(text, reply_markup=markup, parse_mode="HTML")
            except Exception as e2:
                logger.error(f"Yangi xabar yuborish xatolik: {e2}")

    async def _send_subscription_message(self, message: types.Message, text: str, markup: InlineKeyboardMarkup):
        """Obuna xabarini yuborish"""
        try:
            await message.answer(text, reply_markup=markup, parse_mode="HTML")
        except BotBlocked:
            logger.info(f"Bot bloklangan: {message.from_user.id}")
        except ChatNotFound:
            logger.warning(f"Chat topilmadi: {message.chat.id}")
        except UserDeactivated:
            logger.info(f"Foydalanuvchi deaktivlangan: {message.from_user.id}")
        except Exception as e:
            logger.error(f"Obuna xabar yuborish xatolik: {e}")

            # Fallback - sodda xabar
            try:
                await message.answer(
                    "🔐 Botdan foydalanish uchun kanallarga obuna bo'ling!\n"
                    "/start buyrug'ini ishlatib obuna bo'ling."
                )
            except Exception as e2:
                logger.error(f"Fallback xabar ham yuborilmadi: {e2}")

    async def on_post_process_update(self, update: types.Update, result, data: dict):
        """Update dan keyin bajariladigan ishlar"""
        try:
            # Foydalanuvchi faolligini yangilash
            user_id = None
            if update.message:
                user_id = update.message.from_user.id
            elif update.callback_query:
                user_id = update.callback_query.from_user.id

            if user_id and user_db and user_db.select_user(user_id):
                user_db.update_last_active(user_id)

        except Exception as e:
            logger.error(f"Post process xatolik: {e}")

    def clear_cache(self):
        """Cache ni tozalash"""
        self._subscription_cache.clear()

    def get_cache_stats(self) -> dict:
        """Cache statistikasi"""
        import time
        current_time = time.time()
        active_cache = 0

        for user_data in self._subscription_cache.values():
            if current_time - user_data['timestamp'] < self._cache_duration:
                active_cache += 1

        return {
            'total_cached': len(self._subscription_cache),
            'active_cache': active_cache,
            'cache_duration': self._cache_duration
        }