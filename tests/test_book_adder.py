import unittest
import os

from file_converter import FileConverter

class TestBookAdder(unittest.TestCase):
    def setUp(self):
        self.epub_path = os.path.join(os.getcwd(), 'Taganov_Rybya-Krov_3_Morskoy-knyaz.VHl1UQ.432728.fb2')
        pass

    def tearDown(self):
        pass

    def test_book_3rd_text(self):
        file_converter = FileConverter()
        book_name = file_converter.save_file_as_txt(140887, self.epub_path,
                                                    sent_mode="by_sense")
        pass


if __name__ == '__main__':
    unittest.main()
