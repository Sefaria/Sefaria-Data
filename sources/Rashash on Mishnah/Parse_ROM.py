# encoding=utf-8
import sys
import django
django.setup()
from sefaria.model import *
from docx import Document
from sources.yesh_seder_lamishna.Parse_YSLM import make_gematria_list
import re
from concurrent.futures import ThreadPoolExecutor
try:
    import cPickle as pickle
except ImportError:  # python 3.x
    import pickle

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

def break_into_comments(mishnayot):
    for index, mishna in enumerate(mishnayot):
        if mishna:
            # split the string of the entire mishna into a list of comments
            mishnayot[index] = re.split(ur'@', mishna)
            mishnayot[index].pop(0)
    return mishnayot

def post_index_and_version(index_version_tuple):
    server = u'http://ezra.sandbox.sefaria.org'
    index, version = index_version_tuple
    post_index(index, server = server)
    post_text(index[u'title'], version, server=server)


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

    rom_string = re.sub(ur'66', '', rom_string)

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

    # break the text into comments
    for masechet in rom:
        for index, perek in enumerate(rom[masechet]):
            rom[masechet][index] = break_into_comments(perek)

    with open('rom.p', 'wb') as fp:
        pickle.dump(rom, fp)

    mishnah_indexes = library.get_indexes_in_category(u'Mishnah', full_records=True)
    server = u'http://ezra.sandbox.sefaria.org'
    add_term(u'Rashash', u'רש״ש', server = server)
    for seder in [u'Seder Zeraim', u'Seder Moed', u'Seder Nashim', u'Seder Nezikin', u'Seder Kodashim', u'Seder Tahorot']:
        add_category(seder, [u'Mishnah', u'Commentary', u'Rashash', seder], server=server)

    index_list = []
    version_list = []
    for masechet_index in mishnah_indexes:
        english_title = u'Rashash on {}'.format(masechet_index.get_title(u'en'))
        hebrew_title = u'{} {}'.format(u'רש״ש על', masechet_index.get_title(u'he'))

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
            u'collective_title': u'Rashash',
            u'categories': [u'Mishnah',
                            u'Commentary',
                            u'Rashash',
                            seder],
            u'schema': ja.serialize(),
        }
        index_list.append(index_dict)
        #post_index(index_dict, server = server)
        version = {
            u'text': rom[masechet_index.get_title(u'en')],
            u'language': u'he',
            u'versionTitle': u'Vilna Edition',
            u'versionSource': u'https://www.nli.org.il/he/books/NNL_ALEPH001300957/NLI'
        }
        version_list.append(version)
        #post_text(english_title, version, server = server)

    upload_list = zip(index_list, version_list)

    with ThreadPoolExecutor(4) as executer:
        executer.map(post_index_and_version, upload_list)

