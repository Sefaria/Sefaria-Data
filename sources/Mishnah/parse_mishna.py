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
from data_utilities import util
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
                chapters.append(mishnayot)
                mishnayot = []
            else:
                found_first_chapter = True
            continue

        if found_first_chapter:
            if new_mishna:
                if current != []:
                    mishnayot.append(u' '.join(current).lstrip())
                    current = [util.multiple_replace(line, {u'\n': u'', new_mishna.group(): u''})]

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
