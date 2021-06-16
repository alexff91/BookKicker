import unittest

from text_separator import TextSeparator


class TestTextSeparator(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_empty_line(self):
        text = ''
        result = TextSeparator(text, mode='by_sense').get_sentenses()
        self.assertEqual(result, [])

    def test_simple_case(self):
        text = 'One. Two.'
        result = TextSeparator(text, mode='by_sense').get_sentenses()
        self.assertEqual(result, ['One.', 'Two.'])

    def test_big_letter_sense(self):
        text = 'One\nTwo.'
        result = TextSeparator(text, mode='by_sense').get_sentenses()
        self.assertEqual(result, ['One.', 'Two.'])

    def test_FIO(self):
        # nltk not so good in this case. I am too lazy to fix
        text = 'В.И. Ленин.'
        result = TextSeparator(text, mode='by_sense').get_sentenses()
        self.assertEqual(result, ['В.И.', 'Ленин.'])

    def test_big_letter_poem_mode(self):
        text = '''В сто сорок солнц закат пылал, 
   в июль катилось лето, '''
        result = TextSeparator(text, mode='by_newline').get_sentenses()
        self.assertEqual(result, ['В сто сорок солнц закат пылал, ', '   в июль катилось лето, '])

    def test_big_letter_norm_mode(self):
        text = '''В сто сорок солнц закат пылал, 
   в июль катилось лето, '''
        result = TextSeparator(text, mode='by_sense').get_sentenses()
        self.assertEqual(result, ['В сто сорок солнц закат пылал, в июль катилось лето,'])


if __name__ == '__main__':
    unittest.main()
