"""
Optimallashtirilgan Database sinfi
Dublikatlar tozalangan, logging yaxshilangan
"""
import sqlite3
import logging
from contextlib import contextmanager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class Database:
    """Asosiy database sinfi"""

    def __init__(self, path_to_db="main.db"):
        self.path_to_db = path_to_db
        logger.info(f"Database initialized: {path_to_db}")

    @contextmanager
    def get_connection(self):
        """Context manager bilan xavfsiz ulanish"""
        conn = sqlite3.connect(self.path_to_db)
        conn.row_factory = sqlite3.Row  # Dict kabi ishlash uchun
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def execute(self, sql: str, parameters: tuple = None,
                fetchone=False, fetchall=False, commit=False):
        """SQL so'rovini bajarish"""
        parameters = parameters or ()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, parameters)

            if fetchone:
                return cursor.fetchone()
            if fetchall:
                return cursor.fetchall()
            if commit:
                conn.commit()
            return cursor.lastrowid

    def executemany(self, sql: str, data: list):
        """Ko'p qatorli insert"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, data)
            return cursor.rowcount