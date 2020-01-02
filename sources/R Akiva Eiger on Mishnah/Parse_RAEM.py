# encoding=utf-8
import sys
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
import django
django.setup()
from sefaria.model import *
import time

from docx import Document
from data_utilities.util import convert_dict_to_array, ja_to_xml
from sources.functions import post_index, post_text, add_term, add_category
from sources.yesh_seder_lamishna.Parse_YSLM import make_gematria_list
import re
#import copy

def insert_break_tags(text_to_break):
    text_to_break = re.sub(ur'(:)\s*@\s*(<b>)', u'\g<1><br>\g<2>', text_to_break)
    return text_to_break

def insert_brackets(text_to_bracket):
    text_to_bracket = re.sub(ur'(@)\s*(\u05d0\u05d5\u05ea\s*[\u05d0-\u05ea]+)', u'\g<1>[\g<2>]', text_to_bracket)
    return text_to_bracket


def break_into_masechtot(book):
    book = re.split(ur'@\s*\u05de\u05e1\u05db\u05ea\s*[\u05d0-\u05ea]+', book)
    book.pop(0)
    return book


def break_into_perakim(masechtot):
    for key, masechet in masechtot.items():
        # make a list with all the perek letters
        perakim_list = re.findall(ur'@\s*\u05e4\u05e8\u05e7\s*([\u05d0-\u05ea]+)', masechet)
        # make a list with all the perek numbers
        gematria_list = make_gematria_list(perakim_list)
        # split the string of the entire masechet into a list of perakim
        masechtot[key] = re.split(ur'@\s*\u05e4\u05e8\u05e7\s*[\u05d0-\u05ea]', masechet)
        masechtot[key].pop(0)
        # make a dict with the keys being the numbers of perakim and the value being the string of that perek
        masechet_dict = dict(zip(gematria_list, masechtot[key]))
        # convert our dict with each perek having a corresponding key into a list of perakim which will now be padded
        # and store it as the value for the key which is "masechet ___"
        masechtot[key] = convert_dict_to_array(masechet_dict)
    return masechtot


def break_into_mishnayot(perakim):
    for index, perek in enumerate(perakim):
        # check type,if unicode break into mishnayot
        if type(perek) == unicode:
            # make a list with all the mishna letters
            mishna_list = re.findall(ur'@\s*\u05de\u05e9\u05e0\u05d4\s*([\u05d0-\u05ea]+)', perek)
            # make a list with all the mishna numbers
            gematria_list = make_gematria_list(mishna_list)
            # split the string of the entire perek into a list of mishnayot
            perakim[index] = re.split(ur'@\s*\u05de\u05e9\u05e0\u05d4\s*[\u05d0-\u05ea]', perek)
            # get rid of the first item which is just an empty list
            perakim[index].pop(0)
            # make a dict with the keys being the numbers of mishnayot and the value being the string of that mishna
            perek_dict = dict(zip(gematria_list, perakim[index]))
            # convert our dict with each mishna having a corresponding key into a list of mishnayot which will now be padded
            # and store it as the perek in the list of perakim
            if perek_dict:
                perakim[index] = convert_dict_to_array(perek_dict)
    return perakim


def break_mishnah_into_comments(mishnayot):
    for index, mishna in enumerate(mishnayot):
        # check type, if unicode break into comments
        if type(mishna) == unicode:
            # split the string of the entire mishna into a list of comments
            mishnayot[index] = re.split(ur'@\s*(?=\[\u05d0\u05d5\u05ea)', mishna)
            mishnayot[index].pop(0)
    return mishnayot

"""
def break_masechet_into_comments(masechtot):
    for masechet in masechtot:
        # get rid of all perek and mishnah numbers
        masechtot[masechet] = re.sub(ur'@\s*\u05e4\u05e8\u05e7\s*[\u05d0-\u05dc]+\s*', '', masechtot[masechet])
        masechtot[masechet] = re.sub(ur'@\s*\u05de\u05e9\u05e0\u05d4\s*[\u05d0-\u05dc]+\s*', '', masechtot[masechet])
        # make a list with all the comment letters
        comments_list = re.findall(ur'@\s*\u05d0\u05d5\u05ea\s*([\u05d0-\u05ea]+)', masechtot[masechet])
        # make a list with all the comments numbers
        gematria_list = make_gematria_list(comments_list)
        # split masechet into a list of comments
        masechtot[masechet] = re.split(ur'@\s*(?=\u05d0\u05d5\u05ea)', masechtot[masechet])
        # get rid of masechet name
        masechtot[masechet].pop(0)
        # make a dict with the keys being the numbers of comments and the value being the string of that comment
        masechet_dict = dict(zip(gematria_list, masechtot[masechet]))
        # convert our dict with each comment having a corresponding key into a list of comments which will now be in order
        # and store it as the value for the masechet
        masechtot[masechet] = convert_dict_to_array(masechet_dict)
"""

if __name__ == "__main__":
    start = time.time()
    raem = Document(u'{}.docx'.format(u'תוספות רבי עקיבא איגר על המשניות'))
    raem_list = []
    during_bold = False
    # go through entire book and put every run into the list, bolding what needs to be bolded
    for para in raem.paragraphs:
        # put an @ before every paragraph, to be used later for splitting the document
        raem_list.append(u'@')
        for run in para.runs:
            if type(run.text) == unicode:
                # if this is the first bold word insert a starting bold tag
                if not during_bold and run.bold:
                    raem_list.append(u'<b>{}'.format(run.text))
                    during_bold = True
                # if this is the first non-bold word after a bold word insert an ending bold tag
                elif during_bold and not run.bold:
                    raem_list.append(u'</b>{}'.format(run.text))
                    during_bold = False
                else:
                    raem_list.append(run.text)
            else:
                raem_list.append(run.text)
    # convert the list into a string
    raem_string = u''.join(raem_list)

    raem_string = insert_break_tags(raem_string)

    raem_string = insert_brackets(raem_string)

    # break the text into masechtot
    raem_masechtot = break_into_masechtot(raem_string)

    # make a list of masechtot
    mishnah_indexes = library.get_indexes_in_category(u'Mishnah')
    # pop out yadayim and kinnim, no commentary on it
    mishnah_indexes.pop(61)
    mishnah_indexes.pop(50)

    # make a dict with the keys being the names of the masechtot and the values being the text of those masechtot
    raem_dic = dict(zip(mishnah_indexes, raem_masechtot))

    # make another dict with the keys being the names of the masechtot and the values being the text of those masechtot
    # but use it to separate the text into comments instead of perakim
    #raem_comments = copy.deepcopy(raem_dic)
    #break_masechet_into_comments(raem_comments)

    # break the text into perakim
    raem = break_into_perakim(raem_dic)

    # break the text into mishnayot
    for key, masechet in raem.items():
        raem[key] = break_into_mishnayot(masechet)
    # depth 3 ^

    # break the text into comments
    for masechet in raem:
        for index, perek in enumerate(raem[masechet]):
            raem[masechet][index] = break_mishnah_into_comments(perek)
    # depth 4 ^

    # clean the @s
    """
    for masechet in raem_comments:
        for index, comment in enumerate(raem_comments[masechet]):
            if len(comment) > 0:
                raem_comments[masechet][index] = re.sub(ur'@', ' ', comment)
    """
    for masechet in raem:
        for perek in raem[masechet]:
            for mishna in perek:
                for index, comment in enumerate(mishna):
                    if len(comment) > 0:
                        mishna[index] = re.sub(ur'@', ' ', comment)

    # no yadayim and kinnim, no commentary on it
    mishnah_indexes = library.get_indexes_in_category(u'Mishnah', full_records = True)[:50]
    mishnah_indexes = mishnah_indexes + library.get_indexes_in_category(u'Mishnah', full_records = True)[51:61]
    mishnah_indexes = mishnah_indexes + library.get_indexes_in_category(u'Mishnah', full_records = True)[62:]

    server = u'http://ezra.sandbox.sefaria.org'
    add_term(u'Tosafot Rabbi Akiva Eiger', u'תוספות רבי עקיבא איגר', server = server)
    for seder in [u'Seder Zeraim', u'Seder Moed', u'Seder Nashim', u'Seder Nezikin', u'Seder Kodashim', u'Seder Tahorot']:
        add_category(seder, [u'Mishnah', u'Commentary', u'Tosafot Rabbi Akiva Eiger', seder], server=server)


    for masechet_index in mishnah_indexes:
        english_title = u'Tosafot Rabbi Akiva Eiger on {}'.format(masechet_index.get_title(u'en'))
        hebrew_title = u'{} {}'.format(u'תוספות רבי עקיבא איגר על', masechet_index.get_title(u'he'))

        ja = JaggedArrayNode()
        ja.add_primary_titles(english_title, hebrew_title)
        ja.add_structure([u'Chapter', u'Mishnah', u'Comment'])
        ja.validate()

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
        }
        post_index(index_dict, server = server)
        version = {
            u'text': raem[masechet_index.get_title(u'en')],
            u'language': u'he',
            u'versionTitle': u'Vilna, 1908-1909',
            u'versionSource': u'https://www.nli.org.il/he/books/NNL_ALEPH002016147/NLI'
        }
        post_text(english_title, version, server = server)

    #add comment index form

    #ja_to_xml(raem_comments[u'Mishnah Sheviit'], [u'perek', u'mishnah', u'comment'], u'Sheviit_comments_test.xml')

    end = time.time()
    print end-start

