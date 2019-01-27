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
import math
import codecs
from functools import partial
from sources.functions import post_text, post_index, post_link, add_term, add_category
from data_utilities.util import getGematria, convert_dict_to_array, split_version, split_list
from data_utilities.ParseUtil import Description, directed_run_on_list, ParsedDocument, ParseState, ClashError

import django
django.setup()
from sefaria.model import *


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


def format_comment(comment):
    comment = re.sub(u'@\d{2}', u'', comment)

    # dh ends in "." or "כו"
    dh_reg = re.compile(u"^\u05d5?\u05db\u05d5'?$|\.$")

    # dh can be up to %30 of comment but no longer than 15 words.
    max_dh_len = min(int(math.ceil(0.3*len(comment.split()))), 15)

    comment_words = comment.split()
    for i, word in enumerate(comment_words[:max_dh_len], 1):
        if dh_reg.search(word):
            break
    else:
        i = 0

    # dh_reg = re.compile(u'''^([^\s]+\s){{,{}}}?(\u05d5?\u05db\u05d5'?|\.)(?= )'''.format(max_dh_len))
    # comment = dh_reg.sub(u'<b>\g<0></b>', comment)
    if i == 0:
        return comment
    else:
        return u'<b>{}</b>'.format(u' '.join(comment_words[:i])) + u' ' + u' '.join(comment_words[i:])


class Linker(object):
    def __init__(self, state):
        self.state = state
        self.link_list = []
        self.shulchan_ref = Ref("Shulchan Arukh, Orach Chayim")

    def clear_links(self):
        self.link_list = []

    def resolve_link(self, comment):
        siman = self.state.get_ref('Siman', one_indexed=True)
        seif = self.state.get_ref('Seif', one_indexed=True)
        comment_num = self.state.get_ref('Comment', one_indexed=True)

        ma_ref = Ref('Magen Avraham {}:{}'.format(siman, seif))
        mahatzit_ref_string = 'Machatzit HaShekel on Orach Chayim {}:{}:{}'.format(siman, seif, comment_num)
        self.link_list.append({
            'refs': [ma_ref.normal(), mahatzit_ref_string],
            'type': 'commentary',
            'auto': True,
            'generated_by': 'Machatzit HaShekel Parser'
        })

        magen_to_sa_links = ma_ref.linkset().refs_from(self.shulchan_ref, as_tuple=True)

        if len(magen_to_sa_links) > 1:
            print "Multiple links at {}".format(ma_ref.normal())
        elif len(magen_to_sa_links) < 1:
            print "No outgoing link for {}".format(ma_ref.normal())

        for ref_pair in magen_to_sa_links:
            if self.shulchan_ref.contains(ref_pair[0]):
                sref = ref_pair[0].normal()
            else:
                assert self.shulchan_ref.contains(ref_pair[1])
                sref = ref_pair[1].normal()

            self.link_list.append({
                'refs': [sref, mahatzit_ref_string],
                'type': 'super_commentary',
                'auto': True,
                'generated_by': 'Machatzit HaShekel Parser'
            })

    def test_base(self, comment, base_title, problem_set):
        siman = self.state.get_ref('Siman', one_indexed=True)
        seif = self.state.get_ref('Seif', one_indexed=True)
        my_ref = Ref("{} {}:{}".format(base_title, siman, seif))
        if my_ref.is_empty():
            problem_set.add(my_ref.normal())


current_state = ParseState()
split_comments = partial(expanded_split_comments, current_state)
split_seifim = SplitSeifim(current_state)
descriptors = [
    Description('Siman', split_chaps()),
    Description('Seif', split_seifim),
    Description('Comment', split_comments)
]
parser = ParsedDocument("Machatzit HaShekel on Orach Chayim", u"מחצית השקל על אורח חיים", descriptors)
parser.attach_state_tracker(current_state)
parser.parse_document(lines)
mahatzit_ja = parser.filter_ja(format_comment)
ja_node = parser.get_ja_node()
ja_node.toc_zoom = 2

my_index = {
    u'title': u'Machatzit HaShekel on Orach Chayim',
    u'categories': [u'Halakhah', u'Shulchan Arukh', u'Commentary', u'Machatzit HaShekel'],
    u'dependence': u'Commentary',
    u'collective_title': u'Machatzit HaShekel',
    u'base_text_titles': [u'Shulchan Arukh, Orach Chayim', u'Magen Avraham'],
    u'schema': ja_node.serialize()
}

full_version = {
    u"versionTitle": u"Maginei Eretz: Shulchan Aruch Orach Chaim, Lemberg, 1893",
    u"versionSource": u"http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002084080",
    u"language": u"he",
    u"text": mahatzit_ja,
}
version_list = split_version(full_version, 2)

linker = Linker(current_state)
parser.filter_ja(linker.resolve_link)
# parser.filter_ja(linker.resolve_link, "Magen Avraham", "commentary")
# parser.filter_ja(linker.resolve_link, "Shulchan Arukh, Orach Chayim", "super_commentary")

server = 'http://mahatzit.sandbox.sefaria.org'

add_term("Machatzit HaShekel", u"מחצית השקל", server=server)
add_category("Machatzit HaShekel", my_index[u'categories'], server=server)
post_index(my_index, server=server)
for v in version_list:
    post_text("Machatzit HaShekel on Orach Chayim", v, server=server)

for link_group in split_list(linker.link_list, 6):
    post_link(link_group, server=server)

# missing_magen = set()
# parser.filter_ja(linker.test_base, "Magen Avraham", missing_magen)
# for problem in sorted(missing_magen, key=lambda x: Ref(x).sections):
#     print problem
