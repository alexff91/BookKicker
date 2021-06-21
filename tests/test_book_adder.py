import unittest

from book_adder import BookAdder

book_adder = BookAdder()

class TestBookAdder(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_book_3rd_text(self):
        book_adder.add_new_book(1, 1, local_file_path,
                                sending_mode="by_sense")
        pass


if __name__ == '__main__':
    unittest.main()
