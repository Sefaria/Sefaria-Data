# encoding=utf-8
import sys
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
import django
django.setup()
from sefaria.model import *
import time

from sources.functions import post_link
from linking_utilities.dibur_hamatchil_matcher import match_ref
import re
try:
    import cPickle as pickle
except ImportError:  # python 3.x
    import pickle

def sort_comments(daf, daf_index):
    talmud_comments = []
    index_talmud_comments = []
    tosafot_comments = []
    index_tosafot_comments = []
    rashi_comments = []
    index_rashi_comments = []
    for paragraph_index, paragraph in enumerate(daf):
        # take the beginning of the paragraph
        beginning = paragraph[:15]
        # if this is a comment on talmud (גמ׳ or גמרא or משנה or מתני׳)
        if re.search(ur'\u05d2\u05de(?:\'|\u05f3)|\u05d2\u05de\u05e8\u05d0|\u05de\u05e9\u05e0\u05d4|\u05de\u05ea\u05e0\u05d9(?:\'|\u05f3)', beginning):
            talmud_comments.append(paragraph)
            index_talmud_comments.append(u'{}{}:{}'.format(((daf_index + 2) / 2) if daf_index % 2 == 0 else ((daf_index + 1) / 2), u'a' if daf_index % 2 == 0 else u'b', paragraph_index+1))
        # if this is a comment on tosafot (תוס׳)
        elif re.search(ur'\u05ea\u05d5\u05e1(?:\'|\u05f3)', beginning):
            tosafot_comments.append(paragraph)
            index_tosafot_comments.append(u'{}{}:{}'.format(((daf_index + 2) / 2) if daf_index % 2 == 0 else ((daf_index + 1) / 2), u'a' if daf_index % 2 == 0 else u'b', paragraph_index+1))
        # if this is a comment on rashi (רש״י)
        elif re.search(ur'\u05e8\u05e9(?:\"|\u05f4)\u05d9', beginning):
            rashi_comments.append(paragraph)
            index_rashi_comments.append(u'{}{}:{}'.format(((daf_index + 2) / 2) if daf_index % 2 == 0 else ((daf_index + 1) / 2), u'a' if daf_index % 2 == 0 else u'b', paragraph_index+1))
    return talmud_comments, index_talmud_comments, tosafot_comments, index_tosafot_comments, rashi_comments, index_rashi_comments

def talmud_base_tokenizer(text):
    # remove any גמ׳ מתני׳ <b> or </b>
    text = re.sub(ur'\u05d2\u05de(?:\'|\u05f3)|\u05de\u05ea\u05e0\u05d9(?:\'|\u05f3)|<b>|</b>', u'', text)
    # split into separate words
    split_text = re.split(ur' ', text)
    # remove any words that are empty
    return_text = filter(lambda x: x != u'', split_text)
    return return_text

def rashi_tosafot_base_tokenizer(comment):
    dh = re.split(ur'\s*\u2013|\s*-|\.', comment)[0]
    split_dh = re.split(ur' ', dh)
    return_dh = filter(lambda x: x != u'', split_dh)
    return return_dh

def talmud_dh_extract(comment):
    # take until the period, comma, bold or וכו
    comment = re.split(ur'\.|,|\s*\u05d5?\u05db\u05d5|</b>', comment)
    # if the first one has a break tag in it (means its just a letter and break tags until the gemara)
    if re.search(ur'<br>', comment[0]):
        comment[0] = re.sub(ur'[\u05d0-\u05ea]+<br><br>', '', comment[0])
    # if the first one is just שם (maybe bold)
    if len(comment[0]) < 6 and re.search(ur'\u05e9\u05dd', comment[0]):
        comment.pop(0)
    # if the first one is just a title like משנה or גמ etc remove it
    if len(comment[0]) < 9:
        comment.pop(0)
    # if the next one is nothing because two split indicators were right next to each other
    if len(comment[0]) < 2:
        comment.pop(0)
    dh = comment[0]
    # remove unnecessary filler words or characters
    dh = re.sub(ur'<b>|</b>|\u05d2\u05de(?:\'|\u05f3)|\u05d2\u05de\u05e8\u05d0|\u05de\u05e9\u05e0\u05d4|\u05de\u05ea\u05e0\u05d9(?:\'|\u05f3)|\u05d5?\u05d6(?:\"|\u05f4)\u05dc\s*|\s*\u05e2\u05db(?:\"|\u05f4)\u05dc', u'', dh)
    return dh

def rashi_tosafot_dh_extract(comment):
    # take until the period, bold, וכו or וז״ל
    comment = re.split(ur'\.|\s*\u05d5?\u05db\u05d5|</b>|\s*\u05d5?\u05d6(?:\"|\u05f4)\u05dc', comment)
    # if the first one is just שם (maybe bold)
    if len(comment[0]) < 6 and re.search(ur'\u05e9\u05dd', comment[0]):
        comment.pop(0)
    beginning = comment[0]
    # take from the ד״ה by splitting and taking the text after it
    dh = re.split(ur'\u05d3(?:\"|\u05f4)\u05d4\s*', beginning)[-1] # take index [-1] (instead of 1, just in case), but less readable than the second index
    return dh

if __name__ == "__main__":
    start = time.time()
    with open('rs.p', 'rb') as fp:
        rs = pickle.load(fp)

    links = []
    base_links = []

    for masechet in rs:
        # link daf by daf
        for daf_index, daf in enumerate(rs[masechet]):
            if daf:
                # sort all the comments and save their indexes
                talmud_comments, index_talmud_comments, tosafot_comments, index_tosafot_comments, rashi_comments, index_rashi_comments = sort_comments(daf, daf_index)
                if talmud_comments:
                    talmud_matches = match_ref(Ref(u'{} {}{}'.format(masechet, ((daf_index + 2) / 2) if daf_index % 2 == 0 else ((daf_index + 1) / 2), u'a' if daf_index % 2 == 0 else u'b')).text('he', vtitle='William Davidson Edition - Aramaic'), talmud_comments, talmud_base_tokenizer, dh_extract_method=talmud_dh_extract)
                # and the tosafot on this daf exists
                if tosafot_comments and Ref(u'Tosafot on {} {}{}'.format(masechet, ((daf_index + 2) / 2) if daf_index % 2 == 0 else ((daf_index + 1) / 2), u'a' if daf_index % 2 == 0 else u'b')).text('he').text:
                    tosafot_matches = match_ref(Ref(u'Tosafot on {} {}{}'.format(masechet, ((daf_index + 2) / 2) if daf_index % 2 == 0 else ((daf_index + 1) / 2), u'a' if daf_index % 2 == 0 else u'b')).text('he'), tosafot_comments, rashi_tosafot_base_tokenizer, dh_extract_method=rashi_tosafot_dh_extract)
                if rashi_comments:
                    rashi_matches = match_ref(Ref(u'Rashi on {} {}{}'.format(masechet, ((daf_index + 2) / 2) if daf_index % 2 == 0 else ((daf_index + 1) / 2), u'a' if daf_index % 2 == 0 else u'b')).text('he'), rashi_comments, rashi_tosafot_base_tokenizer, dh_extract_method=rashi_tosafot_dh_extract)

                for n, index in enumerate(index_talmud_comments):
                    if talmud_matches[u'matches'][n]:
                        link = {
                            u'refs': [
                                u'Reshimot Shiurim on {} {}'.format(masechet, index),
                                u'{}'.format(talmud_matches[u'matches'][n])
                            ],
                            u'auto': True,
                            u'generated_by': u'Link RS',
                            u'type': u'commentary',
                        }
                        links.append(link)

                for n, index in enumerate(index_tosafot_comments):
                    if tosafot_matches[u'matches'][n]:
                        link = {
                            u'refs': [
                                u'Reshimot Shiurim on {} {}'.format(masechet, index),
                                u'{}'.format(tosafot_matches[u'matches'][n])
                            ],
                            u'auto': True,
                            u'generated_by': u'Link RS',
                            u'type': u'commentary',
                        }
                        links.append(link)
                        talmud_ref = re.search(ur'Tosafot\s*on\s*([a-zA-Z]+\s*[a-zA-Z]*\s*\d+[ab]:\d+)', tosafot_matches[u'matches'][n].normal()).group(1)
                        link = {
                            u'refs': [
                                u'Reshimot Shiurim on {} {}'.format(masechet, index),
                                talmud_ref
                            ],
                            u'auto': True,
                            u'generated_by': u'Link RS',
                            u'type': u'commentary',
                        }
                        base_links.append(link)


                for n, index in enumerate(index_rashi_comments):
                    if rashi_matches[u'matches'][n]:
                        link = {
                            u'refs': [
                                u'Reshimot Shiurim on {} {}'.format(masechet, index),
                                u'{}'.format(rashi_matches[u'matches'][n])
                            ],
                            u'auto': True,
                            u'generated_by': u'Link RS',
                            u'type': u'commentary',
                        }
                        links.append(link)
                        talmud_ref = re.search(ur'Rashi\s*on\s*([a-zA-Z]+\s*[a-zA-Z]*\s*\d+[ab]:\d+)', rashi_matches[u'matches'][n].normal()).group(1)
                        link = {
                            u'refs': [
                                u'Reshimot Shiurim on {} {}'.format(masechet, index),
                                talmud_ref
                            ],
                            u'auto': True,
                            u'generated_by': u'Link RS',
                            u'type': u'commentary',
                        }
                        base_links.append(link)
    end = time.time()
    print end - start

    post_link(base_links, server=u'http://ezra.sandbox.sefaria.org')

    end = time.time()
    print end - start
