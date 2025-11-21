#!/usr/bin/env python3
"""
Improved Telegram Bot Handler for BookKicker
Features:
- Dynamic inline keyboard menus
- Progress tracking and statistics
- Enhanced book management
- Bookmarks support
- Secure database with connection pooling
- Multi-language audio support
"""

import datetime
import sys
import time
import os
from pathlib import Path

import flask
import telebot
from apscheduler.schedulers.background import BackgroundScheduler
from gtts import gTTS
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from langdetect import detect

import config
import tokens
from book_adder import BookAdder
from book_reader import BookReader
from books_library_improved import ImprovedBooksLibrary
from file_extractor import FileExtractor
from info_logger import BotLogger
from dynamic_menus import DynamicMenus

# Configuration
secret = "GUID"
token = tokens.test_token
if '--prod' in sys.argv:
    token = tokens.production_token

webhook_host = tokens.ruvds_server_ip
webhook_url_base = f"https://{webhook_host}:{config.webhook_port}"
webhook_url_path = f"/{token}/"

# Initialize bot
tb = telebot.TeleBot(token, threaded=False)
tb.remove_webhook()
time.sleep(1)
tb.set_webhook(url=webhook_url_base + webhook_url_path,
               certificate=open(config.webhook_ssl_cert, 'r'))

# Flask app for webhook
app = flask.Flask(__name__)


@app.route('/', methods=['GET', 'HEAD'])
def index():
    return ''


@app.route(webhook_url_path, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        tb.process_new_updates([update])
        return ''
    else:
        flask.abort(403)


# Initialize components
book_reader = BookReader()
book_adder = BookAdder()
books_library = ImprovedBooksLibrary(use_redis=False)  # Set to True if Redis is available
dynamic_menus = DynamicMenus(config.message_success_start)
logger = BotLogger()
logger.info('Improved Telebot has been started')

# Storage
poem_mode_user_id_list = set()
user_bookmark_temp = {}  # Temporary storage for bookmark creation


# ==================== Helper Functions ====================

def get_user_lang(user_id: int) -> str:
    """Get user's language preference"""
    return books_library.get_lang(user_id)


def send_message_safe(chat_id: int, text: str, **kwargs):
    """Safely send message with error handling"""
    try:
        return tb.send_message(chat_id, text, **kwargs)
    except Exception as e:
        logger.error(f"Failed to send message to {chat_id}: {e}")
        return None


def send_text_portion(user_id: int, chat_id: int, book_name: str,
                     lang: str = 'ru', with_audio: bool = False):
    """Send next text portion to user"""
    try:
        # Get current position
        pos = books_library.get_pos(user_id, book_name)
        if pos == -1:
            pos = 0

        # Get user settings for chunk size
        settings = books_library.get_user_settings(user_id)
        chunk_size = settings.get('chunk_size', 893)

        # Read next portion
        text, new_pos, chars_read = book_reader.read_portion(
            book_name, pos, chunk_size
        )

        if not text:
            # Book finished
            msg = config.message_book_end.get(lang, config.message_book_end['ru'])
            send_message_safe(chat_id, msg,
                            reply_markup=dynamic_menus.get_main_menu(lang))

            # Record statistics
            books_library.record_reading_session(user_id, book_name, 0, 0)
            return

        # Update position
        lines_read = new_pos - pos
        books_library.update_book_pos(user_id, book_name, new_pos)

        # Record reading session
        books_library.record_reading_session(user_id, book_name, lines_read, chars_read)

        # Get progress info
        progress = books_library.get_book_progress(user_id, book_name)
        progress_percent = progress.get('progress_percent', 0)

        # Add progress info to message
        progress_bar = books_library.get_progress_bar(user_id, book_name, width=15)
        footer = f"\n\n{progress_bar}"

        # Send text
        if with_audio:
            send_audio_message(chat_id, text, lang)

        send_message_safe(
            chat_id,
            text + footer,
            reply_markup=dynamic_menus.get_reading_menu(lang),
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Error sending text portion: {e}")
        msg = "Произошла ошибка" if lang == 'ru' else "An error occurred"
        send_message_safe(chat_id, msg)


def send_audio_message(chat_id: int, text: str, lang: str = 'ru'):
    """Send text as audio message"""
    try:
        # Detect language if not specified
        if not lang or lang not in ['ru', 'en']:
            try:
                detected = detect(text)
                lang = detected if detected in ['ru', 'en'] else 'ru'
            except:
                lang = 'ru'

        # Generate audio
        tts = gTTS(text=text, lang=lang)
        audio_file = f"temp_audio_{chat_id}.ogg"
        tts.save(audio_file)

        # Send audio
        with open(audio_file, 'rb') as audio:
            tb.send_voice(chat_id, audio)

        # Clean up
        os.remove(audio_file)

    except Exception as e:
        logger.error(f"Error sending audio: {e}")


def format_stats_message(stats: dict, lang: str = 'ru') -> str:
    """Format statistics message"""
    if lang == 'ru':
        msg = "📊 *Статистика чтения*\n\n"
        msg += f"📚 Всего книг: {stats.get('total_books', 0)}\n"
        msg += f"📖 Прочитано строк: {stats.get('total_lines_read', 0):,}\n"
        msg += f"🔤 Прочитано символов: {stats.get('total_characters_read', 0):,}\n"
        msg += f"🎯 Всего сессий: {stats.get('total_sessions', 0)}\n"

        if stats.get('first_read_date'):
            msg += f"📅 Первое чтение: {stats['first_read_date']}\n"
        if stats.get('last_read_date'):
            msg += f"📅 Последнее чтение: {stats['last_read_date']}\n"
    else:
        msg = "📊 *Reading Statistics*\n\n"
        msg += f"📚 Total books: {stats.get('total_books', 0)}\n"
        msg += f"📖 Lines read: {stats.get('total_lines_read', 0):,}\n"
        msg += f"🔤 Characters read: {stats.get('total_characters_read', 0):,}\n"
        msg += f"🎯 Total sessions: {stats.get('total_sessions', 0)}\n"

        if stats.get('first_read_date'):
            msg += f"📅 First read: {stats['first_read_date']}\n"
        if stats.get('last_read_date'):
            msg += f"📅 Last read: {stats['last_read_date']}\n"

    return msg


# ==================== Command Handlers ====================

@tb.message_handler(commands=['start'])
def start_handler(message):
    """Handle /start command"""
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        logger.log_message(message)

        lang = get_user_lang(user_id)
        msg = config.message_success_start.get(lang, config.message_success_start['ru'])

        send_message_safe(
            chat_id,
            msg,
            reply_markup=dynamic_menus.get_main_menu(lang)
        )
        logger.log_sent(user_id, chat_id, msg)
    except Exception as e:
        logger.error(f"Error in start_handler: {e}")


@tb.message_handler(commands=['help'])
def help_handler(message):
    """Handle /help command"""
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        lang = get_user_lang(user_id)

        help_msg = config.message_help.get(lang, config.message_help['ru'])

        # Add info about new features
        if lang == 'ru':
            help_msg += "\n\n*Новые возможности:*\n"
            help_msg += "🔖 Закладки для сохранения позиций\n"
            help_msg += "📊 Статистика чтения\n"
            help_msg += "📚 Библиотека с прогрессом\n"
            help_msg += "⚙️ Расширенные настройки\n"
        else:
            help_msg += "\n\n*New Features:*\n"
            help_msg += "🔖 Bookmarks to save positions\n"
            help_msg += "📊 Reading statistics\n"
            help_msg += "📚 Library with progress\n"
            help_msg += "⚙️ Extended settings\n"

        send_message_safe(
            chat_id,
            help_msg,
            reply_markup=dynamic_menus.get_main_menu(lang),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in help_handler: {e}")


@tb.message_handler(commands=['more'])
def more_handler(message):
    """Handle /more command"""
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        lang = get_user_lang(user_id)

        current_book = books_library.get_current_book(user_id)
        if current_book == -1:
            msg = config.message_no_book.get(lang, config.message_no_book['ru'])
            send_message_safe(chat_id, msg)
            return

        audio_enabled = books_library.get_audio(user_id) == 'on'
        send_text_portion(user_id, chat_id, current_book, lang, audio_enabled)

    except Exception as e:
        logger.error(f"Error in more_handler: {e}")


@tb.message_handler(commands=['skip'])
def skip_handler(message):
    """Handle /skip command - skip ahead"""
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        lang = get_user_lang(user_id)

        current_book = books_library.get_current_book(user_id)
        if current_book == -1:
            msg = config.message_no_book.get(lang, config.message_no_book['ru'])
            send_message_safe(chat_id, msg)
            return

        # Skip ahead by ~100 lines
        pos = books_library.get_pos(user_id, current_book)
        new_pos = pos + 100
        books_library.update_book_pos(user_id, current_book, new_pos)

        msg = "⏩ Пропущено ~100 строк" if lang == 'ru' else "⏩ Skipped ~100 lines"
        send_message_safe(chat_id, msg)

        # Send next portion
        audio_enabled = books_library.get_audio(user_id) == 'on'
        send_text_portion(user_id, chat_id, current_book, lang, audio_enabled)

    except Exception as e:
        logger.error(f"Error in skip_handler: {e}")


@tb.message_handler(commands=['menu'])
def menu_handler(message):
    """Handle /menu command - show main menu"""
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        lang = get_user_lang(user_id)

        msg = "Главное меню:" if lang == 'ru' else "Main menu:"
        send_message_safe(
            chat_id,
            msg,
            reply_markup=dynamic_menus.get_main_menu(lang)
        )
    except Exception as e:
        logger.error(f"Error in menu_handler: {e}")


@tb.message_handler(commands=['stats'])
def stats_handler(message):
    """Handle /stats command - show statistics"""
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        lang = get_user_lang(user_id)

        total_stats = books_library.get_total_stats(user_id)

        if not total_stats or total_stats.get('total_books', 0) == 0:
            msg = "Статистика пока пуста" if lang == 'ru' else "No statistics yet"
            send_message_safe(chat_id, msg)
            return

        stats_msg = format_stats_message(total_stats, lang)
        send_message_safe(
            chat_id,
            stats_msg,
            reply_markup=dynamic_menus.get_stats_menu(lang),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in stats_handler: {e}")


@tb.message_handler(commands=['library'])
def library_handler(message):
    """Handle /library command - show book library"""
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        lang = get_user_lang(user_id)

        books = books_library.get_user_books_with_progress(user_id)

        if not books:
            msg = "Ваша библиотека пуста" if lang == 'ru' else "Your library is empty"
            send_message_safe(chat_id, msg)
            return

        msg = f"📚 *{'Ваша библиотека' if lang == 'ru' else 'Your library'}*\n"
        msg += f"{'Всего книг' if lang == 'ru' else 'Total books'}: {len(books)}"

        send_message_safe(
            chat_id,
            msg,
            reply_markup=dynamic_menus.get_library_menu(books, lang),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in library_handler: {e}")


# ==================== Callback Query Handlers ====================

@tb.callback_query_handler(func=lambda call: call.data.startswith('menu:'))
def menu_callback_handler(call: CallbackQuery):
    """Handle menu navigation callbacks"""
    try:
        user_id, chat_id = call.from_user.id, call.message.chat.id
        lang = get_user_lang(user_id)

        menu_type = call.data.split(':')[1]

        if menu_type == 'main':
            msg = "Главное меню:" if lang == 'ru' else "Main menu:"
            markup = dynamic_menus.get_main_menu(lang)

        elif menu_type == 'library':
            books = books_library.get_user_books_with_progress(user_id)
            msg = f"📚 *{'Ваша библиотека' if lang == 'ru' else 'Your library'}*"
            markup = dynamic_menus.get_library_menu(books, lang)

        elif menu_type == 'settings':
            msg = "⚙️ *Настройки:*" if lang == 'ru' else "⚙️ *Settings:*"
            markup = dynamic_menus.get_settings_menu(lang)

        elif menu_type == 'stats':
            msg = "📊 *Статистика:*" if lang == 'ru' else "📊 *Statistics:*"
            markup = dynamic_menus.get_stats_menu(lang)

        else:
            return

        tb.edit_message_text(
            msg,
            chat_id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
        tb.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Error in menu_callback_handler: {e}")
        tb.answer_callback_query(call.id, "Error")


@tb.callback_query_handler(func=lambda call: call.data.startswith('action:'))
def action_callback_handler(call: CallbackQuery):
    """Handle action callbacks"""
    try:
        user_id, chat_id = call.from_user.id, call.message.chat.id
        lang = get_user_lang(user_id)

        action = call.data.split(':')[1]

        if action == 'read_more':
            current_book = books_library.get_current_book(user_id)
            if current_book == -1:
                msg = "Сначала загрузите книгу" if lang == 'ru' else "Please upload a book first"
                tb.answer_callback_query(call.id, msg, show_alert=True)
                return

            audio_enabled = books_library.get_audio(user_id) == 'on'
            send_text_portion(user_id, chat_id, current_book, lang, audio_enabled)
            tb.answer_callback_query(call.id)

        elif action == 'skip':
            current_book = books_library.get_current_book(user_id)
            if current_book != -1:
                pos = books_library.get_pos(user_id, current_book)
                books_library.update_book_pos(user_id, current_book, pos + 100)
                audio_enabled = books_library.get_audio(user_id) == 'on'
                send_text_portion(user_id, chat_id, current_book, lang, audio_enabled)
            tb.answer_callback_query(call.id, "⏩")

        elif action == 'add_bookmark':
            current_book = books_library.get_current_book(user_id)
            if current_book != -1:
                pos = books_library.get_pos(user_id, current_book)
                books_library.add_bookmark(user_id, current_book, pos)
                msg = f"🔖 Закладка добавлена" if lang == 'ru' else f"🔖 Bookmark added"
                tb.answer_callback_query(call.id, msg, show_alert=True)
            else:
                tb.answer_callback_query(call.id)

        elif action == 'help':
            help_handler(call.message)
            tb.answer_callback_query(call.id)

        elif action == 'toggle_auto_send':
            books_library.switch_auto_status(user_id)
            status = books_library.get_auto_status(user_id) == 1
            markup = dynamic_menus.get_auto_send_menu(status, lang)
            tb.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=markup)
            tb.answer_callback_query(call.id, "✅")

    except Exception as e:
        logger.error(f"Error in action_callback_handler: {e}")
        tb.answer_callback_query(call.id, "Error")


@tb.callback_query_handler(func=lambda call: call.data.startswith('setting:'))
def setting_callback_handler(call: CallbackQuery):
    """Handle settings callbacks"""
    try:
        user_id, chat_id = call.from_user.id, call.message.chat.id
        lang = get_user_lang(user_id)

        setting = call.data.split(':')[1]

        if setting == 'auto_send':
            status = books_library.get_auto_status(user_id) == 1
            msg = "🔄 *Автоотправка*" if lang == 'ru' else "🔄 *Auto-send*"
            markup = dynamic_menus.get_auto_send_menu(status, lang)

        elif setting == 'language':
            msg = "🌍 *Выберите язык:*" if lang == 'ru' else "🌍 *Choose language:*"
            markup = dynamic_menus.get_language_menu(lang)

        elif setting == 'frequency':
            rare = int(books_library.get_rare(user_id))
            msg = "⏰ *Частота отправки:*" if lang == 'ru' else "⏰ *Send frequency:*"
            markup = dynamic_menus.get_frequency_menu(rare, lang)

        elif setting == 'audio':
            audio = books_library.get_audio(user_id) == 'on'
            msg = "🔊 *Аудио режим:*" if lang == 'ru' else "🔊 *Audio mode:*"
            markup = dynamic_menus.get_audio_menu(audio, lang)

        elif setting == 'chunk_size':
            settings = books_library.get_user_settings(user_id)
            chunk_size = settings.get('chunk_size', 893)
            msg = "📏 *Размер порции текста:*" if lang == 'ru' else "📏 *Text chunk size:*"
            markup = dynamic_menus.get_chunk_size_menu(chunk_size, lang)

        else:
            return

        tb.edit_message_text(
            msg,
            chat_id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
        tb.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Error in setting_callback_handler: {e}")
        tb.answer_callback_query(call.id, "Error")


@tb.callback_query_handler(func=lambda call: call.data.startswith('lang:set:'))
def lang_set_handler(call: CallbackQuery):
    """Handle language change"""
    try:
        user_id = call.from_user.id
        new_lang = call.data.split(':')[2]

        books_library.update_lang(user_id, new_lang)

        msg = "Язык изменен ✅" if new_lang == 'ru' else "Language changed ✅"
        tb.answer_callback_query(call.id, msg)

        # Refresh settings menu
        markup = dynamic_menus.get_settings_menu(new_lang)
        tb.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )

    except Exception as e:
        logger.error(f"Error in lang_set_handler: {e}")
        tb.answer_callback_query(call.id, "Error")


@tb.callback_query_handler(func=lambda call: call.data.startswith('freq:set:'))
def freq_set_handler(call: CallbackQuery):
    """Handle frequency change"""
    try:
        user_id = call.from_user.id
        lang = get_user_lang(user_id)
        new_freq = int(call.data.split(':')[2])

        books_library.update_rare(user_id, new_freq)

        msg = f"Частота: {new_freq} раз/день ✅" if lang == 'ru' else f"Frequency: {new_freq} times/day ✅"
        tb.answer_callback_query(call.id, msg)

        # Refresh menu
        markup = dynamic_menus.get_frequency_menu(new_freq, lang)
        tb.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )

    except Exception as e:
        logger.error(f"Error in freq_set_handler: {e}")
        tb.answer_callback_query(call.id, "Error")


@tb.callback_query_handler(func=lambda call: call.data.startswith('audio:set:'))
def audio_set_handler(call: CallbackQuery):
    """Handle audio mode change"""
    try:
        user_id = call.from_user.id
        lang = get_user_lang(user_id)
        audio_mode = call.data.split(':')[2]

        books_library.update_audio(user_id, audio_mode)

        msg = "Аудио: " if lang == 'ru' else "Audio: "
        msg += ("Вкл ✅" if audio_mode == 'on' else "Выкл ✅") if lang == 'ru' else ("On ✅" if audio_mode == 'on' else "Off ✅")
        tb.answer_callback_query(call.id, msg)

        # Refresh menu
        audio_enabled = audio_mode == 'on'
        markup = dynamic_menus.get_audio_menu(audio_enabled, lang)
        tb.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )

    except Exception as e:
        logger.error(f"Error in audio_set_handler: {e}")
        tb.answer_callback_query(call.id, "Error")


@tb.callback_query_handler(func=lambda call: call.data.startswith('chunk:set:'))
def chunk_set_handler(call: CallbackQuery):
    """Handle chunk size change"""
    try:
        user_id = call.from_user.id
        lang = get_user_lang(user_id)
        chunk_size = int(call.data.split(':')[2])

        books_library.update_chunk_size(user_id, chunk_size)

        msg = f"Размер порции: {chunk_size} ✅" if lang == 'ru' else f"Chunk size: {chunk_size} ✅"
        tb.answer_callback_query(call.id, msg)

        # Refresh menu
        markup = dynamic_menus.get_chunk_size_menu(chunk_size, lang)
        tb.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )

    except Exception as e:
        logger.error(f"Error in chunk_set_handler: {e}")
        tb.answer_callback_query(call.id, "Error")


@tb.callback_query_handler(func=lambda call: call.data.startswith('book:'))
def book_callback_handler(call: CallbackQuery):
    """Handle book-related callbacks"""
    try:
        user_id, chat_id = call.from_user.id, call.message.chat.id
        lang = get_user_lang(user_id)

        parts = call.data.split(':', 2)
        action = parts[1]
        book_name = parts[2] if len(parts) > 2 else None

        if action == 'read' and book_name:
            # Read from this book
            books_library.update_current_book(user_id, chat_id, book_name)
            audio_enabled = books_library.get_audio(user_id) == 'on'
            send_text_portion(user_id, chat_id, book_name, lang, audio_enabled)
            tb.answer_callback_query(call.id)

        elif action == 'set_current' and book_name:
            # Set as current book
            books_library.update_current_book(user_id, chat_id, book_name)
            msg = "✅ Книга установлена текущей" if lang == 'ru' else "✅ Book set as current"
            tb.answer_callback_query(call.id, msg, show_alert=True)

    except Exception as e:
        logger.error(f"Error in book_callback_handler: {e}")
        tb.answer_callback_query(call.id, "Error")


@tb.callback_query_handler(func=lambda call: call.data.startswith('stats:'))
def stats_callback_handler(call: CallbackQuery):
    """Handle statistics callbacks"""
    try:
        user_id, chat_id = call.from_user.id, call.message.chat.id
        lang = get_user_lang(user_id)

        stat_type = call.data.split(':')[1]

        if stat_type == 'total':
            stats = books_library.get_total_stats(user_id)
            msg = format_stats_message(stats, lang)

        elif stat_type == 'week':
            stats_list = books_library.get_reading_stats(user_id, days=7)
            msg = "📈 *Статистика за неделю*\n\n" if lang == 'ru' else "📈 *Week Statistics*\n\n"
            for stat in stats_list:
                msg += f"📅 {stat['session_date']}: {stat['total_lines']} строк\n"

        elif stat_type == 'month':
            stats_list = books_library.get_reading_stats(user_id, days=30)
            msg = "📅 *Статистика за месяц*\n\n" if lang == 'ru' else "📅 *Month Statistics*\n\n"
            for stat in stats_list:
                msg += f"📅 {stat['session_date']}: {stat['total_lines']} строк\n"

        else:
            return

        tb.edit_message_text(
            msg,
            chat_id,
            call.message.message_id,
            reply_markup=dynamic_menus.get_stats_menu(lang),
            parse_mode='Markdown'
        )
        tb.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Error in stats_callback_handler: {e}")
        tb.answer_callback_query(call.id, "Error")


# ==================== File Handler ====================

@tb.message_handler(content_types=['document'])
def document_handler(message):
    """Handle book file uploads"""
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        lang = get_user_lang(user_id)
        logger.log_message(message)

        # Extract and process file
        file_extractor = FileExtractor(user_id)
        file_path = file_extractor.download(message)

        if not file_path:
            msg = "Ошибка загрузки файла" if lang == 'ru' else "File upload error"
            send_message_safe(chat_id, msg)
            return

        # Add book
        book_name = book_adder.add_book(file_path, user_id)

        if not book_name:
            msg = "Ошибка обработки книги" if lang == 'ru' else "Book processing error"
            send_message_safe(chat_id, msg)
            return

        # Update current book
        books_library.update_current_book(user_id, chat_id, book_name)

        # Try to extract and add metadata
        try:
            file_size = Path(file_path).stat().st_size
            book_txt_path = Path(f"files/{book_name}")

            if book_txt_path.exists():
                with open(book_txt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    total_chars = len(content)
                    total_lines = content.count('\n')

                # Estimate reading time
                estimated_minutes = (total_chars // 5) // 200

                # Extract title from filename
                title = book_name.replace(f"{user_id}_", "").replace(".txt", "")

                # Detect file format
                original_ext = Path(file_path).suffix.lower().replace('.', '')

                books_library.add_book_metadata(
                    user_id=user_id,
                    book_name=book_name,
                    title=title,
                    file_format=original_ext,
                    file_size=file_size,
                    total_chars=total_chars,
                    estimated_time=estimated_minutes
                )

                # Update total lines
                books_library.update_book_pos(user_id, book_name, 0, total_lines)

        except Exception as e:
            logger.error(f"Error adding metadata: {e}")

        # Success message
        msg = f"✅ Книга '{title}' добавлена!" if lang == 'ru' else f"✅ Book '{title}' added!"
        send_message_safe(
            chat_id,
            msg,
            reply_markup=dynamic_menus.get_reading_menu(lang)
        )

        logger.log_sent(user_id, chat_id, msg)

    except Exception as e:
        logger.error(f"Error in document_handler: {e}")
        msg = "Произошла ошибка" if lang == 'ru' else "An error occurred"
        send_message_safe(chat_id, msg)


# ==================== Auto-send Scheduler ====================

def auto_send_task():
    """Task to automatically send portions to users"""
    try:
        logger.info("Running auto-send task...")
        users = books_library.get_users_for_autosend()

        current_hour = datetime.datetime.now().hour

        for user_id, chat_id in users:
            try:
                # Get user's frequency setting
                rare = int(books_library.get_rare(user_id))
                lang = get_user_lang(user_id)

                # Determine if we should send based on frequency
                send_hours = {
                    1: [12],  # Once a day at noon
                    2: [9, 17],  # Twice a day
                    4: [8, 12, 16, 20],  # 4 times a day
                    6: [7, 10, 13, 16, 19, 22],  # 6 times a day
                    12: list(range(7, 22))  # Every hour from 7 AM to 9 PM
                }

                if current_hour not in send_hours.get(rare, []):
                    continue

                # Get current book
                current_book = books_library.get_current_book(user_id)
                if current_book == -1:
                    continue

                # Send portion
                audio_enabled = books_library.get_audio(user_id) == 'on'
                send_text_portion(user_id, chat_id, current_book, lang, audio_enabled)

                logger.info(f"Auto-sent to user {user_id}")

            except Exception as e:
                logger.error(f"Error auto-sending to user {user_id}: {e}")

    except Exception as e:
        logger.error(f"Error in auto_send_task: {e}")


# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(auto_send_task, 'cron', hour='5-21', minute=0)
scheduler.start()

logger.info("Auto-send scheduler started")


# ==================== Start Server ====================

if __name__ == '__main__':
    # Remove old webhook
    tb.remove_webhook()
    time.sleep(1)

    # Set new webhook
    tb.set_webhook(url=webhook_url_base + webhook_url_path,
                   certificate=open(config.webhook_ssl_cert, 'r'))

    # Start Flask server
    logger.info(f"Starting server on port {config.webhook_port}")
    app.run(
        host=config.webhook_listen,
        port=config.webhook_port,
        ssl_context=(config.webhook_ssl_cert, config.webhook_ssl_priv),
        debug=False
    )
