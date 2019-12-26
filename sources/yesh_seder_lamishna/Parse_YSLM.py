# encoding=utf-8
import sys
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
import django
django.setup()
from sefaria.model import *

from data_utilities.util import getGematria, convert_dict_to_array, ja_to_xml
from sources.functions import post_index, post_text, add_term, add_category
import codecs
import re

def make_gematria_list(letters_list):
    for index, letter in enumerate(letters_list):
        if len(letter) > 0:
            letters_list[index] = getGematria(letter) - 1
    return letters_list

def tag_text(text_to_tag):
    #get rid of weird spaces
    text_to_tag = u' '.join(text_to_tag.split())
    #put bold tags around @77-@00
    text_to_tag = re.sub(ur'@77[^@]*@00[^@]*@00|@77[^@]*@00', '<b>\g<0></b>', text_to_tag)
    #put bold tags from after @78-@00 and keep the @78 to split
    text_to_tag = re.sub(ur'@78([^@]*@00[^@]*@00|[^@]*@00)', '@78<b>\g<1></b>', text_to_tag)
    #put a break tag before @24 and bold tag around @24-@00
    text_to_tag = re.sub(ur'@24[^@]*@00', '<br><b>\g<0></b>', text_to_tag)
    #remove superflous tags
    text_to_tag = re.sub(ur'@77|@24|@44|@18|@00', '', text_to_tag)
    return text_to_tag

def break_into_masechtot(book):
    """
    :param unicode book:
    :return:
    """
    book = re.split(r'@11', book)
    book.pop(0)
    #remove introduction
    book.pop(0)
    return book

def break_into_perakim(masechtot):
    """
    :param dict masechtot:
    :return:
    """
    for key, masechet in masechtot.items():
        #make a list with all the perek letters
        perakim_list = re.findall(ur"@55\s*\u05e4\u05e8\u05e7\s*(\u05db[\u05d0-\u05d8]|\u05d9[\u05d0-\u05d8]|\u05d8[\u05d5\u05d6]|[\u05d0-\u05db])", masechet)
        #make a list with all the perek numbers
        gematria_list = make_gematria_list(perakim_list)
        #split the string of the entire masechet into a list of perakim
        masechtot[key] = re.split(r'@55', masechet)
        #get rid of the first item, which is just the masechet name
        masechtot[key].pop(0)
        #make a dict with the keys being the numbers of perakim and the value being the string of that perek
        masechet_dict = dict(zip(gematria_list, masechtot[key]))
        #convert our dict with each perek having a corresponding key into a list of perakim which will now be padded
        # and store it as the value for the key which is "masechet ___"
        masechtot[key] = convert_dict_to_array(masechet_dict)
        #substitute all the perek names with an empty string
        for index, perek in enumerate(masechtot[key]):
            if type(perek) == unicode:
                masechtot[key][index] = re.sub(ur"\s*\u05e4\u05e8\u05e7\s*[\u05d0-\u05db]+\s*", '', perek)
    return masechtot

def break_into_mishnayot(perakim):
    """
    :param: list perakim:
    :return:
    """
    for index, perek in enumerate(perakim):
        #check type,if string break into mishnayot
        if type(perek) == unicode:
            #make a list with all the mishna letters
            mishna_list = re.findall(ur"@66\s*(?:\u05de\u05e9\u05e0\u05d4\s*|\u05de[\"\u05f4])?(\u05d9[\u05d0-\u05d8]|\u05d8[\u05d5\u05d6]|[\u05d0-\u05d9])", perek)
            #make a list with all the mishna numbers
            gematria_list = make_gematria_list(mishna_list)
            #substitute all the mishna names with an empty string and keep the @66 for splitting
            perakim[index] = re.sub(ur"\s*@66\s*(?:\u05de\u05e9\u05e0\u05d4\s*|\u05de[\"\u05f4])?[\u05d0-\u05d9]+\s*", '@66', perek)
            #split the string of the entire perek into a list of mishnayot
            perakim[index] = re.split(r'@66', perek)
            #get rid of the first item which is just an empty list
            if len(perakim[index][0]) < 10:
                perakim[index].pop(0)
            #make a dict with the keys being the numbers of mishnayot and the value being the string of that mishna
            perek_dict = dict(zip(gematria_list, perakim[index]))
            #convert our dict with each mishna having a corresponding key into a list of mishnayot which will now be padded
            #and store it as the perek in the list of perakim
            if perek_dict:
                perakim[index] = convert_dict_to_array(perek_dict)
    return perakim

def break_into_comments(mishnayot):
    for index, mishna in enumerate(mishnayot):
        #check type, if string break into comments
        if type(mishna) == unicode:
            #split the string of the entire mishna into a list of comments
            mishnayot[index] = re.split(r'@17|@22|@75|@78', mishna)
            #clean empty comments
            mishnayot[index] = filter(lambda comment:len(comment)>10, mishnayot[index])
    return mishnayot


if __name__ == "__main__":
    with codecs.open(u'יש סדר למשנה .txt', 'r', 'utf-8') as file_obj:
        yslm_str = file_obj.read()

    #bold text that should be bolded and insert break tags
    yslm_str = tag_text(yslm_str)

    #break the text into masechtot
    yslm_masechtot = break_into_masechtot(yslm_str)  # depth 1

    #make a list of masechtot
    mishnah_indexes = library.get_indexes_in_category(u'Mishnah')
    mishnah_indexes = mishnah_indexes[:23]
    #put an introduction at the beginning
    #mishnah_indexes.insert(0, u'Introduction')
    #make a dict with the keys being the names of the masechtot and the values being the text of those masechtot
    yslm_dic = dict(zip(mishnah_indexes, yslm_masechtot))

    #break the text into perakim
    yslm = break_into_perakim(yslm_dic)  # depth 2

    #break the text into mishnayot
    for key, masechet in yslm.items():
        yslm[key] = break_into_mishnayot(masechet)
    # depth 3 ^

    #break the text into comments
    for masechet in yslm:
        for index, perek in enumerate(yslm[masechet]):
            yslm[masechet][index] = break_into_comments(perek)
    #depth 4 ^

    mishnah_indexes = library.get_indexes_in_category(u'Mishnah', full_records = True)[:23]
    server = u'http://ezra.sandbox.sefaria.org'
    add_term(u'Yesh Seder LaMishnah', u'יש סדר למשנה', server = server)
    for seder in [u'Seder Zeraim', u'Seder Moed']:
        add_category(u'Yesh Seder LaMishnah', [u'Mishnah', u'Commentary', u'Yesh Seder LaMishnah'], server=server)

    for masechet_index in mishnah_indexes:
        english_title = u'Yesh Seder LaMishnah on {}'.format(masechet_index.get_title(u'en'))
        hebrew_title = u'{} {}'.format(u'יש סדר למשנה על', masechet_index.get_title(u'he'))

        ja = JaggedArrayNode()
        ja.add_primary_titles(english_title, hebrew_title)
        ja.add_structure([u'Perek', u'Mishnah', u'Comment'])
        ja.validate()
        index_dict = {
            u'title': english_title,
            u'base_text_titles': [masechet_index.get_title('en')],
            u'dependence': u'Commentary',
            u'base_text_mapping': u'many_to_one',
            u'collective_title': u'Yesh Seder LaMishnah',
            u'categories': [u'Mishnah',
                            u'Commentary',
                            #u'Seder Zeraim' if u'Seder Zeraim' in masechet_index.categories else u'Seder Moed',
                            u'Yesh Seder LaMishnah'],
            u'schema': ja.serialize(),
        }
        post_index(index_dict, server = server)
        version = {
            u'text': yslm[masechet_index.get_title(u'en')],
            u'language': u'he',
            u'versionTitle': u'Vilna, 1908-1909',
            u'versionSource': u'https://www.nli.org.il/he/books/NNL_ALEPH002016147/NLI'
        }
        post_text(english_title, version, server = server)



    #ja_to_xml(yslm[u'Mishnah Sheviit'],[u'perek', u'mishnah', u'comment'], u'Sheviit_test.xml')

