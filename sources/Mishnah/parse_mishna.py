# -*- coding: utf-8 -*-

import os
import sys
import re
import codecs
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


input_file = codecs.open(u'משניות ברכות.txt', 'r', 'utf-8')
output_file = codecs.open(u'test.txt', 'w', 'utf-8')
jagged_array = jaggedarray_from_file(input_file, u'@00(?:פרק |פ)([א-ת,"]{1,3})', u'@22[א-ת]{1,2}')
jagged_array = util.clean_jagged_array(jagged_array, [u'@11', u'@33', u'( )?@44[א-ת,"]{1,3}\)', u'@66', u'@77',
                                                      u'@88', u'@99'])
util.jagged_array_to_file(output_file, jagged_array, [u'פרק ', u'משנה '])
input_file.close()
output_file.close()