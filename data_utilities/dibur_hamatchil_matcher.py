# -*- coding: utf-8 -*-

import math as mathy
import bisect
import csv
import codecs
import itertools
import numpy

import logging
logger = logging.getLogger(__name__)

try:
    import re2 as re
    re.set_fallback_notification(re.FALLBACK_WARNING)
except ImportError:
    logging.warning("Failed to load 're2'.  Falling back to 're' for regular expression parsing. See https://github.com/blockspeiser/Sefaria-Project/wiki/Regular-Expression-Engines")
    import re

import regex

from sefaria.model import *
from sefaria.utils.hebrew import gematria
#from research.talmud_pos_research.language_classifier.language_tools import weighted_levenshtein, weighted_levenshtein_cost
from data_utilities.util import WeightedLevenshtein
from num2words import num2words


fdebug = False
# constants for generating distance score. a 0 means a perfect match, although it will never be 0, due to the smoothing.
normalizingFactor = 100
smoothingFactor = 1
fullWordValue = 3
abbreviationPenalty = 1
ImaginaryContenderPerWord = 22

fSerializeData = False

ourmod = 134217728
pregeneratedKWordValues = []
pregeneratedKMultiwordValues = []
NumPregeneratedValues = 20
kForWordHash = 41
kForMultiWordHash = 39

weighted_levenshtein = WeightedLevenshtein()

lettersInOrderOfFrequency = [ u'ו', u'י', u'א', u'מ', u'ה', u'ל', u'ר', u'נ', u'ב', u'ש', u'ת', u'ד', u'כ', u'ע', u'ח', u'ק', u'פ', u'ס', u'ז', u'ט', u'ג', u'צ' ]

class MatchMatrix(object):
    def __init__(self, daf_hashes, comment_hashes, jump_coordinates, word_threshold, comment_word_skip_threshold = 1, base_word_skip_threshold = 2, overall_word_skip_threshold = 2):
        """
        :param daf_hashes: List of hashes
        :param rashi_hashes: List of hashes
        :param jump_coordinates: List of tuples. each tuple is ((row_start,col_start),(row_end,col_end)) for possible jumps
        :param word_threshold:
        :param comment_word_skip_threshold:
        :param base_word_skip_threshold:
        :param overall_word_skip_threshold: min = max(comment_word_skip_threshold, base_word_skip_threshold) max = comment_word_skip_threshold + base_word_skip_threshold
        :return:
        """

        C = numpy.array(comment_hashes)
        D = numpy.array(daf_hashes)
        self.matrix = (C[:, None] == D).astype(int)
        self.jump_coordinates = jump_coordinates
        for ijump, jump_coord in enumerate(jump_coordinates):
            self.matrix[jump_coord[0]] = ijump + 2

        self.comment_len = self.matrix.shape[0]
        self.daf_len = self.matrix.shape[1]

        self.comment_word_skip_threshold = comment_word_skip_threshold
        self.base_word_skip_threshold = base_word_skip_threshold
        self.overall_word_skip_threshold = overall_word_skip_threshold
        self.mismatch_threshold = mathy.ceil(self.comment_len * word_threshold)

    def _explore_path(self, current_position, daf_start_index,
                      comment_indexes_skipped, daf_indexes_skipped, jump_indexes, mismatches = 0,
                      comment_threshold_hit=False, daf_threshold_hit=False, mismatch_threshold_hit=False):  #, _comment_words_skipped=0, _base_words_skipped=0, _mismatches=0):
        """
        Invoked from both matched and non-matched positions
        Check self, explore next positions, and recourse.

        :param current_position: (comment word, daf word) tuple
        :param daf_start_index:  word index of starting word
        :param comment_indexes_skipped: list of comment words skipped
        :param daf_indexes_skipped: list of daf words skipped
        :return: list of dicts of the form:
                {
                    daf_start_index: #,
                    comment_indexes_skipped: [],
                    daf_indexes_skipped: [],
                    mismatches: #
                 }
        """
        is_a_match = self.matrix[current_position] == 1
        is_jump_start = self.matrix[current_position] > 1
        is_jump_end = len(jump_indexes) > 0 and self.jump_coordinates[jump_indexes[-1]][1] == current_position
        next_base_index = current_position[1] + 1
        next_comment_index = current_position[0] + 1

        # (not is_jump_start or is_jump_end) is meant to capture the edge case when there's a one word abbrev at the end of the dh
        if (not is_jump_start or is_jump_end) and next_comment_index == self.comment_len:
            # We've hit the last comment word
            if is_a_match or is_jump_end:
                return [{
                    "daf_start_index": daf_start_index,
                    "comment_indexes_skipped": comment_indexes_skipped,
                    "daf_indexes_skipped": daf_indexes_skipped,
                    "jump_indexes": jump_indexes,
                    "mismatches": mismatches
                }]
            if not daf_threshold_hit:
                # See if we can match the last word with the base skips left
                possible_base_skips = min(self.overall_word_skip_threshold - (len(daf_indexes_skipped) + len(comment_indexes_skipped)),
                                          self.base_word_skip_threshold,
                                          self.daf_len - next_base_index)
                for skip in range(1, possible_base_skips + 1):
                    if self.matrix[(current_position[0], current_position[1] + skip)] == 1:
                        return [{
                            "daf_start_index": daf_start_index,
                            "comment_indexes_skipped": comment_indexes_skipped,
                            "daf_indexes_skipped": daf_indexes_skipped + range(current_position[1], current_position[1] + skip),
                            "jump_indexes": jump_indexes,
                            "mismatches": mismatches
                        }]
            if not comment_threshold_hit:
                # or allow a comment word miss
                return [{
                    "daf_start_index": daf_start_index,
                    "comment_indexes_skipped": comment_indexes_skipped + [current_position[0]],
                    "daf_indexes_skipped": daf_indexes_skipped,
                    "jump_indexes": jump_indexes,
                    "mismatches": mismatches
                }]
            if not mismatch_threshold_hit:
                # Or allow a mismatch
                return [{
                    "daf_start_index": daf_start_index,
                    "comment_indexes_skipped": comment_indexes_skipped,
                    "daf_indexes_skipped": daf_indexes_skipped,
                    "jump_indexes": jump_indexes,
                    "mismatches": mismatches
                }]
            return [None]
        elif not is_jump_start and next_base_index == self.daf_len:
            # We've hit the end of the daf, but not the end of the comment
            possible_comment_skips = min(self.overall_word_skip_threshold - (len(comment_indexes_skipped) + len(daf_indexes_skipped)),
                                         self.comment_word_skip_threshold - len(comment_indexes_skipped))

            if is_a_match or is_jump_end:
                if current_position[0] + possible_comment_skips + 1 >= self.comment_len:
                    return [{
                        "daf_start_index": daf_start_index,
                        "comment_indexes_skipped": comment_indexes_skipped + range(current_position[0] + 1, self.comment_len),
                        "daf_indexes_skipped": daf_indexes_skipped,
                        "jump_indexes": jump_indexes,
                        "mismatches": mismatches
                    }]
                else:
                    return [None]
            elif not mismatch_threshold_hit:
                if current_position[0] + possible_comment_skips + 1 >= self.comment_len:
                    return [{
                        "daf_start_index": daf_start_index,
                        "comment_indexes_skipped": comment_indexes_skipped + range(current_position[0] + 1, self.comment_len),
                        "daf_indexes_skipped": daf_indexes_skipped,
                        "jump_indexes": jump_indexes,
                        "mismatches": mismatches
                    }]
                else:
                    return [None]
            else:
                return [None]

        # Greedily match next in-sequence match
        if is_a_match or is_jump_end:
            return self._explore_path((next_comment_index, next_base_index),
                                      daf_start_index,
                                      comment_indexes_skipped,
                                      daf_indexes_skipped,
                                      jump_indexes,
                                      mismatches,
                                      comment_threshold_hit,
                                      daf_threshold_hit,
                                      mismatch_threshold_hit)

        # Next in-sequence word doesn't match.  Explore other possibilities
        results = []

        if is_jump_start:
            jump_index = self.matrix[current_position] - 2
            jump_end = self.jump_coordinates[jump_index][1]  # current pos holds info on the jump number
            new_jump_indexes = jump_indexes + [jump_index]
            results += self._explore_path(jump_end,
                                      daf_start_index,
                                      comment_indexes_skipped,
                                      daf_indexes_skipped,
                                      new_jump_indexes,
                                      mismatches,
                                      comment_threshold_hit,
                                      daf_threshold_hit,
                                      mismatch_threshold_hit)

        if not comment_threshold_hit and next_comment_index < self.comment_len:
            new_comment_indexes_skipped = comment_indexes_skipped + [current_position[0]]
            results += self._explore_path((next_comment_index, current_position[1]),
                                          daf_start_index,
                                          new_comment_indexes_skipped,
                                          daf_indexes_skipped,
                                          jump_indexes,
                                          mismatches,
                                          len(new_comment_indexes_skipped) >= self.comment_word_skip_threshold
                                              or len(new_comment_indexes_skipped) + len(daf_indexes_skipped) >= self.overall_word_skip_threshold,
                                          len(daf_indexes_skipped) >= self.base_word_skip_threshold
                                              or len(new_comment_indexes_skipped) + len(daf_indexes_skipped) >= self.overall_word_skip_threshold,
                                          mismatch_threshold_hit)
        if not daf_threshold_hit and next_base_index < self.daf_len:
            new_daf_indexes_skipped = daf_indexes_skipped + [current_position[1]]
            results += self._explore_path((current_position[0], next_base_index),
                                          daf_start_index,
                                          comment_indexes_skipped,
                                          new_daf_indexes_skipped,
                                          jump_indexes,
                                          mismatches,
                                          len(comment_indexes_skipped) >= self.comment_word_skip_threshold
                                              or len(comment_indexes_skipped) + len(new_daf_indexes_skipped) >= self.overall_word_skip_threshold,
                                          len(new_daf_indexes_skipped) >= self.base_word_skip_threshold
                                              or len(comment_indexes_skipped) + len(new_daf_indexes_skipped) >= self.overall_word_skip_threshold,
                                          mismatch_threshold_hit)
        if not mismatch_threshold_hit and next_comment_index < self.comment_len and next_base_index < self.daf_len:
            results += self._explore_path((next_comment_index, next_base_index),
                                          daf_start_index,
                                          comment_indexes_skipped,
                                          daf_indexes_skipped,
                                          jump_indexes,
                                          mismatches + 1,
                                          comment_threshold_hit,
                                          daf_threshold_hit,
                                          mismatches + 1 >= self.mismatch_threshold)

        return results

    def find_paths(self):

        init_base_threshold_hit = 0 == self.base_word_skip_threshold
        init_mismatch_threshold_hit = 0 == self.mismatch_threshold
        paths = []
        # for each potential starting index of the comment, allowing for skips
        for c_skips in range(self.comment_word_skip_threshold + 1):

            init_comment_threshold_hit = c_skips == self.comment_word_skip_threshold
            # find potential start words in the daf, and explore
            last_possible_daf_word_index = self.daf_len - (self.comment_len - (self.comment_word_skip_threshold - c_skips) - len(self.jump_coordinates))
            for word_index in self.matrix[c_skips, 0:last_possible_daf_word_index + 1].nonzero()[0]:
                word_paths = self._explore_path((c_skips, word_index), word_index, range(c_skips), [], [],
                                                comment_threshold_hit=init_comment_threshold_hit,
                                                daf_threshold_hit=init_base_threshold_hit,
                                                mismatch_threshold_hit=init_mismatch_threshold_hit)
                # Return only the best match for each starting word
                # todo: check the mismatch divisor
                sorted_paths = sorted(filter(None, word_paths), key=lambda p: len(p["comment_indexes_skipped"]) + len(p["daf_indexes_skipped"]) + (p["mismatches"] / 3))
                if len(sorted_paths):
                    paths += sorted_paths[:1]

        return paths

    def print_path(self, path):
        """
        :param path: one element of array of output of find_paths()
        :return: None
        """
        start_col = path['daf_start_index']
        comment_indexes_skipped = path['comment_indexes_skipped']
        daf_indexes_skipped = path['daf_indexes_skipped']

        last_matched = (-1,start_col-1)
        jump_mode = False
        jump_is_horiz = False
        for row in xrange(self.comment_len):
            row_str = ''
            char_found = False
            for col in xrange(self.daf_len):
                if not jump_mode:
                    jump_index = self.matrix[row,col] - 2 if self.matrix[row,col] > 1 else None
                if not jump_index is None and not jump_mode:
                    jump_mode = True
                    jump_is_horiz = self.jump_coordinates[jump_index][0][0] == self.jump_coordinates[jump_index][1][0]
                    col_char = '@'
                elif jump_mode:
                    if self.jump_coordinates[jump_index][1] == (row + int(not jump_is_horiz),col + int(jump_is_horiz)):
                        jump_mode = False
                        col_char = '@'
                        last_matched = (row, col)
                    elif jump_is_horiz and self.jump_coordinates[jump_index][0][0] == row:
                        col_char = '-'
                    elif not jump_is_horiz and self.jump_coordinates[jump_index][0][1] == col: #vert
                        col_char = '|'
                    else:
                        col_char = '.'
                else:
                    if not char_found and row in comment_indexes_skipped and col == last_matched[1]:
                        col_char = 'V'
                        last_matched = (row, col)
                        char_found = True
                    elif col in daf_indexes_skipped and col - 1 == last_matched[1] and row == last_matched[0]:
                        col_char = '>'
                        last_matched = (row, col)
                        char_found = True
                    elif not char_found and row == last_matched[0] + 1 and col == last_matched[1] + 1:
                        col_char = 'X' if self.matrix[row,col] == 1 else 'O'
                        last_matched = (row, col)
                        char_found = True
                    else:
                        col_char = '.'


                row_str += col_char
            print row_str

class TextMatch:
    def __init__(self):
        self.textToMatch = ""
        self.textMatched = ""
        self.startWord = 0
        self.endWord = 0
        self.score = 0
        self.skippedRashiWords = []
        self.skippedDafWords = [] # list of words skipped in match
        self.abbrev_matches = [] #list of tuples of range of abbreviation found, if any
        self.match_type = '' # 'exact', 'skip', 'abbrev'

    def __str__(self):
        return u'{} ==> {} ({},{}) Score: {}'.format(self.textToMatch, self.textMatched, self.startWord, self.endWord, self.score)

class AbbrevMatch:
    def __init__(self,abbrev,expanded,rashiRange,gemaraRange,contextBefore,contextAfter,isNumber):
        self.abbrev = abbrev
        self.expanded = expanded
        self.rashiRange = rashiRange
        self.gemaraRange = gemaraRange
        self.contextBefore = contextBefore
        self.contextAfter = contextAfter
        self.isNumber = isNumber
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            #TODO i feel like gemaraRange should be compared here also, but apparently that wasn't right
            return self.abbrev == other.abbrev and self.expanded == other.expanded and self.rashiRange == other.rashiRange
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return u"Abbrev: {}, Expanded: {}, RashiRange: {}, GemaraRange: {} Is Number: {}".format(self.abbrev,u' '.join(self.expanded),self.rashiRange,self.gemaraRange,self.isNumber)

# should be private?
class GemaraDaf:
    def __init__(self,word_list,comments,dh_extraction_method=lambda x: x,prev_matched_results=None,dh_split=None):
        self.allWords = word_list
        self.matched_words = [False for _ in xrange(len(self.allWords))]
        self.gemaraText = " ".join(self.allWords)
        self.wordhashes = CalculateHashes(self.allWords)
        self.allRashi = []
        self.did_dh_split = not dh_split is None
        self.dh_map = []
        # dh split
        dh_list = []
        if dh_split:
            new_comments = []
            for i,comment in enumerate(comments):
                dh = dh_extraction_method(comment)
                sub_dhs = dh_split(dh)
                if sub_dhs:
                    new_comments += [comment for _ in sub_dhs]
                    dh_list += sub_dhs
                    self.dh_map += [dh for _ in sub_dhs]
                else:
                    new_comments.append(comment)
                    dh_list.append(dh)
                    self.dh_map.append(None)
            comments = new_comments
        else:
            dh_list = [dh_extraction_method(comm) for comm in comments]

        count = 0
        for i,comm in enumerate(comments):
            prev_result = prev_matched_results[i] if prev_matched_results else (-1,-1)
            self.allRashi.append(RashiUnit(dh_list[i],comm,count,prev_result))
            count+=1


    def mergeRashis(self):
        if not self.did_dh_split: return
        new_all_rashi = []
        i = 0
        while i < len(self.allRashi):
            if self.dh_map[i]:
                old_dh = self.dh_map[i]
                sub_rashis = []
                start_i = i
                while i < len(self.allRashi) and self.dh_map[i] == old_dh:
                    if self.allRashi[i].startWord != -1:
                        sub_rashis.append(self.allRashi[i])
                    i += 1
                if len(sub_rashis) == 0:
                    new_all_rashi.append(self.allRashi[start_i]) #just append the first one
                else:
                    new_start_word = len(self.gemaraText)
                    new_end_word = -1
                    new_matching_text = u'חדש:'
                    for sub_ru in sub_rashis:
                        #print u"Old {}".format(sub_ru)
                        new_matching_text += u" " + sub_ru.matchedGemaraText
                        if sub_ru.startWord < new_start_word:
                            new_start_word = sub_ru.startWord
                        if sub_ru.endWord > new_end_word:
                            new_end_word = sub_ru.endWord

                    new_ru = RashiUnit(old_dh,sub_rashis[0].fullText,sub_rashis[0].place)
                    new_ru.startWord = new_start_word
                    new_ru.endWord = new_end_word
                    new_ru.matchedGemaraText = new_matching_text
                    #print u"New {}".format(new_ru)

                    new_all_rashi.append(new_ru)
            else:
                new_all_rashi.append(self.allRashi[i])
                i += 1
        self.allRashi = new_all_rashi



class RashiUnit:
    def __init__(self,startingText,fullText,place,prev_result=(-1,-1)):
        self.place = place
        self.disambiguationScore = 0
        self.rashimatches = []  # list of TextMatch
        self.skippedRashiWords = []
        self.skippedDafWords = []
        self.abbrev_matches = []
        self.startingText = startingText
        self.match_type = ''

        normalizedCV = re.sub(ur" ו" + u"?" + u"כו" + u"'?" + u"$", u"", self.startingText).strip()
        temp = re.sub(ur"^(גמ|גמרא|מתני|מתניתין|משנה)'? ", u"", normalizedCV)
        if len(temp) > 4:
            normalizedCV = temp

        # if it starts with הג, then take just 3 words afterwords
        if self.startingText.startswith(u"ה\"ג") or self.startingText.startswith(u"ה״ג"):
            try:
                normalizedCV = re.search(ur"[^ ]+ ([^ ]+( [^ ]+)?( [^ ]+)?)", normalizedCV).group(1)
            except AttributeError:
                print u"Tripped up on " + u"ה״ג"
                normalizedCV = normalizedCV


        # // now remove all non-letters, allowing just quotes
        normalizedCV = re.sub(ur"[^א-ת \"״]", u"", normalizedCV).strip()

        self.startingTextNormalized = normalizedCV
        self.fullText = fullText
        self.startWord = prev_result[0]
        self.endWord = prev_result[1]
        self.cvWordcount = len(re.split(r"\s+",normalizedCV))
        self.matchedGemaraText = ""

        self.words = re.split(ur"\s+", self.startingTextNormalized)
        self.cvhashes = CalculateHashes(self.words)

    def __str__(self):
        return u"\n\t{}\n\t{}\n[{}-{}] place: {} type: {} skipped gemara: {} skipped rashi: {}\nabbrevs:\n\t\t{}".format(
            self.startingText, self.matchedGemaraText, self.startWord, self.endWord, self.place, self.match_type,
            u', '.join(self.skippedDafWords), u', '.join(self.skippedRashiWords), u'\n\t\t'.join([am.__str__() for am in self.abbrev_matches]))


def get_maximum_subset_dh(base_text, comment_text, threshold=90):
    """
    Useful when you have 2 segments, neither of which is a subset of the other. Eg a pasuk quoted in Talmud
    :param base_text: list of strings
    :param comment_text: list of strings
    :param threshold: a weighted levenshtein score above this is considered negative
    :return: range relative to base_text of best match from comment
    """
    wl_tuple_list = [weighted_levenshtein.calculate_best(tword,comment_text,normalize=True) for tword in base_text]
    dist_list = [temp_tup[1]-threshold for temp_tup in wl_tuple_list]
    start,end,cost = max_sesquence_sum(dist_list)
    return start,end


def get_maximum_dh(base_text, comment, tokenizer=lambda x: re.split(ur'\s+',x), max_dh_len=None, word_threshold=0.27, char_threshold=0.2):
    if type(base_text) == TextChunk:
        base_text_str = base_text.ja().flatten_to_string()
    else:
        base_text_str = base_text

    if type(comment) == TextChunk:
        comment_str = comment.ja().flatten_to_string()
    else:
        comment_str = comment

    base_word_list = tokenizer(base_text_str)
    comment_word_list = tokenizer(comment_str)

    if max_dh_len is None:
        max_dh_len = len(comment_word_list)


    InitializeHashTables()
    curDaf = GemaraDaf(base_word_list, [])

    best_dh_start = 0
    best_dh_end = 0
    for i in xrange(max_dh_len):
        curRashi = RashiUnit(u' '.join(comment_word_list[best_dh_start:best_dh_start+i+1]),comment,0)
        matches = GetAllMatches(curDaf,curRashi,0,len(base_word_list)-1,word_threshold,char_threshold)
        if len(matches) > 0:
            best_dh_end = best_dh_start + i
        else:
            break

    return comment_word_list[best_dh_start:best_dh_end+1]

def match_ref(base_text, comments, base_tokenizer, prev_matched_results=None, dh_extract_method=lambda x: x,verbose=False, word_threshold=0.27,char_threshold=0.2,
              with_abbrev_matches=False,with_num_abbrevs=True,boundaryFlexibility=0,dh_split=None, rashi_filter=None, strict_boundaries=False, place_all=False,
              create_ranges=False):
    """
    base_text: TextChunk
    comments: TextChunk or list of comment strings
    base_tokenizer: f(string)->list(string)
    prev_matched_results: [(start,end)] list of start/end indexes found in a previous iteration of match_text
    dh_extract_method: f(string)->string
    verbose: True means print debug info
    word_threshold: float - percentage of mismatched words to allow. higher means allow more non-matching words in a successful match (range is [0,1])
    char_threshold: float - roughly a percentage of letters that can differ in a word match (not all letters are equally weighted so its not a linear percentage). higher allows more differences within a word match. (range is [0,1])
    with_abbrev_matches: True if you want a second return value which is a list AbbrevMatch objects (see class definition above)
    with_num_abbrevs: True if you also allow abbreviations to match corresponding numbers
    boundaryFlexibility: int which indicates how much leeway there is in the order of rashis. higher values allow more disorder in matches. 0 means the start positions of matches must be in order. a high value (higher than the number of words in the doc) means order doesn't matter
    dh_split: prototype, split long dibur hamatchil
    rashi_filter: function(str) -> bool , if False, remove rashi from matching
    strict_boundaries: True means no matches can overlap
    place_all: True means every comment is place, regardless of whether it matches well or not

    :returns: dict
    {"matches": list of base_refs. each element corresponds to each comment in comments,
    "match_word_indices": copied from output of match_text(). (start,end) indexes of text matched in base_text,
    "match_text": text matched for each comment}
    if comments is a TextChunk, dict also contains "comment_refs", list of refs corresponding to comments
    if with_abbrev_matches, dict also contains "abbrevs", list of AbbrevMatches
    if place_all, dict also contains "fixed", list of bools for each comment. True if comment originally didn't match, but later was matched b/c the comments around it were matched
    """

    bas_word_list = [w for seg in base_text.ja().flatten_to_array() for w in base_tokenizer(seg)]
    if len(bas_word_list) == 0:
        raise IndexError("No text in base_text after applying base_tokenizer()")
    bas_ind_list,bas_ref_list,total_len = base_text.text_index_map(base_tokenizer)


    #get all non-empty segment refs for 'comments'
    if type(comments) == TextChunk:
        comment_list = comments.ja().flatten_to_array()
        _, comment_ref_list, _ = comments.text_index_map(base_tokenizer)

        if rashi_filter:
            filter_out = filter(lambda x: rashi_filter(x[0]) if rashi_filter(x[0]) else None,zip(comment_list,comment_ref_list))
            comment_list = [x[0] for x in filter_out]
            comment_ref_list = [x[1] for x in filter_out]

    elif type(comments) == list:
        comment_list = comments
        comment_ref_list = None
        if rashi_filter:
            comment_list = filter(lambda x: rashi_filter(x) if rashi_filter(x) else None, comment_list)

    else:
        raise TypeError("'comments' needs to be either a TextChunk or a list of comment strings")

    matched = match_text(bas_word_list,comment_list,dh_extract_method,verbose,word_threshold,char_threshold,prev_matched_results=prev_matched_results,
                         with_abbrev_matches=with_abbrev_matches,with_num_abbrevs=with_num_abbrevs,boundaryFlexibility=boundaryFlexibility,
                         dh_split=dh_split,rashi_filter=rashi_filter,strict_boundaries=strict_boundaries,place_all=place_all)
    start_end_map = matched['matches']
    text_matches = matched['match_text']
    if with_abbrev_matches:
        abbrev_matches = matched['abbrevs']
    if place_all:
        fixed = matched['fixed']

    if strict_boundaries:
        for ise, se in enumerate(start_end_map):
            # if it slightly overlaps, correct the boundary
            # (49, 64) (65, 80)
            # (49, 65) (66, 80)
            if ise > 0 and start_end_map[ise - 1][0] != -1 and \
                            se[0] != -1 and \
                            se[0] <= start_end_map[ise - 1][1]:

                # you have two options how to fix this. choose the one that doesn't cause a ref split
                # se[0] = start_end_map[ise - 1][1] + 1
                # start_end_map[ise - 1] = se[0] - 1
                start = start_end_map[ise - 1][1] - 1
                end = se[0]
                mid = (1.0*start + end) / 2
                possibilities = [(p, p+1) for p in xrange(start,end + 1)]
                possibilities.sort(key=lambda x: abs(x[0] - mid))

                #print "Before {} After {}".format(start_end_map[ise - 1], se)
                #print "Start {} End {} Mid {}".format(start, end, mid)
                #print "Possibs {}".format(possibilities)
                for p in possibilities:
                    start_ref = bas_ref_list[bisect.bisect_right(bas_ind_list,p[0])-1]
                    end_ref = bas_ref_list[bisect.bisect_right(bas_ind_list,p[1])-1]
                    if start_ref != end_ref:
                        start_end_map[ise - 1] = (start_end_map[ise - 1][0], p[0])
                        start_end_map[ise] = (p[1], start_end_map[ise][1])
                        break

    ref_matches = []
    for i,x in enumerate(start_end_map):
        start = x[0]
        end = x[1]
        if start == -1: #meaning, not found
            matched_ref = None
        else:
            start_ref = bas_ref_list[bisect.bisect_right(bas_ind_list,start)-1]
            end_ref = bas_ref_list[bisect.bisect_right(bas_ind_list,end)-1]
            if start_ref == end_ref:
                matched_ref = start_ref
            else:
                matched_ref = start_ref.to(end_ref)

        ref_matches.append(matched_ref)


    ret = {'matches': ref_matches, 'match_word_indices': start_end_map, 'match_text': text_matches}
    if comment_ref_list:
        ret['comment_refs'] = comment_ref_list
    if with_abbrev_matches:
        ret['abbrevs'] = abbrev_matches
    if place_all:
        ret['fixed'] = fixed

    if create_ranges:
        return set_ranges(ret, base_text)
    else:
        return ret


def match_text(base_text, comments, dh_extract_method=lambda x: x,verbose=False,word_threshold=0.27,char_threshold=0.2,
               prev_matched_results=None,with_abbrev_matches=False,with_num_abbrevs=True,
               boundaryFlexibility=0,dh_split=None,rashi_filter=None,
               strict_boundaries=False, place_all=False):
    """
    base_text: list - list of words
    comments: list - list of comment strings
    dh_extract_method: f(string)->string
    verbose: True means print debug info
    word_threshold: float - percentage of mismatched words to allow. higher means allow more non-matching words in a successful match (range is [0,1])
    char_threshold: float - roughly a percentage of letters that can differ in a word match (not all letters are equally weighted so its not a linear percentage). higher allows more differences within a word match. (range is [0,1])
    prev_matched_results: [(start,end)] list of start/end indexes found in a previous iteration of match_text
    with_abbrev_matches: True if you want a second return value which is a list AbbrevMatch objects (see class definition above)
    with_num_abbrevs: True if you also allow abbreviations to match corresponding numbers
    boundaryFlexibility: int which indicates how much leeway there is in the order of rashis. higher values allow more disorder in matches. 0 means the start positions of matches must be in order. a high value (higher than the number of words in the doc) means order doesn't matter
    dh_split: prototype, split long dibur hamatchil
    rashi_filter: function(str) -> bool , if False, remove rashi from matching
    strict_boundaries: True means no matches can overlap
    place_all: True means every comment is place, regardless of whether it matches well or not

    :returns: dict
    {"matches": list of (start,end) indexes for each comment. indexes correspond to words matched in base_text,
    "match_text": list of str for each comment corresponding to the base_text text matched by each comment}
    if comments is a TextChunk, dict also contains "comment_refs", list of refs corresponding to comments
    if with_abbrev_matches, dict also contains "abbrevs", list of AbbrevMatches
    if place_all, dict also contains "fixed", list of bools for each comment. True if comment originally didn't match, but later was matched b/c the comments around it were matched

    """
    if rashi_filter:
        comments = filter(lambda x: rashi_filter(x) if rashi_filter(x) else None, comments)

    InitializeHashTables()

    curDaf = GemaraDaf(base_text,comments,dh_extract_method,prev_matched_results,dh_split)
    #now we go through each rashi, and find all potential matches for each, with a rating
    for irashi,ru in enumerate(curDaf.allRashi):
        if ru.startWord != -1:
            #this rashi was initialized with the `prev_matched_results` list and should be ignored with regards to matching
            continue

        startword,endword = (0,len(curDaf.allWords)-1) if prev_matched_results == None else GetRashiBoundaries(curDaf.allRashi,ru.place,len(curDaf.allWords),boundaryFlexibility)[0:2]
        #TODO implement startword endword in GetAllMatches()
        ru.rashimatches = GetAllMatches(curDaf,ru,startword,endword,word_threshold,char_threshold,with_num_abbrevs=with_num_abbrevs)

        """
        approxMatches = GetAllApproximateMatches(curDaf,ru,startword,endword,word_threshold,char_threshold)
        approxAbbrevMatches = GetAllApproximateMatchesWithAbbrev(curDaf, ru, startword, endword, word_threshold, char_threshold)
        approxSkipWordMatches = GetAllApproximateMatchesWithWordSkip(curDaf, ru, startword, endword, word_threshold, char_threshold)

        ru.rashimatches += approxMatches + approxAbbrevMatches

        #only add skip-matches that don't overlap with existing matching
        foundpoints = []
        for tm in ru.rashimatches:
            foundpoints.append(tm.startWord)
        # for the skip words, of course, it may find items that are one-off or two-off from the actual match. Filter these out
        for tm in approxSkipWordMatches:
            startword = tm.startWord
            #TODO maybe consider changing the range
            if any([x in foundpoints for x in xrange(startword - 1, startword + 2)]):
                continue
            ru.rashimatches.append(tm)
        """
        #sort the rashis by score
        ru.rashimatches.sort(key=lambda x: x.score) #note: check this works

        #now figure out disambiguation score
        CalculateAndFillInDisambiguity(ru)

    #let's make a list of our rashis in disambiguity order
    rashisByDisambiguity = curDaf.allRashi[:] # note: check if this is what he wanted. List<RashiUnit> rashisByDisambiguity = new List<RashiUnit>(curDaf.allRashi);
    rashisByDisambiguity.sort(key=lambda x: -x.disambiguationScore ) #note: check that this is sorting in the right order. rashisByDisambiguity.Sort((x, y) => y.disambiguationScore.CompareTo(x.disambiguationScore));
    #remove any rashis that have no matches at all
    for temp_rashi in reversed(rashisByDisambiguity):
        if len(temp_rashi.rashimatches) == 0:
            rashisByDisambiguity.remove(temp_rashi)

    while len(rashisByDisambiguity) > 0:

        #take top disambiguous rashi
        topru = rashisByDisambiguity[0]
        #get its boundaries
        startBound,endBound,prevMatchedRashi,nextMatchedRashi = GetRashiBoundaries(curDaf.allRashi,topru.place,len(curDaf.allWords),boundaryFlexibility)

        #take the first bunch in order of disambiguity and put them in
        highestrating = topru.disambiguationScore
        #if we're up to 0 disambiguity, rate them in terms of their plac in the amud
        if highestrating == 0:
            for curru in rashisByDisambiguity:
                #figure out how many are tied, or at least within 5 of each other
                topscore = curru.rashimatches[0].score
                tobesorted = []
                for temp_rashimatchi in curru.rashimatches:
                    if temp_rashimatchi.score == topscore:
                        #this is one of the top matches, and should be sorted
                        tobesorted.append(temp_rashimatchi)

                #sort those top rashis by place
                tobesorted.sort(key=lambda x: x.startWord)
                #now add the rest
                for temp_rashimatchi in curru.rashimatches[len(tobesorted):]:
                    tobesorted.append(temp_rashimatchi)

                #put them all in
                curru.rashimatches = tobesorted
        lowestrating = -1
        rashiUnitsCandidates = []
        for ru in rashisByDisambiguity:
            #if this is outside the region, chuck it
            #the rashis are coming in a completely diff order, hence we need to check each one
            if ru.place <= prevMatchedRashi or ru.place >= nextMatchedRashi:
                continue
            rashiUnitsCandidates.append(ru)


        # now we figure out how many of these we want to process
        # we want to take the top three at the least, seven at most, and anything that fits into the current threshold.
        ruToProcess = []
        threshold = max(rashiUnitsCandidates[0].disambiguationScore - 5, rashiUnitsCandidates[0].disambiguationScore/2)
        thresholdBediavad = rashiUnitsCandidates[0].disambiguationScore/2
        for ru in rashiUnitsCandidates:
            curScore = ru.disambiguationScore
            if (curScore >= threshold or (len(ruToProcess) < 3 and curScore >= thresholdBediavad)) or False:
                ruToProcess.append(ru)
                if highestrating == -1 or ru.disambiguationScore > highestrating:
                    highestrating = ru.disambiguationScore
                if lowestrating == -1 or ru.disambiguationScore < lowestrating:
                    lowestrating = ru.disambiguationScore
            else:
                break

            if len(ruToProcess) == 7:
                break
        # are these in order?
        #.. order them by place in the rashi order
        ruToProcess.sort(key=lambda x: x.place)



        #see if they are in order
        fAllInOrder = True
        fFirstTime = True
        while not fAllInOrder or fFirstTime:
            #if there are ties, allow for those
            fFirstTime = False
            fAllInOrder = True
            prevstartpos = -1
            prevendpos = -1
            for ru in ruToProcess:

                best_rashi = ru.rashimatches[0]

                if strict_boundaries:
                    if best_rashi.startWord < prevendpos:
                        fAllInOrder = False
                        break
                else:
                    #if this one is prior to the current position, break
                    if best_rashi.startWord < prevstartpos:
                        fAllInOrder = False
                        break
                    # if this one is the same as curpos, only ok it it is shorter
                    if best_rashi.startWord == prevstartpos:
                        if best_rashi.endWord >= prevendpos:
                            fAllInOrder = False
                            break

                prevstartpos = best_rashi.startWord
                prevendpos = best_rashi.endWord

            # if they are not in order, then we need to figure out which ones are causing trouble and throw them out
            if not fAllInOrder:
                if len(ruToProcess) == 2:
                    #there are only 2 (duh)
                    #if the top one is much higher in its disambig score than the next one, then don't try to reverse; just take the top score
                    if abs(ruToProcess[0].disambiguationScore - ruToProcess[1].disambiguationScore) > 10:
                        ruToProcess.sort(key=lambda x: -x.disambiguationScore)
                        del ruToProcess[1]
                    else:
                        # if there are only 2, see if we can reverse them by going to the secondary matches
                        # try the first
                        ffixed = False
                        if len(ruToProcess[0].rashimatches) > 1:

                            if (not strict_boundaries and ruToProcess[0].rashimatches[1].startWord < ruToProcess[1].rashimatches[0].startWord) or \
                                (strict_boundaries and ruToProcess[0].rashimatches[1].startWord <= ruToProcess[1].rashimatches[0].endWord):
                                #make sure they are reasonably close
                                if ruToProcess[0].disambiguationScore < 10:
                                    del ruToProcess[0].rashimatches[0]
                                    ffixed = True
                        if not ffixed:
                            #.. try the second
                            ffixed = False
                            if len(ruToProcess[1].rashimatches) > 1:
                                if (not strict_boundaries and ruToProcess[1].rashimatches[1].startWord > ruToProcess[0].rashimatches[0].startWord) or \
                                        (strict_boundaries and ruToProcess[1].rashimatches[1].endWord >= ruToProcess[0].rashimatches[0].startWord):
                                    if ruToProcess[1].disambiguationScore < 10:
                                        del ruToProcess[1].rashimatches[0]
                                        ffixed = True
                        if not ffixed:
                            #try the second of both
                            ffixed = False
                            if len(ruToProcess[0].rashimatches) > 1 and len(ruToProcess[1].rashimatches) > 1:
                                if (not strict_boundaries and ruToProcess[1].rashimatches[1].startWord > ruToProcess[0].rashimatches[1].startWord) or \
                                        (strict_boundaries and ruToProcess[1].rashimatches[1].endWord >= ruToProcess[0].rashimatches[1].startWord):
                                    if ruToProcess[1].disambiguationScore < 10 and ruToProcess[0].disambiguationScore < 10:
                                        del ruToProcess[0].rashimatches[0]
                                        del ruToProcess[1].rashimatches[0]
                                        ffixed = True
                        #if not, take the one with the highest score
                        if not ffixed:
                            ruToProcess.sort( key = lambda x: -x.disambiguationScore)
                            del ruToProcess[1]
                else:
                    outoforder = [0 for i in xrange(len(ruToProcess))]
                    highestDeviation = 0
                    for irashi,temp_irashi in enumerate(ruToProcess):
                        #how many are out of order vis-a-vis this one?
                        for jrashi,temp_jrashi in enumerate(ruToProcess):
                            if jrashi == irashi:
                                continue
                            if irashi < jrashi:
                                #easy case: they start at diff places
                                if strict_boundaries:
                                    if temp_irashi.rashimatches[0].endWord >= temp_jrashi.rashimatches[0].startWord:
                                        outoforder[irashi] += 1
                                else:
                                    if temp_irashi.rashimatches[0].startWord > temp_jrashi.rashimatches[0].startWord:
                                        outoforder[irashi] += 1
                                        #deal with case of same starting word. only ok if irashi is of greater length
                                    elif temp_irashi.rashimatches[0].startWord == temp_jrashi.rashimatches[0].startWord:
                                        if temp_irashi.rashimatches[0].endWord <= temp_jrashi.rashimatches[0].endWord:
                                            outoforder[irashi] += 1
                            else:
                                #in this case, irashi is after jrashi
                                if strict_boundaries:
                                    if temp_irashi.rashimatches[0].startWord <= temp_jrashi.rashimatches[0].endWord:
                                        outoforder[irashi] += 1
                                else:
                                    if temp_irashi.rashimatches[0].startWord < temp_jrashi.rashimatches[0].startWord:
                                        outoforder[irashi] += 1
                                    # deal with case of same starting word. only ok if jrashi is of greater length
                                    elif temp_irashi.rashimatches[0].startWord == temp_jrashi.rashimatches[0].startWord:
                                        if temp_irashi.rashimatches[0].endWord >= temp_jrashi.rashimatches[0].endWord:
                                            outoforder[irashi] += 1
                        if outoforder[irashi] > highestDeviation:
                            highestDeviation = outoforder[irashi]

                    #now throw out all those that have the highest out-of-order ranking
                    for irashi in reversed(xrange(len(ruToProcess))):
                        if outoforder[irashi] == highestDeviation and len(ruToProcess) > 1:
                            del ruToProcess[irashi]
        #TODO: deal with the case of only 2 in ruToProcess in a smarter way


        #by this point they are all in order, so we can put them all in
        for curru in ruToProcess:
            # put it in
            #TODO: if disambiguity is low, apply other criteria


            #find first rashimatch which doesn't overlap too many words in already matched gemara
            if len(curru.rashimatches) > 0 and not filter_matches_out_of_order(curDaf.matched_words, curru.rashimatches[0]):
                if len(curru.rashimatches) > 1 and abs(curru.rashimatches[0].score - curru.rashimatches[1].score) < 10:
                    #only delete if you know the one after is close in score
                    del curru.rashimatches[0]

            if len(curru.rashimatches) == 0:
                if curru in rashisByDisambiguity:
                    rashisByDisambiguity.remove(curru)
                continue


            match = curru.rashimatches[0]
            curru.startWord = match.startWord
            curru.endWord = match.endWord

            for imatchedword in xrange(curru.startWord, curru.endWord+1):
                curDaf.matched_words[imatchedword] = True

            curru.matchedGemaraText = match.textMatched
            curru.skippedRashiWords = match.skippedRashiWords
            curru.skippedDafWords = match.skippedDafWords
            curru.abbrev_matches = match.abbrev_matches
            curru.match_type = match.match_type

            # remove this guy from the disambiguities, now that it is matched up
            rashisByDisambiguity.remove(curru) #check remove
            #recalculate the disambiguities for all those who were potentially relevant, based on this one's place
            RecalculateDisambiguities(curDaf.allRashi, rashisByDisambiguity, prevMatchedRashi, nextMatchedRashi, startBound,
                                      endBound, curru, boundaryFlexibility, len(curDaf.allWords)-1, place_all)

        #resort the disambiguity array
        rashisByDisambiguity.sort(key = lambda x: -x.disambiguationScore)

    unmatched = CountUnmatchedUpRashi(curDaf)
    #now we check for dapim that have a lot of unmatched items, and then we take items out one at a time to see if we can
    #minimize it because usually this results from one misplaced item.

    curDaf.mergeRashis()




    if place_all:
        fixed = []
        #place the unmatched comments which fall between 2 matched comments
        for irm, ru in enumerate(curDaf.allRashi):
            s = ru.startWord
            e = ru.endWord
            prev_match = curDaf.allRashi[irm - 1].endWord if irm > 0                      else -1
            next_match = curDaf.allRashi[irm + 1].startWord if irm < len(curDaf.allRashi) - 1 else -1
            new_match = None
            if s == -1:
                if prev_match != -1 and next_match != -1:
                    new_match = (prev_match, next_match)
                elif irm == 0 and next_match != -1:
                    new_match = (0, next_match)
                elif irm == len(curDaf.allRashi) - 1 and prev_match != -1:
                    new_match = (prev_match, len(curDaf.allWords) - 1)

                if not new_match is None and new_match[0] < new_match[1]:
                    curDaf.allRashi[irm].matchedGemaraText = u" ".join(curDaf.allWords[new_match[0]:new_match[1]+1])
                    curDaf.allRashi[irm].startWord = new_match[0]
                    curDaf.allRashi[irm].endWord = new_match[1]
                    curDaf.allRashi[irm].match_type = 'fixed'
                    fixed.append(True)
                else:
                    fixed.append(False)
            fixed.append(False)

    start_end_map = []
    abbrev_matches = []
    text_matches = []
    #now do a full report
    for iru,ru in enumerate(curDaf.allRashi):
        start_end_map.append((ru.startWord,ru.endWord))
        abbrev_matches.append(ru.abbrev_matches)
        text_matches.append((ru.matchedGemaraText,ru.startingText))

    if verbose:
        sbreport = u""
        for irm, (s, e) in enumerate(start_end_map):
            ru = curDaf.allRashi[irm]
            if s == -1:
                sbreport += u"\nUNMATCHED:\n{}\n".format(ru)
            else:
                sbreport += u"\n{}\n".format(ru)

        print sbreport

    ret = {"matches":start_end_map, "match_text": text_matches}
    if with_abbrev_matches:
        ret["abbrevs"] = abbrev_matches
    if place_all:
        ret["fixed"] = fixed

    return ret


def set_ranges(results, base_text):
    '''
    Takes the results and produces a range wherever there isn't a match.
    Example: If the first matches to 3, the second doesn't match to anything, and the third matches to 10, then this function
    set the second result to the range 3-10.
    :param results:
    :param base_text:
    :return:
    '''
    if None not in results['matches'] or results['matches'] == [None]:
        return results

    base_ref = base_text._oref
    matches = results['matches']
    num_matches_total = 0
    first_ref = None
    last_ref = None
    for count, match in enumerate(matches):
        if match:
            last_ref = match
            num_matches_total += 1
            if first_ref is None:
                first_ref = match
        elif count == 0:
            core = base_ref._core_dict()
            core['sections'] += [1]
            core['toSections'] += [1]
            first_ref = Ref(_obj=core)

    if last_ref is None:
        last_line = len(base_text.text)
        core = base_ref._core_dict()
        core['sections'] += [last_line]
        core['toSections'] += [last_line]
        last_ref = Ref(_obj=core)

    if num_matches_total == 0:
        start_to_end = first_ref.to(last_ref)
        for count in range(len(matches)):
            matches[count] = start_to_end
        results['matches'] = matches
        return results

    num_matches_found = 0
    prev_ref = first_ref
    for i, match in enumerate(matches):
        if match is None:
            start = prev_ref
            end = last_ref
            # iterate through until you get to end, setting end to anything found then set matches[i] to start.to(end)
            for j in range(i + 1, len(matches) - 1):
                if matches[j]:
                    end = matches[j]
                    break
            matches[i] = start.to(end)
        else:
            num_matches_found += 1
            prev_ref = match

    results['matches'] = matches
    return results





def filter_matches_out_of_order(matched_words, temprashimatch):
    num_unmatched = temprashimatch.endWord - temprashimatch.startWord + 1
    for imatchedword in xrange(temprashimatch.startWord, temprashimatch.endWord + 1):
        if matched_words[imatchedword]:
            num_unmatched -= 1

    if (temprashimatch.endWord - temprashimatch.startWord + 1) == 0:
        return False
    percent_matched = 1.0 * num_unmatched / (temprashimatch.endWord - temprashimatch.startWord + 1)
    #if percent_matched <= 0.3:
    #    print "DELETING {}".format(percent_matched)
    return percent_matched > 0.3

def RecalculateDisambiguities(allRashis, rashisByDisambiguity, prevMatchedRashi, nextMatchedRashi, startbound, endbound,
                              newlyMatchedRashiUnit, boundaryFlexibility, maxendbound, place_all):  # List<RashiUnit>,List<RashiUnit>,int,int,int,int,RashiUnit
    for irashi in xrange(len(rashisByDisambiguity) - 1, -1, -1):
        ru = rashisByDisambiguity[irashi]
        if ru.place <= prevMatchedRashi or ru.place >= nextMatchedRashi or ru.place == newlyMatchedRashiUnit.place:
            continue
        # this rashi falls out somewhere inside the current window, either before the newest match or after the newest match
        localstartbound = startbound if (ru.place < newlyMatchedRashiUnit.place) else newlyMatchedRashiUnit.startWord - boundaryFlexibility
        localendbound = endbound if (ru.place > newlyMatchedRashiUnit.place) else newlyMatchedRashiUnit.startWord + boundaryFlexibility

        if localstartbound < 0:
            localstartbound = 0

        if localendbound > maxendbound:
            localendbound = maxendbound

        # now remove any potential matches that are blocked by the newly matched rashi
        if not place_all:
            for imatch in xrange(len(ru.rashimatches) - 1, -1, -1):
                tm = ru.rashimatches[imatch]
                if tm.startWord < localstartbound or tm.startWord > localendbound:
                    del ru.rashimatches[imatch]

        # special shift: if there are two close items, and one is an overlap with a current anchor and one is not, switch (them?) and their scores
        endOfPrevRashi = -1 if prevMatchedRashi == -1 else allRashis[prevMatchedRashi].endWord
        startOfNextRashi = 9999 if nextMatchedRashi == len(allRashis) else allRashis[nextMatchedRashi].startWord

        if len(ru.rashimatches) >= 2:
            # if the top one overlaps
            if ru.rashimatches[0].startWord <= endOfPrevRashi or ru.rashimatches[0].endWord >= startOfNextRashi:
                # and if the next one does not overlap
                if ru.rashimatches[1].startWord > endOfPrevRashi and ru.rashimatches[1].endWord < startOfNextRashi:
                    if ru.rashimatches[1].score - ru.rashimatches[0].score < 20:
                        # let's switch them

                        temp = ru.rashimatches[1]
                        ru.rashimatches[1] = ru.rashimatches[0]
                        ru.rashimatches[0] = temp

                        tempscore = ru.rashimatches[1].score
                        ru.rashimatches[0].score = ru.rashimatches[1].score
                        ru.rashimatches[1].score = tempscore
        # if there are none left, remove it altogether
        if len(ru.rashimatches) == 0 and not place_all:
            del rashisByDisambiguity[irashi]
        else:
            # now recalculate the disambiguity
            CalculateAndFillInDisambiguity(ru)


def CalculateAndFillInDisambiguity(ru):  # RashiUnit
    # if just one, it is close to perfect. Although could be that there is no match...
    if len(ru.rashimatches) == 1:
        # ca;culate it vis-a-vis blank
        ru.disambiguationScore = (ImaginaryContenderPerWord * ru.cvWordcount) - ru.rashimatches[0].score

        if ru.disambiguationScore < 0:
            ru.disambiguationScore = 0
    elif len(ru.rashimatches) == 0:
        ru.disambiguationScore = 0xFFFF
    else:
        ru.disambiguationScore = ru.rashimatches[1].score - ru.rashimatches[0].score

def sigmoid(x):
    return 1.0 / (1 + mathy.exp(-x))

def CountUnmatchedUpRashi(curDaf):  # GemaraDar
    # This function counts all the Rashi's in a given daf and
    # returns the amount of rashi's that still don't have a location within the gemara text.
    toRet = 0
    for rashi in curDaf.allRashi:
        if rashi.startWord == -1:
            toRet += 1
    return toRet

def GetAbbrevs(dafwords, rashiwords, char_threshold, startBound, endBound, with_num_abbrevs=True):
    allabbrevinds = []
    allabbrevs = []
    for id, dword in enumerate(dafwords):
        if id < startBound or id > endBound:
            continue
        if u"\"" in dword or u"״" in dword:
            abbrev_range = None
            for ir, rword in enumerate(rashiwords):
                if abbrev_range and ir in abbrev_range:
                    continue

                isMatch, offset, isNum = isAbbrevMatch(ir,cleanAbbrev(dword),rashiwords, char_threshold, with_num_abbrevs=with_num_abbrevs)
                if isMatch:
                    istartcontext = 3 if id >= 3 else id
                    abbrevMatch = AbbrevMatch(dword, rashiwords[ir:ir+offset+1],(ir,ir+offset),(id,id),
                                              dafwords[id-istartcontext:id],dafwords[id+1:id+4],isNum)
                    allabbrevs.append(abbrevMatch)
                    allabbrevinds.append(((ir,id),(ir+offset,id)))
                    abbrev_range = range(ir,ir+offset+1)
    for ir, rword in enumerate(rashiwords):
        if u"\"" in rword or u"״" in rword:
            abbrev_range = None
            for id, dword in enumerate(dafwords):
                if abbrev_range and id in abbrev_range:
                    continue
                isMatch, offset, isNum = isAbbrevMatch(id,cleanAbbrev(rword),dafwords, char_threshold, with_num_abbrevs=with_num_abbrevs)
                if isMatch:
                    istartcontext = 3 if id >= 3 else id
                    abbrevMatch = AbbrevMatch(rword, dafwords[id:id+offset+1],(ir,ir),(id,id+offset),
                                              dafwords[id-istartcontext:id],dafwords[id+offset+1:id+offset+4],isNum)
                    allabbrevs.append(abbrevMatch)
                    allabbrevinds.append(((ir,id),(ir,id+offset)))
                    abbrev_range = range(id,id+offset+1)

    return allabbrevinds, allabbrevs


def GetAllMatches(curDaf, curRashi, startBound, endBound,
                             word_threshold, char_threshold, daf_skips=2, rashi_skips=1, overall=2,with_num_abbrevs=True):
    allMatches = []
    startText = curRashi.startingTextNormalized
    global normalizingFactor

    dafwords = curDaf.allWords[startBound:endBound+1]
    dafhashes = curDaf.wordhashes[startBound:endBound+1]

    if curRashi.place == 5:
        pass

    allabbrevinds, allabbrevs = GetAbbrevs(dafwords, curRashi.words, char_threshold, startBound, endBound, with_num_abbrevs=with_num_abbrevs)

    daf_skips = int(min(daf_skips, mathy.floor((curRashi.cvWordcount-1)/2)))
    rashi_skips = int(min(rashi_skips, mathy.floor((curRashi.cvWordcount-1)/2)))
    overall = overall if daf_skips + rashi_skips >= overall else daf_skips + rashi_skips
    mm = MatchMatrix(dafhashes,
                     curRashi.cvhashes,
                     allabbrevinds,
                     word_threshold,
                     comment_word_skip_threshold=rashi_skips,
                     base_word_skip_threshold=daf_skips,
                     overall_word_skip_threshold=overall)
    paths = mm.find_paths()

    """
        daf_start_index: #,
        comment_indexes_skipped: [],
        daf_indexes_skipped: [],
        mismatches: #
    """
    for path in paths:
        curMatch = TextMatch()
        curMatch.match_type = 'skip'
        #print 'PATH'
        #print path
        #mm.print_path(path)
        gemaraWordToIgnore = path["daf_indexes_skipped"][0] + startBound if len(path["daf_indexes_skipped"]) > 0 else -1
        gemaraSecondWordToIgnore = path["daf_indexes_skipped"][1] + startBound if len(path["daf_indexes_skipped"]) > 1 else -1
        iRashiWordToIgnore = path["comment_indexes_skipped"][0] if len(path["comment_indexes_skipped"]) > 0 else -1
        abbrevs = [allabbrevs[iabbrev] for iabbrev in path["jump_indexes"]]
        iGemaraWord = path["daf_start_index"] + startBound


        #figure out the bounds of what you actually matched
        rashiSkipWords = []
        dafSkipWords = []
        len_matched = curRashi.cvWordcount
        for abb in abbrevs:
            #normalize to startBound
            abb.gemaraRange = (abb.gemaraRange[0] + startBound, abb.gemaraRange[1] + startBound)

            if abb.rashiRange[0] == abb.rashiRange[1]:
                rashiSkipWords.append(abb.rashiRange[0])
                len_matched -= 1
            else:
                rashiSkipWords += range(abb.rashiRange[0],abb.rashiRange[1]+1)
                len_matched -= (abb.rashiRange[1] - abb.rashiRange[0] + 1)
            if abb.gemaraRange[0] == abb.gemaraRange[1]:
                dafSkipWords.append(abb.gemaraRange[0])
                len_matched += 1
            else:
                dafSkipWords += range(abb.gemaraRange[0],abb.gemaraRange[1]+1)
                len_matched += (abb.gemaraRange[1] - abb.gemaraRange[0] + 1)

        if iRashiWordToIgnore != -1:
            rashiSkipWords.append(iRashiWordToIgnore)
            len_matched -= 1

        if gemaraWordToIgnore != -1:
            dafSkipWords.append(gemaraWordToIgnore)
            len_matched += 1
        if gemaraSecondWordToIgnore != -1:
            dafSkipWords.append(gemaraSecondWordToIgnore)
            len_matched += 1

        alternateStartText = BuildPhraseFromArray(curRashi.words, 0, len(curRashi.words), rashiSkipWords)
        # the "text matched" is the actual text of the gemara, including the word we skipped.



        targetPhrase = BuildPhraseFromArray(curDaf.allWords, iGemaraWord , len_matched, dafSkipWords)

        #print u'target {} alt {}'.format(targetPhrase,alternateStartText)

        fIsMatch = True
        #check small matches to make sure they actually match
        if curRashi.cvWordcount <= 4:
            distance, fIsMatch = IsStringMatch(alternateStartText, targetPhrase, char_threshold)

        if fIsMatch:

            dist = ComputeLevenshteinDistanceByWord(alternateStartText, targetPhrase)

            # add penalty for skipped words
            if gemaraWordToIgnore >= 0:
                dist += fullWordValue #weighted_levenshtein.cost_str(curDaf.allWords[gemaraWordToIgnore])
            if gemaraSecondWordToIgnore >= 0:
                dist += fullWordValue #weighted_levenshtein.cost_str(curDaf.allWords[gemaraSecondWordToIgnore])
            if iRashiWordToIgnore >= 0:
                dist += fullWordValue #weighted_levenshtein.cost_str(curRashi.words[iRashiWordToIgnore])
            if len(abbrevs) > 0:
                dist += abbreviationPenalty


            normalizedDistance = 1.0 * (dist + smoothingFactor) / (len(startText) + smoothingFactor) * normalizingFactor
            curMatch.score = normalizedDistance
            curMatch.textToMatch = curRashi.startingText
            curMatch.textMatched = BuildPhraseFromArray(curDaf.allWords, iGemaraWord , len_matched)
            curMatch.startWord = iGemaraWord
            curMatch.abbrev_matches = abbrevs
            curMatch.endWord = iGemaraWord + len_matched - 1
            curMatch.skippedRashiWords = [curRashi.words[iskip] for iskip in path['comment_indexes_skipped']]
            curMatch.skippedDafWords = [curDaf.allWords[iskip] for iskip in path['daf_indexes_skipped']]
            allMatches += [curMatch]


    return allMatches

def GetAllApproximateMatches(curDaf, curRashi, startBound, endBound,
                             word_threshold, char_threshold):  # inputs (GemaraDaf, RashiUnit, int, int, double)
    global normalizingFactor
    allMatches = []
    startText = curRashi.startingTextNormalized
    wordCount = curRashi.cvWordcount
    allowedMismatches = mathy.ceil(wordCount * word_threshold)
    cvhashes = curRashi.cvhashes
    if wordCount == 0:
        return allMatches
    # Okay, start going through all the permutations..
    distance = 0

    iWord = startBound
    while iWord <= len(curDaf.allWords) - wordCount and iWord + wordCount - 1 <= endBound:
        fIsMatch = False
        # if phrase is 4 or more words, use the 2-letter hashes
        if wordCount >= 4:

            if curDaf.wordhashes[iWord] == cvhashes[0]:
                # see if the rest match up
                mismatches = 0

                for icvword in xrange(1, wordCount):
                    if curDaf.wordhashes[iWord + icvword] != cvhashes[icvword]:
                        mismatches += 1

                # now we need to decide if we can let it go

                if mismatches <= allowedMismatches:
                    distance = mismatches
                    fIsMatch = True

        else:
            # build the phrase
            targetPhrase = BuildPhraseFromArray(curDaf.allWords, iWord, wordCount)

            # now check if it is a match
            distance, fIsMatch = IsStringMatch(startText, targetPhrase, char_threshold)

        # if it is, add it in
        if fIsMatch:
            curMatch = TextMatch()
            curMatch.textToMatch = curRashi.startingText
            curMatch.textMatched = BuildPhraseFromArray(curDaf.allWords, iWord, wordCount)
            curMatch.startWord = iWord
            curMatch.endWord = iWord + wordCount - 1
            curMatch.match_type = 'exact'

            # calculate the score - how distant is it
            dist = ComputeLevenshteinDistanceByWord(startText, curMatch.textMatched)
            normalizedDistance = 1.0*(dist + smoothingFactor) / (len(startText) + smoothingFactor) * normalizingFactor
            curMatch.score = normalizedDistance

            allMatches.append(curMatch)
        iWord += 1

    return allMatches


def GetAllApproximateMatchesWithAbbrev(curDaf, curRashi, startBound, endBound,
                                       word_threshold, char_threshold):  # inputs (GemaraDaf, RashiUnit, int, int, double)
    global normalizingFactor

    allMatches = []

    startText = curRashi.startingTextNormalized

    wordCountRashi = curRashi.cvWordcount
    wordCountGemara = len(curDaf.allWords)
    if wordCountRashi == 0:
        return allMatches

    # convert string into an array of words
    startTextWords = re.split(ur"\s+", startText)
    allowedMismatches = mathy.ceil(len(startTextWords) * word_threshold)

    # go through all possible starting words in the gemara text

    iStartingWordInGemara = startBound
    while iStartingWordInGemara < wordCountGemara: #and iStartingWordInGemara + wordCountRashi - 1 <= endBound:
        abbrev_matches = []
        fIsMatch = False
        offsetWithinGemara = 0
        offsetWithinRashiCV = 0
        distance = 0
        totaldistance = 0
        mismatches = 0

        # now we loop according to the number of words in the cv
        # .. keep track of how the gemara text differs from rashi length
        gemaraDifferential = 0

        iWordWithinPhrase = 0
        while iWordWithinPhrase + offsetWithinRashiCV < wordCountRashi  and iStartingWordInGemara + offsetWithinGemara + iWordWithinPhrase < wordCountGemara:
            # first check if the cv word has a quotemark


            #try:
            if u"\"" in startTextWords[iWordWithinPhrase + offsetWithinRashiCV] or u"״" in startTextWords[iWordWithinPhrase + offsetWithinRashiCV]:
                # get our ראשי תיבות word without the quote mark
                cleanRT = cleanAbbrev(startTextWords[iWordWithinPhrase + offsetWithinRashiCV])
                maxlen = len(cleanRT)

                # let's see if this matches the start of the next few words
                curpos = iStartingWordInGemara + iWordWithinPhrase + offsetWithinGemara
                fIsMatch,newOffsetWithinGemara, fIsNumber = isAbbrevMatch(curpos,cleanRT,curDaf.allWords, char_threshold)


                iStartContext = 3 if curpos >= 3 else curpos

                if fIsMatch:
                    abbrevMatch = AbbrevMatch(cleanRT,curDaf.allWords[curpos:curpos+newOffsetWithinGemara+1],(
                        iWordWithinPhrase+offsetWithinRashiCV,iWordWithinPhrase+offsetWithinRashiCV),
                                                   (curpos,curpos+newOffsetWithinGemara),
                                                   curDaf.allWords[curpos-iStartContext:curpos],
                                                   curDaf.allWords[curpos+newOffsetWithinGemara+1:curpos+newOffsetWithinGemara+4],
                                                    fIsNumber)
                    if not abbrevMatch in abbrev_matches:
                        abbrev_matches.append(abbrevMatch)
                offsetWithinGemara += newOffsetWithinGemara

                if not fIsMatch:
                    mismatches += 1
                    if mismatches > allowedMismatches:
                        break

            # now increment the offset to correspond, so that we'll know we're skipping over x number of words
            elif u"\"" in curDaf.allWords[iStartingWordInGemara + offsetWithinGemara + iWordWithinPhrase] or u"״" in curDaf.allWords[iStartingWordInGemara + offsetWithinGemara + iWordWithinPhrase]:
                # get our ראשי תיבות word without the quote mark
                cleanRT = cleanAbbrev(curDaf.allWords[iStartingWordInGemara + offsetWithinGemara + iWordWithinPhrase])
                maxlen = len(cleanRT)

                # let's see if this matches the start of the next few words
                curpos = iWordWithinPhrase + offsetWithinRashiCV
                fIsMatch,newOffsetWithinRashiCV, fIsNumber = isAbbrevMatch(curpos,cleanRT,startTextWords, char_threshold)

                curposGemara = iStartingWordInGemara + offsetWithinGemara + iWordWithinPhrase
                iStartContext = 3 if curposGemara >= 3 else curposGemara
                if fIsMatch:
                    abbrevMatch = AbbrevMatch(cleanRT, startTextWords[curpos:curpos + newOffsetWithinRashiCV + 1],
                                                   (curpos, curpos + newOffsetWithinRashiCV),
                                                   (curposGemara,curposGemara),
                                                   curDaf.allWords[curposGemara - iStartContext:curposGemara],
                                                   curDaf.allWords[curposGemara + 1:curposGemara + 4],
                                                    fIsNumber)
                    if not abbrevMatch in abbrev_matches:
                        abbrev_matches.append(abbrevMatch)
                offsetWithinRashiCV += newOffsetWithinRashiCV

                if not fIsMatch:
                    mismatches += 1
                    if mismatches > allowedMismatches:
                        break
            else:
                # great, this is a basic compare.
                distance, fMatch = IsStringMatch(startTextWords[iWordWithinPhrase + offsetWithinRashiCV],
                                                 curDaf.allWords[
                                                       iStartingWordInGemara + offsetWithinGemara + iWordWithinPhrase],
                                                 char_threshold)
                totaldistance += distance
                # if these words don't match, break and this isn't a match.
                if not fMatch:
                    mismatches += 1
                    if mismatches > allowedMismatches:
                        fIsMatch = False
                        break
            #except IndexError:
            #    continue
            iWordWithinPhrase += 1
        gemaraDifferential = offsetWithinRashiCV
        gemaraDifferential -= offsetWithinGemara

        # if it is, add it in!
        # else you didn't match the whole rashi b/c you got to the end of the daf too quickly
        if fIsMatch and iStartingWordInGemara + wordCountRashi - gemaraDifferential - 1 < wordCountGemara:

            curMatch = TextMatch()
            curMatch.textToMatch = curRashi.startingText
            curMatch.textMatched = BuildPhraseFromArray(curDaf.allWords, iStartingWordInGemara,
                                                        wordCountRashi - gemaraDifferential)
            curMatch.startWord = iStartingWordInGemara
            curMatch.endWord = iStartingWordInGemara + wordCountRashi - gemaraDifferential - 1 # I added the -1 b/c there was an off-by-one error
            curMatch.match_type = 'abbrev'

            #one final check on abbrev matches. get rid of any matches that are subsets
            new_abbrev_matches = []
            for iam1 in range(len(abbrev_matches)):
                am1 = abbrev_matches[iam1]
                issubset = False
                for iam2 in range(len(abbrev_matches)):
                    if iam1 == iam2: continue
                    am2 = abbrev_matches[iam2]
                    if am1.rashiRange[0] >= am2.rashiRange[0] and am1.rashiRange[1] <= am2.rashiRange[1]:
                        issubset = True
                        break
                if not issubset:
                    new_abbrev_matches.append(am1)


            #if we found an abbrev in gemara, save the words which matched in the TextMatch
            curMatch.abbrev_matches = new_abbrev_matches
            # calculate the score, adding in the penalty for abbreviation
            totaldistance += abbreviationPenalty
            normalizedDistance = 1.0*(totaldistance + smoothingFactor) / (len(startText) + smoothingFactor) * normalizingFactor
            curMatch.score = normalizedDistance


            allMatches.append(curMatch)

        iStartingWordInGemara += 1
    return allMatches


def GetAllApproximateMatchesWithWordSkip(curDaf, curRashi, startBound, endBound, word_threshold, char_threshold):  # GemaraDaf, RashiUnit,int,int,double

    allMatches = []
    startText = curRashi.startingTextNormalized
    global normalizingFactor

    daf_skips = int(min(2, mathy.floor((curRashi.cvWordcount-1)/2)))
    rashi_skips = 1 if daf_skips > 0 else 0
    overall = 2 if daf_skips + rashi_skips >= 2 else 1
    mm = MatchMatrix(curDaf.wordhashes,
                     curRashi.cvhashes,
                     word_threshold,
                     comment_word_skip_threshold=rashi_skips,
                     base_word_skip_threshold=daf_skips,
                     overall_word_skip_threshold=overall)
    paths = mm.find_paths()

    """
        daf_start_index: #,
        comment_indexes_skipped: [],
        daf_indexes_skipped: [],
        mismatches: #
    """
    for path in paths:
        curMatch = TextMatch()
        curMatch.match_type = 'skip'
        #print 'PATH'
        #mm.print_path(path)
        gemaraWordToIgnore = path["daf_indexes_skipped"][0] if len(path["daf_indexes_skipped"]) > 0 else -1
        gemaraSecondWordToIgnore = path["daf_indexes_skipped"][1] if len(path["daf_indexes_skipped"]) > 1 else -1
        iRashiWordToIgnore = path["comment_indexes_skipped"][0] if len(path["comment_indexes_skipped"]) > 0 else -1
        iGemaraWord = path["daf_start_index"]


        #figure out the bounds of what you actually matched
        if iRashiWordToIgnore != -1:
            alternateStartText = u' '.join(curRashi.words[:iRashiWordToIgnore] + curRashi.words[iRashiWordToIgnore+1:])
            rashiWordCount = curRashi.cvWordcount - 1
        else:
            rashiWordCount = curRashi.cvWordcount
            alternateStartText = startText
        # the "text matched" is the actual text of the gemara, including the word we skipped.
        len_matched = rashiWordCount
        if gemaraWordToIgnore != -1:
            len_matched += 1
        if gemaraSecondWordToIgnore != -1:
            len_matched += 1

        targetPhrase = BuildPhraseFromArray(curDaf.allWords, iGemaraWord , len_matched,
                                            gemaraWordToIgnore, gemaraSecondWordToIgnore)

        fIsMatch = True
        #check small matches to make sure they actually match
        if curRashi.cvWordcount <= 4:
            distance, fIsMatch = IsStringMatch(alternateStartText, targetPhrase, char_threshold)

        if fIsMatch:

            dist = ComputeLevenshteinDistanceByWord(alternateStartText, targetPhrase)

            # add penalty for skipped words
            if gemaraWordToIgnore >= 0:
                dist += fullWordValue #weighted_levenshtein.cost_str(curDaf.allWords[gemaraWordToIgnore])
            if gemaraSecondWordToIgnore >= 0:
                dist += fullWordValue #weighted_levenshtein.cost_str(curDaf.allWords[gemaraSecondWordToIgnore])
            if iRashiWordToIgnore >= 0:
                dist += fullWordValue #weighted_levenshtein.cost_str(curRashi.words[iRashiWordToIgnore])

            normalizedDistance = 1.0 * (dist + smoothingFactor) / (len(startText) + smoothingFactor) * normalizingFactor
            curMatch.score = normalizedDistance
            curMatch.textToMatch = curRashi.startingText
            curMatch.textMatched = BuildPhraseFromArray(curDaf.allWords, iGemaraWord , len_matched)
            curMatch.startWord = iGemaraWord
            curMatch.endWord = iGemaraWord + len_matched - 1
            curMatch.skippedRashiWords = [curRashi.words[iskip] for iskip in path['comment_indexes_skipped']]
            curMatch.skippedDafWords = [curDaf.allWords[iskip] for iskip in path['daf_indexes_skipped']]
            allMatches += [curMatch]


    return allMatches


#done
def BuildPhraseFromArray(allWords, iWord, leng, skipWords=None):  # list<string>,int,int,int,int
    if skipWords:
        wordList = [w for i,w in enumerate(allWords[iWord:iWord+leng]) if i+iWord not in skipWords]
        return u" ".join(wordList).strip()
    else:
        return u" ".join(allWords[iWord:iWord + leng]).strip()


#done
def CountWords(s):
    pattern = re.compile(ur"\S+")
    return len(re.findall(pattern, s))

#done
def IsStringMatch(orig, target, threshold):  # string,string,double,out double
    # if our threshold is 0, just compare them one to eachother.
    if threshold == 0:
        score = 0
        return (score, orig == target)

    # if equal
    if orig == target:
        score = 0
        return (score, True)

    # wait: if one is a substring of the other, then that can be considered an almost perfect match
    # check that the word is at least half as long as the bigger one
    if (orig.startswith(target) or target.startswith(orig)) and 1.0 * min(len(target), len(orig)) / max(len(target), len(orig)) > 0.5:
        score = -1
        return (score, True)

    # Otherwise, now we need to levenshtein.
    dist = ComputeLevenshteinDistance(orig, target)

    # Now get the actual threshold
    maxDist = mathy.ceil(len(orig) * threshold)

    score = dist

    # return if it is a matchup

    return (score, dist <= maxDist)


def cleanAbbrev(str):
    str = re.sub(ur'[\"״]',u'',str)
    str = re.sub(ur"[^א-ת]", u"", str).strip()
    str = u"".join([weighted_levenshtein.sofit_map.get(c,c) for c in str])
    return str


def isAbbrevMatch(curpos, abbrevText, unabbrevText, char_threshold, with_num_abbrevs=True):
    maxAbbrevLen = len(abbrevText)
    isMatch = False

    abbrevPatterns = [[],[1],[2],[3],[1,1],[2,1],[2,2]]
    for comboList in abbrevPatterns:

        numWordsCombined = sum(comboList)
        if curpos + maxAbbrevLen <= len(unabbrevText) + numWordsCombined:
            if maxAbbrevLen > numWordsCombined + 1:
                isMatch = True

                prev_combo_sum = 0
                for i_combo,currCombo in enumerate(comboList):
                    if len(unabbrevText[curpos+i_combo]) <= currCombo+1 or unabbrevText[curpos+i_combo][:currCombo+1] != abbrevText[prev_combo_sum:prev_combo_sum+currCombo+1]:
                        isMatch = False
                        break
                    prev_combo_sum += currCombo+1

                for igemaraword in xrange(curpos + len(comboList), curpos + maxAbbrevLen - numWordsCombined):
                    if unabbrevText[igemaraword][0] != abbrevText[igemaraword - curpos + numWordsCombined]:
                        isMatch = False
                        break
                if isMatch:
                    return isMatch, maxAbbrevLen - (1 + numWordsCombined), False

    #prepare text for hebrew check
    if with_num_abbrevs:
        if len(abbrevText) > 1:
            hebrew_num = u'{}"{}'.format(abbrevText[:-1],abbrevText[-1])
        else:
            hebrew_num = u"{}'".format(abbrevText)

        if is_hebrew_number(hebrew_num):
            potential_unabbrev_number = unabbrevText[curpos:curpos + len(abbrevText)]
            #print u"IS HEB NUM {} {} {} {}".format(hebrew_num, abbrevText,gematria(abbrevText),num2words(gematria(abbrevText), lang='he'))
            dist, isMatch = IsStringMatch(u' '.join(potential_unabbrev_number), num2words(gematria(abbrevText), lang='he'), char_threshold)
            if isMatch:
                #print u"NUMBER FOUND {} == {} DIST: {}".format(u' '.join(unabbrevText),num2words(gematria(abbrevText),lang='he'),dist)
                return isMatch, len(abbrevText) - 1, True

        #if still not matched, check if there's a prefix
        if len(hebrew_num) > 1 and is_hebrew_number(hebrew_num[1:]):
            prefix = hebrew_num[0]
            potential_unabbrev_number = unabbrevText[curpos:curpos + len(abbrevText) - 1]
            dist, isMatch = IsStringMatch(u' '.join(potential_unabbrev_number), prefix + num2words(gematria(abbrevText[1:]), lang='he'), char_threshold)
            if isMatch:
                #print u"PREFIX NUMBER FOUND {} == {} DIST: {}".format(u' '.join(unabbrevText), prefix + num2words(gematria(abbrevText[1:]),lang='he'),
                #                                               dist)
                return isMatch, len(abbrevText) - 2, True # to account for the prefix


    return isMatch, 0, False


def GetRashiBoundaries(allRashi, dwRashi, maxBound,boundaryFlexibility):  # List<RashiUnit>, int
    # often Rashis overlap - e.g., first שבועות שתים שהן ארבע and then שתים and then שהן ארבע
    # so we can't always close off the boundaries
    # but sometimes we want to

    # maxbound is the number of words on the amud
    startBound = 0
    endBound = maxBound - 1

    prevMatchedRashi = -1
    nextMatchedRashi = len(allRashi)

    # Okay, look as much up as you can from iRashi to find the start bound

    for iRashi in xrange(dwRashi - 1, -1, -1):
        if allRashi[iRashi].startWord == -1:
            continue
        prevMatchedRashi = iRashi
        # // Okay, this is our closest one on top that has a value
        # // allow it to overlap (changed to not allow overlap. you can get overlap with boundaryFlexibility param)
        startBound = allRashi[iRashi].endWord + 1
        break

    # // Second part, look down as much as possible to find the end bound
    for iRashi in xrange(dwRashi + 1, len(allRashi)):
        if allRashi[iRashi].startWord == -1 or allRashi[iRashi].startWord < startBound: #added startWord < startBound condition to avoid getting endBound which might be before startBound in the case when rashis matched out of order
            continue
        # // Okay, this is the closest one below that has a value
        # // our end bound will be the startword - 1.

        nextMatchedRashi = iRashi

        # DONT allow it to overlap
        endBound = allRashi[iRashi].startWord - 1

        break

    # Done!
    startBound = startBound - boundaryFlexibility if startBound - boundaryFlexibility >= 0 else 0
    endBound = endBound + boundaryFlexibility if endBound + boundaryFlexibility < maxBound else maxBound-1
    return startBound, endBound, prevMatchedRashi, nextMatchedRashi


def CleanText(curLine):  # string
    return re.sub(ur"</?[^>]+>", u"", curLine).strip()


def ComputeLevenshteinDistanceByWord(s, t):  # s and t are strings
    global fullWordValue
    # we take it word by word, each word can be, at most, the value of a full word

    words1 = s.split(' ')
    words2 = t.split(' ')

    totaldistance = 0

    for i in xrange(len(words1)):
        if i >= len(words2):
            totaldistance += fullWordValue
        else:
            # if equal, no distance
            if s == t:
                continue

            # wait: if one is a substring of the other, then that can be considered an almost perfect match
            # note: we changed this from the original c# code which was if (s.StartsWith(t) || t.StartsWith(s))
            if s.startswith(t) or t.startswith(s):
                totaldistance += 0.5

            totaldistance += min(ComputeLevenshteinDistance(words1[i], words2[i]), fullWordValue)

    return totaldistance

def ComputeLevenshteinDistance(s, t):
    return weighted_levenshtein.calculate(s, t, normalize=False)


def InitializeHashTables():
    global pregeneratedKWordValues, pregeneratedKMultiwordValues
    # Populate the pregenerated K values for the polynomial hash calculation
    pregeneratedKWordValues = [GetPolynomialKValueReal(i, kForWordHash) for i in xrange(NumPregeneratedValues)]
    # pregenerated K values for the multi word
    # these need to go from higher to lower, for the rolling algorithm
    # and we know that it will always be exactly 4
    pregeneratedKMultiwordValues = [GetPolynomialKValueReal(3 - i, kForMultiWordHash) for i in xrange(4)]


def CalculateHashes(allwords):  # input list
    return [GetWordSignature(w) for w in allwords]


alefint = ord(u"א")

def GetWordSignature(word):
    # make sure there is nothing but letters
    word = re.sub(ur"[^א-ת]", u"", word)
    word = Get2LetterForm(word)

    hash = 0
    for i, char in enumerate(word):
        chval = ord(char)
        chval = chval - alefint + 1
        hash += (chval * GetPolynomialKWordValue(i))

    return hash


def GetPolynomialKMultiWordValue(pos):
    global kForWordHash, NumPregeneratedValues, pregeneratedKMultiwordValues
    if pos < NumPregeneratedValues:
        return pregeneratedKMultiwordValues[pos]

    return GetPolynomialKValueReal(pos, kForMultiWordHash)


def GetPolynomialKWordValue(pos):
    global kForWordHash, NumPregeneratedValues, pregeneratedKWordValues
    if (pos < NumPregeneratedValues):
        return pregeneratedKWordValues[pos]

    return GetPolynomialKValueReal(pos, kForWordHash)


def GetPolynomialKValueReal(pos, k):
    # assuming that k is 41
    return k ** pos


# Merge into util.py?
_sofit_transx_table = {
    1498: u'\u05db',
    1501: u'\u05de',
    1503: u'\u05e0',
    1507: u'\u05e4',
    1509: u'\u05e6'
}

def Get2LetterForm(stringy):
    if stringy == u"ר":
        return u"רב"

    if len(stringy) < 3:
        return stringy

    # take a word, and keep only the two most infrequent letters
    stringy = stringy.translate(_sofit_transx_table)
    freqchart = [(lettersInOrderOfFrequency.index(tempchar), i) for i, tempchar in enumerate(stringy)]

    # sort it descending, so the higher they are the more rare they are
    freqchart.sort(key=lambda freq: -freq[0])
    letter1 = freqchart[0][1]
    letter2 = freqchart[1][1]
    # now put those two most frequent letters in order according to where they are in the words
    return u"{}{}".format(stringy[letter1], stringy[letter2]) if letter1 < letter2 else u"{}{}".format(stringy[letter2],
                                                                                                    stringy[letter1])

def is_hebrew_number(str):
    matches = regex.findall(hebrew_number_regex(), str)
    if len(matches) == 0:
        return False
    return matches[0] == str


def hebrew_number_regex():
    """
    Regular expression component to capture a number expressed in Hebrew letters
    :return string:
    \p{Hebrew} ~= [\u05d0–\u05ea]
    """
    rx =  ur"""                                    # 1 of 3 styles:
    ((?=[\u05d0-\u05ea]+(?:"|\u05f4|'')[\u05d0-\u05ea])    # (1: ") Lookahead:  At least one letter, followed by double-quote, two single quotes, or gershayim, followed by  one letter
            \u05ea*(?:"|\u05f4|'')?				    # Many Tavs (400), maybe dbl quote
            [\u05e7-\u05ea]?(?:"|\u05f4|'')?	    # One or zero kuf-tav (100-400), maybe dbl quote
            [\u05d8-\u05e6]?(?:"|\u05f4|'')?	    # One or zero tet-tzaddi (9-90), maybe dbl quote
            [\u05d0-\u05d8]?					    # One or zero alef-tet (1-9)															#
        |[\u05d0-\u05ea]['\u05f3]					# (2: ') single letter, followed by a single quote or geresh
        |(?=[\u05d0-\u05ea])					    # (3: no punc) Lookahead: at least one Hebrew letter
            \u05ea*								    # Many Tavs (400)
            [\u05e7-\u05ea]?					    # One or zero kuf-tav (100-400)
            [\u05d8-\u05e6]?					    # One or zero tet-tzaddi (9-90)
            [\u05d0-\u05d8]?					    # One or zero alef-tet (1-9)
    )"""

    return regex.compile(rx, regex.VERBOSE)

def max_sesquence_sum(l):
    best = cur = 0
    curi = starti = besti = 0
    for ind, i in enumerate(l):
        if cur + i > 0:
            cur += i
        else:  # reset start position
            cur, curi = 0, ind + 1

        if cur > best:
            starti, besti, best = curi, ind + 1, cur
    return starti, besti, best
#if it can get this, it can get anything
#print isAbbrevMatch(0,u'בחוהמ',[u'בחול',u'המועד'])
#he = [u'י״א',u'י׳',u'א״י']
#for h in he:
#    print h, is_hebrew_number(h)