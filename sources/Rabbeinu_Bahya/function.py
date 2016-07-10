# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
from sources.Match import match_new
from sources.Match.match import Match
from sefaria.model.schema import AddressTalmud, SchemaNode, JaggedArrayNode
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
import pdb
import os
import sys
import re

p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, p)

os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"

hebrew_names = []
english_names = []
bereishit = [u'בראשית', u'נח', u'לך-לך', u'וירא', u'חיי שרה', u'תולדות', u'ויצא', u'וישלח', u'וישב', u'מקץ', u'ויגש',
             u'ויחי']
shemot = [u'שמות', u'וארא', u'בא', u'בשלח', u'יתרו', u'משפטים', u'תרומה', u'תצוה', u'כי תשא', u'ויקהל', u'פקודי']
vayikra = [u'ויקרא', u'צו', u'שמיני', u'תזריא', u'מצרא', u'אחרי מות', u'קדשים', u'אמור', u'בהר', u'בחקתי']
bamidbar = [u'במדבר', u'נשא', u'בהעלתך', u'שלח', u'קרח', u'חקת', u'בלק', u'פינחס', u'מטות', u'מסעי']
devarim = [u'דברים', u'ואתחנן', u'עקב', u'ראה', u'שפטים', u'כי תצא', u'כי תבוא', u'נצבים', u'וילך', u'האזינו',
           u'וזאת הברכה']
hebrew_names.append(bereishit)
hebrew_names.append(shemot)
hebrew_names.append(vayikra)
hebrew_names.append(bamidbar)
hebrew_names.append(devarim)

bereishit_english = ['Bereishit', 'Noah', 'Lech Lecha', 'Vayeira', 'Chaya Sarah', 'Toldos', 'Vayetze', 'Vayishlach',
                     'Vayeishev', 'Miketz', 'Vayigash', 'Vayihi']
shemot_english = ['Shemot', 'Varah', 'Bo', 'Beshalah', 'Yitro', 'Mishpatim', 'Terumah', 'Tizaveh', 'Ki Tisa', 'Vayekel',
                  'Pikudei']
vayikra_english = ['Vayikra', 'Tzav', 'Shimini', 'Tazria', 'Metzora', 'Ahrei Mot', 'Kedoshim', 'Emor', 'Behar',
                   'Behukotai']
bamidbar_english = ['Bamidbar', 'Naso', 'Behaloteha', 'Shelah', 'Korah', 'Hukat', 'Balak', 'Pinheas', 'Matos', 'Masai']
devarim_english = ['Devarim', 'Veethanan', 'Ekev', 'Reah', 'Shoftim', 'Ki Taza', 'Ki Tavo', 'Netzavim', 'Vayaleh',
                   'Hazinu', 'Vzot Habraha']
english_names.append(bereishit_english)
english_names.append(shemot_english)
english_names.append(vayikra_english)
english_names.append(bamidbar_english)
english_names.append(devarim_english)

introduction_en = 'Introduction '
introduction_he = u'הקדמה '


def create_indices():
    rabbeinu_bahya_book = rabbeinu_bahya_index()
    rabbeinu_bahya_book.validate()
    index = {
        "title": "Rabbeinu Bahya on Torah",
        "titleVariants": ["Rabbeinu Bechaye on Torah", "Rabbeinu Bahya ben Asher on Torah"],
        "categories": ["Torah", "Commentary2"],
        "schema": rabbeinu_bahya_book.serialize()
    }
    return index


def rabbeinu_bahya_index():
    rb_on_humash = SchemaNode()
    rb_on_humash.add_title('Rabbeinu Bahya on Torah', 'en', primary=True)
    rb_on_humash.add_title(u'רבינו בחיי על תורה', 'he', primary=True)
    rb_on_humash.key = 'Rabbeinu Bahya on Torah'
    rb_on_humash.append(create_unique_intro_nodes('Torah', u'תורה'))
    for en_names, he_names in zip(english_names, hebrew_names):
        rb_on_humash.append(create_book_node(en_names, he_names))
    return rb_on_humash


def create_book_node(en_dict, he_dict):
    book = SchemaNode()
    book.key = 'Rabbeinu Bahya on Sefer {}'.format(en_dict[0])
    book.add_title('Rabbeinu Bahya on Sefer {}'.format(en_dict[0]), 'en', primary=True)
    book.add_title(u'רבינו בחיי על ספר {}'.format(he_dict[0]), 'he', primary=True)
    if en_dict[0] == 'Bereishit':
        book.append(create_unique_intro_nodes('Sefer Bereishit', u'ספר בראשית'))
    for en_name, he_name in zip(en_dict, he_dict):
        book.append(create_parsha_node(en_name, he_name))
    return book


def create_parsha_node(parhsa_name_en, parsha_name_he):
    parsha = SchemaNode()
    parsha.add_title('Rabbeinu Bahya on Parsha {}'.format(parhsa_name_en), 'en', primary=True)
    parsha.add_title(u'רבינו בחיי על פרשה {}'.format(parsha_name_he), 'he', primary=True)
    parsha.key = 'Rabbeinu Bahya on Parsha {}'.format(parhsa_name_en)
    parsha_one_intro_node = create_jagged_array_node(parhsa_name_en, parsha_name_he, introduction_en, introduction_he)
    parsha_one_content_node = create_jagged_array_node(parhsa_name_en, parsha_name_he)
    parsha.append(parsha_one_intro_node)
    parsha.append(parsha_one_content_node)
    return parsha


def create_jagged_array_node(parhsa_name_en, parsha_name_he, intro_en='', intro_he=''):
    intro_node = JaggedArrayNode()
    intro_node.add_title('Rabbeinu Bahya {}on Parsha {}'.format(intro_en, parhsa_name_en), "en", primary=True)
    intro_node.add_title(u'רבינו בחיי {}על פרשה {}'.format(intro_he, parsha_name_he), "he", primary=True)
    intro_node.key = 'Rabbeinu Bahya {}on Parsha {}'.format(intro_en, parhsa_name_en)
    intro_node.depth = 1
    intro_node.addressTypes = ["Integer"]
    intro_node.sectionNames = ["Comment"]
    return intro_node


def create_unique_intro_nodes(en_name, he_name):
    intro_node = JaggedArrayNode()
    intro_node.add_title('Rabbeinu Bahya Introduction on {}'.format(en_name), "en", primary=True)
    intro_node.add_title(u'רבינו בחיי הקדמה על {}'.format(he_name), "he", primary=True)
    intro_node.key = 'Rabbeinu Bahya Introduction on {}'.format(en_name)
    intro_node.depth = 1
    intro_node.addressTypes = ["Integer"]
    intro_node.sectionNames = ["Comment"]
    return intro_node


def parse_and_post(rabbeinu_bahya_text_file):
    array_of_comments = []
    book_counter = 0
    parsha_counter = 0
    intro_counter = 0
    parsha_was_changed = False
    work_intro = "Rabbeinu Bahya Introduction on Torah"
    bereishit_intro = "Rabbeinu Bahya Introduction on Sefer Bereishit"
    introduction = "Rabbeinu Bahya Introduction on Parsha"
    comment = "Rabbeinu Bahya on Parsha"
    with codecs.open(rabbeinu_bahya_text_file, 'r', 'utf-8') as the_file:
        for each_line in the_file:
            if "@00" in each_line:
                if intro_counter == 0:
                    functions.post_text(work_intro, array_of_comments)
                elif intro_counter == 1:
                    functions.post_text(bereishit_intro, array_of_comments)
                else:
                    post_the_text(array_of_comments, comment, book_counter, parsha_counter)
                array_of_comments = []
                intro_counter += 1
                parsha_was_changed = True

            elif "@01" in each_line and parsha_was_changed:
                post_the_text(array_of_comments, introduction, book_counter, parsha_counter)
                array_of_comments = []
                parsha_counter += 1
                parsha_was_changed = False

            elif "@99" in each_line:
                post_the_text(array_of_comments, introduction, book_counter, parsha_counter)
                array_of_comments = []
                book_counter += 1

            else:
                array_of_comments.append(each_line)


def post_the_text(jagged_array, reference, book_number, parsha_number):
    ref = '{} {}'.format(reference, english_names[book_number][parsha_number])

    text = {
        "versionTitle": "Midrash Rabbeinu Bachya [ben Asher]. Warsaw, 1878",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001202474",
        "language": "he",
        "text": jagged_array
    }

    functions.post_text(ref, text)
