"""
Dynamic menu system for Telegram bot with inline keyboards
"""

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DynamicMenus:
    """Dynamic menu generator for bot interactions"""

    def __init__(self, config_messages: Dict = None):
        self.config = config_messages or {}

    # ==================== Main Menus ====================

    def get_main_menu(self, lang: str = 'ru') -> InlineKeyboardMarkup:
        """Get main menu with primary actions"""
        markup = InlineKeyboardMarkup()
        markup.row_width = 2

        if lang == 'ru':
            markup.add(
                InlineKeyboardButton("📖 Читать дальше", callback_data="action:read_more"),
                InlineKeyboardButton("📚 Моя библиотека", callback_data="menu:library")
            )
            markup.add(
                InlineKeyboardButton("⚙️ Настройки", callback_data="menu:settings"),
                InlineKeyboardButton("📊 Статистика", callback_data="menu:stats")
            )
            markup.add(
                InlineKeyboardButton("❓ Помощь", callback_data="action:help")
            )
        else:  # English
            markup.add(
                InlineKeyboardButton("📖 Read more", callback_data="action:read_more"),
                InlineKeyboardButton("📚 My library", callback_data="menu:library")
            )
            markup.add(
                InlineKeyboardButton("⚙️ Settings", callback_data="menu:settings"),
                InlineKeyboardButton("📊 Statistics", callback_data="menu:stats")
            )
            markup.add(
                InlineKeyboardButton("❓ Help", callback_data="action:help")
            )

        return markup

    def get_reading_menu(self, lang: str = 'ru', show_skip: bool = True) -> InlineKeyboardMarkup:
        """Get reading control menu"""
        markup = InlineKeyboardMarkup()
        markup.row_width = 2

        if lang == 'ru':
            markup.add(
                InlineKeyboardButton("📖 Еще", callback_data="action:read_more")
            )
            if show_skip:
                markup.add(
                    InlineKeyboardButton("⏩ Пропустить", callback_data="action:skip"),
                    InlineKeyboardButton("🔖 Закладка", callback_data="action:add_bookmark")
                )
            markup.add(
                InlineKeyboardButton("◀️ Главное меню", callback_data="menu:main")
            )
        else:
            markup.add(
                InlineKeyboardButton("📖 More", callback_data="action:read_more")
            )
            if show_skip:
                markup.add(
                    InlineKeyboardButton("⏩ Skip", callback_data="action:skip"),
                    InlineKeyboardButton("🔖 Bookmark", callback_data="action:add_bookmark")
                )
            markup.add(
                InlineKeyboardButton("◀️ Main menu", callback_data="menu:main")
            )

        return markup

    # ==================== Library Menu ====================

    def get_library_menu(self, books: List[Dict[str, Any]], lang: str = 'ru',
                        page: int = 0, page_size: int = 5) -> InlineKeyboardMarkup:
        """Get library menu with book list"""
        markup = InlineKeyboardMarkup()
        markup.row_width = 1

        # Calculate pagination
        start_idx = page * page_size
        end_idx = start_idx + page_size
        page_books = books[start_idx:end_idx]

        # Add book buttons
        for book in page_books:
            book_name = book.get('book_name', '')
            title = book.get('title', self._format_book_name(book_name))
            progress = book.get('progress_percent', 0)

            # Create button text with progress
            if progress > 0:
                button_text = f"📖 {title} ({progress:.0f}%)"
            else:
                button_text = f"📖 {title}"

            markup.add(
                InlineKeyboardButton(button_text,
                                   callback_data=f"book:select:{book_name}")
            )

        # Add pagination buttons
        nav_buttons = []
        if page > 0:
            prev_text = "◀️ Назад" if lang == 'ru' else "◀️ Previous"
            nav_buttons.append(
                InlineKeyboardButton(prev_text,
                                   callback_data=f"library:page:{page-1}")
            )
        if end_idx < len(books):
            next_text = "Вперед ▶️" if lang == 'ru' else "Next ▶️"
            nav_buttons.append(
                InlineKeyboardButton(next_text,
                                   callback_data=f"library:page:{page+1}")
            )

        if nav_buttons:
            markup.row(*nav_buttons)

        # Back button
        back_text = "◀️ Главное меню" if lang == 'ru' else "◀️ Main menu"
        markup.add(
            InlineKeyboardButton(back_text, callback_data="menu:main")
        )

        return markup

    def get_book_details_menu(self, book_name: str, lang: str = 'ru',
                             has_bookmarks: bool = False) -> InlineKeyboardMarkup:
        """Get book details menu"""
        markup = InlineKeyboardMarkup()
        markup.row_width = 2

        if lang == 'ru':
            markup.add(
                InlineKeyboardButton("📖 Читать", callback_data=f"book:read:{book_name}"),
                InlineKeyboardButton("🔄 Выбрать текущей", callback_data=f"book:set_current:{book_name}")
            )
            if has_bookmarks:
                markup.add(
                    InlineKeyboardButton("🔖 Закладки", callback_data=f"book:bookmarks:{book_name}")
                )
            markup.add(
                InlineKeyboardButton("❌ Удалить", callback_data=f"book:delete:{book_name}")
            )
            markup.add(
                InlineKeyboardButton("◀️ Библиотека", callback_data="menu:library")
            )
        else:
            markup.add(
                InlineKeyboardButton("📖 Read", callback_data=f"book:read:{book_name}"),
                InlineKeyboardButton("🔄 Set as current", callback_data=f"book:set_current:{book_name}")
            )
            if has_bookmarks:
                markup.add(
                    InlineKeyboardButton("🔖 Bookmarks", callback_data=f"book:bookmarks:{book_name}")
                )
            markup.add(
                InlineKeyboardButton("❌ Delete", callback_data=f"book:delete:{book_name}")
            )
            markup.add(
                InlineKeyboardButton("◀️ Library", callback_data="menu:library")
            )

        return markup

    # ==================== Settings Menu ====================

    def get_settings_menu(self, lang: str = 'ru') -> InlineKeyboardMarkup:
        """Get settings menu"""
        markup = InlineKeyboardMarkup()
        markup.row_width = 1

        if lang == 'ru':
            markup.add(
                InlineKeyboardButton("🔄 Автоотправка", callback_data="setting:auto_send"),
                InlineKeyboardButton("🌍 Язык", callback_data="setting:language"),
                InlineKeyboardButton("⏰ Частота отправки", callback_data="setting:frequency"),
                InlineKeyboardButton("🔊 Аудио режим", callback_data="setting:audio"),
                InlineKeyboardButton("📏 Размер порции", callback_data="setting:chunk_size"),
                InlineKeyboardButton("🌐 Часовой пояс", callback_data="setting:timezone")
            )
            markup.add(
                InlineKeyboardButton("◀️ Главное меню", callback_data="menu:main")
            )
        else:
            markup.add(
                InlineKeyboardButton("🔄 Auto-send", callback_data="setting:auto_send"),
                InlineKeyboardButton("🌍 Language", callback_data="setting:language"),
                InlineKeyboardButton("⏰ Frequency", callback_data="setting:frequency"),
                InlineKeyboardButton("🔊 Audio mode", callback_data="setting:audio"),
                InlineKeyboardButton("📏 Chunk size", callback_data="setting:chunk_size"),
                InlineKeyboardButton("🌐 Timezone", callback_data="setting:timezone")
            )
            markup.add(
                InlineKeyboardButton("◀️ Main menu", callback_data="menu:main")
            )

        return markup

    def get_auto_send_menu(self, current_status: bool, lang: str = 'ru') -> InlineKeyboardMarkup:
        """Get auto-send toggle menu"""
        markup = InlineKeyboardMarkup()
        markup.row_width = 1

        status_emoji = "✅" if current_status else "❌"

        if lang == 'ru':
            status_text = "Включена" if current_status else "Выключена"
            markup.add(
                InlineKeyboardButton(
                    f"{status_emoji} Автоотправка: {status_text}",
                    callback_data="action:toggle_auto_send"
                )
            )
            markup.add(
                InlineKeyboardButton("◀️ Настройки", callback_data="menu:settings")
            )
        else:
            status_text = "Enabled" if current_status else "Disabled"
            markup.add(
                InlineKeyboardButton(
                    f"{status_emoji} Auto-send: {status_text}",
                    callback_data="action:toggle_auto_send"
                )
            )
            markup.add(
                InlineKeyboardButton("◀️ Settings", callback_data="menu:settings")
            )

        return markup

    def get_language_menu(self, current_lang: str) -> InlineKeyboardMarkup:
        """Get language selection menu"""
        markup = InlineKeyboardMarkup()
        markup.row_width = 2

        langs = [
            ('ru', '🇷🇺 Русский'),
            ('en', '🇬🇧 English')
        ]

        for lang_code, lang_name in langs:
            emoji = "✅" if lang_code == current_lang else ""
            markup.add(
                InlineKeyboardButton(
                    f"{emoji} {lang_name}",
                    callback_data=f"lang:set:{lang_code}"
                )
            )

        back_text = "◀️ Настройки" if current_lang == 'ru' else "◀️ Settings"
        markup.add(
            InlineKeyboardButton(back_text, callback_data="menu:settings")
        )

        return markup

    def get_frequency_menu(self, current_freq: int, lang: str = 'ru') -> InlineKeyboardMarkup:
        """Get reading frequency menu"""
        markup = InlineKeyboardMarkup()
        markup.row_width = 1

        frequencies = [
            (12, '12 раз в день' if lang == 'ru' else '12 times a day'),
            (6, '6 раз в день' if lang == 'ru' else '6 times a day'),
            (4, '4 раза в день' if lang == 'ru' else '4 times a day'),
            (2, '2 раза в день' if lang == 'ru' else '2 times a day'),
            (1, '1 раз в день' if lang == 'ru' else '1 time a day')
        ]

        for freq_value, freq_text in frequencies:
            emoji = "✅" if freq_value == current_freq else ""
            markup.add(
                InlineKeyboardButton(
                    f"{emoji} {freq_text}",
                    callback_data=f"freq:set:{freq_value}"
                )
            )

        back_text = "◀️ Настройки" if lang == 'ru' else "◀️ Settings"
        markup.add(
            InlineKeyboardButton(back_text, callback_data="menu:settings")
        )

        return markup

    def get_audio_menu(self, current_audio: bool, lang: str = 'ru') -> InlineKeyboardMarkup:
        """Get audio mode menu"""
        markup = InlineKeyboardMarkup()
        markup.row_width = 2

        if lang == 'ru':
            markup.add(
                InlineKeyboardButton(
                    f"{'✅' if current_audio else ''} Включить",
                    callback_data="audio:set:on"
                ),
                InlineKeyboardButton(
                    f"{'✅' if not current_audio else ''} Выключить",
                    callback_data="audio:set:off"
                )
            )
            markup.add(
                InlineKeyboardButton("◀️ Настройки", callback_data="menu:settings")
            )
        else:
            markup.add(
                InlineKeyboardButton(
                    f"{'✅' if current_audio else ''} Enable",
                    callback_data="audio:set:on"
                ),
                InlineKeyboardButton(
                    f"{'✅' if not current_audio else ''} Disable",
                    callback_data="audio:set:off"
                )
            )
            markup.add(
                InlineKeyboardButton("◀️ Settings", callback_data="menu:settings")
            )

        return markup

    def get_chunk_size_menu(self, current_size: int, lang: str = 'ru') -> InlineKeyboardMarkup:
        """Get chunk size selection menu"""
        markup = InlineKeyboardMarkup()
        markup.row_width = 2

        sizes = [
            (500, 'Маленький' if lang == 'ru' else 'Small'),
            (893, 'Средний' if lang == 'ru' else 'Medium'),
            (1500, 'Большой' if lang == 'ru' else 'Large'),
            (2500, 'Очень большой' if lang == 'ru' else 'Very Large')
        ]

        for size_value, size_text in sizes:
            emoji = "✅" if size_value == current_size else ""
            markup.add(
                InlineKeyboardButton(
                    f"{emoji} {size_text} ({size_value})",
                    callback_data=f"chunk:set:{size_value}"
                )
            )

        back_text = "◀️ Настройки" if lang == 'ru' else "◀️ Settings"
        markup.add(
            InlineKeyboardButton(back_text, callback_data="menu:settings")
        )

        return markup

    # ==================== Statistics Menu ====================

    def get_stats_menu(self, lang: str = 'ru') -> InlineKeyboardMarkup:
        """Get statistics menu"""
        markup = InlineKeyboardMarkup()
        markup.row_width = 1

        if lang == 'ru':
            markup.add(
                InlineKeyboardButton("📊 Общая статистика", callback_data="stats:total"),
                InlineKeyboardButton("📈 За неделю", callback_data="stats:week"),
                InlineKeyboardButton("📅 За месяц", callback_data="stats:month")
            )
            markup.add(
                InlineKeyboardButton("◀️ Главное меню", callback_data="menu:main")
            )
        else:
            markup.add(
                InlineKeyboardButton("📊 Total statistics", callback_data="stats:total"),
                InlineKeyboardButton("📈 This week", callback_data="stats:week"),
                InlineKeyboardButton("📅 This month", callback_data="stats:month")
            )
            markup.add(
                InlineKeyboardButton("◀️ Main menu", callback_data="menu:main")
            )

        return markup

    # ==================== Bookmarks Menu ====================

    def get_bookmarks_menu(self, bookmarks: List[Dict[str, Any]], book_name: str,
                          lang: str = 'ru') -> InlineKeyboardMarkup:
        """Get bookmarks menu for a book"""
        markup = InlineKeyboardMarkup()
        markup.row_width = 1

        for bookmark in bookmarks[:10]:  # Limit to 10 bookmarks
            bm_id = bookmark.get('id')
            position = bookmark.get('position')
            note = bookmark.get('note', '')

            button_text = f"🔖 Позиция {position}" if lang == 'ru' else f"🔖 Position {position}"
            if note:
                button_text += f": {note[:20]}..."

            markup.add(
                InlineKeyboardButton(
                    button_text,
                    callback_data=f"bookmark:goto:{book_name}:{bm_id}"
                )
            )

        back_text = "◀️ К книге" if lang == 'ru' else "◀️ Back to book"
        markup.add(
            InlineKeyboardButton(back_text, callback_data=f"book:details:{book_name}")
        )

        return markup

    # ==================== Confirmation Menus ====================

    def get_confirmation_menu(self, action: str, data: str, lang: str = 'ru') -> InlineKeyboardMarkup:
        """Get confirmation menu for destructive actions"""
        markup = InlineKeyboardMarkup()
        markup.row_width = 2

        if lang == 'ru':
            markup.add(
                InlineKeyboardButton("✅ Да", callback_data=f"confirm:{action}:{data}"),
                InlineKeyboardButton("❌ Нет", callback_data="cancel")
            )
        else:
            markup.add(
                InlineKeyboardButton("✅ Yes", callback_data=f"confirm:{action}:{data}"),
                InlineKeyboardButton("❌ No", callback_data="cancel")
            )

        return markup

    # ==================== Helper Methods ====================

    def _format_book_name(self, book_name: str) -> str:
        """Format book name for display"""
        # Remove user ID prefix and .txt extension
        name = book_name.split('_', 1)[-1] if '_' in book_name else book_name
        name = name.replace('.txt', '')
        return name.capitalize()

    @staticmethod
    def create_reply_keyboard(items: List[str], one_time: bool = True) -> ReplyKeyboardMarkup:
        """Create a reply keyboard from list of items"""
        markup = ReplyKeyboardMarkup(one_time_keyboard=one_time, resize_keyboard=True)
        for item in items:
            markup.row(item)
        return markup
