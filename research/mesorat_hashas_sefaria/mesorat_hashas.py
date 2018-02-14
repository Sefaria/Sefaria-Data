# -*- coding: utf-8 -*-

"""
algorithm - credit Dicta (dicta.org.il):
- make 484 (=22^2) hashtables
- each hash_table should have a size of 22^6
- go through shas. for every 5 words 5-gram, do:
    - get skip-gram-list for 5-gram
    - for temp-skip-gram in skip-gram-list:
        - append temp-skip-gram to corresponding hashtable with as a tuple of  (mes_name,ref,word number) (is that necessary?)
- for every 5-gram do:
    word_offset <- first gram
    6-letter-rep-list <- the 4 skip grams corresponding to the remaining 4 grams
    match-list <- for every 6-let in 6-letter-rep-list get list of matches from hash-table `word_offset`

    we define a cluster as follows: a set of i or more matching skip-grams with gaps of no more than j words in between
    the skip-grams, stretching across a total of at least k words from the start of the first skip-gram to the end of the
    last one. For this paper, we use the values i=3, j=8, k=20.



a = Mesorah_Match(here)
skip_matches = ht[a]


"""

import regex as re
import time as pytime
import numpy as np
import cPickle as pickle
import bisect, csv, codecs, json
from collections import OrderedDict, defaultdict
import itertools
import bleach
from sefaria.model import *
from sources.functions import post_link
from sefaria.system.exceptions import DuplicateRecordError
from sefaria.system.exceptions import InputError
from data_utilities.dibur_hamatchil_matcher import get_maximum_subset_dh
import logging
import multiprocessing

from sefaria.profiling import *

logging.disable(logging.WARNING)


def get_texts_from_category(category):
    if isinstance(category,str):
        categories = [category]
    else:
        categories = category

    text_names = []
    for cat in categories:
        if cat == "Talmud":
            text_names += [name for name in library.get_indexes_in_category("Talmud") if
                           not "Jerusalem " in name and not "Ritva " in name and not "Rif " in name]

        elif cat == "Mishnah" or cat == "Tosefta" or cat == "Tanakh" or cat == "Midrash":
            text_names += library.get_indexes_in_category(cat)
        elif cat == "All":
            cats = ['Bavli','Mishnah', 'Tosefta','Midrash Rabbah']
            text_names += ["Mekhilta d'Rabbi Yishmael", 'Seder Olam Rabbah','Sifra' ,'Mekhilta DeRabbi Shimon Bar Yochai','Sifrei Bamidbar','Megillat Taanit','Otzar Midrashim','Pirkei DeRabbi Eliezer','Pesikta D\'Rav Kahanna','Tanna Debei Eliyahu Rabbah','Tanna debei Eliyahu Zuta','Pesikta Rabbati']
            for c in cats:
                text_names += library.get_indexes_in_category(c)

        elif cat == "Debug":
            text_names += ["Berakhot","Taanit"]

        else:
            text_names += []

    return text_names

def tokenize_words_old(str):
    str = str.replace(u"־"," ")
    str = re.sub(r"</?[^>]+>","",str) #get rid of html tags
    str = re.sub(r"\([^\(\)]+\)","",str) #get rid of refs
    str = str.replace('"',"'")
    word_list = filter(bool,re.split(r"[\s\:\-\,\.\;\(\)\[\]\{\}]",str))
    return word_list

stop_words = [u"ר'",u'רב',u'רבי',u'בן',u'בר',u'בריה',u'אמר',u'כאמר',u'וכאמר',u'דאמר',u'ודאמר',u'כדאמר',u'וכדאמר',u'ואמר',u'כרב',
              u'ורב',u'כדרב',u'דרב',u'ודרב',u'וכדרב',u'כרבי',u'ורבי',u'כדרבי',u'דרבי',u'ודרבי',u'וכדרבי',u"כר'",u"ור'",u"כדר'",
              u"דר'",u"ודר'",u"וכדר'",u'א״ר',u'וא״ר',u'כא״ר',u'דא״ר',u'דאמרי',u'משמיה',u'קאמר',u'קאמרי',u'לרב',u'לרבי',
              u"לר'",u'ברב',u'ברבי',u"בר'",u'הא',u'בהא',u'הך',u'בהך',u'ליה',u'צריכי',u'צריכא',u'וצריכי',u'וצריכא',u'הלל',u'שמאי', u"וגו'",u'וגו׳']
stop_phrases = [u'למה הדבר דומה',u'כלל ופרט וכלל',u'אלא כעין הפרט',u'מה הפרט',u'כלל ופרט',u'אין בכלל',u'אלא מה שבפרט', u'אשר קדשנו במצותיו וצונו']


def tokenize_words(base_str):
    base_str = base_str.strip()
    base_str = bleach.clean(base_str, tags=[], strip=True)
    for match in re.finditer(ur'\(.*?\)', base_str):
        if library.get_titles_in_string(match.group()) and len(match.group().split()) <= 5:
            base_str = base_str.replace(match.group(), u"")
            # base_str = re.sub(ur"(?:\(.*?\)|<.*?>)", u"", base_str)
    base_str = re.sub(ur'־',u' ',base_str)
    base_str = re.sub(ur'[A-Za-z]',u'',base_str)
    for phrase in stop_phrases:
        base_str = base_str.replace(phrase,u'')
    word_list = re.split(ur"\s+", base_str)
    word_list = [w for w in word_list if len(w.strip()) > 0 and w not in stop_words]
    return word_list

class Gemara_Hashtable:

    def __init__(self, skip_gram_size):
        self.letter_freqs_list = [u'י', u'ו', u'א', u'מ', u'ה', u'ל', u'ר', u'נ', u'ב', u'ש', u'ת', u'ד', u'כ', u'ע', u'ח', u'ק',
                         u'פ', u'ס', u'ט', u'ז', u'ג', u'צ']

        self.sofit_map = {
        u'ך': u'כ',
        u'ם': u'מ',
        u'ן': u'נ',
        u'ף': u'פ',
        u'ץ': u'צ',
        }

        self.letters = [u'א', u'ב', u'ג', u'ד', u'ה',
                        u'ו', u'ז', u'ח', u'ט', u'י',
                        u'כ', u'ל', u'מ', u'נ', u'ס',
                        u'ע', u'פ', u'צ', u'ק', u'ר',
                        u'ש', u'ת', unichr(ord(u'ת')+1)]

        self._hash_table = defaultdict(set)
        self._already_matched_start_items = defaultdict(bool)
        self.loaded = False
        self.skip_gram_size = skip_gram_size

    def __setitem__(self,skip_gram,value):
        """

        :param skip_gram: string of 8 consecutive characters
        :param Mesorah_Item value:
        """
        index = self.w2i(skip_gram)
        temp_set = self._hash_table[index]
        temp_set.add(value)


    def __getitem__(self,five_gram):

        skip_gram_list = self.get_skip_grams(five_gram)
        #ht = self.ht_list[self.w2i(skip_gram_list[0][0])]  # should be the same for all four skip grams
        results = set()
        for skip_gram in skip_gram_list:
            index = self.w2i(skip_gram)
            results |= self._hash_table[index]

        return results


    def get_skip_grams(self,five_gram):
        """

        :param five_gram: list of 5 consecutive words
        :return: list of the 4 skip grams (in 2 letter form)
        """

        two_letter_five_gram = [self.get_two_letter_word(w) for w in five_gram]
        skip_gram_list = [u''.join(temp_skip) for temp_skip in itertools.combinations(two_letter_five_gram, self.skip_gram_size)]
        del skip_gram_list[-1] # last one is the one that skips the first element
        return skip_gram_list

    def w2i(self,w):
        """

        :param l: hebrew letters
        :return: corresponding integer
        """
        i = 0
        for ic,c in enumerate(reversed(w)):
            i += 23**ic * self.letters.index(c)

        return i

    def sofit_swap(self,C):
        return self.sofit_map[C] if C in self.sofit_map else C

    def get_two_letter_word(self,word):
        temp_word = u''
        for i, C in enumerate(word):
            temp_word += self.sofit_swap(C)

        temp_word = re.sub(ur'[^א-ת]+',u'',temp_word)
        if len(temp_word) < 2:
            if len(temp_word) == 1:
                return u'{}{}'.format(temp_word,self.letters[-1])
            else: #efes
                return u'{}{}'.format(self.letters[-1],self.letters[-1])

        indices = map(lambda c: self.letter_freqs_list.index(c), temp_word)
        first_max,i_first_max = self.letter_freqs_list[max(indices)],indices.index(max(indices))
        del indices[i_first_max]
        sec_max,i_sec_max     = self.letter_freqs_list[max(indices)],indices.index(max(indices))

        if i_first_max <= i_sec_max:
            return u'{}{}'.format(first_max,sec_max)
        else:
            return u'{}{}'.format(sec_max,first_max)


    def save(self):
        pickle.dump(self._hash_table, open('gemara_chamutz.pkl','wb'))

    def put_already_started(self, mesorah_tuple):
        self._already_matched_start_items[mesorah_tuple] = True

    def already_started_here(self, mesorah_tuple):
        return self._already_matched_start_items[mesorah_tuple]


class Mesorah_Item:

    def __init__(self, mesechta, mesechta_index, location,ref, min_distance_between_matches):
        self.mesechta = mesechta
        self.mesechta_index = mesechta_index
        self.location = location
        self.ref = ref
        self.min_distance_between_matches = min_distance_between_matches


    def __iadd__(self, other):
        if other.mesechta_index == self.mesechta_index:
            temp_loc = (self.location[0],other.location[1])
            temp_ref = self.ref.starting_ref().to(other.ref.ending_ref())
            return Mesorah_Item(self.mesechta,self.mesechta_index, temp_loc,temp_ref, self.min_distance_between_matches)
        else:
            raise ValueError("Mesechtot need to be the same")

    def __add__(self, other):
        if other.mesechta_index == self.mesechta_index:
            temp_loc = (self.location[0],other.location[1])
            temp_ref = self.ref.starting_ref().to(other.ref.ending_ref())
            return Mesorah_Item(self.mesechta, self.mesechta_index, temp_loc, temp_ref, self.min_distance_between_matches)
        else:
            raise ValueError("Mesechtot need to be the same")

    def __str__(self):
        return "{} - {} - {}".format(self.mesechta,self.location,self.ref)

    def __len__(self):
        return self.location[1] - self.location[0] + 1

    def __sub__(self, other):
        """
        :param other:
        :return:
        """
        if self.mesechta != other.mesechta:
            return None
        else:
            return other.location[0] - self.location[0]

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        return hash(str(self.mesechta_index) + str(self.location))

    def contains(self,other):
        return self.mesechta_index == other.mesechta_index and \
               ((self.location[0] < other.location[0] and self.location[1] >= other.location[1]) or
            (self.location[0] <= other.location[0] and self.location[1] > other.location[1]))

    def too_close(self, other):
        if self.mesechta_index != other.mesechta_index:
            return False
        else:
            if self.ref.is_bavli():
                assert other.ref.is_bavli()
                return abs(self.location[0] - other.location[0]) < self.min_distance_between_matches
            else:
                return self.ref == other.ref and \
                       abs(self.location[0] - other.location[0]) < self.min_distance_between_matches


    def mesechta_diff(self, other):
        return self.mesechta_index - other.mesechta_index

    def compare(self, other):
        """
        for use in sort()
        :param Mesorah_Item other:
        :param list mes_list:
        :return:
        """
        if self.mesechta_index != other.mesechta_index:
            return self.mesechta_diff(other)
        else:
            return self.location[0] - other.location[0]

    def copy(self):
        return Mesorah_Item(self.mesechta, self.mesechta_index, self.location, self.ref, self.min_distance_between_matches)


class Mesorah_Match:

    def __init__(self, a, b, min_words_in_match, score=0):
        yo = sorted((a, b), key=lambda x: x.ref.order_id())
        self.a = yo[0]
        self.b = yo[1]
        self.min_words_in_match = min_words_in_match
        self.score = score

    def __str__(self):
        return "{} <===> {}: SCORE: {}".format(self.a,self.b, self.score)

    def __eq__(self, other):
       return self.__hash__() == other.__hash__()

    def __hash__(self):
        return hash(self.a.mesechta + str(self.a.location) + self.b.mesechta + str(self.b.location))

    def valid(self):
        return len(self.a) >= self.min_words_in_match and len(self.b) >= self.min_words_in_match

class PartialMesorahMatch:

    def __init__(self, a_start, a_end, b_start, b_end, min_words_in_match):
        """

        :param Mesorah_Item a_start:
        :param Mesorah_Item a_end:
        :param Mesorah_Item b_start:
        :param Mesorah_Item b_end:
        """
        self.a_start = a_start
        self.a_end = a_end
        self.b_start = b_start
        self.b_end = b_end
        self.min_words_in_match = min_words_in_match

    def __len__(self):
        # TODO does this need to distinguish b/w len(a) and len(b)
        return self.a_start - self.a_end + 4

    def last_a_word_matched(self):
        return self.a_end.location[1]

    def finalize(self, score=0):
        """
        Convert this partial match into a regular Mesorah_Match
        :return:
        """
        return Mesorah_Match(self.a_start + self.a_end, self.b_start + self.b_end, self.min_words_in_match, score)


class ParallelMatcher:

    def __init__(self, tokenizer, dh_extract_method=None, ngram_size=5, max_words_between=4, min_words_in_match=9,
                 min_distance_between_matches=1000, all_to_all=True, parallelize=False, verbose=True, calculate_score=None):
        """

        :param tokenizer: returns list of words
        :param f(str) -> str dh_extract_method: takes the full text of `comment` and returns only the dibur hamatchil. `self.tokenizer` will be applied to it afterward. this will only be used if `comment_index_list` in `match()` is not None
        :param ngram_size: int, basic unit of matching. 1 word will be skipped in each ngram of size `ngram_size`
        :param max_words_between: max words between consecutive ngrams
        :param min_words_in_match: min words for a match to be considered valid
        :param min_distance_between_matches: min distance between matches. If matches are closer than this, the first one will be chosen (i think)
        :param bool all_to_all: if True, make between everything either in index_list or ref_list. False means results get filtered to only match inter-ref matches
        :param bool parallelize: Do you want this to run in parallel? WARNING: this uses up way more RAM. and this is already pretty RAM-hungry
        """
        self.tokenizer = tokenizer
        self.dh_extract_method = dh_extract_method
        self.ngram_size = ngram_size
        self.skip_gram_size = self.ngram_size - 1
        self.ght = Gemara_Hashtable(self.skip_gram_size)
        self.max_words_between = max_words_between
        self.min_words_in_match = min_words_in_match
        self.min_distance_between_matches = min_distance_between_matches
        self.all_to_all = all_to_all
        self.parallelize = parallelize
        self.verbose = verbose
        if calculate_score:
            self.with_scoring = True
            self.calculate_score = calculate_score


    def reset(self):
        self.ght = Gemara_Hashtable(self.skip_gram_size)

    def filter_matches_by_score_and_duplicates(self, matches, min_score=30):
        '''
        :param matches: List of Mesorah_Matches
        :param min_score: The minimum score found by the callback function, calculate_score

        It removes anything with a score less than min_score and also removes duplicate matches.

        :return:
        '''
        matches = [x.b.ref for x in matches if x.score >= min_score]
        match_set = set()
        for match in matches:
            match_set.add(match)
        return list(match_set)

    def match(self, index_list=None, tc_list=None, comment_index_list=None, use_william=False, output_root="", return_obj=False):
        """

        :param list[str] index_list: list of index names to match against
        :param list[TextChunk] tc_list: alternatively, you can give a list of TextChunks to match to
        :param list[int] comment_index_list: list of indexes which correspond to either `index_list` or `tc_list` (whichever is not None). each index in this list indicates that the corresponding element should be treated as a `comment` meaning `self.dh_extract_method()` will be used on it.
        :param bool use_william: True if you want to use William Davidson version for Talmud refs
        :return: mesorat_hashas, mesorat_hashas_indexes
        """
        self.reset()
        start_time = pytime.time()

        if not index_list is None and not tc_list is None:
            raise Exception("Can only pass one. Choose either index_list or tc_list")
        if index_list is None and tc_list is None:
            raise Exception("Either index_list xor tc_list needs to be not None")

        if not index_list is None:
            unit_list = index_list
            using_indexes = True
        else:
            unit_list = tc_list
            using_indexes = False

        talmud_titles = library.get_indexes_in_category('Bavli')
        talmud_titles = talmud_titles[:talmud_titles.index('Horayot') + 1]
        text_index_map_data = [None for yo in xrange(len(unit_list))]
        for iunit, unit in enumerate(unit_list):
            if comment_index_list is not None and iunit in comment_index_list:
                # this unit is a comment. modify tokenizer so that it applies dh_extract_method first
                unit_tokenizer = lambda x: self.tokenizer(self.dh_extract_method(x))
            else:
                unit_tokenizer = self.tokenizer

            if self.verbose: print "Hashing {}".format(unit)
            if using_indexes:
                index = library.get_index(unit)
                if unit in talmud_titles and use_william:
                    vtitle = 'William Davidson Edition - Aramaic'
                else:
                    vtitle = None
                unit_il, unit_rl = index.text_index_map(unit_tokenizer, lang='he', vtitle=vtitle, strict=False)
                unit_list_temp = index.nodes.traverse_to_list(
                    lambda n, _: TextChunk(n.ref(), "he", vtitle=vtitle).ja().flatten_to_array() if not n.children else [])
                unit_wl = [w for seg in unit_list_temp for w in unit_tokenizer(seg)]
                unit_str = unit
            elif isinstance(unit, TextChunk):
                assert isinstance(unit, TextChunk)
                unit_il, unit_rl, total_len = unit.text_index_map(unit_tokenizer)
                unit_wl = [w for seg in unit.ja().flatten_to_array() for w in unit_tokenizer(seg)]
                unit_str = unit._oref.normal()
            else:
                # otherwise, format is a tuple with (str, textname)
                assert isinstance(unit, tuple)
                unit_il, unit_rl = [0], [Ref("Berakhot 58a")]  # random ref, doesn't actually matter
                unit_wl = unit_tokenizer(unit[0])
                unit_str = u"{}".format(unit[1])
            text_index_map_data[iunit] = (unit_wl, unit_il, unit_rl, unit_str)
            total_len = len(unit_wl)
            if not return_obj:
                pickle.dump((unit_il, unit_rl, total_len), open('{}text_index_map/{}.pkl'.format(output_root, unit), 'wb'))

            for i_word in xrange(len(unit_wl) - self.skip_gram_size):
                skip_gram_list = self.ght.get_skip_grams(unit_wl[i_word:i_word + self.skip_gram_size + 1])
                # ht = self.ht_list[self.w2i(skip_gram_list[0])] #should be the same for all four skip grams
                for skip_gram in skip_gram_list:
                    start_index = i_word
                    end_index = i_word + self.skip_gram_size

                    start_ref = unit_rl[bisect.bisect_right(unit_il, start_index) - 1]
                    end_ref = unit_rl[bisect.bisect_right(unit_il, end_index) - 1]
                    if start_ref == end_ref:
                        matched_ref = start_ref
                    else:
                        try:
                            matched_ref = start_ref.to(end_ref)
                        except AssertionError:
                            continue

                    self.ght[skip_gram] = Mesorah_Item(unit_str, iunit, (start_index, end_index), matched_ref, self.min_distance_between_matches)


        if self.parallelize:
            pool = multiprocessing.Pool()
            mesorat_hashas = reduce(lambda a,b: a + b, pool.map(self.get_matches_in_unit, enumerate(text_index_map_data)), [])
            pool.close()
        else:
            mesorat_hashas = []
            for input in enumerate(text_index_map_data):
                mesorat_hashas += self.get_matches_in_unit(input)


        # deal with one-off error at end of matches
        for mm in mesorat_hashas:
            mes_wl_a, mes_il_a, mes_rl_a, unit = text_index_map_data[mm.a.mesechta_index]
            mes_wl_b, mes_il_b, mes_rl_b, unit = text_index_map_data[mm.b.mesechta_index]

            new_loc = (mm.a.location[0], mm.a.location[1] - 1)
            new_start_ref = mes_rl_a[bisect.bisect_right(mes_il_a, new_loc[0]) - 1]

            new_end_ref = mes_rl_a[bisect.bisect_right(mes_il_a, new_loc[1]) - 1]
            mm.a = Mesorah_Item(mm.a.mesechta, mm.a.mesechta_index, new_loc, new_start_ref.to(new_end_ref),
                                 mm.a.min_distance_between_matches)
            new_loc = (mm.b.location[0], mm.b.location[1] - 1)
            new_start_ref = mes_rl_b[bisect.bisect_right(mes_il_b, new_loc[0]) - 1]
            new_end_ref = mes_rl_b[bisect.bisect_right(mes_il_b, new_loc[1]) - 1]
            mm.b = Mesorah_Item(mm.b.mesechta, mm.b.mesechta_index, new_loc, new_start_ref.to(new_end_ref),
                                 mm.b.min_distance_between_matches)

            if self.with_scoring:
                mm.score = self.calculate_score(mes_wl_a[mm.a.location[0]:mm.a.location[1]+1], mes_wl_b[mm.b.location[0]:mm.b.location[1]+1])



        if self.verbose: print "...{}s".format(round(pytime.time() - start_time, 2))
        if return_obj:
            return mesorat_hashas
        else:
            obj = [[mm.a.ref.normal(), mm.b.ref.normal()] for mm in mesorat_hashas]
            obj_with_indexes = \
                [{
                     "match": [mm.a.ref.normal(), mm.b.ref.normal()],
                     "match_index": [list(mm.a.location), list(mm.b.location)],
                     "score": mm.score
                 }
                 for mm in mesorat_hashas]
            objStr = json.dumps(obj, indent=4, ensure_ascii=False)
            with open('{}mesorat_hashas.json'.format(output_root), "wb") as f:
                f.write(objStr.encode('utf-8'))
            objStr = json.dumps(obj_with_indexes, indent=4, ensure_ascii=False)
            with open('{}mesorat_hashas_indexes.json'.format(output_root), "wb") as f:
                f.write(objStr.encode('utf-8'))

    def compare_new_skip_matches(self, old_partials, new_b_skips, current_a):
        """

        :param list[PartialMesorahMatch] old_partials:
        :param list[Mesorah_Item] new_a_skips:
        :return tuple[list[PartialMesorahMatch],list[PartialMesorahMatch]]
        """
        good = []
        bad = []

        # print u'OLD', u' - '.join([str(o) for o in old])
        # print u'NEW', u' - '.join([str(o) for o in new])
        up_to = 0
        for o in old_partials:
            found = False

            while up_to < len(new_b_skips):
                n = new_b_skips[up_to]
                dist = o.b_end - n
                mes_dist = o.b_end.mesechta_diff(n)
                if dist:
                    new_is_ahead = dist > 0
                else:
                    new_is_ahead = mes_dist < 0

                if new_is_ahead:
                    if dist and 0 < dist <= self.max_words_between + self.skip_gram_size:  # plus the length of a single skip-gram
                        # extend o until n
                        o.a_end = current_a
                        o.b_end = n
                        good += [o]
                        found = True
                    break
                else:
                    up_to += 1
            if not found:
                bad += [o]

        return good, bad




    def get_matches_in_unit(self, input):
        imes, (mes_wl, mes_il, mes_rl, mes) = input
        if self.verbose: print 'Searching {}'.format(mes)
        already_matched_dict = defaultdict(list)  # keys are word indexes that have matched. values are lists of Mesorah_Items that they matched to.
        matches = []
        for i_word in xrange(len(mes_wl) - self.skip_gram_size):
            # if i_word % 4000 == 0:
            #    print "{}\t{}%\tNum Found: {}".format(mes, round(100.0 * global_i_word / total_num_words, 2),len(mesorat_hashas))
            # global_i_word += 1
            start_ref = mes_rl[bisect.bisect_right(mes_il, i_word) - 1]
            end_ref = mes_rl[bisect.bisect_right(mes_il, i_word + self.skip_gram_size) - 1]

            if start_ref == end_ref:
                matched_ref = start_ref
            else:
                try:
                    matched_ref = start_ref.to(end_ref)
                except AssertionError:
                    continue

            a = Mesorah_Item(mes, imes, (i_word, i_word + self.skip_gram_size), matched_ref, self.min_distance_between_matches)
            skip_matches = self.ght[mes_wl[i_word:i_word + self.skip_gram_size + 1]]
            skip_matches.remove(a)  # remove the skip match that we're inspecting
            if not self.all_to_all:
                # filter anything that's in this TextChunk
                skip_matches = filter(lambda x: not imes == x.mesechta_index, skip_matches)
            skip_matches = filter(lambda x: not x.too_close(a), skip_matches)
            skip_matches = filter(lambda x: not self.ght.already_started_here((a, x)), skip_matches) # TODO use some closeness metric here also
            try:
                # avoid matching things close to what we already matched
                temp_already_matched_list = already_matched_dict[i_word]

                for temp_already_matched in temp_already_matched_list:
                    skip_matches = filter(lambda x: not x.too_close(temp_already_matched), skip_matches)
            except KeyError:
                pass
            skip_matches.sort(lambda x, y: x.compare(y))
            partial_match_list = [PartialMesorahMatch(a, a, b, b, self.min_words_in_match) for b in skip_matches]

            for j_word in xrange(i_word + 1, len(mes_wl) - self.skip_gram_size):
                if len(partial_match_list) == 0:
                    break
                temp_start_ref = mes_rl[bisect.bisect_right(mes_il, j_word) - 1]
                temp_end_ref = mes_rl[bisect.bisect_right(mes_il, j_word + self.skip_gram_size) - 1]
                if temp_start_ref == temp_end_ref:
                    temp_matched_ref = temp_start_ref
                else:
                    try:
                        temp_matched_ref = temp_start_ref.to(temp_end_ref)
                    except AssertionError:
                        continue

                temp_a = Mesorah_Item(mes, imes, (j_word, j_word + self.skip_gram_size), temp_matched_ref, self.min_distance_between_matches)
                temp_skip_matches = self.ght[mes_wl[j_word:j_word + self.skip_gram_size + 1]]
                temp_skip_matches.remove(temp_a)
                temp_skip_matches = filter(lambda x: not x.too_close(temp_a), temp_skip_matches)
                temp_skip_matches.sort(lambda x, y: x.compare(y))
                new_partial_match_list, dead_matches_possibly = self.compare_new_skip_matches(partial_match_list,
                                                                                         temp_skip_matches, temp_a)

                for dead in dead_matches_possibly:
                    distance_from_last_match = j_word - dead.last_a_word_matched()
                    if distance_from_last_match > self.max_words_between:
                        if len(dead) > self.min_words_in_match:
                            self.ght.put_already_started((dead.b_start, dead.a_start))
                            for i_matched_word in xrange(dead.a_start.location[0], dead.a_end.location[1] + 100):
                                already_matched_dict[i_matched_word] += [dead.b_start]
                            try:
                                matches += [dead.finalize()]
                            except AssertionError:
                                pass
                    else:
                        # still could be good
                        new_partial_match_list += [dead]

                partial_match_list = new_partial_match_list

            # account for matches at end of book
            for dead in partial_match_list:
                distance_from_last_match = (len(mes_wl)-self.skip_gram_size) - dead.last_a_word_matched()
                if distance_from_last_match > self.max_words_between:
                    if len(dead) > self.min_words_in_match:
                        self.ght.put_already_started((dead.b_start, dead.a_start))
                        try:
                            matches += [dead.finalize()]
                        except AssertionError:
                            pass

        return matches





def filter_pasuk_matches(category, mesorat_hashas_name):

    def bible_tokenizer(s):

        words = re.split(ur'\s+',re.sub(u'\u05be', u' ',s))
        words = filter(lambda w: not (u'[' in w and u']' in w) and w != u'',words) # strip out kri
        return words

    def talmud_tokenizer(s):
        for match in re.finditer(ur'\(.*?\)', s):
            if library.get_titles_in_string(match.group()) and len(match.group().split()) <= 5:
                s = s.replace(match.group(), u"")
        for phrase in stop_phrases:
            s = s.replace(phrase, u'')
        words = [w for w in re.split(ur'\s+',s) if w not in stop_words and w != u'']
        return words


    num_nonpasuk_match_words = 4
    mesorat_hashas = json.load(open(mesorat_hashas_name, 'rb'))

    mesechtot_names = get_texts_from_category(category)

    pickle_jar = {}
    for mes in mesechtot_names:
        pickle_jar[mes] = pickle.load(open('text_index_map/{}.pkl'.format(mes)))

    matches = {}
    for l in mesorat_hashas:
        tup_l = tuple(sorted(l['match']))
        if tup_l not in matches:
            try:
                matches[tup_l] = (Ref(tup_l[0]), Ref(tup_l[1]),l['match_index'])
            except InputError:
                pass
    #mesorat_hashas = [{'match':['Berakhot 4a:1-3','Berakhot 5a:1-3'],'match_index':[[1,2],[3,4]]}]


    bible_set_cache = {}
    text_array_cache = {}
    bible_array_cache = {}

    new_mesorat_hashas = []
    bad_mesorat_hashas = []

    len_m = len(matches.items())
    for ildict, (match_str_tup, (ref1, ref2, inds)) in enumerate(matches.items()):
        if ildict % 100 == 0:
            print "{}/{}--------------------------------------------".format(ildict,len_m)
        bad_match = False
        m = ref1.index.title
        ind_list = pickle_jar[m][0]
        for ir,rr in enumerate([ref1,ref2]):
            try:
                str_r = str(rr)
            except UnicodeEncodeError:
                continue

            if str_r not in text_array_cache:
                tt = talmud_tokenizer(rr.text("he").ja().flatten_to_string())
                text_array_cache[str_r] = tt
                biblset = rr.linkset().filter("Tanakh")
                bible_set_cache[str_r] = biblset
            else:
                tt = text_array_cache[str_r]
                biblset = bible_set_cache[str_r]



            s = ind_list[bisect.bisect_right(ind_list, inds[ir][0]) - 1]
            os = inds[ir][0] - s
            oe = inds[ir][1] - s
            match_len = oe-os + 1

            tb = {yo: 0 for yo in xrange(os,oe+1)}
            tt_slice = tt[os:oe+1]

            for bl in biblset:
                try:
                    if not Ref(bl.refs[1]).is_segment_level():
                        #print bl.refs[1]
                        continue
                    bt = bible_tokenizer(Ref(bl.refs[1]).text('he','Tanach with Text Only').as_string()) if bl.refs[1] not in bible_array_cache else bible_array_cache[bl.refs[1]]
                except InputError as e:
                    print e
                    print u"This ref is problematic {} on this Talmud ref {}".format(bl.refs[1],unicode(rr))
                    continue
                bs,be = get_maximum_subset_dh(tt_slice,bt,threshold=85)
                if bs != -1 and be != -1:
                    for ib in xrange(bs+os,be+os):
                        tb[ib] = 1


            #e = bisect.bisect_right(ind_list, inds[ir][1])-1


            num_pasuk  = sum(tb.values())
            if match_len - num_pasuk < num_nonpasuk_match_words:
                bad_match = True
                break

        if not bad_match:
            new_mesorat_hashas.append(list(match_str_tup))
        else:
            bad_mesorat_hashas.append(list(match_str_tup))

    print bad_mesorat_hashas
    print "Old: {} New: {} Difference: {}".format(len_m, len(new_mesorat_hashas),
                                                  len_m - len(new_mesorat_hashas))

    objStr = json.dumps(bad_mesorat_hashas, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_pasuk_filtered_bad.json', "w") as f:
        f.write(objStr.encode('utf-8'))
    objStr = json.dumps(new_mesorat_hashas, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_pasuk_filtered.json', "w") as f:
        f.write(objStr.encode('utf-8'))

def filter_close_matches(mesorat_hashas_name, max_cluster_dist=20, filter_only_talmud=False):

    mesorat_hashas = json.load(open(mesorat_hashas_name,'rb'))
    new_mesorat_hashas = set()

    seg_map = defaultdict(set)
    all_bad_links = set()
    for l in mesorat_hashas:

        if Ref(l[0]).order_id() < Ref(l[1]).order_id():
            r = Ref(l[0])
            ir = 0
        else:
            r = Ref(l[1])
            ir = 1
        other_r = Ref(l[int(ir == 0)])

        rray = r.range_list()
        for temp_r in rray:

            seg_map[temp_r.normal()].add((r,other_r))
        rray = other_r.range_list()
        for temp_r in rray:
            seg_map[temp_r.normal()].add((other_r, r))

    m = len(seg_map.items())
    for iseg, (strr, rset) in enumerate(seg_map.items()):
        rray = list(rset)
        if iseg % 100 == 0:
            print "{}/{}".format(iseg,m)
        n = len(rray)
        dist_mat = np.zeros((n,n))
        for i in range(n):
            for j in range(i+1,n):
                if i == j:
                    dist_mat[i,j] = 0
                else:
                    try:
                        dist_mat[i,j] = rray[i][1].distance(rray[j][1])
                    except Exception:
                        dist_mat[i,j] = -1

        clusters = []
        non_clustered = set()
        clustered_indexes = set()
        for i in range(n):
            for j in range(i+1,n):
                if dist_mat[i,j] <= max_cluster_dist and dist_mat[i,j] != -1 and (rray[i][1].type == 'Talmud' or not filter_only_talmud):
                    #we've found an element in a cluster!
                    #figure out if a cluster already exists containing one of these guys
                    found = False
                    for c in clusters:
                        if rray[i][1] in c or rray[j][1] in c:
                            c.add(rray[i])
                            c.add(rray[j])
                            clustered_indexes.add(i)
                            clustered_indexes.add(j)
                            found = True
                            break
                    if not found:
                        c = set()
                        c.add(rray[i])
                        c.add(rray[j])
                        clustered_indexes.add(i)
                        clustered_indexes.add(j)
                        clusters += [c]

        for ir, r in enumerate(rray):
            if ir not in clustered_indexes:
                non_clustered.add(r)


        #if len(clusters) + len(non_clustered) > 5:
        #    print list(non_clustered)[0]

        for c in clusters:
            #add one from each cluster
            other_r = None
            for temp_other_r in c:
                if other_r is None or temp_other_r[1].order_id() < other_r[1].order_id():
                    other_r = temp_other_r

            c.remove(other_r)
            for temp_other_r in c:
                temp_link = tuple(sorted((unicode(temp_other_r[0]), unicode(temp_other_r[1])), key=lambda r: Ref(r).order_id()))
                all_bad_links.add(temp_link)

            temp_link = tuple(sorted((unicode(other_r[0]),unicode(other_r[1])),key=lambda r: Ref(r).order_id()))

            # make sure temp_link isn't within max_dist of itself
            try:
                ref_obj1 = Ref(temp_link[0])
                ref_obj2 = Ref(temp_link[1])
                if (ref_obj1.type == 'Talmud' and ref_obj2.type == 'Talmud') or not filter_only_talmud:
                    temp_dist = ref_obj1.distance(ref_obj2,max_cluster_dist)
                else:
                    temp_dist = -1
            except Exception:
                temp_dist = -1
            if temp_dist == -1: # they're far away from each other
                new_mesorat_hashas.add(temp_link)

        for other_r in non_clustered:
            temp_link = tuple(sorted((unicode(other_r[0]),unicode(other_r[1])),key=lambda r: Ref(r).order_id()))

            # make sure temp_link isn't within max_dist of itself
            try:
                ref_obj1 = Ref(temp_link[0])
                ref_obj2 = Ref(temp_link[1])
                if (ref_obj1.type == 'Talmud' and ref_obj2.type == 'Talmud') or not filter_only_talmud:
                    temp_dist = ref_obj1.distance(ref_obj2,max_cluster_dist)
                else:
                    temp_dist = -1
            except Exception:
                temp_dist = -1
            if temp_dist == -1: # they're far away from each other
                new_mesorat_hashas.add(temp_link)


    filtered_mesorat_hashas = []
    for l in new_mesorat_hashas:
        if l not in all_bad_links:
            lray = list(l)
            filtered_mesorat_hashas += [lray]
        else:
            pass
            #print l



    print "Old: {} New: {} Difference: {}".format(len(mesorat_hashas),len(filtered_mesorat_hashas),len(mesorat_hashas)-len(filtered_mesorat_hashas))
    objStr = json.dumps(filtered_mesorat_hashas, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_clustered.json', "w") as f:
        f.write(objStr.encode('utf-8'))

def remove_mishnah_talmud_dups(mesorat_hashas_name):
    mesorat_hashas = json.load(open(mesorat_hashas_name, 'rb'))
    mishnah_set = LinkSet({'type': 'mishnah in talmud'}).array()
    mishnah_set = [(Ref(ms.refs[0]), Ref(ms.refs[1])) for ms in mishnah_set]

    new_mesorat_hashas = []
    for l in mesorat_hashas:
        is_bad_link = False
        try:
            lr = sorted([Ref(l[0]), Ref(l[1])], key=lambda x: x.order_id())
        except InputError:
            continue
        if lr[0] is None or lr[1] is None:
            continue
        if lr[0].type == 'Mishnah' and lr[1].type == 'Talmud':
            for mish_link in mishnah_set:
                if lr[0].overlaps(mish_link[0]) and lr[1].overlaps(mish_link[1]):
                    is_bad_link = True
                    break

        if not is_bad_link:
            new_mesorat_hashas += [l]

    print "Old: {} New: {} Difference: {}".format(len(mesorat_hashas), len(new_mesorat_hashas),
                                                  len(mesorat_hashas) - len(new_mesorat_hashas))
    objStr = json.dumps(new_mesorat_hashas, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_mishnah_filtered.json', "w") as f:
        f.write(objStr.encode('utf-8'))


def save_links_local(category, mesorat_hashas_name):
    mesorat_hashas = json.load(open(mesorat_hashas_name,'rb'))

    num_dups = 0
    for link in mesorat_hashas:
        for i,l in enumerate(link):
            link[i] = l.replace(u'<d>',u'')
        link_obj = {"auto": True, "refs": link, "anchorText": "", "generated_by": "mesorat_hashas.py {}".format(category),
                    "type": "Automatic Mesorat HaShas"}
        try:
            Link(link_obj).save()
        except DuplicateRecordError:
            num_dups += 1
            pass  # poopy

    print "num dups {}".format(num_dups)



def save_links_post_request(category):
    query = {"generated_by": "mesorat_hashas.py {}".format(category), "auto": True,
             "type": "Automatic Mesorat HaShas"}
    ls = LinkSet(query)
    links = [l.contents() for l in ls]
    i = 0
    while i < len(links):
        print "Posting [{}:{}]".format(i, i+4999)
        post_link(links[i:i+5000])
        i += 5000
        pytime.sleep(10)
class Mesorah_Match_Ref:

    def __init__(self,a,b, id=None):
        """

        :param str a:
        :param str b:
        """
        a = a.replace("<d>","")
        b = b.replace("<d>","")

        yo = sorted((Ref(a),Ref(b)), key=lambda r: r.order_id())
        self.a = yo[0]
        self.b = yo[1]
        self.id = id

    def __eq__(self, other):
        return self.a == other.a and self.b == other.b

    def __lt__(self, other):
        if self.a != other.a:
            return self.a.order_id() < other.a.order_id()
        else:
            return self.b.order_id() < other.b.order_id()

    def __gt__(self, other):
        if self.a != other.a:
            return self.a.order_id() > other.a.order_id()
        else:
            return self.b.order_id() > other.b.order_id()

    def normal(self, with_ids=False):
        if with_ids:
            return {"refs": self.normal(with_ids=False), "_id": self.id}
        else:
            return [self.a.normal(), self.b.normal()]

    def distance(self, other):
        return self.a.distance(other.a), self.b.distance(other.b)

def compare_mesorat_hashas(compare_a_name, compare_b_name):
    compare_a = json.load(open(compare_a_name,'rb'))
    compare_b = json.load(open(compare_b_name,'rb'))

    def mesorah_match_sort(m1,m2):
        if m1 < m2:
            return -1
        elif m1 > m2:
            return 1
        else:
            return 0

    compare_a_mmr = sorted([Mesorah_Match_Ref(m[0],m[1]) for m in compare_a], cmp=mesorah_match_sort)
    compare_b_mmr = sorted([Mesorah_Match_Ref(m[0],m[1]) for m in compare_b], cmp=mesorah_match_sort)

    inbnota = []
    j = 0
    for i,m in enumerate(compare_b_mmr):
        if i % 1000 == 0:
            print "({}/{})".format(i,len(compare_b))
        while compare_a_mmr[j] < m and j < len(compare_a_mmr) - 1:
            j += 1
        if compare_a_mmr[j] > m:
            inbnota += [m.normal()]

    print "Num in B not in A: {}".format(len(inbnota))
    objStr = json.dumps(inbnota, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_comparison.json', "w") as f:
        f.write(objStr.encode('utf-8'))

def filter_subset(mesorat_hashas_name):
    mesorat_hashas = json.load(open(mesorat_hashas_name, 'rb'))
    new_mesorat_hashas = []

    def mesorah_match_sort(m1,m2):
        if m1 < m2:
            return -1
        elif m1 > m2:
            return 1
        else:
            return 0
    mesorat_hashas_mmr = sorted([Mesorah_Match_Ref(m[0], m[1]) for m in mesorat_hashas], cmp=mesorah_match_sort)
    for immr, mmr in enumerate(mesorat_hashas_mmr):
        next_20 = mesorat_hashas_mmr[immr:immr+20]
        w = len(next_20)
        dist_array = np.zeros((w, w))
        for i in xrange(w):
            for j in xrange(i+1, w):
                dist_array[i,j] = next_20[i].distance(next_20[j])


    objStr = json.dumps(new_mesorat_hashas, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_mishnah_filtered.json', "w") as f:
        f.write(objStr.encode('utf-8'))


def sort_n_save(mesorat_hashas_name):
    mesorat_hashas = json.load(open(mesorat_hashas_name, 'rb'))
    def mesorah_match_sort(m1,m2):
        if m1 < m2:
            return -1
        elif m1 > m2:
            return 1
        else:
            return 0

    sorted_match_refs = sorted([Mesorah_Match_Ref(m[0],m[1]) for m in mesorat_hashas], cmp=mesorah_match_sort)
    sorted_mh = [[mmr.a.normal(), mmr.b.normal()] for mmr in sorted_match_refs]
    objStr = json.dumps(sorted_mh, indent=4, ensure_ascii=False)
    with open(mesorat_hashas_name, "wb") as f:
        f.write(objStr.encode('utf-8'))

def count_cats(mesorat_hashas_name):
    mesorat_hashas = json.load(open(mesorat_hashas_name, 'rb'))
    mishnah = get_texts_from_category('Mishnah')
    tosefta = get_texts_from_category('Tosefta')
    midrash = get_texts_from_category('Midrash')
    talmud = get_texts_from_category('Talmud')

    mish, tos, mid, tal = 0,0,0,0

    for link in mesorat_hashas:
        for l in link:
            temp_title = Ref(l).index.title
            if temp_title in mishnah:
                mish += 1
            elif temp_title in tosefta:
                tos += 1
            elif temp_title in midrash:
                mid += 1
            elif temp_title in talmud:
                tal += 1

    print 'Mish {}, Tos {}, Mid {}, Tal {}'.format(mish, tos, mid, tal)

def daf_with_most_links(mesorat_hashas_name):
    mesorat_hashas = json.load(open(mesorat_hashas_name, 'rb'))

    counter = defaultdict(int)
    for link in mesorat_hashas:
        for i, l in enumerate(link):
            r = Ref(l)
            if r.is_bavli() and not Ref(link[int(i == 0)]).is_bavli():
                rs = r.range_list()
                for temp_r in rs:
                    counter[temp_r] += 1

    max = 0
    max_ref = None
    yo = sorted(counter.items(), key=lambda x: x[1])
    print yo[-20:]

def get_diff_ids(sefaria_mesorat_hashas_name, mongo_export):
    mesorat_hashas = json.load(open(sefaria_mesorat_hashas_name,'rb'))
    export = json.load(open(mongo_export,'rb'))

    def mesorah_match_sort(m1,m2):
        if m1 < m2:
            return -1
        elif m1 > m2:
            return 1
        else:
            return 0

    mesorah_mmr = sorted([Mesorah_Match_Ref(m[0],m[1]) for m in mesorat_hashas], cmp=mesorah_match_sort)
    export_mmr = sorted([Mesorah_Match_Ref(m['refs'][0],m['refs'][1],m['_id']['$oid']) for m in export], cmp=mesorah_match_sort)

    inbnota = []
    j = 0
    for i,m in enumerate(export_mmr):
        if i % 1000 == 0:
            print "({}/{})".format(i,len(export_mmr))
        while mesorah_mmr[j] < m and j < len(mesorah_mmr) - 1:
            j += 1
        if mesorah_mmr[j] > m:
            inbnota += [m.normal(with_ids=True)]

    print "Num in B not in A: {}".format(len(inbnota))
    objStr = json.dumps(inbnota, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_comparison.json', "w") as f:
        f.write(objStr.encode('utf-8'))


def bulk_delete(id_file_name):
    import urllib2
    id_file = json.load(open(id_file_name,'rb'))

    for obj in id_file:
        id = obj['_id']
        url = 'http://www.sefaria.org/api/links/{}'.format(id)
        request = urllib2.Request(url)
        request.get_method = lambda: 'DELETE'
        try:
            response = urllib2.urlopen(request)
            print response.read()
        except urllib2.HTTPError:
            print "{} error".format(id)
