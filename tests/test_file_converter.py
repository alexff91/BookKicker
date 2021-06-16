import os
import unittest

from file_converter import FileConverter


class TestEpubReader(unittest.TestCase):
    def setUp(self):
        self.epub_path = os.path.join(os.getcwd(), 'test_book.epub')
        pass

    def tearDown(self):
        pass

    def test_book_convertion(self):
        path_for_save = os.path.normpath(os.getcwd().replace('tests', 'files'))
        fc = FileConverter(path_for_save)
        result = fc.save_file_as_txt(140887, self.epub_path)
        self.assertEqual(result, '140887_gippopotam.txt')


if __name__ == '__main__':
    unittest.main()
