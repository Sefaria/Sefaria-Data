# encoding=utf-8
import sys
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
import django
django.setup()
from sefaria.model import *

from sources.functions import post_index, post_text, add_term, add_category, post_link
from docx import Document
from data_utilities.util import convert_dict_to_array, getGematria
import re
import codecs


#return a list of the gematria of the letters -1 so that index 0 would be א
def make_gematria_list(letters_list):
    for index, letter in enumerate(letters_list):
        if len(letter) > 0:
            letters_list[index] = getGematria(letter) - 1
    return letters_list

def bold_text(text):
    text = re.sub(r'@03|@66', '<b>', text)
    text = re.sub(r'@04', '</b>', text)
    return text

def insert_brackets(text_to_bracket):
    text_to_bracket = re.sub(r'(@08)\s*(\u05d0\u05d5\u05ea\s*[\u05d0-\u05ea]+)', u'\g<1>[\g<2>] ', text_to_bracket)
    return text_to_bracket

def break_into_simanim(text):
    # make a list with all the siman letters:
    simanim_list = re.findall(r'@01\s*\u05e1\u05d9\u05de\u05df\s*([\u05d0-\u05ea]+)', text)
    # make a list with all the siman numbers
    gematria_list = make_gematria_list(simanim_list)
    # split the string of the entire text into a list of simanim
    er_simanim = re.split(r'@01\s*\u05e1\u05d9\u05de\u05df\s*[\u05d0-\u05ea]+\s*@02', text)
    #er_simanim = re.split(r'@01', text)
    er_simanim.pop(0)
    # make a dict with the keys being the numbers of simanim and the value being the string of that siman
    simanim_dict = dict(zip(gematria_list, er_simanim))
    # convert our dict with each siman having a corresponding key into a list of simanim which will now be padded
    er_simanim = convert_dict_to_array(simanim_dict)
    return er_simanim

def break_into_seifim(simanim):
    for index, siman in enumerate(simanim):
        if siman:
            # make a list with all the seif letters:
            seifim_list = re.findall(r'@07\s*\u05e1\u05e2\u05d9\u05e3\s*([\u05d0-\u05ea]+)', siman)
            # make a list with all the seif numbers:
            gematria_list = make_gematria_list(seifim_list)
            for i, gematria in enumerate(gematria_list):
                gematria_list[i]+=1
            simanim[index] = re.split(r'@07', siman)
            if not simanim[index][0]:
                simanim[index].pop(0)
            else:
                gematria_list.insert(0, 0)
            # if theres only one seif in the siman, no indication and gematria list will just be one 0. change it to 1
            if len(gematria_list) == 1 and gematria_list[0] == 0:
                gematria_list[0] += 1
            # make a dict with the keys being the numbers of seifim and the value being the string of that seif
            seifim_dict = dict(zip(gematria_list, simanim[index]))
            # convert our dict with each seif having a corresponding key into a list of seifim which will now be padded
            simanim[index] = convert_dict_to_array(seifim_dict)
    return simanim

def break_into_letters(er):
    for index, siman in enumerate(er):
        for i, seif in enumerate(siman):
            if seif:
                er[index][i] = re.split(r'@08', seif)
                er[index][i].pop(0)
    return er

def depth_2(old_er):
    new_er, links = [[]], [[]]
    for index, siman in enumerate(old_er):
        for i, seif in enumerate(siman):
            for n, letter in enumerate(seif):
                new_er[index].append(letter)
                if not i == 0:
                    links[index].append(f'{index+1}:{i}')
                else:
                    links[index].append('unlinked')
        new_er.append([])
        links.append([])
    return new_er, links

def link_obvious(links):
    fixed = 0
    for index, siman in enumerate(links):
        if siman and index > 133:
            if siman[0] == 'unlinked':
                for i, link in enumerate(siman):
                    # if first actual link is seif 1 or 2, put unlinked before that into seif 1
                    if not link == 'unlinked' and int(link[-1]) < 3:
                        for n in range(0, i):
                            links[index][n] = f'{index+1}:1'
                        break
                    elif not link == 'unlinked':
                        break




if __name__ == "__main__":
    er_doc = Document('{}.docx'.format('אליה רבה'))
    er_list = []
    for para in er_doc.paragraphs:
        er_list.append(para.text)

    # convert the list into a string
    er_string = ''.join(er_list)
    er_string = re.sub(r'>FJ<', '', er_string)


    # bold text
    er_string = bold_text(er_string)

    # bracket the אות א etc
    er_string = insert_brackets(er_string)

    # simanim from 0-
    er_simanim = break_into_simanim(er_string)

    # seifim from 1- (0 would mean unlinked comments)
    er_seifim = break_into_seifim(er_simanim)

    er = break_into_letters(er_seifim)

    # convert to depth 2 while keeping track of linking
    er, indexes = depth_2(er)

    # put unlinked that are followed by seif 1 or 2 into seif 1
    link_obvious(indexes)

    # remove links for comments on levush kadishin
    for i in range(8, 19):
        indexes[131].pop(8)

    # produce links and report of unlinked comments
    unlinked_comments = []
    unlinked_indexes = []
    links = []
    for index, siman in enumerate(indexes):
        for i, link in enumerate(siman):
            if link == 'unlinked':
                unlinked_indexes.append(index+1)
                unlinked_comments.append(er[index][i])
            else:
                match = {
                    'refs': [
                        f'Eliyah Rabbah on Shulchan Arukh, Orach Chayim {index+1}:{i+1}',
                        f'Shulchan Arukh, Orach Chayim {link}'
                    ],
                    'auto': True,
                    'generated_by': 'Parse_ER',
                    'type': 'commentary',
                }
                links.append(match)

    """
    with open('Unlinked Eliyah Rabbah.txt', 'w') as er_unlinked:
        for index, comment in enumerate(unlinked_comments):
            er_unlinked.write(str(unlinked_indexes[index]))
            er_unlinked.write('\n')
            er_unlinked.write(comment)
            er_unlinked.write('\n')
    """


    server = 'https://eliyah-rabbah.cauldron.sefaria.org'
    erh = 'אליה רבה'
    add_term('Eliyah Rabbah', erh, server = server)
    add_category('Eliyah Rabbah',['Halakhah', 'Shulchan Arukh', 'Commentary', 'Eliyah Rabbah'], server = server)

    english_title = 'Eliyah Rabbah on Shulchan Arukh, Orach Chayim'
    hebrew_title = 'אליה רבה על שלחן ערוך אורח חיים'

    ja = JaggedArrayNode()
    ja.add_primary_titles(english_title, hebrew_title)
    ja.add_structure(['Siman', 'Seif Katan'], address_types=[u'Siman', u'Integer'])
    ja.validate()

    index_dict = {
        'title': english_title,
        'base_text_titles': ['Shulchan Arukh, Orach Chayim'],
        'dependence': 'Commentary',
        'collective_title': 'Eliyah Rabbah',
        'categories': [
            'Halakhah',
            'Shulchan Arukh',
            'Commentary',
            'Eliyah Rabbah'
        ],
        'schema': ja.serialize(),
    }

    post_index(index_dict, server=server)

    version = {
        'text': er,
        'language': 'he',
        'versionTitle': 'Eliya Rabba, Sulzbach 1757',
        'versionSource': 'https://www.nli.org.il/he/books/NNL_ALEPH002086789/NLI',
    }

    post_text(english_title, version, server=server)

    with codecs.open('Manual links.txt', 'r', 'utf-8') as file_obj:
        manual_links_str =  file_obj.read()

    manual_links = re.split(r'\n', manual_links_str)

    for item in manual_links:
        match = {
            'refs': [
                f'Eliyah Rabbah on Shulchan Arukh, Orach Chayim {item[:5]}',
                f'Shulchan Arukh, Orach Chayim {item[6:]}'
            ],
            'auto': True,
            'generated_by': 'Parse_ER - Manual Links',
            'type': 'commentary',
        }
        links.append(match)

    #286:10 - 286:3
    match = {
        'refs': [
            'Eliyah Rabbah on Shulchan Arukh, Orach Chayim 286:10',
            'Shulchan Arukh, Orach Chayim 286:3'
        ],
        'auto': True,
        'generated_by': 'Parse_ER - Manual Links',
        'type': 'commentary',
    }
    links.append(match)

    post_link(links, server=server)
