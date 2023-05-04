# encoding=utf-8
import sys
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
import django
django.setup()
from sefaria.model import *

from sources.functions import post_link
from linking_utilities.dibur_hamatchil_matcher import match_ref
from sources.R_Akiva_Eiger_on_Mishnah.Upload_RAEM import extract_and_split_dh
import re
try:
    import cPickle as pickle
except ImportError:  # python 3.x
    import pickle

# make a list of all the comments in a perek on a specific perush (bartenura or toyt)
def extract_specific_comments(perek, perek_index, regex, index_list):
    list_of_comments = []
    for mishna_index, mishna in enumerate(perek):
        for comment_index, comment in enumerate(mishna):
            # take the beginning of the comment
            beginning = comment[:20]
            # if the beginning of this comment references what we are looking for (bartenura or toyt)
            if re.search(regex, beginning):
                list_of_comments.append(comment)
                index_list.append(u'{}:{}:{}'.format(perek_index + 1, mishna_index + 1, comment_index + 1))
    return list_of_comments

# extract dh from YSLM comment
def dh_extract_method(comment):
    #take the beginning of the comment (until the </b>, וכו or the first period. whatever comes first)
    comment_split = re.split(ur'</b>|\s?\u05d5?\u05db\u05d5|\.', comment)
    # capture the dh after ד״ה
    if re.search(ur'\u05d3(?:\"|\u05f4)\u05d4 (.*)', comment_split[0]):
        dh = re.search(ur'\u05d3(?:\"|\u05f4)\u05d4 (.*)', comment_split[0]).group(1)
    # if no ד״ה capture the dh after the bold
    elif re.search(ur'<b>(.*)', comment_split[0]):
        dh = re.search(ur'<b>(.*)', comment_split[0]).group(1)
    # if no bold or ד״ה then take the whole thing
    else:
        dh = comment_split[0]
    dh = re.sub(ur'<b>', u'', dh)
    return dh

if __name__ == "__main__":
    with open('yslm.p', 'rb') as fp:
        yslm = pickle.load(fp)

    links = []

    for masechet in yslm:
        for perek_index, perek in enumerate(yslm[masechet]):
            if perek:
                bartenura_index_list = []
                bartenura_comments_list = extract_specific_comments(perek, perek_index, ur'\u05e8(?:\"|\u05f4)\u05d1', bartenura_index_list)
                if bartenura_comments_list:
                    bartenura_matches = match_ref(Ref(u'Bartenura on {} {}'.format(masechet, perek_index+1)).text('he'), bartenura_comments_list, extract_and_split_dh, dh_extract_method=dh_extract_method,word_threshold=.5)
                toyt_index_list = []
                toyt_comments_list = extract_specific_comments(perek, perek_index, ur'\u05ea\u05d5?\u05d9(?:\"|\u05f4)\u05d8', toyt_index_list)
                if toyt_comments_list:
                    toyt_matches = match_ref(Ref(u'Tosafot Yom Tov on {} {}'.format(masechet, perek_index+1)).text('he'), toyt_comments_list, extract_and_split_dh, dh_extract_method=dh_extract_method,word_threshold=.5)

                for n, index in enumerate(bartenura_index_list):
                    if bartenura_matches[u'matches'][n]:
                        link = {
                            u'refs': [
                                u'Yesh Seder LaMishnah on {} {}'.format(masechet, index),
                                u'{}'.format(bartenura_matches[u'matches'][n])
                            ],
                            u'auto': True,
                            u'generated_by': u'Link YSLM',
                            u'type': u'commentary',
                        }
                        links.append(link)

                for n, index in enumerate(toyt_index_list):
                    if toyt_matches[u'matches'][n]:
                        link = {
                            u'refs': [
                                u'Yesh Seder LaMishnah on {} {}'.format(masechet, index),
                                u'{}'.format(toyt_matches[u'matches'][n])
                            ],
                            u'auto': True,
                            u'generated_by': u'Link YSLM',
                            u'type': u'commentary',
                        }
                        links.append(link)

    post_link(links, server=u'http://ezra.sandbox.sefaria.org')


