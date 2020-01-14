# encoding=utf-8
import sys
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
import django
django.setup()
from sefaria.model import *


from sources.functions import post_index, post_text, add_term, add_category
from data_utilities.util import getGematria, convert_dict_to_array
import codecs
import re


def make_index_list(dapim):
    index_list = []
    for index in dapim:
        info = re.search(ur'([\u05d0-\u05ea]+), ([\u05d0\u05d1])', index)
        daf = info.group(1)
        amud = info.group(2)
        if amud == u'א':
            index_list.append(((getGematria(daf) - 1) * 2) - 2)
        else: #amud b
            index_list.append(((getGematria(daf) - 1) * 2) - 1)
    return index_list


def break_into_amudim(masechtot):
    for masechet, text in masechtot.items():
        # make a list with all the daf indexes
        dapim_list = re.findall(ur'@([\u05d0-\u05ea]+, [\u05d0\u05d1])', text)
        # make a list of indexes with corresponding text
        index_list = make_index_list(dapim_list)
        # split the masechet into amudim
        masechtot[masechet] = re.split(ur'@[\u05d0-\u05ea]+, [\u05d0\u05d1]', text)
        masechtot[masechet].pop(0)
        # make a dict with the keys being the index of the amud and the text being the text of that amud
        dict_ = dict(zip(index_list, masechtot[masechet]))
        # convert our dict with each amud having a corresponding index into a list of amudim which will now be padded
        masechtot[masechet] = convert_dict_to_array(dict_)
        # add 2 empty lists at the beginning so daf .ב is at index 2
        masechtot[masechet].insert(0, [])
        masechtot[masechet].insert(0, [])

def break_into_paragraphs(amudim):
    for i, amud in enumerate(amudim):
        if amud:
            amudim[i] = re.split(ur'\n', amud)
            #if first paragraph is empty
            if not len(amudim[i][0]) > 0:
                amudim[i].pop(0)
    return amudim


if __name__ == "__main__":
    masechtot = [u'Berakhot', u'Yevamot', u'Bava Kamma', u'Bava Metzia']
    version_titles = [u'Reshimot Shiurim, Berakhot, New York, 2012', u'Reshimot Shiurim, Yevamot, New York, 2011', u'Reshimot Shiurim, Bava Kamma, New York, 1998', u'Reshimot Shiurim, Bava Metzia, New York, 2016']
    version_sources = [u'https://www.nli.org.il/he/books/NNL_ALEPH003482107/NLI', u'https://www.nli.org.il/he/books/NNL_ALEPH003364522/NLI', u'https://www.nli.org.il/he/books/NNL_ALEPH005051416/NLI', u'https://www.nli.org.il/he/books/NNL_ALEPH003969350/NLI']
    rs_str = u''
    for masechet in masechtot:
        rs_str = rs_str + u'masechet'
        with codecs.open(u'Reshimot Shiurim {}.txt'.format(masechet), 'r', 'utf-8') as file_obj:
            rs_str = rs_str + file_obj.read()

    rs_split = re.split(ur'masechet', rs_str)
    rs_split.pop(0)

    # make a dict with the keys being the names of the masechtot and the values being the text of those masechtot
    rs = dict(zip(masechtot, rs_split))

    break_into_amudim(rs)

    for masechet, amudim in rs.items():
        rs[masechet] = break_into_paragraphs(amudim)


    all_talmud_indexes = library.get_indexes_in_category(u'Talmud')
    my_talmud_indexes = []
    for masechet in masechtot:
        my_talmud_indexes.append(all_talmud_indexes.index(masechet))
    for i, index in enumerate(my_talmud_indexes):
        my_talmud_indexes[i] = library.get_indexes_in_category(u'Talmud', full_records=True)[index]

    server = u'http://ezra.sandbox.sefaria.org'
    add_term(u'Reshimot Shiurim', u'רשימות שיעורים', server = server)
    for seder in [u'Seder Zeraim', u'Seder Nashim', u'Seder Nezikin']:
        add_category(seder, [u'Talmud', u'Commentary', u'Reshimot Shiurim', seder], server = server)

    for i, masechet_index in enumerate(my_talmud_indexes):
        english_title = u'Reshimot Shiurim on {}'.format(masechet_index.get_title(u'en'))
        hebrew_title = u'{} {}'.format(u'רשימות שיעורים על', masechet_index.get_title(u'he'))

        ja = JaggedArrayNode()
        ja.add_primary_titles(english_title, hebrew_title)
        ja.add_structure([u'Daf', u'Paragraph'])
        ja.validate()

        if u'Seder Zeraim' in masechet_index.categories:
            seder = u'Seder Zeraim'
        elif u'Seder Nashim' in masechet_index.categories:
            seder = u'Seder Nashim'
        elif u'Seder Nezikin' in masechet_index.categories:
            seder = u'Seder Nezikin'

        index_dict = {
            u'title': english_title,
            u'base_text_titles': [masechet_index.get_title('en')],
            u'dependence': u'Commentary',
            u'base_text_mapping': u'many_to_one',
            u'collective_title': u'Reshimot Shiurim',
            u'categories': [u'Talmud',
                            u'Commentary',
                            u'Reshimot Shiurim',
                            seder],
            u'schema': ja.serialize(),
        }
        post_index(index_dict, server = server)
        version = {
            u'text': rs[masechet_index.get_title(u'en')],
            u'language': u'he',
            u'versionTitle': version_titles[i],
            u'versionSource': version_sources[i],
        }
        post_text(english_title, version, server = server)