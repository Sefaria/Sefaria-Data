# encoding=utf-8
import sys
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
import django
django.setup()
from sefaria.model import *

from docx import Document
from data_utilities.util import convert_dict_to_array, ja_to_xml
from sources.yesh_seder_lamishna.Parse_YSLM import make_gematria_list
import re

def break_into_masechtot(book):
    book = re.split(ur'@\s*\u05de\u05e1\u05db\u05ea\s*[\u05d0-\u05ea]+\s*(?:[\u05d0-\u05ea]+)?', book)
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
        if perek:
            # make a list with all the mishna letters
            mishna_list = re.findall(ur'@\s*\u05de\u05e9\u05e0\u05d4\s*([\u05d0-\u05ea]+)', perek)
            # make a list with all the mishna numbers
            gematria_list = make_gematria_list(mishna_list)
            # split the string of the entire perek into a list of mishnayot
            perakim[index] = re.split(ur'@\s*\u05de\u05e9\u05e0\u05d4\s*[\u05d0-\u05ea]', perek)
            # get rid of the first item which is just an empty list (or a letter from mishna/perek)
            perakim[index].pop(0)
            # make a dict with the keys being the numbers of mishnayot and the value being the string of that mishna
            perek_dict = dict(zip(gematria_list, perakim[index]))
            # convert our dict with each mishna having a corresponding key into a list of mishnayot which will now be padded
            # and store it as the perek in the list of perakim
            if perek_dict:
                perakim[index] = convert_dict_to_array(perek_dict)
    return perakim

if __name__ == "__main__":
    rom_doc = Document(u'Rashash on Mishnah.docx')
    rom_list = []
    during_bold = False
    # go through entire book and put every run into the list, bolding what needs to be bolded
    for para in rom_doc.paragraphs:
        # put an @ before every paragraph, to be used later for splitting the document
        rom_list.append(u'@')
        for run in para.runs:
            if type(run.text) == unicode:
                # if this is the first bold word insert a starting bold tag
                if not during_bold and run.bold:
                    rom_list.append(u'<b>{}'.format(run.text))
                    during_bold = True
                # if this is the first non-bold word after a bold word insert an ending bold tag
                elif during_bold and not run.bold:
                    rom_list.append(u'</b>{}'.format(run.text))
                    during_bold = False
                else:
                    rom_list.append(run.text)
            else:
                rom_list.append(run.text)
    # convert the list into a string
    rom_string = u''.join(rom_list)

    # break the text into masechtot
    rom_masechtot = break_into_masechtot(rom_string)

    # make a list of masechtot
    mishnah_indexes = library.get_indexes_in_category(u'Mishnah')

    # make a dict with the keys being the names of the masechtot and the values being the text of those masechtot
    rom_dic = dict(zip(mishnah_indexes, rom_masechtot))

    # break the text into perakim
    rom = break_into_perakim(rom_dic)

    # break the text into mishnayot
    for key, masechet in rom.items():
        rom[key] = break_into_mishnayot(masechet)


