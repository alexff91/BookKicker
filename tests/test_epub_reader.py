import os
import unittest

from epub_reader import EpubReader


class TestEpubReader(unittest.TestCase):
    def setUp(self):
        self.epub_path = os.path.join(os.getcwd(), 'test_book._some_spacec.here.epub')
        pass

    def tearDown(self):
        pass

    def test_empty_line(self):
        # input empty line as a epub file path
        epub_path = ''
        result = EpubReader(epub_path).get_booktitle()
        self.assertEqual(result, '')

    def test_book_title(self):
        # check title returning
        result = EpubReader(self.epub_path).get_booktitle()
        self.assertEqual(result, 'Гиппопотам')

    def test_book_3rd_text(self):
        # check first word from text of 3rd doc
        efr = EpubReader(self.epub_path)
        for i in range(4):
            text = efr.get_next_item_text()
        result = text.split()
        self.assertEqual(result[1], 'II')


if __name__ == '__main__':
    unittest.main()
