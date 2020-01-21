# encoding=utf-8
import sys
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
import django
django.setup()
from sefaria.model import *

from sources.functions import post_link
from data_utilities.dibur_hamatchil_matcher import match_ref
from sources.R_Akiva_Eiger_on_Mishnah.Upload_RAEM import extract_and_split_dh
import re
try:
    import cPickle as pickle
except ImportError:  # python 3.x
    import pickle

def sort_comments(perek, perek_index):
    bartenura_comments = []
    index_bartenura_comments = []
    toyt_comments = []
    index_toyt_comments = []
    for mishna_index, mishna in enumerate(perek):
        for comment_index, comment in enumerate(mishna):
            # take the beginning of the comment
            beginning = comment[:15]
            # if this is a comment on bartenura
            if re.search(ur'\u05e8\u05e2?(?:\"|\u05f4)\u05d1', beginning):
                bartenura_comments.append(comment)
                index_bartenura_comments.append(u'{}:{}:{}'.format(perek_index+1, mishna_index+1, comment_index+1))
            # if this is a comment on toyt
            if re.search(ur'\u05ea\u05d5?\u05d9(?:\"|\u05f4)\u05d8', beginning):
                toyt_comments.append(comment)
                index_toyt_comments.append(u'{}:{}:{}'.format(perek_index+1, mishna_index+1, comment_index+1))
    return bartenura_comments, index_bartenura_comments, toyt_comments, index_toyt_comments

# extract dh from ROM comment
def dh_extract_method(comment):
    # take the beginning of the comment (until the </b>, וכו or the first period. whatever comes first)
    beginning = re.split(ur'\s*</b>|\s*\u05d5?\u05db\u05d5(?:\'|\u05f3)|\.', comment)[0]
    # take from the ד״ה by splitting and taking the text after it
    dh = re.split(ur'\u05d3(?:\"|\u05f4)\u05d4\s*', beginning)[-1]  # take index [-1] (instead of 1, just in case), but less readable than the second index
    return dh



if __name__ == "__main__":
    with open('rom.p', 'rb') as fp:
        rom = pickle.load(fp)

    links = []

    for masechet in rom:
        for perek_index, perek in enumerate(rom[masechet]):
            if perek:
                # sort the comments and save their indexes
                bartenura_comments, index_bartenura_comments, toyt_comments, index_toyt_comments = sort_comments(perek, perek_index)
                if bartenura_comments:
                    bartenura_matches = match_ref(Ref(u'Bartenura on {} {}'.format(masechet, perek_index + 1)).text('he'), bartenura_comments, extract_and_split_dh, dh_extract_method=dh_extract_method)
                if toyt_comments:
                    toyt_matches = match_ref(Ref(u'Tosafot Yom Tov on {} {}'.format(masechet, perek_index + 1)).text('he'), toyt_comments, extract_and_split_dh, dh_extract_method=dh_extract_method)

                for n, index in enumerate(index_bartenura_comments):
                    if bartenura_matches[u'matches'][n]:
                        link = {
                            u'refs': [
                                u'Rashash on {} {}'.format(masechet, index),
                                bartenura_matches[u'matches'][n].normal()
                            ],
                            u'auto': True,
                            u'generated_by': u'Link ROM',
                            u'type': u'commentary',
                        }
                        links.append(link)

                for n, index in enumerate(index_toyt_comments):
                    if toyt_matches[u'matches'][n]:
                        link = {
                            u'refs': [
                                u'Rashash on {} {}'.format(masechet, index),
                                toyt_matches[u'matches'][n].normal()
                            ],
                            u'auto': True,
                            u'generated_by': u'Link ROM',
                            u'type': u'commentary',
                        }
                        links.append(link)

    post_link(links, server=u'http://ezra.sandbox.sefaria.org')