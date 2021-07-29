from database import *


class BooksLibrary(object):
    """class for manage user books and auto status"""

    def __init__(self):
        self.db = DataBase()
        self.lang_cache = {}
        self.rare_cache = {}
        self.audio_cache = {}
        self.pos_cache = {}

    def update_current_book(self, user_id, chat_id, book_name):
        lang = self.get_lang(user_id)
        self.db.update_current_book(user_id, chat_id, book_name, lang)
        pass

    def update_book_pos(self, user_id, current_book, new_pos):
        self.db.update_book_pos(user_id, current_book, new_pos)
        pass

    def switch_auto_staus(self, user_id):
        self.db.update_auto_status(user_id)
        pass

    def update_lang(self, user_id, lang):
        self.db.update_lang(user_id, lang)
        self.lang_cache[user_id] = lang
        return 0

    def update_rare(self, user_id, rare):
        if rare == '12 раз в день':
            rare = 12
        elif rare == '6 раз в день':
            rare = 6
        elif rare == '4 раза в день':
            rare = 4
        elif rare == '2 раза в день':
            rare = 2
        elif rare == '1 раз в день':
            rare = 1
        else:
            rare = 12
        self.db.update_rare(user_id, rare)
        self.rare_cache[user_id] = rare
        return 0

    def update_audio(self, user_id, audio):
        self.db.update_audio(user_id, audio)
        self.audio_cache[user_id] = audio
        return 0

    def get_pos(self, user_id, book_name):
        return self.db.get_pos(user_id, book_name)

    def get_lang(self, user_id):
        lang = self.lang_cache.get(user_id, None)
        if lang is None:
            lang = self.db.get_lang(user_id)
            if lang is None:
                lang = 'ru'
                self.update_lang(user_id, lang)
        return lang

    def get_rare(self, user_id):
        rare = self.rare_cache.get(user_id, None)
        if rare is None:
            rare = self.db.get_rare(user_id)
            if rare is None:
                rare = '12'
                self.update_rare(user_id, '12 раз в день')
        return rare

    def get_audio(self, user_id):
        audio = self.audio_cache.get(user_id, None)
        if audio is None:
            audio = self.db.get_audio(user_id)
            if audio is None:
                audio = 'off'
                self.update_audio(user_id, audio)
        return audio

    def get_user_books(self, user_id):
        return self.db.get_user_books(user_id)

    def get_auto_status(self, user_id):
        auto_status = self.db.get_auto_status(user_id)
        if auto_status is None:
            return -1
        return auto_status

    def get_users_for_autosend(self):
        return self.db.get_users_for_autosend()

    def get_current_book(self, user_id, format_name=False):
        current_book = self.db.get_current_book(user_id)
        if current_book is None:
            return -1
        if format_name:
            current_book = self._format_name(current_book, user_id)
        return current_book

    def _format_name(self, file_name, user_id):
        # Just del user_id and .txt from file_name
        formatted_name = file_name
        formatted_name = formatted_name.replace(str(user_id) + '_', '')
        formatted_name = formatted_name.replace('.txt', '')
        formatted_name = formatted_name.capitalize()
        return '📖' + formatted_name
