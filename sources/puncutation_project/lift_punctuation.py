# encoding=utf-8

from __future__ import unicode_literals, print_function

import re

import sefaria_classes as sef
import bleach
from sefaria.utils.hebrew import strip_nikkud
from data_utilities.dibur_hamatchil_matcher import match_text


# base_vtitle = 'William Davidson Edition - Aramaic'
base_vtitle = 'William Davidson Edition - Vocalized Aramaic'
elucidated_vtitle = 'William Davidson Edition - Hebrew'
punctuated_vtitle = 'William Davidson Edition - Aramaic Punctuated'


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
        self._connect_talmud()

    def _load_pairs(self):
        matches = list(re.finditer(r'<b>([^<]+)</b>', self._raw_segment))
        for i, (match, next_match) in enumerate(zip(matches[:-1], matches[1:])):

            # handle segment introductions
            if i == 0 and match.start() != 0:
                self._ts_pairs.append(SteinsaltzIntro.load_talmud_steinsaltz(self._raw_segment, match.start()))

            ts = TalmudSteinsaltz.load_talmud_steinsaltz(
                self._raw_segment, match.start(), match.end(), next_match.start())
            if ConnectedTalmud.is_connected(ts.talmud):
                self._ts_pairs.append(ConnectedTalmud(ts.talmud, ts.steinsaltz))
            else:
                self._ts_pairs.append(ts)

        # last one
        ts = TalmudSteinsaltz.load_talmud_steinsaltz(
            self._raw_segment, matches[-1].start(), matches[-1].end(), len(self._raw_segment)
        )
        if ConnectedTalmud.is_connected(ts.talmud):
            self._ts_pairs.append(ConnectedTalmud(ts.talmud, ts.steinsaltz))
        else:
            self._ts_pairs.append(ts)

    def reform_segment(self):
        return u''.join([ts.reform_pair() for ts in self._ts_pairs])

    def get_ts_objects(self):
        return self._ts_pairs[:]

    def _connect_talmud(self):
        """
        Connect talmud where Steinsaltz introduced elucidation within a word.
        :return:
        """
        for current, next_obj in zip(self._ts_pairs[:-1], self._ts_pairs[1:]):
            if isinstance(current, ConnectedTalmud):
                next_obj.make_connection(current)

        self._ts_pairs = [ts for ts in self._ts_pairs if not isinstance(ts, ConnectedTalmud)]


class TalmudSteinsaltz(object):
    """
    Talmud with the following Steinsaltz elucidation
    """
    def __init__(self, talmud, steinsaltz):
        self.talmud = talmud
        self.steinsaltz = steinsaltz

    @staticmethod
    def punctuation_list():
        return ['?!', '?', '!', ':', '.', ',']

    @classmethod
    def punctuation_regex(cls):
        marks = [re.escape(s) for s in cls.punctuation_list()]
        return u'|'.join(marks)

    def lift_punctuation(self):
        if not self.talmud:
            return ''
        priority_map = {
            punc: i
            for i, punc in enumerate(self.punctuation_list())
        }
        punc_regex = re.compile(self.punctuation_regex())
        punc_marks = [match.group() for match in punc_regex.finditer(self.steinsaltz)]
        talmud_mark = re.search('r{}$'.format(punc_regex.pattern), self.talmud)
        if talmud_mark:
            punc_marks.append(talmud_mark.group())
        if punc_marks:
            return min(punc_marks, key=lambda x: priority_map[x])
        else:
            return ''

    def reform_pair(self):
        return '{}{}'.format(self.talmud, self.steinsaltz)

    def get_talmud(self):
        return self.talmud

    def get_steinsaltz(self):
        return self.steinsaltz

    def talmud_word_count(self):
        return len(self.talmud.split())

    def make_connection(self, other):
        """
        :param ConnectedTalmud other:
        :return:
        """
        self.talmud = u'{}{}'.format(other.talmud, self.talmud)

    @classmethod
    def load_talmud_steinsaltz(cls, segment, current_start, current_end, next_start):
        talmud = segment[current_start:current_end]
        if current_end == next_start:
            steinsaltz = ''
        else:
            steinsaltz = segment[current_end:next_start]
        return cls(actual_bleach(talmud), actual_bleach(steinsaltz))


class SteinsaltzIntro(TalmudSteinsaltz):
    """
    Steinsaltz introduction parts. There is no Talmud preceding
    """
    def __init__(self, steinsaltz):
        super(SteinsaltzIntro, self).__init__('', steinsaltz)

    @classmethod
    def load_talmud_steinsaltz(cls, segment, next_start, *args):
        return cls(segment[:next_start])

    def lift_punctuation(self):
        return ''


class ConnectedTalmud(TalmudSteinsaltz):

    @staticmethod
    def is_connected(talmud_piece):
        # option 1: prefix letter (בהוכלמש)
        if re.match(r'^"?[\u05d1\u05d4\u05d5\u05db\u05dc\u05de\u05e9]$', talmud_piece):
            return True
        # option 2: no hebrew
        if re.match(r'^[^\u05d0-\u05ea]+$', talmud_piece):
            return True
        return False

    def lift_punctuation(self):
        return ''


class TSMap(object):
    """
    represents a map from TalmudSteinsaltz onto base Talmud
    """
    def __init__(self, reg_talmud, talmud_steinsaltz):
        """
        :param unicode reg_talmud:
        :param TalmudSteinsaltz talmud_steinsaltz:
        """
        self.reg_talmud = reg_talmud
        self.talmud_steinsaltz = talmud_steinsaltz

    def get_punctuation_for_talmud(self):
        cleaned_talmud = re.sub('{}$'.format(TalmudSteinsaltz.punctuation_regex()), '', self.reg_talmud)
        return '{}{}'.format(cleaned_talmud, self.talmud_steinsaltz.lift_punctuation())

    @classmethod
    def build_from_map(cls, segment, ts, mapping):
        if mapping[0] == -1 and mapping[1] == -1:
            return cls(u'', ts)
        return cls(u' '.join(segment.split()[mapping[0]:mapping[1]]), ts)

    def actually_has_talmud(self):
        """
        Indidcates if there is actually Talmud associated with this Steinsaltz.
        :return: bool
        """
        return bool(self.reg_talmud)


class TSSuite(object):
    def __init__(self, tsmap_list):
        self.suite = tsmap_list

    def get_punctuated_talmud(self):
        return u' '.join([tsmap.get_punctuation_for_talmud() for tsmap in self.suite if tsmap.actually_has_talmud()])


def build_maps(simple_segment, ellucidated_segment):
    modeled = ModeledSegment(ellucidated_segment)
    words = actual_bleach(strip_nikkud(simple_segment)).split()
    ts_objects = modeled.get_ts_objects()
    elucidated_words = reduce(lambda x, y: x + y.talmud_word_count(), ts_objects, 0)

    if len(words) == elucidated_words:
        mapping, current_loc = [], 0
        for ts in ts_objects:
            end = current_loc + ts.talmud_word_count()
            mapping.append((current_loc, end))
            current_loc = end
    else:
        mapping = match_text(words, [ts.get_talmud() for ts in ts_objects], overall=0)['matches']
        mapping = map(lambda x: (x[0], x[1]+1), mapping)

        last_word = 0
        for i in range(len(mapping)):
            """
            Start at 0.
            For each item, make sure the end is higher than the beginning
            if smaller:
                if the next item has a valid start value, set the end to that value
                otherwise, make this a 0 length segment

            """
            start, end = last_word, mapping[i][-1]
            if end < start:
                end = start
            mapping[i] = (start, end)
            last_word = end

        mapping[-1] = (mapping[-1][0], len(words))  # make sure mapping goes to the end

    return TSSuite([TSMap.build_from_map(simple_segment, ts, single_map)
                    for ts, single_map in zip(ts_objects, mapping)])


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

my_r = sef.Ref("Steinsaltz on Berakhot 47b.12")
base_r = sef.Ref("Berakhot 47b.12")
my_t = my_r.text('he', elucidated_vtitle).text
base_t = base_r.text('he', base_vtitle).text
maps = build_maps(base_t, my_t)
print(base_t, my_t, maps.get_punctuated_talmud(), sep='\n\n')

simple, elucidated = sef.Ref("Berakhot"), sef.Ref("Steinsaltz on Berakhot")
for simple_seg in simple.all_segment_refs():
    print(simple_seg.normal())
    elucidated_seg = sef.Ref("Steinsaltz on {}".format(simple_seg.normal()))
    assert simple_seg.sections == elucidated_seg.sections
    base_t, eluc_t = simple_seg.text('he', base_vtitle).text, elucidated_seg.text('he', elucidated_vtitle).text
    new_tc = simple_seg.text('he', punctuated_vtitle)
    if not eluc_t:
        new_tc.text = base_t
    else:
        maps = build_maps(base_t, eluc_t)
        punctuated_text = maps.get_punctuated_talmud()
        new_tc.text = punctuated_text
    new_tc.save()
