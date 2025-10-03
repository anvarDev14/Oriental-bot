"""
User Database - Optimallashtirilgan va dublikatsiz
"""
from .database import Database
from datetime import datetime, timedelta
import pytz
import logging

logger = logging.getLogger(__name__)


class UserDatabase(Database):
    def __init__(self, path_to_db: str):
        super().__init__(path_to_db)
        self.tz = pytz.timezone("Asia/Tashkent")

    def _now(self):
        """Joriy vaqt"""
        return datetime.now(self.tz)

    def _start_of_day(self, date=None):
        """Kun boshlanishi"""
        d = date or self._now()
        return d.replace(hour=0, minute=0, second=0, microsecond=0)

    def create_table(self):
        """Users jadvalini yaratish"""
        sql = """
        CREATE TABLE IF NOT EXISTS Users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id BIGINT NOT NULL UNIQUE,
            username VARCHAR(255),
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            faculty VARCHAR(255),
            is_blocked BOOLEAN DEFAULT 0,
            is_admin BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_active DATETIME,
            total_downloads INTEGER DEFAULT 0
        )
        """
        self.execute(sql, commit=True)
        logger.info("✅ Users table ready")

    # ==================== CRUD ====================
    def add_user(self, telegram_id, username=None, first_name=None,
                 last_name=None, faculty=None):
        """Foydalanuvchi qo'shish"""
        sql = """
        INSERT OR IGNORE INTO Users(telegram_id, username, first_name, 
                                    last_name, faculty, created_at, last_active) 
        VALUES(?, ?, ?, ?, ?, ?, ?)
        """
        now = self._now().isoformat()
        self.execute(sql, (telegram_id, username, first_name,
                          last_name, faculty, now, now), commit=True)

    def select_user(self, telegram_id):
        """Foydalanuvchi ma'lumotlari"""
        sql = "SELECT * FROM Users WHERE telegram_id = ?"
        return self.execute(sql, (telegram_id,), fetchone=True)

    def update_user_info(self, telegram_id, username, first_name, last_name):
        """Ma'lumotlarni yangilash"""
        sql = """
        UPDATE Users SET username=?, first_name=?, last_name=? 
        WHERE telegram_id=?
        """
        self.execute(sql, (username, first_name, last_name, telegram_id), commit=True)

    def update_last_active(self, telegram_id):
        """Faollik vaqtini yangilash"""
        sql = "UPDATE Users SET last_active=? WHERE telegram_id=?"
        self.execute(sql, (self._now().isoformat(), telegram_id), commit=True)

    # ==================== FAKULTET ====================
    def update_faculty(self, telegram_id, faculty):
        """Fakultet belgilash"""
        sql = "UPDATE Users SET faculty=? WHERE telegram_id=?"
        self.execute(sql, (faculty, telegram_id), commit=True)

    def get_user_faculty(self, telegram_id):
        """Foydalanuvchi fakulteti"""
        user = self.select_user(telegram_id)
        return user['faculty'] if user else None

    # ==================== ADMIN ====================
    def check_if_admin(self, telegram_id):
        """Admin tekshirish"""
        user = self.select_user(telegram_id)
        return bool(user and user['is_admin'])

    def set_admin(self, telegram_id):
        """Admin qilish"""
        sql = "UPDATE Users SET is_admin=1 WHERE telegram_id=?"
        self.execute(sql, (telegram_id,), commit=True)

    def remove_admin(self, telegram_id):
        """Adminlikdan olish"""
        sql = "UPDATE Users SET is_admin=0 WHERE telegram_id=?"
        self.execute(sql, (telegram_id,), commit=True)

    def get_all_admins(self):
        """Barcha adminlar"""
        sql = """
        SELECT telegram_id, username, first_name, last_name 
        FROM Users WHERE is_admin=1
        """
        return self.execute(sql, fetchall=True)

    # ==================== STATISTIKA ====================
    def count_users(self):
        """Jami foydalanuvchilar"""
        sql = "SELECT COUNT(*) FROM Users WHERE is_blocked=0"
        result = self.execute(sql, fetchone=True)
        return result[0] if result else 0

    def count_daily_users(self):
        """Bugungi yangi foydalanuvchilar"""
        today = self._start_of_day()
        tomorrow = today + timedelta(days=1)
        sql = "SELECT COUNT(*) FROM Users WHERE created_at >= ? AND created_at < ?"
        result = self.execute(sql, (today.isoformat(), tomorrow.isoformat()), fetchone=True)
        return result[0] if result else 0

    def count_weekly_users(self):
        """Haftalik yangi foydalanuvchilar"""
        week_ago = self._now() - timedelta(days=7)
        sql = "SELECT COUNT(*) FROM Users WHERE created_at >= ?"
        result = self.execute(sql, (week_ago.isoformat(),), fetchone=True)
        return result[0] if result else 0

    def count_monthly_users(self):
        """Oylik yangi foydalanuvchilar"""
        month_ago = self._now() - timedelta(days=30)
        sql = "SELECT COUNT(*) FROM Users WHERE created_at >= ?"
        result = self.execute(sql, (month_ago.isoformat(),), fetchone=True)
        return result[0] if result else 0

    def count_active_daily_users(self):
        """Bugun faol foydalanuvchilar"""
        today = self._start_of_day()
        tomorrow = today + timedelta(days=1)
        sql = """
        SELECT COUNT(*) FROM Users 
        WHERE last_active >= ? AND last_active < ? AND is_blocked=0
        """
        result = self.execute(sql, (today.isoformat(), tomorrow.isoformat()), fetchone=True)
        return result[0] if result else 0

    def count_active_weekly_users(self):
        """Hafta faol foydalanuvchilar"""
        week_ago = self._now() - timedelta(days=7)
        sql = "SELECT COUNT(*) FROM Users WHERE last_active >= ? AND is_blocked=0"
        result = self.execute(sql, (week_ago.isoformat(),), fetchone=True)
        return result[0] if result else 0

    def count_active_monthly_users(self):
        """Oy faol foydalanuvchilar"""
        month_ago = self._now() - timedelta(days=30)
        sql = "SELECT COUNT(*) FROM Users WHERE last_active >= ? AND is_blocked=0"
        result = self.execute(sql, (month_ago.isoformat(),), fetchone=True)
        return result[0] if result else 0

    def count_users_by_faculty(self, faculty):
        """Fakultet bo'yicha foydalanuvchilar"""
        sql = "SELECT COUNT(*) FROM Users WHERE faculty=? AND is_blocked=0"
        result = self.execute(sql, (faculty,), fetchone=True)
        return result[0] if result else 0

    def get_faculty_distribution(self):
        """Fakultet taqsimoti"""
        sql = """
        SELECT faculty, COUNT(*) as count
        FROM Users 
        WHERE is_blocked=0 AND faculty IS NOT NULL
        GROUP BY faculty 
        ORDER BY count DESC
        """
        return self.execute(sql, fetchall=True)

    def get_top_downloaders(self, limit=10):
        """Eng ko'p yuklovchilar"""
        sql = """
        SELECT telegram_id, username, first_name, total_downloads, faculty
        FROM Users 
        WHERE is_blocked=0 AND total_downloads > 0
        ORDER BY total_downloads DESC 
        LIMIT ?
        """
        return self.execute(sql, (limit,), fetchall=True)

    def increment_downloads(self, telegram_id):
        """Yuklanish +1"""
        sql = "UPDATE Users SET total_downloads = total_downloads + 1 WHERE telegram_id=?"
        self.execute(sql, (telegram_id,), commit=True)

    # ==================== QIDIRISH ====================
    def select_all_users(self):
        """Barcha foydalanuvchilar"""
        sql = "SELECT * FROM Users ORDER BY created_at DESC"
        return self.execute(sql, fetchall=True)

    def search_users(self, query):
        """Qidirish"""
        sql = """
        SELECT telegram_id, username, first_name, last_name, faculty
        FROM Users 
        WHERE (username LIKE ? OR first_name LIKE ? OR last_name LIKE ?) 
        AND is_blocked=0
        """
        q = f"%{query}%"
        return self.execute(sql, (q, q, q), fetchall=True)

    # ==================== BLOK ====================
    def block_user(self, telegram_id):
        """Bloklash"""
        sql = "UPDATE Users SET is_blocked=1 WHERE telegram_id=?"
        self.execute(sql, (telegram_id,), commit=True)

    def unblock_user(self, telegram_id):
        """Blokdan chiqarish"""
        sql = "UPDATE Users SET is_blocked=0 WHERE telegram_id=?"
        self.execute(sql, (telegram_id,), commit=True)