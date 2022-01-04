import errno
import re
import nltk

nltk.download('punkt')
from nltk.tokenize import sent_tokenize


class TextSeparator(object):
    """Split text to sentences, the way depends on mode value
    If the mode is by_sense, bot try to make sentences even if they finished without a dot
    Else the bot make sentences just only by newline symbols"""

    def __init__(self, in_text='', mode=''):
        """Constructor"""
        try:
            self._input_text = in_text
            self._spit_text_to_sensenses(mode=mode)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        pass

    def get_sentences(self):
        return self._output_sentences

    def _spit_text_to_sensenses(self, mode):
        text = self._input_text
        spec_regex = r'\w[\n\r\f\v]+[0-9A-ZА-Я]'
        dot_without_space_regex = r'\w\\.\w\w'  # ex: отстраняются от работы.Важнейший принцип работы мозга
        if mode == 'by_sense':
            # replace [letter or digit] + newline + big letter after --> '. '
            text = re.sub(spec_regex, self._new_strings_to_space, text,
                          flags=re.M)
            # replace [letter or digit] + dot + two letters after --> '. '
            text = re.sub(dot_without_space_regex, self._add_space_to_dot,
                          text,
                          flags=re.M)
            # make one big string from all textlines and then separate them by dot
            # text = re.sub(r'\s+', ' ', text, flags=re.M)
            self._output_sentences = sent_tokenize(text, 'russian')
            # todo: auto detect lang
            # todo: limit max sentence size
        else:
            self._output_sentences = text.split(sep='\n')
        pass

    def _new_strings_to_space(self, matchobj):
        # replace newstring to '. '
        text_piace = matchobj.group(0)
        return re.sub(r'[\n\r\f\v]+', '. ', text_piace, flags=re.M)

    def _add_space_to_dot(self, matchobj):
        # replace '.' to '. '
        text_piace = matchobj.group(0)
        return re.sub(r'\\.', '. ', text_piace, flags=re.M)

    def _print(self):
        for sent in self._output_sentences:
            print(sent)
        pass
