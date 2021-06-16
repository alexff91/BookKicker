import unittest

from text_transliter import TextTransliter


class TestTextTransliter(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_empty_line(self):
        text = ''
        result = TextTransliter(text, input_lang='ru').get_translitet()
        self.assertEqual(result, '')

    # only digit string
    def test_digit_string(self):
        text = '0123456789'
        result = TextTransliter(text, input_lang='ru').get_translitet()
        self.assertEqual(result, '0123456789')

    # alphabet string
    def test_big_letter_sense(self):
        text = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя'
        result = TextTransliter(text, input_lang='ru').get_translitet()
        self.assertEqual(result,
                         'ABVGDEEZhZIJKLMNOPRSTUFHTsChShSch\'Y\'EJuJaabvgdeezhzijklmnoprstufhtschshsch\'y\'ejuja')


if __name__ == '__main__':
    unittest.main()
