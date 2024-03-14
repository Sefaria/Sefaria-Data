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
from tqdm import tqdm
from functools import cmp_to_key
import django
from functools import reduce
django.setup()
import regex as re
import time as pytime
import numpy as np
import pickle as pickle
import bisect, json
from collections import defaultdict
import itertools
import bleach
from sefaria.model import *
from sefaria.system.exceptions import DuplicateRecordError
from sefaria.system.exceptions import InputError
from sefaria.system.exceptions import PartialRefInputError
from linking_utilities.dibur_hamatchil_matcher import get_maximum_subset_dh, get_maximum_dh, ComputeLevenshteinDistanceByWord

import logging
import multiprocessing


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
            cats = ['Bavli','Mishnah', 'Tosefta','Midrash Rabbah', 'Minor Tractates']
            text_names += ["Mekhilta d'Rabbi Yishmael", 'Seder Olam Rabbah','Sifra' ,'Mekhilta DeRabbi Shimon Bar Yochai','Sifrei Bamidbar','Megillat Taanit','Otzar Midrashim','Pirkei DeRabbi Eliezer','Pesikta D\'Rav Kahanna','Tanna Debei Eliyahu Rabbah','Tanna debei Eliyahu Zuta','Pesikta Rabbati']
            for c in cats:
                text_names += library.get_indexes_in_category(c)

        elif cat == "Debug":
            text_names += ["Avot D'Rabbi Natan","Berakhot", "Taanit"]

        else:
            text_names += []

    return text_names


stop_words = ["ר'",'רב','רבי','בן','בר','בריה','אמר','כאמר','וכאמר','דאמר','ודאמר','כדאמר','וכדאמר','ואמר','כרב',
              'ורב','כדרב','דרב','ודרב','וכדרב','כרבי','ורבי','כדרבי','דרבי','ודרבי','וכדרבי',"כר'","ור'","כדר'",
              "דר'","ודר'","וכדר'",'א״ר','וא״ר','כא״ר','דא״ר','דאמרי','משמיה','קאמר','קאמרי','לרב','לרבי',
              "לר'",'ברב','ברבי',"בר'",'הא','בהא','הך','בהך','ליה','צריכי','צריכא','וצריכי','וצריכא','הלל','שמאי', "וגו'",'וגו׳']
stop_phrases = ['למה הדבר דומה','כלל ופרט וכלל','אלא כעין הפרט','מה הפרט','כלל ופרט','אין בכלל','אלא מה שבפרט', 'אשר קדשנו במצותיו וצונו']


def tokenize_words(base_str):
    base_str = base_str.strip()
    base_str = bleach.clean(base_str, tags=[], strip=True)
    for match in re.finditer(r'\(.*?\)', base_str):
        if library.get_titles_in_string(match.group()) and len(match.group().split()) <= 5:
            base_str = base_str.replace(match.group(), "")
            # base_str = re.sub(ur"(?:\(.*?\)|<.*?>)", u"", base_str)
    base_str = re.sub(r'־',' ',base_str)
    base_str = re.sub(r'[A-Za-z]','',base_str)
    for phrase in stop_phrases:
        base_str = base_str.replace(phrase,'')
    word_list = re.split(r"\s+", base_str)
    word_list = [w for w in word_list if len(w.strip()) > 0 and w not in stop_words]
    return word_list


def tokinzer_removed_indices(str, segNum):
    #TODO this function is not completely parallel to `tokenize_words()`. notably, it doesn't account for adding words by splitting on maqaf.
    #TODO i needed this function just for talmud which doesn't have maqaf so i didn't worry about it
    filter_reg_html = "<.*?>"
    filter_reg_paren = "[:\(\[]*\(.*?\)[:\)\]]*"
    filter_reg_eng = "[A-Za-z]+"
    filter_reg_stop_phrases = "|".join(stop_phrases)
    filter_reg_stop_words = "|".join(stop_words)
    regs = [filter_reg_html, filter_reg_paren, filter_reg_eng, filter_reg_stop_phrases,filter_reg_stop_words]
    match_spans = []
    match_text = []
    match_word_counts = []
    prev_removed_citations = []
    for ireg, reg in enumerate(regs):
        if ireg == 3:
            full_reg = "(?<=\s)[משדהוכלב]?(?:{}):?(?=\s|$)|^[משדהוכלב]?(?:{}):?(?=\s|$)".format(reg, reg)
        else:
            full_reg = "(?<=\s)(?:{})(?=\s|$)|^(?:{})(?=\s|$)".format(reg, reg)
        for m in re.finditer(full_reg, str):
            if ireg == 0:
                cleaned_match = bleach.clean(m.group(), tags=[], strip=True)
                len_removed = len(m.group().split()) - len(cleaned_match.split())
                removes_words = len_removed > 0
                if not removes_words:
                    # make sure HTML doesn't prevent other matches
                    str = str.replace(m.group(), cleaned_match)
            elif ireg == 1:
                removes_words = library.get_titles_in_string(m.group()) and len(m.group().split()) <= 5
                prev_removed_citations += [m.group()]
                whats_left = m.group()
                for prev_removed in prev_removed_citations:
                    actually_removed = re.findall(r"\(.*?\)", prev_removed)[0]
                    whats_left = whats_left.replace(actually_removed, "")
                len_removed = len(m.group().split()) - len(whats_left.strip().split())
            elif ireg == 3:
                whats_left = m.group()
                for phrase in stop_phrases:
                    whats_left = whats_left.replace(phrase, "")
                len_removed = len(m.group().split()) - len(whats_left.split())
                removes_words = len_removed > 0
            else:
                removes_words = True
                len_removed = len(re.split(r'\s+', m.group()))

            if removes_words:
                match_text.append(m.group())
                match_spans.append(m.span(0))
                match_word_counts.append(len_removed)

    sort_unzip = list(zip(*sorted(zip(match_spans, match_text, match_word_counts), key=lambda x: x[0][0])))
    match_spans, match_text, match_word_counts = ([], [], []) if len(sort_unzip) == 0 else sort_unzip
    word_iter = re.finditer(r"\s+", str)
    word_spans = [m.start(0) for m in word_iter]
    word_removed_indices = [bisect.bisect_right(word_spans, span[0]) for span in match_spans]
    word_removed_indices = reduce(lambda a, b: a + [b - len(a)], word_removed_indices, [])

    #add multiples for multiple words removed in a row
    real_word_removed_indices = []
    for iwri,wri in enumerate(word_removed_indices):
        num_skipped_words_passed = sum(match_word_counts[:iwri]) - iwri
        real_word_removed_indices += ([wri - num_skipped_words_passed]*match_word_counts[iwri])

    if len(re.split(r"\s+", str.strip())) - len(real_word_removed_indices) != len(tokenize_words(str)):
        print("Badness {}".format(segNum))

    return real_word_removed_indices

class Gemara_Hashtable:

    def __init__(self, skip_gram_size, lemmatizer=None, lemma2index=None):
        """
        :param lemmatizer: function that takes a word and returns the lemma of the word. Default is `self.get_two_letter_word` which is useful for Hebrew
        :param lemma2index: function that takes a string of concatenated lemmas (from self.lemmatizer) and produces a key to store those lemmas in the hashtable
        """
        self.lemmatizer = self.get_two_letter_word if lemmatizer is None else lemmatizer
        self.lemma2index = self.w2i if lemma2index is None else lemma2index
        self.letter_freqs_list = ['י', 'ו', 'א', 'מ', 'ה', 'ל', 'ר', 'נ', 'ב', 'ש', 'ת', 'ד', 'כ', 'ע', 'ח', 'ק',
                         'פ', 'ס', 'ט', 'ז', 'ג', 'צ']

        self.letter_freqs_dict = {
            k: v for v, k in enumerate(self.letter_freqs_list)
        }

        self._two_letter_cache = {}

        self.sofit_map = {
            'ך': 'כ',
            'ם': 'מ',
            'ן': 'נ',
            'ף': 'פ',
            'ץ': 'צ',
        }
        self.full_heb_map = self.sofit_map
        for l in self.letter_freqs_dict:
            self.full_heb_map[l] = l

        self.letters = ['א', 'ב', 'ג', 'ד', 'ה',
                        'ו', 'ז', 'ח', 'ט', 'י',
                        'כ', 'ל', 'מ', 'נ', 'ס',
                        'ע', 'פ', 'צ', 'ק', 'ר',
                        'ש', 'ת', chr(ord('ת')+1)]

        self.letters_dict = {
            k: v for v, k in enumerate(self.letters)
        }

        self._hash_table = defaultdict(set)
        self._already_matched_start_items = defaultdict(bool)
        self.loaded = False
        self.skip_gram_size = skip_gram_size

    def __setitem__(self,skip_gram,value):
        """

        :param skip_gram: string of 8 consecutive characters
        :param Mesorah_Item value:
        """
        index = self.lemma2index(skip_gram)
        temp_set = self._hash_table[index]
        temp_set.add(value)


    def __getitem__(self,five_gram):

        skip_gram_list = self.get_skip_grams(five_gram)
        results = set()
        for skip_gram in skip_gram_list:
            index = self.lemma2index(skip_gram)
            results |= self._hash_table[index]

        return results

    def get_small_skip_gram_matches(self, small_five_gram):
        """

        :param small_five_gram: a list of words which is self.skip_gram_size as opposed to self.skip_gram_size + 1. used for looking up last skip gram in book
        :return:
        """
        lemmas = ''.join([self.lemmatizer(w) for w in small_five_gram])
        index = self.lemma2index(lemmas)
        return self._hash_table[index]


    def get_skip_grams(self,five_gram, is_end=False):
        """

        :param five_gram: list of 5 consecutive words
        :param is_end: bool, True if five_gram is last five_gram in unit
        :return: list of the 4 skip grams (in 2 letter form)
        """

        lemmas = [self.lemmatizer(w) for w in five_gram]
        skip_gram_list = [''.join(temp_skip) for temp_skip in itertools.combinations(lemmas, self.skip_gram_size)]
        if not is_end:
            del skip_gram_list[-1] # last one is the one that skips the first element
        return skip_gram_list

    def w2i_reducer(self, a, b):
        return a + (23**b[0] * self.letters_dict[b[1]])

    def w2i(self,w):
        """

        :param l: hebrew letters
        :return: corresponding integer
        """
        return reduce(self.w2i_reducer, enumerate(w), 0)

    def sofit_swap(self,C):
        return self.sofit_map[C] if C in self.sofit_map else C

    def get_two_letter_word(self,word):
        cache = self._two_letter_cache.get(word, None)
        if cache:
            return cache
        temp_word = ''.join([self.full_heb_map.get(C, '') for C in word])

        if len(temp_word) < 2:
            if len(temp_word) == 1:
                two_letter_word = '{}{}'.format(temp_word,self.letters[-1])
            else:  # efes
                two_letter_word = '{}{}'.format(self.letters[-1],self.letters[-1])
        else:
            indices = [self.letter_freqs_dict[c] for c in temp_word]
            current_max = max(indices)
            first_max, i_first_max = self.letter_freqs_list[current_max], indices.index(current_max)
            del indices[i_first_max]
            current_max = max(indices)
            sec_max, i_sec_max = self.letter_freqs_list[current_max],indices.index(current_max)

            if i_first_max <= i_sec_max:
                two_letter_word = '{}{}'.format(first_max,sec_max)
            else:
                two_letter_word = '{}{}'.format(sec_max,first_max)
        self._two_letter_cache[word] = two_letter_word
        return two_letter_word


    def save(self):
        # see here for why we're using -1 protocol
        # https://stackoverflow.com/questions/2204155/why-am-i-getting-an-error-about-my-class-defining-slots-when-trying-to-pickl
        pickle.dump(self._hash_table, open('gemara_chamutz.pkl','wb'), -1)

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
            if self.ref.is_bavli() and other.ref.is_bavli():
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

    def get_text(self, pm):
        """
        return text associated with locations of mesorah_item
        """
        words = pm.word_list_map[self.mesechta]
        return " ".join(words[self.location[0]:self.location[1]+1])

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

    def __init__(self, a_start, a_end, b_start, b_end, min_words_in_match, both_sides_have_min_words):
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
        self.both_sides_have_min_words = both_sides_have_min_words

    def has_min_words(self):
        pooling_func = min if self.both_sides_have_min_words else max
        return pooling_func(self.a_end.location[1] - self.a_start.location[0], self.b_end.location[1] - self.b_start.location[0]) >= self.min_words_in_match

    def last_a_word_matched(self):
        return self.a_end.location[1]

    def finalize(self, score=0):
        """
        Convert this partial match into a regular Mesorah_Match
        :return:
        """
        return Mesorah_Match(self.a_start + self.a_end, self.b_start + self.b_end, self.min_words_in_match, score)


def default_calculate_score(words_a, words_b):
    if len(words_a) > 500:
        return 0
    best_match = get_maximum_dh(words_a, words_b, min_dh_len=len(words_b)-1, max_dh_len=len(words_b))
    length_factor = len(words_b)
    if best_match:
        return -best_match.score/length_factor
    else:
        return -ComputeLevenshteinDistanceByWord(" ".join(words_a), " ".join(words_b))/length_factor


class ParallelMatcher:

    def __init__(self, tokenizer, dh_extract_method=None, ngram_size=5, max_words_between=4, min_words_in_match=9,
                 min_distance_between_matches=100, all_to_all=True, parallelize=False, verbose=True,
                 calculate_score=None, only_match_first=False, lemmatizer=None, lemma2index=None, ignore_subset_results=True, both_sides_have_min_words=False):
        """
        Minimal usage would be:
        >>> p = ParallelMatcher(lambda s: s.split())
        >>> p.match()

        :param tokenizer: f(str)->[].   Returns list of words.  E.g. a function to remove HTML and split on space.
        :param f(str) -> str dh_extract_method: takes the full text of `comment` and returns only the dibur hamatchil. `self.tokenizer` will be applied to it afterward. this will only be used if `comment_index_list` in `match()` is not None
        :param ngram_size: int, basic unit of matching. 1 word will be skipped in each ngram of size `ngram_size`
        :param max_words_between: max words between consecutive ngrams
        :param min_words_in_match: min words for a match to be considered valid. By default, only one side needs to have min_words. However, if both_sides_have_min_words is True, then both need (see both_sides_have_min_words param)
        :param min_distance_between_matches: min distance between matches. If matches are closer than this, the first one will be chosen. NOTE: only applies to matches that are within the same book to avoid matching within the same discussion
        :param bool all_to_all: if True, make between everything either in index_list or ref_list. False means results get filtered to only match inter-ref matches
        :param bool parallelize: Do you want this to run in parallel? WARNING: this uses up way more RAM. and this is already pretty RAM-hungry TODO: interesting question on sharing ram: https://stackoverflow.com/questions/14124588/shared-memory-in-multiprocessing
        :param f(str, str) -> float: function that takes two strings as parameters, representing both sides of a match. returns float representing score. This score does not affect the algorithm at all. it's purpose is to be used for post-processing on the results
        :param bool only_match_first: True if you want to return matches to the first item in the list
        :param f(str) -> str lemmatizer: function that takes a word and returns the lemma of the word. Default is `self.get_two_letter_word` which is useful for Hebrew
        :param f(str) -> hashable lemma2index: function that takes a string of concatenated lemmas (from self.lemmatizer) and produces a key to store those lemmas in the hashtable
        :param bool ignore_subset_results: if True, filters out subset results before returning
        :param bool both_sides_have_min_words: if True, both a and b sides of match need min_words_in_match. If False, only one side needs min_words_in_match.
        """
        self.tokenizer = tokenizer
        self.dh_extract_method = dh_extract_method
        self.ngram_size = ngram_size
        self.skip_gram_size = self.ngram_size - 1
        self.ght = Gemara_Hashtable(self.skip_gram_size, lemmatizer, lemma2index)
        self.max_words_between = max_words_between
        self.min_words_in_match = min_words_in_match
        self.min_distance_between_matches = min_distance_between_matches
        self.all_to_all = all_to_all
        self.parallelize = parallelize
        self.verbose = verbose
        self.with_scoring = False
        self.calculate_score = None
        self.only_match_first = only_match_first
        self.word_list_map = {}
        self.with_scoring = True  # hard-coding to True now that calculate_score has a default
        self.ignore_subset_results = ignore_subset_results
        self.both_sides_have_min_words = both_sides_have_min_words
        if calculate_score:
            self.calculate_score = calculate_score
        else:
            self.calculate_score = default_calculate_score



    def reset(self):
        self.ght = Gemara_Hashtable(self.skip_gram_size, self.ght.lemmatizer, self.ght.lemma2index)

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

    def match(self, tref_list, lang="he", comment_index_list=None, use_william=False, output_root="",
              return_obj=False, vtitle_list=None):
        """

        :param list[str] tref_list: list of trefs names to match against.
            Each item in the list can be either:
                - str: will be interpretted as a tref. str have multiple trefs in it separated by '|'. This is useful when you want to match against a whole category of texts (e.g. Tanakh)
                - tuple: where the tuples look like (content, unique_id) where `content` is the text to match and `unique_id` is a unique id.
        :param list[int] comment_index_list: list of indexes which correspond to either `index_list` or `tc_list` (whichever is not None). each index in this list indicates that the corresponding element should be treated as a `comment` meaning `self.dh_extract_method()` will be used on it.
        :param list[tuple] vtitle_list: optional list of version title where each item is a string that represents a version title. You can put None for any version you want to be the default version. If passed, should be same length as tref_list. version title will only be used when passing trefs and not when passing tuples of (content, unique_id).
        :return: mesorat_hashas, mesorat_hashas_indexes
        """
        self.reset()
        start_time = pytime.time()
        vtitle_list = vtitle_list or [None]*len(tref_list)
        assert len(vtitle_list) == len(tref_list), f"If passing vtitle_list, vtitle_list must be the same length as tref_list. len(vtitle_list) == {len(vtitle_list)}, len(tref_list) == {len(tref_list)}"
        text_index_map_data = [None for yo in range(len(tref_list))]
        for iunit, (tref, vtitle) in enumerate(zip(tref_list, vtitle_list)):
            if comment_index_list is not None and iunit in comment_index_list:
                # this unit is a comment. modify tokenizer so that it applies dh_extract_method first
                unit_tokenizer = lambda x: self.tokenizer(self.dh_extract_method(x))
            else:
                unit_tokenizer = self.tokenizer

            if self.verbose: print("Hashing {}".format(tref[1] if isinstance(tref, tuple) else tref))
            if isinstance(tref, tuple):
                # otherwise, format is a tuple with (str, textname)
                unit_il, unit_rl = [0], [Ref("Berakhot 58a")]  # random ref, doesn't actually matter
                unit_wl = unit_tokenizer(tref[0])
                unit_str = "{}".format(tref[1])
            else:
                unit_il, unit_wl, unit_rl, last_total_len = [], [], [], 0
                for temp_tref in tref.split("|"):
                    oref = Ref(temp_tref)
                    try:
                        # jagged array, can be instantiated as TextChunk
                        text_chunk = oref.text(lang, vtitle, lang)
                        temp_unit_il, temp_unit_rl, total_len, unit_flattened = text_chunk.text_index_map(unit_tokenizer, ret_ja=True)
                        temp_unit_wl = [w for seg in unit_flattened for w in unit_tokenizer(seg)]
                    except InputError:
                        # schema node
                        schema_node = oref.index_node
                        assert schema_node.ref() == oref, "Schema Node {} isn't equal to original ref {}".format(schema_node.ref().normal(), oref.normal())
                        temp_unit_il, temp_unit_rl = schema_node.text_index_map(unit_tokenizer, lang=lang, vtitle=vtitle, strict=False)
                        unit_list_temp = schema_node.traverse_to_list(
                            lambda n, _: TextChunk(n.ref(), lang, vtitle=vtitle).ja().flatten_to_array() if not n.children else [])
                        temp_unit_wl = [w for seg in unit_list_temp for w in unit_tokenizer(seg)]
                    if len(unit_il) > 0:
                        temp_unit_il = [x + last_total_len for x in temp_unit_il]
                    unit_il += temp_unit_il
                    unit_rl += temp_unit_rl
                    last_total_len += len(temp_unit_wl)
                    unit_wl += temp_unit_wl
                unit_str = tref
            self.word_list_map[unit_str] = unit_wl
            text_index_map_data[iunit] = (unit_wl, unit_il, unit_rl, unit_str)
            total_len = len(unit_wl)
            if not return_obj:
                with open('{}text_index_map/{}.pkl'.format(output_root, tref), 'wb') as my_pickle:
                    pickle.dump((unit_il, unit_rl, total_len), my_pickle, -1)

            itt = range(len(unit_wl) - self.skip_gram_size)
            if self.verbose and False:
                itt = tqdm(itt, leave=False, smoothing=0)
            for i_word in itt:
                is_unit_end = i_word == (len(unit_wl) - self.skip_gram_size - 1)
                skip_gram_list = self.ght.get_skip_grams(unit_wl[i_word:i_word + self.skip_gram_size + 1], is_end=is_unit_end)
                for iskip_gram, skip_gram in enumerate(skip_gram_list):
                    # if you're at the last skip gram in the unit, you skipped the first word of the skip gram
                    start_index = i_word + 1 if is_unit_end and iskip_gram == len(skip_gram_list) - 1 else i_word
                    end_index = i_word + self.skip_gram_size + 1 if is_unit_end and iskip_gram == len(skip_gram_list) - 1 else i_word + self.skip_gram_size

                    start_ref = unit_rl[bisect.bisect_right(unit_il, start_index) - 1]
                    end_ref = unit_rl[bisect.bisect_right(unit_il, end_index) - 1]
                    if start_ref == end_ref:
                        matched_ref = start_ref
                    else:
                        try:
                            matched_ref = start_ref.to(end_ref)
                        except (AssertionError, InputError):
                            continue

                    self.ght[skip_gram] = Mesorah_Item(unit_str, iunit, (start_index, end_index), matched_ref, self.min_distance_between_matches)


        if self.parallelize:
            pool = multiprocessing.Pool()
            mesorat_hashas = reduce(lambda a,b: a + b, pool.map(self.get_matches_in_unit, enumerate(text_index_map_data)), [])
            pool.close()
        else:
            mesorat_hashas = []

            for input in enumerate(text_index_map_data):
                if input[0] == len(text_index_map_data) - 1 and not self.all_to_all:
                    break  # dont need to check last item if not all to all
                if input[0] == 1 and self.only_match_first:
                    break  # dont need to check past the first item if `only_match_first`
                mesorat_hashas += self.get_matches_in_unit(input)


        # deal with one-off error at end of matches
        itt = mesorat_hashas
        if self.verbose:
            itt = tqdm(itt, leave=False, smoothing=0)
        for mm in itt:
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
        if self.ignore_subset_results:
            mesorat_hashas = self._filter_subset_results(mesorat_hashas)
        if self.verbose: print("...{}s".format(round(pytime.time() - start_time, 2)))
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

    @staticmethod
    def _filter_subset_results(matches):
        matches_by_books_and_end_loc = defaultdict(list)
        for m in matches:
            key = (m.a.mesechta, m.b.mesechta, m.a.location[1]) if m.a.mesechta < m.b.mesechta else (m.b.mesechta, m.a.mesechta, m.a.location[1])
            matches_by_books_and_end_loc[key] += [m]
        new_matches = []
        for m_list in matches_by_books_and_end_loc.values():
            m_list.sort(key=lambda x: (x.score or 0.0001) / ((x.a.location[1] - x.a.location[0]) + (x.b.location[1] - x.b.location[0])))
            new_matches += [m_list[-1]]
        return new_matches

    def compare_new_skip_matches(self, old_partials, new_b_skips, current_a):
        """

        :param list[PartialMesorahMatch] old_partials:
        :param list[Mesorah_Item] new_b_skips:
        :return tuple[list[PartialMesorahMatch],list[PartialMesorahMatch]]
        """
        good = []
        bad = []
        for o in old_partials:
            found = False
            for n in new_b_skips:
                if o.b_end.mesechta_index != n.mesechta_index:
                    continue
                diff = o.b_end - n
                if diff is not None and 0 < diff <= self.max_words_between + self.skip_gram_size:  # plus the length of a single skip-gram
                    # extend o until n
                    o.a_end = current_a
                    o.b_end = n
                    good += [o]
                    found = True
                    break
            if not found:
                bad += [o]

        return good, bad




    def get_matches_in_unit(self, input):
        imes, (mes_wl, mes_il, mes_rl, mes) = input
        if self.verbose: print('Searching {}'.format(mes))
        already_matched_dict = defaultdict(list)  # keys are word indexes that have matched. values are lists of Mesorah_Items that they matched to.
        matches = []
        itt = range(len(mes_wl) - self.skip_gram_size)
        if self.verbose:
            itt = tqdm(itt, leave=False, smoothing=0)
        for i_word in itt:
            start_ref = mes_rl[bisect.bisect_right(mes_il, i_word) - 1]
            end_ref = mes_rl[bisect.bisect_right(mes_il, i_word + self.skip_gram_size) - 1]

            if start_ref == end_ref:
                matched_ref = start_ref
            else:
                try:
                    matched_ref = start_ref.to(end_ref)
                except (AssertionError, InputError):
                    continue

            a = Mesorah_Item(mes, imes, (i_word, i_word + self.skip_gram_size), matched_ref, self.min_distance_between_matches)
            skip_matches = self.ght[mes_wl[i_word:i_word + self.skip_gram_size + 1]]
            skip_matches.remove(a)  # remove the skip match that we're inspecting
            if not self.all_to_all:
                # filter anything that's in this TextChunk
                skip_matches = [x for x in skip_matches if imes != x.mesechta_index]
            skip_matches = [x for x in skip_matches if not x.too_close(a)]
            skip_matches = [x for x in skip_matches if not self.ght.already_started_here((a, x))] # TODO use some closeness metric here also
            try:
                # avoid matching things close to what we already matched
                temp_already_matched_list = already_matched_dict[i_word]

                for temp_already_matched in temp_already_matched_list:
                    # only check for too_close if x is in same book as a. otherwise, too_close metric is arbitrarily filtering skip_matches that are close to previous matches in x, but maybe not be in the same book as a
                    skip_matches = [x for x in skip_matches if (x.mesechta_index != imes or not x.too_close(temp_already_matched))]
            except KeyError:
                pass
            skip_matches.sort(key=cmp_to_key(lambda x, y: x.compare(y)))
            partial_match_list = [PartialMesorahMatch(a, a, b, b, self.min_words_in_match, self.both_sides_have_min_words) for b in skip_matches]

            for j_word in range(i_word + 1, len(mes_wl) - self.skip_gram_size + 1):  # +1 at end of range to get last incomplete skip-gram
                if len(partial_match_list) == 0:
                    break
                temp_start_ref = mes_rl[bisect.bisect_right(mes_il, j_word) - 1]
                temp_end_ref = mes_rl[bisect.bisect_right(mes_il, j_word + self.skip_gram_size) - 1]
                if temp_start_ref == temp_end_ref:
                    temp_matched_ref = temp_start_ref
                else:
                    try:
                        temp_matched_ref = temp_start_ref.to(temp_end_ref)
                    except (AssertionError, InputError):
                        continue

                temp_a = Mesorah_Item(mes, imes, (j_word, j_word + self.skip_gram_size), temp_matched_ref, self.min_distance_between_matches)
                if j_word + self.skip_gram_size == len(mes_wl):
                    temp_skip_matches = self.ght.get_small_skip_gram_matches(mes_wl[j_word:j_word + self.skip_gram_size])
                else:
                    temp_skip_matches = self.ght[mes_wl[j_word:j_word + self.skip_gram_size + 1]]
                    temp_skip_matches.remove(temp_a)  # temp_a wont be in temp_skip_matches if the if path is true
                temp_skip_matches = [x for x in temp_skip_matches if not x.too_close(temp_a)]
                temp_skip_matches.sort(key=cmp_to_key(lambda x, y: x.compare(y)))
                new_partial_match_list, dead_matches_possibly = self.compare_new_skip_matches(partial_match_list,
                                                                                         temp_skip_matches, temp_a)

                for dead in dead_matches_possibly:
                    distance_from_last_match = j_word - dead.last_a_word_matched()
                    if distance_from_last_match > self.max_words_between:
                        if dead.has_min_words():
                            self.ght.put_already_started((dead.b_start, dead.a_start))
                            for i_matched_word in range(dead.a_start.location[0], dead.a_end.location[1] + self.min_distance_between_matches):
                                already_matched_dict[i_matched_word] += [dead.b_start]
                            try:
                                matches += [dead.finalize()]
                            except (AssertionError, InputError):
                                pass
                    else:
                        # still could be good
                        new_partial_match_list += [dead]

                partial_match_list = new_partial_match_list

            # account for matches at end of book
            for dead in partial_match_list:
                distance_from_last_match = (len(mes_wl)-self.skip_gram_size) - dead.last_a_word_matched()
                if dead.has_min_words():
                    self.ght.put_already_started((dead.b_start, dead.a_start))
                    try:
                        matches += [dead.finalize()]
                    except (AssertionError, InputError):
                        pass

        return matches



def get_normalizer():
    from sefaria.helper.normalization import NormalizerComposer
    return NormalizerComposer(['unidecode', 'br-tag', 'itag', 'html', 'maqaf', 'cantillation', 'double-space'])

def filter_pasuk_matches(category, mesorat_hashas_name):
    normalizer = get_normalizer()
    def bible_tokenizer(s):

        words = re.split(r'\s+',re.sub('\u05be', ' ',s))
        words = [w for w in words if not ('[' in w and ']' in w) and w != ''] # strip out kri
        return words

    def talmud_tokenizer(s):
        for match in re.finditer(r'\(.*?\)', s):
            if library.get_titles_in_string(match.group()) and len(match.group().split()) <= 5:
                s = s.replace(match.group(), "")
        for phrase in stop_phrases:
            s = s.replace(phrase, '')
        words = [w for w in re.split(r'\s+',s) if w not in stop_words and w != '']
        return words


    num_nonpasuk_match_words = 4
    mesorat_hashas = json.load(open(mesorat_hashas_name, 'rb'))

    # mesechtot_names = get_texts_from_category(category)
    mesechtot_names = ['Mekhilta DeRabbi Yishmael, Tractate Pischa', 'Pesachim 2a-20a']

    pickle_jar = {}
    for mes in mesechtot_names:
        # pickle_jar[mes] = pickle.load(open('text_index_map/{}.pkl'.format(mes)))
        pickle_jar[mes] = pickle.load(open('text_index_map/{}.pkl'.format(mes), 'rb'))

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

    len_m = len(list(matches.items()))
    for ildict, (match_str_tup, (ref1, ref2, inds)) in enumerate(matches.items()):
        if ildict % 100 == 0:
            print("{}/{}--------------------------------------------".format(ildict,len_m))
        bad_match = False
        # m = ref1.index.title
        m = str(ref1.top_section_ref().index_node)
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

            tb = {yo: 0 for yo in range(os,oe+1)}
            tt_slice = tt[os:oe+1]

            for bl in biblset:
                bible_ref = bl.refs[1] if rr == bl.refs[0] else bl.refs[0]
                try:
                    if not Ref(bible_ref).is_segment_level():
                        #print bl.refs[1]
                        continue
                    bt = bible_tokenizer(Ref(bible_ref).text('he','Tanach with Text Only').as_string()) if bible_ref not in bible_array_cache else bible_array_cache[bible_ref]
                except InputError as e:
                    print(e)
                    print("This ref is problematic {} on this Talmud ref {}".format(bible_ref,str(rr)))
                    continue
                bs,be = get_maximum_subset_dh(tt_slice,bt,threshold=85)
                if bs != -1 and be != -1:
                    for ib in range(bs+os,be+os):
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

    print(bad_mesorat_hashas)
    print("Old: {} New: {} Difference: {}".format(len_m, len(new_mesorat_hashas),
                                                  len_m - len(new_mesorat_hashas)))

    objStr = json.dumps(bad_mesorat_hashas, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_pasuk_filtered_bad.json', "w") as f:
        # f.write(objStr.encode('utf-8'))
        f.write(objStr.encode('utf-8').decode('utf-8'))
    objStr = json.dumps(new_mesorat_hashas, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_pasuk_filtered.json', "w") as f:
        # f.write(objStr.encode('utf-8'))
        f.write(objStr.encode('utf-8').decode('utf-8'))

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

    m = len(list(seg_map.items()))
    for iseg, (strr, rset) in enumerate(seg_map.items()):
        rray = list(rset)
        if iseg % 100 == 0:
            print("{}/{}".format(iseg,m))
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
                if dist_mat[i,j] <= max_cluster_dist and dist_mat[i,j] != -1 and (rray[i][1].primary_category == 'Talmud' or not filter_only_talmud):
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
                temp_link = tuple(sorted((str(temp_other_r[0]), str(temp_other_r[1])), key=lambda r: Ref(r).order_id()))
                all_bad_links.add(temp_link)

            temp_link = tuple(sorted((str(other_r[0]),str(other_r[1])),key=lambda r: Ref(r).order_id()))

            # make sure temp_link isn't within max_dist of itself
            try:
                ref_obj1 = Ref(temp_link[0])
                ref_obj2 = Ref(temp_link[1])
                if (ref_obj1.primary_category == 'Talmud' and ref_obj2.primary_category == 'Talmud') or not filter_only_talmud:
                    temp_dist = ref_obj1.distance(ref_obj2,max_cluster_dist)
                else:
                    temp_dist = -1
            except Exception:
                temp_dist = -1
            if temp_dist == -1: # they're far away from each other
                new_mesorat_hashas.add(temp_link)

        for other_r in non_clustered:
            temp_link = tuple(sorted((str(other_r[0]),str(other_r[1])),key=lambda r: Ref(r).order_id()))

            # make sure temp_link isn't within max_dist of itself
            try:
                ref_obj1 = Ref(temp_link[0])
                ref_obj2 = Ref(temp_link[1])
                if (ref_obj1.primary_category == 'Talmud' and ref_obj2.primary_category == 'Talmud') or not filter_only_talmud:
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



    print("Old: {} New: {} Difference: {}".format(len(mesorat_hashas),len(filtered_mesorat_hashas),len(mesorat_hashas)-len(filtered_mesorat_hashas)))
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
        if lr[0].primary_category == 'Mishnah' and lr[1].primary_category == 'Talmud':
            for mish_link in mishnah_set:
                if lr[0].overlaps(mish_link[0]) and lr[1].overlaps(mish_link[1]):
                    is_bad_link = True
                    break

        if not is_bad_link:
            new_mesorat_hashas += [l]

    print("Old: {} New: {} Difference: {}".format(len(mesorat_hashas), len(new_mesorat_hashas),
                                                  len(mesorat_hashas) - len(new_mesorat_hashas)))
    objStr = json.dumps(new_mesorat_hashas, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_mishnah_filtered.json', "w") as f:
        f.write(objStr.encode('utf-8'))


def save_links_local(category, mesorat_hashas_name):
    mesorat_hashas = json.load(open(mesorat_hashas_name,'rb'))

    num_dups = 0
    for link in mesorat_hashas:
        for i,l in enumerate(link):
            link[i] = l.replace('<d>','')
        link_obj = {"auto": True, "refs": link, "anchorText": "", "generated_by": "mesorat_hashas.py {}".format(category),
                    "type": "mesorat hashas"}
        try:
            Link(link_obj).save()
        except DuplicateRecordError:
            num_dups += 1
            pass  # poopy

    print("num dups {}".format(num_dups))


def save_links_post_request(category):
    from sources.functions import post_link

    query = {"generated_by": "mesorat_hashas.py {}".format(category), "auto": True,
             "type": "mesorat hashas"}
    ls = LinkSet(query)
    links = [l.contents() for l in ls]
    i = 0
    while i < len(links):
        print("Posting [{}:{}]".format(i, i+499))
        print(post_link(links[i:i+500]))
        i += 500


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
            print("({}/{})".format(i,len(compare_b)))
        while compare_a_mmr[j] < m and j < len(compare_a_mmr) - 1:
            j += 1
        if compare_a_mmr[j] > m:
            inbnota += [m.normal()]

    print("Num in B not in A: {}".format(len(inbnota)))
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
        for i in range(w):
            for j in range(i+1, w):
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

    print('Mish {}, Tos {}, Mid {}, Tal {}'.format(mish, tos, mid, tal))

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
    yo = sorted(list(counter.items()), key=lambda x: x[1])
    print(yo[-20:])

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
            print("({}/{})".format(i,len(export_mmr)))
        while mesorah_mmr[j] < m and j < len(mesorah_mmr) - 1:
            j += 1
        if mesorah_mmr[j] > m:
            inbnota += [m.normal(with_ids=True)]

    print("Num in B not in A: {}".format(len(inbnota)))
    objStr = json.dumps(inbnota, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_comparison.json', "w") as f:
        f.write(objStr.encode('utf-8'))


def bulk_delete(id_file_name):
    import urllib.request, urllib.error, urllib.parse
    id_file = json.load(open(id_file_name,'rb'))

    for obj in id_file:
        id = obj['_id']
        url = 'http://www.sefaria.org/api/links/{}'.format(id)
        request = urllib.request.Request(url)
        request.get_method = lambda: 'DELETE'
        try:
            response = urllib.request.urlopen(request)
            print(response.read())
        except urllib.error.HTTPError:
            print("{} error".format(id))


def filter_index_file(filtered_mesorat_hashas, index_mesorat_hashas):
    fmh = json.load(open(filtered_mesorat_hashas, 'rb'))
    imh = json.load(open(index_mesorat_hashas, 'rb'))
    link_set = set()
    for link in fmh:
        link_set.add((link[0], link[1]))
    new_index_mesorat_hashas = [x for x in imh if (x["match"][0], x["match"][1]) in link_set]
    print("{}".format(len(fmh)))
    print("Old {} New {}".format(len(imh), len(new_index_mesorat_hashas)))
    objStr = json.dumps(new_index_mesorat_hashas, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_indexed_mishnah_filtered_2018_06_14.json', "wb") as f:
        f.write(objStr.encode('utf-8'))


def test_tokenize_words_remove_indexes(index_mesorat_hashas):
    aramaic_books = ["Pesikta D'Rav Kahanna", "Bereishit Rabbah", "Vayikra Rabbah", "Eichah Rabbah"]
    imh = json.load(open(index_mesorat_hashas, 'rb'))
    talmud_indexes = [library.get_index("Megillah")] #library.get_indexes_in_category("Bavli", full_records=True)
    talmud_titles = ["Megillah"] #library.get_indexes_in_category("Bavli")
    willy_titles = talmud_titles[:talmud_titles.index('Megillah') + 1]
    talmud_words_dict = {}
    for iindex, index in enumerate(talmud_indexes):
        print("Tokenizing {} ({}/{})".format(index.title, iindex, len(talmud_indexes)))
        vtitle = 'William Davidson Edition - Aramaic' if index.title in willy_titles else None
        seg_list = index.nodes.traverse_to_list(
                lambda n, _: TextChunk(n.ref(), "he", vtitle=vtitle).ja().flatten_to_array())
        seg_list_tokenized = [tokenize_words(seg) for seg in seg_list]
        seg_list_cumul_len = reduce(lambda a, b: a + [len(b) + a[-1]], seg_list_tokenized, [0])
        word_list = [w for seg in seg_list_tokenized for w in seg]
        word_list_space = [w for seg in seg_list for w in re.split(r"\s+", seg.strip())]
        index_list, ref_list = index.text_index_map(vtitle=vtitle)
        word_list_removed = [w + seg_list_cumul_len[iseg] for iseg, seg in enumerate(seg_list) for w in tokinzer_removed_indices(seg, iseg)]
        talmud_words_dict[index.title] = {
            "orig": word_list,
            "space": word_list_space,
            "removed": word_list_removed,
            "index_list": index_list,
            "ref_list": [r.normal() for r in ref_list],
            "total_len": len(word_list_space),
            "linked": set()
        }
    for ilink, link in enumerate(imh):
        if ilink % 1000 == 0:
            print("{}/{}".format(ilink, len(imh)))
        try:
            ref_link = [Ref(r) for r in link["match"]]
        except PartialRefInputError as e:
            print(link["match"])
        except InputError as e:
            print(link["match"])
        for il, l in enumerate(ref_link):
            other_l = ref_link[int(il == 0)]
            if l.primary_category == "Talmud" and l.index.title == "Megillah" and other_l.primary_category != "Talmud" and other_l.index.title not in aramaic_books:
                title = l.index.title
                orig_start = link["match_index"][il][0]
                orig_end = link["match_index"][il][1]
                orig_str = talmud_words_dict[title]["orig"][orig_start:orig_end+1]
                space_start = bisect.bisect_right(talmud_words_dict[title]["removed"], orig_start)
                space_end = bisect.bisect_right(talmud_words_dict[title]["removed"], orig_end)
                space_str = talmud_words_dict[title]["space"][orig_start + space_start : orig_end + space_end + 1]

                for i in range(orig_start + space_start, orig_end + space_end+1):
                    if i == 400425:
                        print("oh no")
                    talmud_words_dict[title]["linked"].add(i)
                if len(space_str) == 0 and len(orig_str) != 0:
                    "One is len 0"
                    continue
                if len(space_str) == 0:
                    continue
                first_space = tokenize_words(space_str[0])
                last_space = tokenize_words(space_str[-1])
                if len(first_space) == 0 or len(last_space) == 0:
                    print("Zero length word")
                    continue
                if orig_str[0] != first_space[0]:
                    print("Not the same First")
                if orig_str[-1] != last_space[0]:
                    print("Not the same last")
    mishnah_map = LinkSet({"type": "mishnah in talmud"})
    for link in mishnah_map:
        link_refs = [Ref(r) for r in link.refs]
        for r in link_refs:
            if r.primary_category == "Talmud" and r.index.title == "Megillah":
                start_index = talmud_words_dict[r.index.title]["index_list"][
                    talmud_words_dict[r.index.title]["ref_list"].index(r.starting_ref().normal())]
                try:
                    end_index = talmud_words_dict[r.index.title]["index_list"][
                        talmud_words_dict[r.index.title]["ref_list"].index(r.ending_ref().normal())+1] - 1
                except IndexError as e:
                    end_index = talmud_words_dict[r.index.title]["total_len"] - 1
                for i in range(start_index, end_index + 1):
                    if i == 400425:

                        print('oh no mishnah')
                    talmud_words_dict[r.index.title]["linked"].add(i)

    num_linked = 0
    num_words = 0
    talmud_range_dict = {}
    for index in talmud_indexes:
        linked = talmud_words_dict[index.title]["linked"]
        linked_list = sorted(list(linked))

        num_linked += len(linked)
        num_words += talmud_words_dict[index.title]["total_len"]
        ranges = []
        begin_range = None
        prev_link_index = None
        talmud_range_dict[index.title] = {
            "linked_words": len(linked),
            "num_words": talmud_words_dict[index.title]["total_len"]
        }
        for link_index in linked_list:
            if begin_range is None:
                begin_range = link_index
            elif link_index - prev_link_index > 1:
                end_range = prev_link_index
                ranges += [[begin_range, end_range]]
                begin_range = link_index
            prev_link_index = link_index
        talmud_range_dict[index.title]["ranges"] = ranges
    objStr = json.dumps(talmud_range_dict, indent=4, ensure_ascii=False)
    print("{}/{} {}".format(num_linked, num_words, 1.0*num_linked/num_words))
    with open('talmud_hebrew_ranges.json', "wb") as fout:
        fout.write(objStr.encode('utf-8'))
