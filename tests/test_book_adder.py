import unittest
import os

from file_converter import FileConverter

class TestBookAdder(unittest.TestCase):
    def setUp(self):
        self.epub_path = os.path.join(os.getcwd(), 'test_book._some_spacec.here.epub')
        pass

    def tearDown(self):
        pass

    def test_book_3rd_text(self):
        file_converter = FileConverter()
        book_name = file_converter.save_file_as_txt(140887, self.epub_path)
        pass


if __name__ == '__main__':
    unittest.main()
