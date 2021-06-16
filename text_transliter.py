import errno

from langdetect import detect
from transliterate import translit, get_available_language_codes


class TextTransliter(object):
    # convert text from one alphabet to other.

    def __init__(self, input_text='', input_lang=''):
        try:
            self._input_text = input_text
            self._transliterate(input_lang)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        pass

    def _transliterate(self, input_lang):
        # convert from russian to translit
        try:
            if input_lang == '':
                input_lang = detect(self._input_text)
            if input_lang not in get_available_language_codes():
                input_lang = 'ru'
            self._output_text = translit(self._input_text, input_lang, reversed=True)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        pass

    def get_translitet(self):
        return self._output_text
