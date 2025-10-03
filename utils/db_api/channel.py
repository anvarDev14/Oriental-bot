import sqlite3
import os
import logging

logger = logging.getLogger(__name__)


class ChannelDB:
    def __init__(self, path_to_db):
        self.path_to_db = path_to_db

        # Database faylini avval yaratish
        db_dir = os.path.dirname(path_to_db)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        if not os.path.exists(path_to_db):
            try:
                open(path_to_db, 'a').close()
                logger.info(f"Database fayl yaratildi: {path_to_db}")
            except Exception as e:
                logger.error(f"Database yaratish xatosi: {e}")

        self.conn = sqlite3.connect(path_to_db, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_table()


    def create_table(self):
        """Kanallar jadvalini yaratish"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                channel_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                invite_link TEXT NOT NULL DEFAULT ''
            )
        ''')
        self.conn.commit()
        logger.info("✅ Channels table ready")

    def add_channel(self, channel_id, title, invite_link):
        """Kanal qo'shish"""
        try:
            self.cursor.execute(
                "INSERT OR REPLACE INTO channels VALUES (?, ?, ?)",
                (channel_id, title, invite_link)
            )
            self.conn.commit()
            logger.info(f"➕ Kanal: {title}")
            return True
        except Exception as e:
            logger.error(f"Kanal qo'shish xatosi: {e}")
            return False

    def get_all_channels(self):
        """Barcha kanallar"""
        self.cursor.execute("SELECT channel_id, title, invite_link FROM channels")
        return self.cursor.fetchall()

    def get_channel(self, channel_id):
        """Bitta kanal"""
        self.cursor.execute(
            "SELECT * FROM channels WHERE channel_id=?",
            (channel_id,)
        )
        return self.cursor.fetchone()

    def delete_channel(self, channel_id):
        """Kanalni o'chirish"""
        try:
            self.cursor.execute("DELETE FROM channels WHERE channel_id=?", (channel_id,))
            self.conn.commit()
            logger.info(f"🗑 Kanal deleted: {channel_id}")
            return True
        except Exception as e:
            logger.error(f"Kanal o'chirish xatosi: {e}")
            return False

    def channel_exists(self, channel_id):
        """Kanal mavjudligini tekshirish"""
        self.cursor.execute("SELECT 1 FROM channels WHERE channel_id=?", (channel_id,))
        return bool(self.cursor.fetchone())

    def count_channels(self):
        """Kanallar soni"""
        self.cursor.execute("SELECT COUNT(*) FROM channels")
        result = self.cursor.fetchone()
        return result[0] if result else 0

    def close(self):
        """Ulanishni yopish"""
        self.conn.close()