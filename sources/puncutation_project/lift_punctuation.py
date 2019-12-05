# encoding=utf-8

from __future__ import unicode_literals, print_function

import re

import sefaria_classes as sef
import bleach
from sefaria.utils.hebrew import strip_nikkud
from data_utilities.dibur_hamatchil_matcher import match_text
from data_utilities.util import WeightedLevenshtein
from collections import namedtuple

Quotation = namedtuple('Quotation', ['word_index', 'type'])


# base_vtitle = 'William Davidson Edition - Aramaic'
base_vtitle = 'William Davidson Edition - Vocalized Aramaic'
elucidated_vtitle = 'William Davidson Edition - Hebrew'
punctuated_vtitle = 'William Davidson Edition - Aramaic Punctuated'
WL = WeightedLevenshtein()


def best_match_word_match(base_words, punctuated_words, word_index):
    """
    Get the index of the word in base_words that best matches punctuated_words[word_number]
    :param list base_words: words we're looking to find a match
    :param list punctuated_words: list of words where the word in question came from
    :param int word_index: index of the word in question
    :return: int
    """
    try:
        word_in_question = punctuated_words[word_index]
    except IndexError:
        word_in_question = punctuated_words[-1]

    if base_words.count(word_in_question) == 1:  # single perfect match
        return base_words.index(word_in_question)

    else:
        levenshteins = [WL.calculate(base_word, word_in_question, False) for base_word in base_words]
        distance_penalties = [1 + abs(0.2*(i-word_index)) for i in range(len(base_words))]
        scores = [i*j for i, j in zip(levenshteins, distance_penalties)]
        return min(range(len(scores)), key=lambda x: scores[x])


def identify_quotations(stein_talmud):
    quotations = []

    for i, word in enumerate(stein_talmud.split()):
        if re.search(r'(?:^|\s)"[\u05d0-\u05ea]', word):
            quotations.append(Quotation(i, 'open'))
        if re.search(r'[\u05d0-\u05ea]"(?:[^\u05d0-\u05ea]|$)', word):
            quotations.append(Quotation(i, 'close'))

    return quotations


def add_quote_to_word(quotation, word):
    """
    :param Quotation quotation:
    :param unicode word:
    :return:
    """
    if quotation.type == 'open':
        return '"{}'.format(word)
    else:
        word = '{}"'.format(word)
        return re.sub(r'({})(")$'.format(TalmudSteinsaltz.punctuation_regex()), r'\g<2>\g<1>', word)


def extract_quotations(regular_talmud, stein_talmud):
    """
    place quotations from steinsaltz into talmud
    :param unicode regular_talmud: Basic talmud as lifted from database. Can have punctuation and nikkud
    :param unicode stein_talmud: Talmud part of Steinsaltz ellucidation. Must be preparsed to remove Steinsaltz.
    :return: unicode
    """
    quotations = identify_quotations(stein_talmud)
    cleaned_talmud = re.sub(r'[^\u05d0-\u05ea\s]', '', regular_talmud)
    cleaned_stein = re.sub(r'[^\u05d0-\u05ea\s]', '', stein_talmud)

    talmud_words, stein_words = regular_talmud.split(), stein_talmud.split()
    clean_talmud_words, clean_stein_words = cleaned_talmud.split(), cleaned_stein.split()

    for quote in quotations:
        if len(talmud_words) == len(stein_words):
            word_index = quote.word_index
        else:
            word_index = best_match_word_match(clean_talmud_words, clean_stein_words, quote.word_index)

        talmud_words[word_index] = add_quote_to_word(quote, talmud_words[word_index])

    return re.sub(r'"{2,}', '"', ' '.join(talmud_words))


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
        talmud_mark = re.search(r'({})$'.format(punc_regex.pattern), self.talmud)

        # Talmud mark takes priority, with the exception of the comma.
        if talmud_mark:
            if talmud_mark == ',':
                # Comma gets treated as standard punctuation (this is just a rule-of-thumb, feel free to revisit)
                punc_marks.append(talmud_mark.group(1))
            else:
                return talmud_mark.group(1)

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
        """
        For punctuation within bold - use simple word counts. In places where the length of both Talmud fragments don't match
        up, make a(n educated) guess, but mark with a tilda (~)
        Let's write two methods: One uses word counts, the other uses word matching.
        """
        if len(cleaned_talmud.split()) == len(self.talmud_steinsaltz.talmud.split()):
            cleaned_talmud = self.lift_from_bold_counts(cleaned_talmud, self.talmud_steinsaltz)
        else:
            cleaned_talmud = self.lift_from_bold_word_match(cleaned_talmud, self.talmud_steinsaltz)

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

    @staticmethod
    def lift_from_bold_counts(simple_talmud, talmud_steinsaltz):
        """
        Add punctuation that appears inside bold part of Steinsaltz elucidation (not at the edges though). This method
        is only to be used when both versions have the same number of words
        :param unicode simple_talmud:
        :param TalmudSteinsaltz talmud_steinsaltz:
        :return: unicode
        """
        simple_words, stein_words = simple_talmud.split(), talmud_steinsaltz.talmud.split()
        assert len(simple_words) == len(stein_words)

        punc_regex = re.compile(r'({})$'.format(TalmudSteinsaltz.punctuation_regex()))

        def lift_punctuation(simple, stein):
            punc_match = punc_regex.search(stein)
            if punc_match:
                return '{}{}'.format(simple, punc_match.group(1))
            else:
                return simple
        temp_talmud = u' '.join(map(lift_punctuation, simple_words, stein_words))

        # strip out punctuation on the edge - this will need to take punctuation from Steinsaltz into account
        return punc_regex.sub('', temp_talmud)

    @staticmethod
    def lift_from_bold_word_match(simple_talmud, talmud_steinsaltz):
        """
        Extract punctuation using text matching.
        Go for exact string match first where there is only one match. If that doesn't work, use "rule-of-thumb"
        but mark with a `~`
        :param unicode simple_talmud:
        :param TalmudSteinsaltz talmud_steinsaltz:
        :return:
        """

        punc_regex = re.compile(r'({})$'.format(talmud_steinsaltz.punctuation_regex()))
        talmud_words, cleaned_talmud_words = simple_talmud.split(), strip_nikkud(simple_talmud).split()

        for word_num, stein_word in enumerate(talmud_steinsaltz.talmud.split()[:-1]):  # don't bother with last word
            punc_match = punc_regex.search(stein_word)
            if not punc_match:
                continue

            stripped = re.sub(r'[^\u05d0-\u05ea]', '', stein_word)
            if cleaned_talmud_words.count(stripped) == 1:  # single, perfect match
                word_index = cleaned_talmud_words.index(stripped)
                talmud_words[word_index] = '{}{}'.format(talmud_words[word_index], punc_match.group(1))

            else:
                levenshteins = [WL.calculate(stripped, talmud_word, False) for talmud_word in cleaned_talmud_words]
                distance_penalties = [1 + abs(0.05*(i-word_num)) for i in range(len(cleaned_talmud_words))]
                # yes, numpy would be better, don't over engineer though
                scores = [i*j for i, j in zip(levenshteins, distance_penalties)]
                best_match = min(range(len(scores)), key=lambda x: scores[x])

                # since we're using fuzzy matching, mark with a `~` for manual review
                talmud_words[best_match] = '{}~{}'.format(talmud_words[best_match], punc_match.group(1))
        return ' '.join(talmud_words)


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


if __name__ == '__main__':
    my_r = sef.Ref("Steinsaltz on Berakhot 2b.2")
    base_r = sef.Ref("Berakhot 2b.2")
    my_t = my_r.text('he', elucidated_vtitle).text
    base_t = base_r.text('he', base_vtitle).text
    ms = ModeledSegment(my_t)
    stein_without_stein = u' '.join(t.get_talmud() for t in ms.get_ts_objects())
    maps = build_maps(base_t, my_t)
    partial_punctuation = maps.get_punctuated_talmud()
    final_punctuation = extract_quotations(partial_punctuation, stein_without_stein)
    print(base_t, my_t, partial_punctuation, final_punctuation, sep='\n\n')

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
            ms = ModeledSegment(eluc_t)
            stein_without_stein = u' '.join(t.get_talmud() for t in ms.get_ts_objects())
            punctuated_text = extract_quotations(punctuated_text,stein_without_stein)
            new_tc.text = punctuated_text
        new_tc.save()
