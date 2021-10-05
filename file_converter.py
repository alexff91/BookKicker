import logging
import re

import config
from epub_reader import EpubReader
from text_transliter import TextTransliter
from txt_file import TxtFile
from pathlib import Path
import lxml.etree as et


class FileConverter(object):
    """convert file from epub to txt"""

    def __init__(self, path_for_save=''):
        # db = database.DataBase()
        logging.basicConfig(filename="sample.log", filemode="w",
                            level=logging.ERROR)
        logger = logging.getLogger("ex")
        if path_for_save != '':
            self._path_for_save = path_for_save
        else:
            self._path_for_save = config.path_for_save
        pass

    @staticmethod
    def _make_filename(user_id='', book_title=''):
        trans_title = TextTransliter(book_title).get_translitet()
        trans_title = trans_title.replace(" ", "_").lower()
        filename = str(user_id) + '_' + trans_title
        return filename

    def save_file_as_txt(self, user_id, epub_path, sent_mode='by_sense'):
        if epub_path.endswith(".epub"):
            # put text of book from epub in new txt file. Return txt file name
            book_reader = EpubReader(epub_path)
            book_title = book_reader.get_booktitle()
            # remove special character
            book_title.isalnum()
            txt_title = self._make_filename(user_id, book_title)
            txt_title.isalnum()
            txt_title = txt_title.replace("'", "").replace("\\", "")[0:150]
            txt_title = re.sub('[^A-z0-9 _]', '', txt_title).lower().replace(" ", "_")
            txt_file = TxtFile()
            txt_file.create_file(self._path_for_save, txt_title)

            cur_text = book_reader.get_next_item_text()
            while cur_text is not None:
                txt_file.write_text(cur_text, sent_mode)
                cur_text = book_reader.get_next_item_text()
            txt_file.stop_writing()
            return txt_file.get_filename()
        elif epub_path.endswith(".fb2"):
            txt_title = self._make_filename(user_id, Path(epub_path).stem)
            txt_title.isalnum()
            txt_title = txt_title.replace("'", "").replace("\\", "")[0:150]
            txt_file = TxtFile()
            txt_file.create_file(self._path_for_save, txt_title)
            with open(epub_path, 'rb') as f_in:
                check = f_in.read()
                tree = et.fromstring(check)
                ns = {'ns': "http://www.gribuser.ru/xml/fictionbook/2.0"}
                for bin_eb in tree.xpath('//ns:binary', namespaces=ns):
                    bin_eb.getparent().remove(bin_eb)
                for bin_ed in tree.xpath('//ns:description', namespaces=ns):
                    bin_ed.getparent().remove(bin_ed)
                cleart = et.tounicode(tree)
                cleart = re.sub(r'\<[^>]*\>', '', cleart)
                txt_file.write_text(cleart, sent_mode)
                txt_file.stop_writing()
            return txt_file.get_filename()
        elif epub_path.endswith(".txt"):
            txt_title = self._make_filename(user_id, Path(epub_path).stem)
            txt_title.isalnum()
            txt_title = txt_title.replace("'", "").replace("\\", "")[0:150]
            txt_title = re.sub('[^A-z0-9 _]', '', txt_title).lower().replace(" ", "_")
            txt_file = TxtFile()
            txt_file.create_file(self._path_for_save, txt_title)
            with open(epub_path) as fp:
                line = fp.readline()
                cnt = 1
                while line:
                    print("Line {}: {}".format(cnt, line.strip()))
                    txt_file.write_text(line, sent_mode)
                    line = fp.readline()
                    cnt += 1
            txt_file.stop_writing()
            return txt_file.get_filename()