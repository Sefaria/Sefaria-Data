# -*- coding: utf-8 -*-
"""
Some regular expressions for the Mishnah. Tip: Use https://www.branah.com/unicode-converter to convert hebrew
words to unicode for easier regex writing.


u'@00(?:\u05e4\u05e8\u05e7 |\u05e4)([\u05d0-\u05ea,"]{1,3})'
- Grabs a new chapter. Capture group 1 gives the chapter number as a hebrew character.


u'@22[\u50d0-\u05ea]{1,2}'
- Grabs a new Mishna


u'( )?@44[\u05d0-\u05ea,"]{1,3}\)'
- Finds the Yachin tags with an optional leading space
"""

import os
import sys
import re
import codecs
import json
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from data_utilities import util, sanity_checks
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from sources.local_settings import *
from sources import functions
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *


# get tractate list
tractates = library.get_indexes_in_category('Mishnah')


def jaggedarray_from_file(input_file, perek_tag, mishna_tag):
    """
    :param input_file: File to parse
    :param perek_tag: Used to identify the start of a new perek.
    :param mishna_tag: Identify next mishna.
    :return: A 2D jaggedArray to match Sefaria's format. Rough, will require more processing.
    """

    chapters, mishnayot, current = [], [], []
    found_first_chapter = False

    for line in input_file:

        # look for tags
        new_chapter, new_mishna = re.search(perek_tag, line), re.search(mishna_tag, line)

        # make sure perek and mishna don't appear on the same line
        if new_chapter and new_mishna:
            print 'Mishna starts on same line as chapter\n'
            print '{}\n\n'.format(new_chapter.group())
            input_file.close()
            sys.exit(1)

        # found chapter tag.
        if new_chapter:
            if found_first_chapter:
                if current != []:
                    mishnayot.append(u' '.join(current).lstrip())
                    current = []
                chapters.append(mishnayot)
                mishnayot = []
            else:
                found_first_chapter = True
            continue

        if found_first_chapter:
            if new_mishna:
                if current != []:
                    mishnayot.append(u' '.join(current).lstrip())
                current = [util.multiple_replace(line, {u'\n': u'', u'\r': u'', new_mishna.group(): u''})]

            else:
                current.append(util.multiple_replace(line, {u'\n': u'', }))
            # add next line

    else:
        mishnayot.append(u''.join(current).lstrip())
        chapters.append(mishnayot)

    return chapters


def get_cards_from_trello(list_name, board_json):
    """
    Trello can export a board as a JSON object. Use this function to grab the names of all the cards that
    belong to a certain list on the board.
    :param list_name: Name of the list that holds the cards of interest
    :param board_json: The exported JSON file from trello that relates to the board of interest
    :return: A list of all the cards on the specified Trello list.
    """

    board = json.loads(board_json.read())

    list_id = u''
    for column in board['lists']:
        if column['name'] == list_name:
            list_id = column['id']

    cards = []
    for card in board['cards']:
        if card['idList'] == list_id:
            cards.append(card['name'])

    return cards


def clean_list():
    """
    List of regular expressions to remove unnecessary tags
    """
    return [u'@11', u'@33', u'( )?@44([!?*])?[\u05d0-\u05ea"]{1,3}(\))?', u'@44\(שם\)',
            u'@44(\(|\))', u'@44 קנח', u'@44 ד\)', u'@55', u'@66', u'@77', u'@88', u'@99', u'@']


def upload(text, text_name):
    """
    Upload Mishnah tractate.
    :param text:  Jagged array like object of the tractate.
    :param text_name: name of the text - to be used for url derivation for upload
    """

    tractate = {
        "versionTitle": "Vilna Mishna",
        "versionSource": "http://www.daat.ac.il/encyclopedia/value.asp?id1=836",
        "language": "he",
        "text": text,
    }
    print 'uploading {}'.format(text_name)
    functions.post_text(text_name, tractate)


trello = open('trello_board.json')
tracs = get_cards_from_trello('Parse Mishnah', trello)
trello.close()
for trac in tracs:
    name = re.search(u'[\u05d0-\u05ea].+', trac)
    name = name.group().replace(u'משנה', u'משניות')
    infile = codecs.open(u'{}.txt'.format(name), 'r', 'utf-8')
    jagged = jaggedarray_from_file(infile, u'@00(?:\u05e4\u05e8\u05e7 |\u05e4)([\u05d0-\u05ea"]{1,3})',
                                   u'@22[\u05d0-\u05ea]{1,2}')
    parsed = util.clean_jagged_array(jagged, clean_list())
    infile.close()

    en_name = re.search(u'[a-zA-Z ]+', trac).group().rstrip()
    if en_name not in tractates:
        print '{} not a valid ref'.format(en_name)
        sys.exit(1)
    upload(parsed, en_name)

