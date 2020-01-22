# encoding=utf-8
import sys
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
import django
django.setup()
from sefaria.model import *

from sources.functions import post_index, post_text, add_term, add_category, post_link
from data_utilities.dibur_hamatchil_matcher import match_ref
from data_utilities.util import getGematria
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
            if re.search(ur'<b>(.*?)</b>', comment):
                beginning = re.search(ur'<b>(.*?)</b>', comment).group(1)
            # if no bold just take the whole comment
            else:
                beginning = comment
            # if the beginning of this comment references what we are looking for (bartenura or toyt)
            if re.search(regex, beginning):
                list_of_comments.append(comment)
                index_list.append(u'{}:{}:{}'.format(perek_index+1, mishna_index+1, comment_index+1))

            # if this comment is referencing an earlier one (שם ד״ה)
            elif re.search(ur'\u05e9\u05dd \u05d3(?:\"|\u05f4)\u05d4', beginning):
                base_not_found = True
                belongs = False
                temp_comment_index = comment_index
                while base_not_found:
                    temp_comment_index = temp_comment_index - 1
                    base_beginning = re.search(ur'<b>(.*?)</b>', mishna[temp_comment_index]).group(1)
                    # if no שם or בא״ד in the comment before then we found the base
                    if not re.search(ur'(?:\u05e9\u05dd \u05d3(?:\"|\u05f4)\u05d4|\u05d1\u05d0(?:\"|\u05f4)\u05d3)', base_beginning):
                        base_not_found = False
                        if re.search(regex, base_beginning):
                            belongs = True
                    # else keep looking back
                # bubble back up adding comments with a שם ד״ה but not including ones with בא״ד
                if belongs:
                    while temp_comment_index < comment_index:
                        temp_comment_index = temp_comment_index + 1
                        current_comment_beginning = re.search(ur'<b>(.*?)</b>', mishna[temp_comment_index]).group(1)
                        if re.search(ur'\u05e9\u05dd \u05d3(?:\"|\u05f4)\u05d4', current_comment_beginning):
                            list_of_comments.append(mishna[temp_comment_index])
                            index_list.append(u'{}:{}:{}'.format(perek_index+1, mishna_index+1, temp_comment_index+1))
                # else, doesnt belong, do nothing and go on to next comment
    return list_of_comments

# base tokenizer (for bartenura or toyt)
def extract_and_split_dh(comment):
    # if theres bold take everything bolded
    if re.search(ur'<b>(.*?)</b>', comment):
        dh = re.search(ur'<b>(.*?)</b>', comment).group(1)
    # if there isn't take until the first period
    elif re.search(ur'(.*?)\.', comment):
        dh = re.search(ur'(.*?)\.', comment).group(1)
    # if theres no period take the whole thing
    else:
        dh = comment
    dh_split = re.split(ur' ', dh)
    # remove וכו׳?
    return dh_split

# extract dh from RAEM comment
def dh_extract_method(comment):
    # capture the dh between ד״ה and .
    if re.search(ur'\u05d3(?:\"|\u05f4)\u05d4 (.*?)\.', comment):
        dh = re.search(ur'\u05d3(?:\"|\u05f4)\u05d4 (.*?)\.', comment).group(1)
    # if no ד״ה take until the first period
    else:
        dh = re.search(ur'(.*?)\.', comment).group(1)
    # remove the וכו׳ (if there is one...)
    dh = re.sub(ur' \u05d5?\u05db\u05d5(?:\'|\u05f3)', u'', dh)
    return dh

# collect all comments with בא״ד
def bod_index_list(text):
    bod_index_list = []
    for perek_index, perek in enumerate(text):
        for mishna_index, mishna in enumerate(perek):
            for comment_index, comment in enumerate(mishna):
                # take the beginning of the comment
                if re.search(ur'<b>(.*?)</b>', comment):
                    beginning = re.search(ur'<b>(.*?)</b>', comment).group(1)
                # if no bold just take the whole comment
                else:
                    beginning = comment
                if re.search(ur'\u05d1\u05d0(?:\"|\u05f4)\u05d3', beginning):
                    bod_index_list.append(u'{}:{}:{}'.format(perek_index + 1, mishna_index + 1, comment_index + 1))
    return bod_index_list

def get_comments(text, comment_indexes):
    comments = []
    for perek_index, perek in enumerate(text):
        for mishna_index, mishna in enumerate(perek):
            for comment_index, comment in enumerate(mishna):
                # take the comment title (אות א)
                if re.search(ur'\[(.*?)\]', comment):
                    if re.search(ur'\[(.*?)\]', comment).group(1) in comments:
                        comments.append(u'{} {}'.format(re.search(ur'\[(.*?)\]', comment).group(1), u'ב'))
                    else:
                        comments.append(re.search(ur'\[(.*?)\]', comment).group(1))
                else:
                    comments.append(re.search(ur'([^\s]+\s[^\s]+)', comment).group(1))
                # add the coordinates
                comment_indexes.append(u'{}:{}:{}'.format(perek_index + 1, mishna_index + 1, comment_index + 1))
    return comments



if __name__ == "__main__":
    with open('raem.p', 'rb') as fp:
        raem = pickle.load(fp)
    links = []
    links_helper_list = []
    comments = {}
    comments_indexes = {}

    # link with bartenura and tosfot yom tov
    for masechet in raem:
        #link perek by perek
        for perek_index, perek in enumerate(raem[masechet]):
            #list for specific index of comments in original perek mishna breakdown (i.e. p:m:c)
            bartenura_index_list = []
            bartenura_comments_list = extract_specific_comments(perek, perek_index, ur'\u05e8\u05e2?(?:\"|\u05f4)\u05d1', bartenura_index_list)
            bartenura_matches = match_ref(Ref(u'Bartenura on {} {}'.format(masechet, perek_index+1)).text('he'), bartenura_comments_list, extract_and_split_dh, dh_extract_method=dh_extract_method)
            toyt_index_list = []
            toyt_comments_list = extract_specific_comments(perek, perek_index, ur'\u05ea\u05d5?\u05d9(?:\"|\u05f4)\u05d8', toyt_index_list)
            toyt_matches = match_ref(Ref(u'Tosafot Yom Tov on {} {}'.format(masechet, perek_index+1)).text('he'), toyt_comments_list, extract_and_split_dh, dh_extract_method=dh_extract_method)

            for n, index in enumerate(bartenura_index_list):
                if bartenura_matches[u'matches'][n]:
                    link = {
                        u'refs': [
                            u'Tosafot Rabbi Akiva Eiger on {} {}'.format(masechet, index),
                            u'{}'.format(bartenura_matches[u'matches'][n])
                        ],
                        u'auto': True,
                        u'generated_by': u'Upload RAEM',
                        u'type': u'commentary',
                    }
                    links.append(link)
                    links_helper_list.append(link[u'refs'][0])

            for n, index in enumerate(toyt_index_list):
                if toyt_matches[u'matches'][n]:
                    link = {
                        u'refs': [
                            u'Tosafot Rabbi Akiva Eiger on {} {}'.format(masechet, index),
                            u'{}'.format(toyt_matches[u'matches'][n])
                        ],
                        u'auto': True,
                        u'generated_by': u'Upload RAEM',
                        u'type': u'commentary',
                    }
                    links.append(link)
                    links_helper_list.append(link[u'refs'][0])

        bod_indexes = bod_index_list(raem[masechet])
        for n, index in enumerate(bod_indexes):
            index_groups = re.search(ur'(\d+):(\d+):(\d+)', index)
            if u'Tosafot Rabbi Akiva Eiger on {} {}:{}:{}'.format(masechet, index_groups.group(1), index_groups.group(2), int(index_groups.group(3))-1) in links_helper_list:
                link = {
                    u'refs': [
                        u'Tosafot Rabbi Akiva Eiger on {} {}'.format(masechet, index),
                        links[links_helper_list.index(u'Tosafot Rabbi Akiva Eiger on {} {}:{}:{}'.format(masechet, index_groups.group(1), index_groups.group(2), int(index_groups.group(3))-1))][u'refs'][1]
                    ],
                    u'auto': True,
                    u'generated_by': u'Upload RAEM',
                    u'type': u'commentary',
                }
                links.append(link)
                links_helper_list.append(link[u'refs'][0])

    for masechet in raem:
        comment_indexes = []
        comments[masechet] = get_comments(raem[masechet], comment_indexes)
        comments_indexes[masechet] = comment_indexes

    # no yadayim and kinnim, no commentary on it
    mishnah_indexes = library.get_indexes_in_category(u'Mishnah', full_records=True)[:50]
    mishnah_indexes = mishnah_indexes + library.get_indexes_in_category(u'Mishnah', full_records=True)[51:61]
    mishnah_indexes = mishnah_indexes + library.get_indexes_in_category(u'Mishnah', full_records=True)[62:]

    server = u'http://ezra.sandbox.sefaria.org'
    add_term(u'Tosafot Rabbi Akiva Eiger', u'תוספות רבי עקיבא איגר', server=server)
    for seder in [u'Seder Zeraim', u'Seder Moed', u'Seder Nashim', u'Seder Nezikin', u'Seder Kodashim',
                  u'Seder Tahorot']:
        add_category(seder, [u'Mishnah', u'Commentary', u'Tosafot Rabbi Akiva Eiger', seder], server=server)


    for masechet_index in mishnah_indexes:
        english_title = u'Tosafot Rabbi Akiva Eiger on {}'.format(masechet_index.get_title(u'en'))
        hebrew_title = u'{} {}'.format(u'תוספות רבי עקיבא איגר על', masechet_index.get_title(u'he'))

        ja = JaggedArrayNode()
        ja.add_primary_titles(english_title, hebrew_title)
        ja.add_structure([u'Chapter', u'Mishnah', u'Comment'])
        ja.validate()

        scn = SchemaNode()
        
        for index, comment in enumerate(comments[masechet_index.get_title(u'en')]):
            amn_hebrew_title = comment
            amn_english_title = u'Letter {}'.format(getGematria(re.search(ur'[^\s]+\s([^\s]+)', comment).group(1)))
            amn = ArrayMapNode()
            amn.add_primary_titles(amn_english_title, amn_hebrew_title)
            amn.depth = 0
            amn.wholeRef = u'{} {}'.format(english_title, comments_indexes[masechet_index.get_title(u'en')][index])
            scn.append(amn)

        if u'Seder Zeraim' in masechet_index.categories:
            seder = u'Seder Zeraim'
        elif u'Seder Moed' in masechet_index.categories:
            seder = u'Seder Moed'
        elif u'Seder Nashim' in masechet_index.categories:
            seder = u'Seder Nashim'
        elif u'Seder Nezikin' in masechet_index.categories:
            seder = u'Seder Nezikin'
        elif u'Seder Kodashim' in masechet_index.categories:
            seder = u'Seder Kodashim'
        else:
            seder = u'Seder Tahorot'

        index_dict = {
            u'title': english_title,
            u'base_text_titles': [masechet_index.get_title('en')],
            u'dependence': u'Commentary',
            u'base_text_mapping': u'many_to_one',
            u'collective_title': u'Tosafot Rabbi Akiva Eiger',
            u'categories': [u'Mishnah',
                            u'Commentary',
                            u'Tosafot Rabbi Akiva Eiger',
                            seder],
            u'schema': ja.serialize(),
            u'alt_structs': {
                u'Letter': scn.serialize()
            }
        }
        post_index(index_dict, server=server)
        version = {
            u'text': raem[masechet_index.get_title(u'en')],
            u'language': u'he',
            u'versionTitle': u'Vilna, 1908-1909',
            u'versionSource': u'https://www.nli.org.il/he/books/NNL_ALEPH002016147/NLI'
        }
        post_text(english_title, version, server=server)
    post_link(links, server=server)


