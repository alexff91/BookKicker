"""
Improved Database Module for BookKicker
Features:
- Connection pooling for better performance
- Parameterized queries to prevent SQL injection
- Enhanced schema with metadata, preferences, bookmarks, and statistics
- Context managers for proper resource management
- Comprehensive error handling
"""

import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional, List, Dict, Tuple, Any
import logging
from datetime import datetime, timezone

import tokens

logger = logging.getLogger(__name__)


class DatabasePool:
    """Singleton connection pool manager"""
    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabasePool, cls).__new__(cls)
        return cls._instance

    def initialize(self, min_conn=2, max_conn=10):
        """Initialize the connection pool"""
        if self._pool is None:
            try:
                self._pool = psycopg2.pool.ThreadedConnectionPool(
                    min_conn,
                    max_conn,
                    user=tokens.user,
                    password=tokens.password,
                    host=tokens.host,
                    port="5432",
                    database=tokens.db
                )
                logger.info(f"Database pool initialized with {min_conn}-{max_conn} connections")
            except Exception as e:
                logger.error(f"Failed to initialize database pool: {e}")
                raise

    def get_connection(self):
        """Get a connection from the pool"""
        if self._pool is None:
            self.initialize()
        return self._pool.getconn()

    def return_connection(self, conn):
        """Return a connection to the pool"""
        if self._pool:
            self._pool.putconn(conn)

    def close_all(self):
        """Close all connections in the pool"""
        if self._pool:
            self._pool.closeall()
            logger.info("All database connections closed")


class ImprovedDatabase:
    """Improved database class with security and performance enhancements"""

    def __init__(self):
        self.pool = DatabasePool()
        self.pool.initialize()
        self._create_tables()

    @contextmanager
    def get_cursor(self, dict_cursor=False):
        """Context manager for database operations"""
        conn = None
        cursor = None
        try:
            conn = self.pool.get_connection()
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            yield cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.pool.return_connection(conn)

    def _create_tables(self):
        """Create all necessary tables with enhanced schema"""
        with self.get_cursor() as cursor:
            # Enhanced books position table with composite unique constraint
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books_pos_table (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    book_name TEXT NOT NULL,
                    pos INTEGER DEFAULT 0,
                    total_lines INTEGER DEFAULT 0,
                    last_read_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, book_name)
                );
            """)

            # Create index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_books_pos_user_id
                ON books_pos_table(user_id);
            """)

            # Enhanced current book table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS current_book_table (
                    user_id INTEGER PRIMARY KEY,
                    chat_id BIGINT NOT NULL,
                    book_name TEXT,
                    is_auto_send BOOLEAN DEFAULT FALSE,
                    lang VARCHAR(10) DEFAULT 'ru',
                    audio BOOLEAN DEFAULT FALSE,
                    rare INTEGER DEFAULT 12,
                    timezone VARCHAR(50) DEFAULT 'UTC',
                    chunk_size INTEGER DEFAULT 893,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Book metadata table for storing book information
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS book_metadata (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    book_name TEXT NOT NULL,
                    title TEXT,
                    author TEXT,
                    language VARCHAR(10),
                    file_format VARCHAR(10),
                    file_size_bytes INTEGER,
                    total_characters INTEGER,
                    estimated_read_time_minutes INTEGER,
                    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, book_name)
                );
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_book_metadata_user_id
                ON book_metadata(user_id);
            """)

            # Bookmarks table for saving specific positions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    book_name TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    note TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bookmarks_user_book
                ON bookmarks(user_id, book_name);
            """)

            # Reading statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reading_stats (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    book_name TEXT NOT NULL,
                    lines_read INTEGER DEFAULT 0,
                    characters_read INTEGER DEFAULT 0,
                    session_date DATE DEFAULT CURRENT_DATE,
                    read_count INTEGER DEFAULT 1,
                    last_session_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, book_name, session_date)
                );
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_reading_stats_user_date
                ON reading_stats(user_id, session_date);
            """)

            # User preferences table (extended settings)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id INTEGER PRIMARY KEY,
                    daily_goal_lines INTEGER DEFAULT 100,
                    daily_goal_minutes INTEGER DEFAULT 30,
                    reading_speed_wpm INTEGER DEFAULT 200,
                    notification_enabled BOOLEAN DEFAULT TRUE,
                    theme VARCHAR(20) DEFAULT 'default',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)

        logger.info("Database tables created/verified successfully")

    # ==================== Book Position Methods ====================

    def update_book_pos(self, user_id: int, book_name: str, new_pos: int,
                       total_lines: int = 0) -> bool:
        """Update reading position for a book"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO books_pos_table
                        (user_id, book_name, pos, total_lines, last_read_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, book_name)
                    DO UPDATE SET
                        pos = %s,
                        total_lines = COALESCE(NULLIF(%s, 0), books_pos_table.total_lines),
                        last_read_at = %s
                """, (user_id, book_name, new_pos, total_lines, datetime.now(timezone.utc),
                      new_pos, total_lines, datetime.now(timezone.utc)))
                return True
        except Exception as e:
            logger.error(f"Error updating book position: {e}")
            return False

    def get_pos(self, user_id: int, book_name: str) -> int:
        """Get current reading position for a book"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT pos FROM books_pos_table
                    WHERE user_id = %s AND book_name = %s
                """, (user_id, book_name))
                result = cursor.fetchone()
                return result[0] if result else -1
        except Exception as e:
            logger.error(f"Error getting position: {e}")
            return -1

    def get_book_progress(self, user_id: int, book_name: str) -> Dict[str, Any]:
        """Get detailed progress information for a book"""
        try:
            with self.get_cursor(dict_cursor=True) as cursor:
                cursor.execute("""
                    SELECT
                        pos,
                        total_lines,
                        CASE
                            WHEN total_lines > 0
                            THEN ROUND((pos::NUMERIC / total_lines * 100), 2)
                            ELSE 0
                        END as progress_percent,
                        last_read_at
                    FROM books_pos_table
                    WHERE user_id = %s AND book_name = %s
                """, (user_id, book_name))
                result = cursor.fetchone()
                return dict(result) if result else {}
        except Exception as e:
            logger.error(f"Error getting book progress: {e}")
            return {}

    # ==================== Current Book Methods ====================

    def update_current_book(self, user_id: int, chat_id: int, book_name: str,
                           lang: str = 'ru') -> bool:
        """Update the current book being read by user"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO current_book_table
                        (user_id, chat_id, book_name, is_auto_send, lang, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id)
                    DO UPDATE SET
                        chat_id = %s,
                        book_name = %s,
                        is_auto_send = TRUE,
                        lang = %s,
                        updated_at = %s
                """, (user_id, chat_id, book_name, True, lang, datetime.now(timezone.utc),
                      chat_id, book_name, lang, datetime.now(timezone.utc)))
                return True
        except Exception as e:
            logger.error(f"Error updating current book: {e}")
            return False

    def get_current_book(self, user_id: int) -> Optional[str]:
        """Get the current book for a user"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT book_name FROM current_book_table
                    WHERE user_id = %s
                """, (user_id,))
                result = cursor.fetchone()
                return result[0] if result and result[0] else None
        except Exception as e:
            logger.error(f"Error getting current book: {e}")
            return None

    # ==================== Auto-send Methods ====================

    def update_auto_status(self, user_id: int, status: Optional[bool] = None) -> bool:
        """Update or toggle auto-send status"""
        try:
            with self.get_cursor() as cursor:
                if status is None:
                    # Toggle status
                    cursor.execute("""
                        INSERT INTO current_book_table (user_id, is_auto_send, chat_id)
                        VALUES (%s, TRUE, 0)
                        ON CONFLICT (user_id)
                        DO UPDATE SET
                            is_auto_send = NOT current_book_table.is_auto_send,
                            updated_at = %s
                    """, (user_id, datetime.now(timezone.utc)))
                else:
                    # Set specific status
                    cursor.execute("""
                        INSERT INTO current_book_table (user_id, is_auto_send, chat_id)
                        VALUES (%s, %s, 0)
                        ON CONFLICT (user_id)
                        DO UPDATE SET
                            is_auto_send = %s,
                            updated_at = %s
                    """, (user_id, status, status, datetime.now(timezone.utc)))
                return True
        except Exception as e:
            logger.error(f"Error updating auto status: {e}")
            return False

    def get_auto_status(self, user_id: int) -> int:
        """Get auto-send status (1=ON, 0=OFF, -1=not set)"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT is_auto_send FROM current_book_table
                    WHERE user_id = %s
                """, (user_id,))
                result = cursor.fetchone()
                if result is None:
                    return -1
                return 1 if result[0] else 0
        except Exception as e:
            logger.error(f"Error getting auto status: {e}")
            return -1

    def get_users_for_autosend(self) -> List[Tuple[int, int]]:
        """Get all users with auto-send enabled"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT user_id, chat_id
                    FROM current_book_table
                    WHERE is_auto_send = TRUE
                """)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting autosend users: {e}")
            return []

    # ==================== User Settings Methods ====================

    def update_lang(self, user_id: int, lang: str) -> bool:
        """Update user's language preference"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO current_book_table (user_id, lang, chat_id)
                    VALUES (%s, %s, 0)
                    ON CONFLICT (user_id)
                    DO UPDATE SET lang = %s, updated_at = %s
                """, (user_id, lang, lang, datetime.now(timezone.utc)))
                return True
        except Exception as e:
            logger.error(f"Error updating language: {e}")
            return False

    def get_lang(self, user_id: int) -> Optional[str]:
        """Get user's language preference"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT lang FROM current_book_table
                    WHERE user_id = %s
                """, (user_id,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting language: {e}")
            return None

    def update_rare(self, user_id: int, rare: int) -> bool:
        """Update reading frequency (times per day)"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO current_book_table (user_id, rare, chat_id)
                    VALUES (%s, %s, 0)
                    ON CONFLICT (user_id)
                    DO UPDATE SET rare = %s, updated_at = %s
                """, (user_id, rare, rare, datetime.now(timezone.utc)))
                return True
        except Exception as e:
            logger.error(f"Error updating rare: {e}")
            return False

    def get_rare(self, user_id: int) -> Optional[str]:
        """Get reading frequency"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT rare FROM current_book_table
                    WHERE user_id = %s
                """, (user_id,))
                result = cursor.fetchone()
                return str(result[0]) if result else None
        except Exception as e:
            logger.error(f"Error getting rare: {e}")
            return None

    def update_audio(self, user_id: int, audio: bool) -> bool:
        """Update audio mode preference"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO current_book_table (user_id, audio, chat_id)
                    VALUES (%s, %s, 0)
                    ON CONFLICT (user_id)
                    DO UPDATE SET audio = %s, updated_at = %s
                """, (user_id, audio, audio, datetime.now(timezone.utc)))
                return True
        except Exception as e:
            logger.error(f"Error updating audio: {e}")
            return False

    def get_audio(self, user_id: int) -> Optional[bool]:
        """Get audio mode preference"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT audio FROM current_book_table
                    WHERE user_id = %s
                """, (user_id,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting audio: {e}")
            return None

    def update_timezone(self, user_id: int, timezone_str: str) -> bool:
        """Update user's timezone"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO current_book_table (user_id, timezone, chat_id)
                    VALUES (%s, %s, 0)
                    ON CONFLICT (user_id)
                    DO UPDATE SET timezone = %s, updated_at = %s
                """, (user_id, timezone_str, timezone_str, datetime.now(timezone.utc)))
                return True
        except Exception as e:
            logger.error(f"Error updating timezone: {e}")
            return False

    def update_chunk_size(self, user_id: int, chunk_size: int) -> bool:
        """Update preferred chunk size"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO current_book_table (user_id, chunk_size, chat_id)
                    VALUES (%s, %s, 0)
                    ON CONFLICT (user_id)
                    DO UPDATE SET chunk_size = %s, updated_at = %s
                """, (user_id, chunk_size, chunk_size, datetime.now(timezone.utc)))
                return True
        except Exception as e:
            logger.error(f"Error updating chunk size: {e}")
            return False

    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get all user settings"""
        try:
            with self.get_cursor(dict_cursor=True) as cursor:
                cursor.execute("""
                    SELECT * FROM current_book_table
                    WHERE user_id = %s
                """, (user_id,))
                result = cursor.fetchone()
                return dict(result) if result else {}
        except Exception as e:
            logger.error(f"Error getting user settings: {e}")
            return {}

    # ==================== Book Library Methods ====================

    def get_user_books(self, user_id: int) -> List[str]:
        """Get all books for a user"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT book_name FROM books_pos_table
                    WHERE user_id = %s
                    ORDER BY last_read_at DESC
                """, (user_id,))
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting user books: {e}")
            return []

    def get_user_books_with_progress(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all books with progress information"""
        try:
            with self.get_cursor(dict_cursor=True) as cursor:
                cursor.execute("""
                    SELECT
                        bp.book_name,
                        bp.pos,
                        bp.total_lines,
                        CASE
                            WHEN bp.total_lines > 0
                            THEN ROUND((bp.pos::NUMERIC / bp.total_lines * 100), 2)
                            ELSE 0
                        END as progress_percent,
                        bp.last_read_at,
                        bm.title,
                        bm.author
                    FROM books_pos_table bp
                    LEFT JOIN book_metadata bm
                        ON bp.user_id = bm.user_id AND bp.book_name = bm.book_name
                    WHERE bp.user_id = %s
                    ORDER BY bp.last_read_at DESC
                """, (user_id,))
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting books with progress: {e}")
            return []

    # ==================== Book Metadata Methods ====================

    def add_book_metadata(self, user_id: int, book_name: str,
                         title: str = None, author: str = None,
                         language: str = None, file_format: str = None,
                         file_size: int = None, total_chars: int = None,
                         estimated_time: int = None) -> bool:
        """Add or update book metadata"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO book_metadata
                        (user_id, book_name, title, author, language, file_format,
                         file_size_bytes, total_characters, estimated_read_time_minutes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, book_name)
                    DO UPDATE SET
                        title = COALESCE(%s, book_metadata.title),
                        author = COALESCE(%s, book_metadata.author),
                        language = COALESCE(%s, book_metadata.language),
                        file_format = COALESCE(%s, book_metadata.file_format),
                        file_size_bytes = COALESCE(%s, book_metadata.file_size_bytes),
                        total_characters = COALESCE(%s, book_metadata.total_characters),
                        estimated_read_time_minutes = COALESCE(%s, book_metadata.estimated_read_time_minutes)
                """, (user_id, book_name, title, author, language, file_format,
                      file_size, total_chars, estimated_time,
                      title, author, language, file_format, file_size, total_chars, estimated_time))
                return True
        except Exception as e:
            logger.error(f"Error adding book metadata: {e}")
            return False

    def get_book_metadata(self, user_id: int, book_name: str) -> Dict[str, Any]:
        """Get metadata for a specific book"""
        try:
            with self.get_cursor(dict_cursor=True) as cursor:
                cursor.execute("""
                    SELECT * FROM book_metadata
                    WHERE user_id = %s AND book_name = %s
                """, (user_id, book_name))
                result = cursor.fetchone()
                return dict(result) if result else {}
        except Exception as e:
            logger.error(f"Error getting book metadata: {e}")
            return {}

    # ==================== Bookmarks Methods ====================

    def add_bookmark(self, user_id: int, book_name: str,
                    position: int, note: str = None) -> bool:
        """Add a bookmark at a specific position"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO bookmarks (user_id, book_name, position, note)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, book_name, position, note))
                return True
        except Exception as e:
            logger.error(f"Error adding bookmark: {e}")
            return False

    def get_bookmarks(self, user_id: int, book_name: str) -> List[Dict[str, Any]]:
        """Get all bookmarks for a book"""
        try:
            with self.get_cursor(dict_cursor=True) as cursor:
                cursor.execute("""
                    SELECT * FROM bookmarks
                    WHERE user_id = %s AND book_name = %s
                    ORDER BY position
                """, (user_id, book_name))
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting bookmarks: {e}")
            return []

    def delete_bookmark(self, bookmark_id: int, user_id: int) -> bool:
        """Delete a specific bookmark"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    DELETE FROM bookmarks
                    WHERE id = %s AND user_id = %s
                """, (bookmark_id, user_id))
                return True
        except Exception as e:
            logger.error(f"Error deleting bookmark: {e}")
            return False

    # ==================== Statistics Methods ====================

    def record_reading_session(self, user_id: int, book_name: str,
                               lines_read: int, chars_read: int) -> bool:
        """Record a reading session"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO reading_stats
                        (user_id, book_name, lines_read, characters_read,
                         session_date, read_count, last_session_at)
                    VALUES (%s, %s, %s, %s, CURRENT_DATE, 1, %s)
                    ON CONFLICT (user_id, book_name, session_date)
                    DO UPDATE SET
                        lines_read = reading_stats.lines_read + %s,
                        characters_read = reading_stats.characters_read + %s,
                        read_count = reading_stats.read_count + 1,
                        last_session_at = %s
                """, (user_id, book_name, lines_read, chars_read, datetime.now(timezone.utc),
                      lines_read, chars_read, datetime.now(timezone.utc)))
                return True
        except Exception as e:
            logger.error(f"Error recording reading session: {e}")
            return False

    def get_reading_stats(self, user_id: int, days: int = 7) -> List[Dict[str, Any]]:
        """Get reading statistics for the last N days"""
        try:
            with self.get_cursor(dict_cursor=True) as cursor:
                cursor.execute("""
                    SELECT
                        session_date,
                        SUM(lines_read) as total_lines,
                        SUM(characters_read) as total_characters,
                        SUM(read_count) as total_sessions,
                        COUNT(DISTINCT book_name) as books_read
                    FROM reading_stats
                    WHERE user_id = %s
                        AND session_date >= CURRENT_DATE - %s
                    GROUP BY session_date
                    ORDER BY session_date DESC
                """, (user_id, days))
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting reading stats: {e}")
            return []

    def get_total_stats(self, user_id: int) -> Dict[str, Any]:
        """Get total reading statistics for user"""
        try:
            with self.get_cursor(dict_cursor=True) as cursor:
                cursor.execute("""
                    SELECT
                        COUNT(DISTINCT book_name) as total_books,
                        SUM(lines_read) as total_lines_read,
                        SUM(characters_read) as total_characters_read,
                        SUM(read_count) as total_sessions,
                        MIN(session_date) as first_read_date,
                        MAX(session_date) as last_read_date
                    FROM reading_stats
                    WHERE user_id = %s
                """, (user_id,))
                result = cursor.fetchone()
                return dict(result) if result else {}
        except Exception as e:
            logger.error(f"Error getting total stats: {e}")
            return {}

    # ==================== User Preferences Methods ====================

    def update_user_preferences(self, user_id: int,
                               daily_goal_lines: int = None,
                               daily_goal_minutes: int = None,
                               reading_speed_wpm: int = None,
                               notification_enabled: bool = None) -> bool:
        """Update user preferences"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_preferences
                        (user_id, daily_goal_lines, daily_goal_minutes,
                         reading_speed_wpm, notification_enabled)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id)
                    DO UPDATE SET
                        daily_goal_lines = COALESCE(%s, user_preferences.daily_goal_lines),
                        daily_goal_minutes = COALESCE(%s, user_preferences.daily_goal_minutes),
                        reading_speed_wpm = COALESCE(%s, user_preferences.reading_speed_wpm),
                        notification_enabled = COALESCE(%s, user_preferences.notification_enabled),
                        updated_at = %s
                """, (user_id, daily_goal_lines, daily_goal_minutes, reading_speed_wpm, notification_enabled,
                      daily_goal_lines, daily_goal_minutes, reading_speed_wpm, notification_enabled,
                      datetime.now(timezone.utc)))
                return True
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False

    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user preferences"""
        try:
            with self.get_cursor(dict_cursor=True) as cursor:
                cursor.execute("""
                    SELECT * FROM user_preferences
                    WHERE user_id = %s
                """, (user_id,))
                result = cursor.fetchone()
                return dict(result) if result else {}
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return {}

    def close(self):
        """Close all database connections"""
        self.pool.close_all()
