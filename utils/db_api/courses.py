"""
Courses/Lessons Database - To'liq optimallashtirilgan
"""
from .database import Database
from datetime import datetime
import pytz
import logging

logger = logging.getLogger(__name__)


class CourseDatabase(Database):
    def __init__(self, path_to_db: str):
        super().__init__(path_to_db)
        self.tz = pytz.timezone("Asia/Tashkent")

    def _now(self):
        return datetime.now(self.tz).isoformat()

    def create_tables(self):
        """Jadvalarni yaratish"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS Fakultet (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Mavzu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fakultet_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (fakultet_id) REFERENCES Fakultet(id) ON DELETE CASCADE,
                UNIQUE(fakultet_id, name)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Lesson (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fakultet_id INTEGER NOT NULL,
                mavzu_id INTEGER,
                code TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                file_id VARCHAR(2000) NOT NULL,
                file_name TEXT,
                file_size INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                count_download INTEGER DEFAULT 0,
                FOREIGN KEY (fakultet_id) REFERENCES Fakultet(id) ON DELETE CASCADE,
                FOREIGN KEY (mavzu_id) REFERENCES Mavzu(id) ON DELETE SET NULL
            )
            """
        ]
        for sql in tables:
            self.execute(sql, commit=True)
        logger.info("✅ Tables ready")

    # ==================== FAKULTET ====================
    def add_fakultet(self, name):
        """Fakultet qo'shish"""
        sql = "INSERT INTO Fakultet(name) VALUES(?)"
        self.execute(sql, (name,), commit=True)
        logger.info(f"➕ Fakultet: {name}")

    def get_all_fakultetlar(self):
        """Barcha fakultetlar"""
        sql = "SELECT id, name FROM Fakultet ORDER BY name"
        return self.execute(sql, fetchall=True)

    def get_fakultet_by_name(self, name):
        """Fakultetni topish"""
        sql = "SELECT id, name FROM Fakultet WHERE name=?"
        return self.execute(sql, (name,), fetchone=True)

    def delete_fakultet(self, fakultet_id):
        """Fakultetni o'chirish"""
        sql = "DELETE FROM Fakultet WHERE id=?"
        self.execute(sql, (fakultet_id,), commit=True)
        logger.info(f"🗑 Fakultet deleted: {fakultet_id}")

    # ==================== MAVZU ====================
    def add_mavzu(self, fakultet_id, name):
        """Mavzu qo'shish"""
        sql = "INSERT OR IGNORE INTO Mavzu(fakultet_id, name) VALUES(?,?)"
        self.execute(sql, (fakultet_id, name), commit=True)

    def get_mavzular_by_fakultet(self, fakultet_id):
        """Fakultet bo'yicha mavzular"""
        sql = "SELECT id, name FROM Mavzu WHERE fakultet_id=? ORDER BY name"
        return self.execute(sql, (fakultet_id,), fetchall=True)

    def get_or_create_mavzu(self, fakultet_id, mavzu_name):
        """Mavzuni topish yoki yaratish"""
        sql = "SELECT id FROM Mavzu WHERE fakultet_id=? AND name=?"
        result = self.execute(sql, (fakultet_id, mavzu_name), fetchone=True)

        if result:
            return result[0]

        # Yangi mavzu yaratish
        self.add_mavzu(fakultet_id, mavzu_name)
        result = self.execute(sql, (fakultet_id, mavzu_name), fetchone=True)
        return result[0] if result else None

    # ==================== DARS ====================
    def add_dars(self, dars_id, code, title, file_id, mavzu_name=None,
                 file_name=None, file_size=0):
        """Dars qo'shish"""
        mavzu_id = None
        if mavzu_name:
            mavzu_id = self.get_or_create_mavzu(dars_id, mavzu_name)

        sql = """
        INSERT INTO Lesson(fakultet_id, mavzu_id, code, title, file_id, 
                          file_name, file_size)
        VALUES(?, ?, ?, ?, ?, ?, ?)
        """
        self.execute(sql, (dars_id, mavzu_id, code, title, file_id,
                           file_name, file_size), commit=True)
        logger.info(f"➕ Dars: {code} - {title}")

    def get_dars_by_fakultet(self, fakultet_id):
        """Fakultet bo'yicha darslar"""
        sql = """
        SELECT l.code, l.title, l.count_download, m.name as mavzu_name
        FROM Lesson l
        LEFT JOIN Mavzu m ON l.mavzu_id = m.id
        WHERE l.fakultet_id = ?
        ORDER BY m.name, l.title
        """
        return self.execute(sql, (fakultet_id,), fetchall=True)

    def get_dars_by_mavzu(self, fakultet_id, mavzu_name):
        """Mavzu bo'yicha darslar"""
        sql = """
        SELECT l.code, l.title, l.count_download
        FROM Lesson l
        JOIN Mavzu m ON l.mavzu_id = m.id
        WHERE l.fakultet_id=? AND m.name=?
        ORDER BY l.title
        """
        return self.execute(sql, (fakultet_id, mavzu_name), fetchall=True)

    def search_dars_by_code(self, code):
        """Darsni kod bo'yicha topish"""
        sql = "SELECT * FROM Lesson WHERE code=?"
        return self.execute(sql, (code,), fetchone=True)

    def delete_dars(self, code):
        """Darsni o'chirish"""
        sql = "DELETE FROM Lesson WHERE code=?"
        self.execute(sql, (code,), commit=True)
        logger.info(f"🗑 Dars deleted: {code}")

    def update_download_count(self, code):
        """Yuklanish +1"""
        sql = "UPDATE Lesson SET count_download = count_download + 1 WHERE code=?"
        self.execute(sql, (code,), commit=True)

    # ==================== STATISTIKA ====================
    def count_all_darslar(self):
        """Jami darslar"""
        sql = "SELECT COUNT(*) FROM Lesson"
        result = self.execute(sql, fetchone=True)
        return result[0] if result else 0

    def count_dars_by_fakultet(self, fakultet_id):
        """Fakultetdagi darslar"""
        sql = "SELECT COUNT(*) FROM Lesson WHERE fakultet_id=?"
        result = self.execute(sql, (fakultet_id,), fetchone=True)
        return result[0] if result else 0

    def get_total_downloads(self):
        """Jami yuklanishlar"""
        sql = "SELECT SUM(count_download) FROM Lesson"
        result = self.execute(sql, fetchone=True)
        return result[0] if result and result[0] else 0

    def get_top_downloaded_darslar(self, limit=10):
        """Eng ko'p yuklangan darslar"""
        sql = """
        SELECT l.code, l.title, f.name as fakultet, 
               l.count_download, m.name as mavzu
        FROM Lesson l
        JOIN Fakultet f ON l.fakultet_id = f.id
        LEFT JOIN Mavzu m ON l.mavzu_id = m.id
        ORDER BY l.count_download DESC
        LIMIT ?
        """
        return self.execute(sql, (limit,), fetchall=True)

    def get_recent_darslar(self, limit=10):
        """Eng yangi darslar"""
        sql = """
        SELECT l.title, l.created_at, f.name as fakultet
        FROM Lesson l
        JOIN Fakultet f ON l.fakultet_id = f.id
        ORDER BY l.created_at DESC
        LIMIT ?
        """
        return self.execute(sql, (limit,), fetchall=True)

    def get_fakultet_stats(self):
        """Fakultet statistikasi"""
        sql = """
        SELECT f.name, 
               COUNT(l.id) as dars_count,
               COALESCE(SUM(l.count_download), 0) as total_downloads
        FROM Fakultet f
        LEFT JOIN Lesson l ON f.id = l.fakultet_id
        GROUP BY f.id, f.name
        ORDER BY dars_count DESC
        """
        return self.execute(sql, fetchall=True)

    def search_dars_by_title(self, fakultet_id, query):
        """Darslarni qidirish"""
        sql = """
        SELECT l.code, l.title
        FROM Lesson l
        WHERE l.fakultet_id=? AND l.title LIKE ?
        ORDER BY l.title
        LIMIT 20
        """
        return self.execute(sql, (fakultet_id, f"%{query}%"), fetchall=True)