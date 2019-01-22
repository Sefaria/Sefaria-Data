# encoding=utf-8

"""
vol. 2 starts at 242
vol. 3 starts at 417

Parsing strategy for Seifim:
Search for:
סק <סעיף>
at the beginning of of a line. Filter out punctuation, parentheses and @ marks. A space does not have to appear between
the סק and the Seif. Anything that is not marked at the beginning becomes part of Seif א.

Parsing strategy for Comments:
Here we need to take different strategies for vol. 1 and volumes 2 & 3. Vol. 1 is already split reasonably well. 2 & 3
need to be split. For that, we'll start with splitting on ":" characters.

Formatting:
We'll want to strip out all @ marks. We want to mark dh by looking ahead for כו or a period, but only in the first
several words. This heuristic could be an alternative comment parsing strategy for the comments of vol. 2 & 3.
"""

import re
import codecs
from functools import partial
from data_utilities.util import getGematria, convert_dict_to_array
from data_utilities.ParseUtil import Description, directed_run_on_list, ParsedDocument, ParseState, ClashError


chap_regex = re.compile(u"^@22(\u05e1\u05d9\u05de\u05df|\u05e1\u05d9'?)\s(?P<chap>[\u05d0-\u05ea\"]{1,5})$")

with codecs.open('Mahatzit.txt', 'r', 'utf-8') as fp:
    lines = fp.readlines()


def get_chap_values():
    for line in lines:
        match = chap_regex.match(line)
        if match:
            yield getGematria(match.group('chap'))


def split_chaps():
    """
    Returns a function
    :return:
    """
    def resolver(text_line):
        match = chap_regex.match(text_line)
        if match:
            return getGematria(match.group('chap'))
        else:
            return False
    return directed_run_on_list(resolver, include_matches=False, one_indexed=True)


class SplitSeifim(object):
    def __init__(self, parsing_state):
        self._state = parsing_state

    def get_siman(self):
        return self._state.get_ref("Siman", one_indexed=True)

    @staticmethod
    def is_new_seif(comment):
        first_words = u' '.join(comment.split()[:4])
        first_words = re.sub(u'[^\u05d0-\u05ea\s!]', u'', first_words)
        match = re.search(u'(^|\s)\u05e1\u05e7\s?(?P<seif>[\u05d0-\u05ea]{1,3})\s', first_words)

        if not match:
            return False, -1
        else:
            return True, getGematria(match.group('seif'))

    def __call__(self, comments):
        """
        just make a dict of lists. Just start appending to the list. Special case first seif.

        Point the dict to an updating list. If a seif gets hit twice raise a ClashError, unless this is Seif א.
        Use the ParseState to help with reporting in case of a clash
        :param comments:
        :return:
        """
        seif_mapping = {}
        seif_index, current_seif = 1, []
        max_seif = seif_index
        seif_mapping[seif_index] = current_seif

        for comment in comments:
            is_new, seif_index = self.is_new_seif(comment)

            if is_new:
                assert seif_index >= 1

                if seif_index in seif_mapping:
                    # Don't report on 1 unless we know that we've gone beyond the first seif
                    if seif_index > 1 or max_seif > 1:
                        print u"Seif {} appeared twice in Siman {}".format(seif_index, self.get_siman())
                    current_seif = seif_mapping[seif_index]

                else:
                    if seif_index < max_seif:
                        print u"Seif {} appeared after {} in Siman {}".format(seif_index, max_seif, self.get_siman())
                    else:
                        max_seif = seif_index

                    current_seif = []
                    seif_mapping[seif_index] = current_seif
            current_seif.append(comment)
        return convert_dict_to_array(seif_mapping)[1:]


def expanded_split_comments(parse_state, comment_list):
    cur_siman = parse_state.get_ref('Siman', one_indexed=True)
    cur_seif = parse_state.get_ref('Seif', one_indexed=True)
    if cur_siman < 242:
        return comment_list
    if len(comment_list) > 1 and cur_seif > 1:
        print "Weird occurrence at {}:{}".format(cur_siman, cur_seif)
        conjoined = u' '.join(comment_list)
    else:
        try:
            conjoined = comment_list[0]
        except IndexError:
            return comment_list

    comment_list = re.split(u'(?<=:)\s', conjoined)
    return comment_list


current_state = ParseState()
split_comments = partial(expanded_split_comments, current_state)
split_seifim = SplitSeifim(current_state)
descriptors = [
    Description('Siman', split_chaps()),
    Description('Seif', split_seifim),
    Description('Comment', split_comments)
]
parser = ParsedDocument("Mahatzit HaShekel", u"מחצית השקל", descriptors)
parser.attach_state_tracker(current_state)
parser.parse_document(lines)
mahatzit_ja = parser.get_ja()
