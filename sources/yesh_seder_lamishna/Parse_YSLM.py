# encoding=utf-8
import sys
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
import django
django.setup()
from sefaria.model import *

from data_utilities.util import getGematria
import codecs
import re


def break_into_masechtot(book):
    """
    :param unicode book:
    :return:
    """
    book = re.split('@11', book)
    book.pop(0)
    return book

def break_into_perakim(masechtot):
    """
    :param dict masechtot:
    :return:
    """
    for key, masechet in masechtot.items():
        masechtot[key] = re.split('@55', masechet)
        masechtot[key].pop(0)
        for index in masechtot[key]:
            #regex for perek numbers, keep values and set to empty strings
            #use gematria to see what prakim there are
            #insert(index with no commentary, [])
    return masechtot

def break_into_mishnayot(perakim):
    """
    :param: list perakim:
    :return:
    """
    for index, perek in enumerate(perakim):
        #check type, if list do nothing, if string split
        perakim[index] = re.split('@66', perek)
        perakim[index].pop(0)
        #for mishna in perakim[index]
            # regex for mishna numbers, keep values and set to empty strings
            # use gematria to see what mishnayot there are
            # insert(index with no commentary, [])
    return perakim

if __name__ == "__main__":
    with codecs.open(u'יש סדר למשנה .txt', 'r', 'utf-8') as file_obj:
        yslm_str = file_obj.read()

    yslm_masechtot = break_into_masechtot(yslm_str)  # depth 1

    mishnah_indexes = library.get_indexes_in_category("Mishnah")
    mishnah_indexes = mishnah_indexes[0:23]
    mishnah_indexes.pop(7)
    mishnah_indexes.insert(0, u'Introduction')

    yslm_dic = dict(zip(yslm_masechtot, mishnah_indexes))

    yslm_masechtot_with_perakim = break_into_perakim(yslm_dic)  # depth 2

    for key, masechet in yslm_masechtot_with_perakim.values():
        yslm_masechtot_with_perakim[key] = break_into_mishnayot(masechet)
    # depth 3 ^
    print getGematria(u'ג')