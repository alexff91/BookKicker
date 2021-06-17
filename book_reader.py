import database
from books_library import *
from txt_file import *


class BookReader():
    """Getting text from book and getting books """

    def __init__(self):
        self.db = database.DataBase()
        self.books_lib = BooksLibrary()

    def get_next_portion(self, user_id):
        # Return next part of text of the book on filename
        # Do not recognise end of file. Return '/more' in the end of message
        current_book = self.books_lib.get_current_book(user_id)
        if current_book == -1:
            return None  # 'Sorry, did not find you in users.
        pos = self.books_lib.get_pos(user_id, current_book)
        file_path = os.path.join(config.path_for_save, current_book)
        txt_file = TxtFile()
        text_piece, i = txt_file.read_piece(file_path, pos, config.piece_size)
        self.books_lib.update_book_pos(user_id, current_book, i + 1)
        return text_piece + '\n__стр.' + str(i) + '__'
