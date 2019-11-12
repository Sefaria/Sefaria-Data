# encoding=utf-8

from __future__ import unicode_literals, print_function

import re

import sefaria_classes as sef
import bleach
from data_utilities.dibur_hamatchil_matcher import match_text


base_vtitle = ''
elucidated_vtitle = ''


def extract_talmud_text(text_segment):
    """
    :param unicode text_segment:
    :return:
    """
    return [r.group(1) for r in re.finditer(r'<b>([^<]+)</b>', text_segment)]


def actual_bleach(text_segment):
    return bleach.clean(text_segment, tags=[], attributes={}, strip=True)


def get_words(word_list, start, end):
    return u' '.join(word_list[start:end+1])


class ModeledSegment(object):

    def __init__(self, segment):
        self._raw_segment = segment
        self._ts_pairs = []
        self._load_pairs()

    def _load_pairs(self):
        matches = list(re.finditer(r'<b>([^<]+)</b>', self._raw_segment))
        for i, (match, next_match) in enumerate(zip(matches[:-1], matches[1:])):

            # handle segment introductions
            if i == 0 and match.start() != 0:
                self._ts_pairs.append(SteinsaltzIntro.load_talmud_steinsaltz(self._raw_segment, match.start()))
            self._ts_pairs.append(TalmudSteinsaltz.load_talmud_steinsaltz(
                self._raw_segment, match.start(), match.end(), next_match.start()))

        # last one
        self._ts_pairs.append(TalmudSteinsaltz.load_talmud_steinsaltz(
            self._raw_segment, matches[-1].start(), matches[-1].end(), len(self._raw_segment)
        ))

    def reform_segment(self):
        return u''.join([ts.reform_pair() for ts in self._ts_pairs])

    def get_ts_objects(self):
        return self._ts_pairs[:]


class TalmudSteinsaltz(object):
    """
    Talmud with the following Steinsaltz elucidation
    """
    def __init__(self, talmud, steinsaltz):
        self.talmud = talmud
        self.steinsaltz = steinsaltz

    def lift_punctuaion(self):
        return ''

    def reform_pair(self):
        return '{}{}'.format(self.talmud, self.steinsaltz)

    def get_talmud(self):
        return self.talmud

    def get_steinsaltz(self):
        return self.steinsaltz

    @classmethod
    def load_talmud_steinsaltz(cls, segment, current_start, current_end, next_start):
        talmud = segment[current_start:current_end]
        if current_end == next_start:
            steinsaltz = ''
        else:
            steinsaltz = segment[current_end:next_start]
        return cls(talmud, steinsaltz)


class SteinsaltzIntro(TalmudSteinsaltz):
    """
    Steinsaltz introduction parts. There is no Talmud preceding
    """
    def __init__(self, steinsaltz):
        super(SteinsaltzIntro, self).__init__('', steinsaltz)

    @classmethod
    def load_talmud_steinsaltz(cls, segment, next_start, *args):
        return cls(segment[:next_start])



# base_text = actual_bleach(sef.Ref("Berakhot 2a.1").text('he', base_vtitle).text)
# base_text_words = base_text.split()
# expanded_text = sef.Ref("Steinsaltz on Berakhot 2a.1").text('he', elucidated_vtitle).text
# expanded_text_pieces = extract_talmud_text(expanded_text)
# print(base_text, extract_talmud_text(expanded_text), '\n', sep='\n')
#
# result = match_text(base_text_words, expanded_text_pieces)
# for r, x in zip(result['matches'], expanded_text_pieces):
#     print(get_words(base_text_words, *r), x, '\n', sep='\n')

"""
We can keep track of non-talmud pieces by using the start and end methods of the regex. We'll want a class that will
describe the Talmud and non-Talmud parts. This ability should give us all the data we need to lift punctuation and
know which Talmud segment it belongs to.

Then we can write a method that takes an index and knows which punctuation to lift from said method. Using the match,
we should be able to decide where that punctuation belongs.

This only deals with punctuation in the elucdation (and possibly on the border). We'll still need to consider
punctuation within the Talmud quote.

We'll want to have pairs strings - Talmud, ellucidation. This will be a class. Ideally, all the punctuation lifting
logic can be here. The elucidation will always follow the Talmud. We'll want to have a special "intro" subclass. 
"""

my_r = sef.Ref("Steinsaltz on Berakhot 2a.1")
my_t = my_r.text('he', elucidated_vtitle).text
ms = ModeledSegment(my_t)
print(my_t, ms.reform_segment(), sep='\n\n')
