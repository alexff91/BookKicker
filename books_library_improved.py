"""
Improved Books Library with enhanced caching and features
"""

from database_improved import ImprovedDatabase
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Try to import Redis for caching, fall back to dict cache
try:
    import redis
    from redis.exceptions import ConnectionError as RedisConnectionError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache")


class ImprovedBooksLibrary:
    """Enhanced books library with caching and new features"""

    def __init__(self, use_redis=False):
        self.db = ImprovedDatabase()
        self.use_redis = use_redis and REDIS_AVAILABLE

        # Initialize cache
        if self.use_redis:
            try:
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    db=0,
                    decode_responses=True,
                    socket_connect_timeout=2
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except (RedisConnectionError, Exception) as e:
                logger.warning(f"Redis connection failed: {e}, falling back to dict cache")
                self.use_redis = False
                self.cache = {}
        else:
            self.cache = {}

    def _get_cache_key(self, prefix: str, user_id: int, suffix: str = "") -> str:
        """Generate cache key"""
        return f"{prefix}:{user_id}:{suffix}" if suffix else f"{prefix}:{user_id}"

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.use_redis:
                return self.redis_client.get(key)
            else:
                return self.cache.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def _set_to_cache(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL (seconds)"""
        try:
            if self.use_redis:
                self.redis_client.setex(key, ttl, str(value))
            else:
                self.cache[key] = value
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    def _invalidate_cache(self, key: str):
        """Invalidate specific cache key"""
        try:
            if self.use_redis:
                self.redis_client.delete(key)
            else:
                self.cache.pop(key, None)
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")

    # ==================== Book Management ====================

    def update_current_book(self, user_id: int, chat_id: int, book_name: str):
        """Update current book with cache invalidation"""
        lang = self.get_lang(user_id)
        success = self.db.update_current_book(user_id, chat_id, book_name, lang)
        if success:
            self._invalidate_cache(self._get_cache_key("current_book", user_id))
        return success

    def update_book_pos(self, user_id: int, current_book: str, new_pos: int,
                       total_lines: int = 0):
        """Update book position with cache invalidation"""
        success = self.db.update_book_pos(user_id, current_book, new_pos, total_lines)
        if success:
            self._invalidate_cache(self._get_cache_key("pos", user_id, current_book))
            self._invalidate_cache(self._get_cache_key("progress", user_id, current_book))
        return success

    def get_current_book(self, user_id: int, format_name: bool = False) -> Any:
        """Get current book with caching"""
        cache_key = self._get_cache_key("current_book", user_id)
        cached = self._get_from_cache(cache_key)

        if cached and not format_name:
            return cached

        current_book = self.db.get_current_book(user_id)
        if current_book is None:
            return -1

        self._set_to_cache(cache_key, current_book)

        if format_name:
            current_book = self._format_name(current_book, user_id)

        return current_book

    def get_pos(self, user_id: int, book_name: str) -> int:
        """Get reading position with caching"""
        cache_key = self._get_cache_key("pos", user_id, book_name)
        cached = self._get_from_cache(cache_key)

        if cached is not None:
            return int(cached)

        pos = self.db.get_pos(user_id, book_name)
        if pos >= 0:
            self._set_to_cache(cache_key, pos)

        return pos

    def get_book_progress(self, user_id: int, book_name: str) -> Dict[str, Any]:
        """Get detailed book progress"""
        return self.db.get_book_progress(user_id, book_name)

    def get_user_books(self, user_id: int) -> List[str]:
        """Get all user books"""
        return self.db.get_user_books(user_id)

    def get_user_books_with_progress(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all books with progress information"""
        return self.db.get_user_books_with_progress(user_id)

    # ==================== Auto-send Management ====================

    def switch_auto_status(self, user_id: int):
        """Toggle auto-send status"""
        success = self.db.update_auto_status(user_id)
        if success:
            self._invalidate_cache(self._get_cache_key("auto_status", user_id))
        return success

    def get_auto_status(self, user_id: int) -> int:
        """Get auto-send status with caching"""
        cache_key = self._get_cache_key("auto_status", user_id)
        cached = self._get_from_cache(cache_key)

        if cached is not None:
            return int(cached)

        status = self.db.get_auto_status(user_id)
        if status >= 0:
            self._set_to_cache(cache_key, status)

        return status

    def get_users_for_autosend(self):
        """Get all users with auto-send enabled"""
        return self.db.get_users_for_autosend()

    # ==================== Language Settings ====================

    def update_lang(self, user_id: int, lang: str):
        """Update user language with cache"""
        success = self.db.update_lang(user_id, lang)
        if success:
            self._set_to_cache(self._get_cache_key("lang", user_id), lang)
        return success

    def get_lang(self, user_id: int) -> str:
        """Get user language with caching and default"""
        cache_key = self._get_cache_key("lang", user_id)
        cached = self._get_from_cache(cache_key)

        if cached:
            return cached

        lang = self.db.get_lang(user_id)
        if lang is None:
            lang = 'ru'
            self.update_lang(user_id, lang)
        else:
            self._set_to_cache(cache_key, lang)

        return lang

    # ==================== Reading Frequency ====================

    def update_rare(self, user_id: int, rare: Any):
        """Update reading frequency with parsing"""
        # Parse frequency from various formats
        if isinstance(rare, str):
            rare_map = {
                '12 раз в день': 12,
                '6 раз в день': 6,
                '4 раза в день': 4,
                '2 раза в день': 2,
                '1 раз в день': 1,
                '12 times a day': 12,
                '6 times a day': 6,
                '4 times a day': 4,
                '2 times a day': 2,
                '1 time a day': 1
            }
            rare_int = rare_map.get(rare, 12)
        else:
            rare_int = int(rare)

        success = self.db.update_rare(user_id, rare_int)
        if success:
            self._set_to_cache(self._get_cache_key("rare", user_id), str(rare_int))
        return success

    def get_rare(self, user_id: int) -> str:
        """Get reading frequency with caching"""
        cache_key = self._get_cache_key("rare", user_id)
        cached = self._get_from_cache(cache_key)

        if cached:
            return cached

        rare = self.db.get_rare(user_id)
        if rare is None:
            rare = '12'
            self.update_rare(user_id, 12)
        else:
            self._set_to_cache(cache_key, rare)

        return rare

    # ==================== Audio Settings ====================

    def update_audio(self, user_id: int, audio: Any):
        """Update audio mode"""
        # Parse audio setting
        if isinstance(audio, str):
            audio_bool = audio.lower() in ('on', 'true', '1', 'yes')
        else:
            audio_bool = bool(audio)

        success = self.db.update_audio(user_id, audio_bool)
        if success:
            audio_str = 'on' if audio_bool else 'off'
            self._set_to_cache(self._get_cache_key("audio", user_id), audio_str)
        return success

    def get_audio(self, user_id: int) -> str:
        """Get audio mode with caching"""
        cache_key = self._get_cache_key("audio", user_id)
        cached = self._get_from_cache(cache_key)

        if cached:
            return cached

        audio = self.db.get_audio(user_id)
        if audio is None:
            audio = False
            self.update_audio(user_id, 'off')
            return 'off'
        else:
            audio_str = 'on' if audio else 'off'
            self._set_to_cache(cache_key, audio_str)
            return audio_str

    # ==================== Book Metadata ====================

    def add_book_metadata(self, user_id: int, book_name: str, **kwargs):
        """Add book metadata"""
        return self.db.add_book_metadata(user_id, book_name, **kwargs)

    def get_book_metadata(self, user_id: int, book_name: str) -> Dict[str, Any]:
        """Get book metadata"""
        return self.db.get_book_metadata(user_id, book_name)

    # ==================== Bookmarks ====================

    def add_bookmark(self, user_id: int, book_name: str,
                    position: int, note: str = None):
        """Add bookmark"""
        return self.db.add_bookmark(user_id, book_name, position, note)

    def get_bookmarks(self, user_id: int, book_name: str) -> List[Dict[str, Any]]:
        """Get bookmarks for a book"""
        return self.db.get_bookmarks(user_id, book_name)

    def delete_bookmark(self, bookmark_id: int, user_id: int):
        """Delete bookmark"""
        return self.db.delete_bookmark(bookmark_id, user_id)

    # ==================== Statistics ====================

    def record_reading_session(self, user_id: int, book_name: str,
                               lines_read: int, chars_read: int):
        """Record reading session"""
        return self.db.record_reading_session(user_id, book_name, lines_read, chars_read)

    def get_reading_stats(self, user_id: int, days: int = 7) -> List[Dict[str, Any]]:
        """Get reading statistics"""
        return self.db.get_reading_stats(user_id, days)

    def get_total_stats(self, user_id: int) -> Dict[str, Any]:
        """Get total reading statistics"""
        return self.db.get_total_stats(user_id)

    # ==================== User Settings ====================

    def update_timezone(self, user_id: int, timezone_str: str):
        """Update user timezone"""
        return self.db.update_timezone(user_id, timezone_str)

    def update_chunk_size(self, user_id: int, chunk_size: int):
        """Update chunk size"""
        success = self.db.update_chunk_size(user_id, chunk_size)
        if success:
            self._invalidate_cache(self._get_cache_key("chunk_size", user_id))
        return success

    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get all user settings"""
        return self.db.get_user_settings(user_id)

    def update_user_preferences(self, user_id: int, **kwargs):
        """Update user preferences"""
        return self.db.update_user_preferences(user_id, **kwargs)

    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user preferences"""
        return self.db.get_user_preferences(user_id)

    # ==================== Helper Methods ====================

    def _format_name(self, file_name: str, user_id: int) -> str:
        """Format book name for display"""
        formatted_name = file_name
        formatted_name = formatted_name.replace(str(user_id) + '_', '')
        formatted_name = formatted_name.replace('.txt', '')
        formatted_name = formatted_name.capitalize()
        return '📖 ' + formatted_name

    def get_progress_bar(self, user_id: int, book_name: str, width: int = 10) -> str:
        """Generate a visual progress bar"""
        progress = self.get_book_progress(user_id, book_name)
        if not progress or 'progress_percent' not in progress:
            return "▱" * width

        percent = float(progress.get('progress_percent', 0))
        filled = int(width * percent / 100)
        empty = width - filled

        return "▰" * filled + "▱" * empty + f" {percent:.1f}%"

    def get_formatted_book_info(self, user_id: int, book_name: str) -> str:
        """Get formatted book information with progress"""
        progress = self.get_book_progress(user_id, book_name)
        metadata = self.get_book_metadata(user_id, book_name)

        formatted_name = self._format_name(book_name, user_id)
        info_lines = [formatted_name]

        if metadata.get('author'):
            info_lines.append(f"✍️ {metadata['author']}")

        if progress.get('total_lines', 0) > 0:
            pos = progress.get('pos', 0)
            total = progress.get('total_lines', 0)
            percent = progress.get('progress_percent', 0)
            info_lines.append(f"📊 Progress: {pos}/{total} lines ({percent}%)")
            info_lines.append(self.get_progress_bar(user_id, book_name))

        return "\n".join(info_lines)

    def close(self):
        """Close database connections"""
        self.db.close()
