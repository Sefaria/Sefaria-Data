# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
# from sources.Match import match_new
# from sources.Match.match import Match
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

bereishit = [u'בראשית', u'נח', u'לך-לך', u'וירא', u'חיי שרה', u'תולדות', u'ויצא', u'וישלח', u'וישב', u'מקץ', u'ויגש',
             u'ויחי']
shemot = [u'שמות', u'וארא', u'בא', u'בשלח', u'יתרו', u'משפטים', u'תרומה', u'תצוה', u'כי תשא', u'ויקהל', u'פקודי']
vayikra = [u'ויקרא', u'צו', u'שמיני', u'תזריא', u'מצרא', u'אחרי מות', u'קדשים', u'אמור', u'בהר', u'בחקתי']
bamidbar = [u'במדבר', u'נשא', u'בהעלתך', u'שלח', u'קרח', u'חקת', u'בלק', u'פינחס', u'מטות', u'מסעי']
devarim = [u'דברים', u'ואתחנן', u'עקב', u'ראה', u'שפטים', u'כי תצא', u'כי תבוא', u'נצבים', u'וילך', u'האזינו',
           u'וזאת הברכה']
hebrew_names = [bereishit, shemot, vayikra, bamidbar, devarim]

bereishit_english = [u'Bereshit', u'Noach', u'Lech Lecha', u'Vayera', u'Chayei Sara', u'Toldot', u'Vayetzei',
                     u'Vayishlach', u'Vayeshev', u'Miketz', u'Vayigash', u'Vayechi']
shemot_english = [u'Shemot', u'Vaera', u'Bo', u'Beshalach', u'Yitro', u'Mishpatim', u'Terumah', u'Tetzaveh',
                  u'Ki Tisa', u'Vayakhel', u'Pekudei']
vayikra_english = [u'Vayikra', u'Tzav', u'Shmini', u'Tazria', u'Metzora', u'Achrei Mot', u'Kedoshim', u'Emor',
                   u'Behar', u'Bechukotai']
bamidbar_english = [u'Bamidbar', u'Nasso', u"Beha'alotcha", u"Sh'lach", u'Korach', u'Chukat', u'Balak',
                    u'Pinchas', u'Matot', u'Masei']
devarim_english = [u'Devarim', u'Vaetchanan', u'Eikev', u"Re'eh", u'Shoftim', u'Ki Teitzei', u'Ki Tavo',
                   u'Nitzavim', u'Vayeilech', u"Ha'Azinu", u"V'Zot HaBerachah"]
english_names = [bereishit_english, shemot_english, vayikra_english, bamidbar_english, devarim_english]




introduction_en = 'Introduction '
introduction_he = u'הקדמה '

parsha_sefer_dictionary = {
        'Parsha': 'Parsha',
        'Sefer': 'Sefer'
    }


def create_indices():
    rabbeinu_bahya_book = rabbeinu_bahya_index()
    rabbeinu_bahya_book.validate()
    index = {
        "title": "Rabbeinu Bahya",
        "titleVariants": ["Rabbeinu Bechaye", "Rabbeinu Bahya ben Asher"],
        "categories": ["Commentary2", "Tanakh"],
        "schema": rabbeinu_bahya_book.serialize()
    }
    return index


def rabbeinu_bahya_index():
    rb_on_humash = SchemaNode()
    rb_on_humash.add_title('Rabbeinu Bahya', 'en', primary=True)
    rb_on_humash.add_title(u'רבינו בחיי', 'he', primary=True)
    rb_on_humash.key = 'Rabbeinu Bahya'
    rb_on_humash.append(create_intro_nodes())
    for en_names, he_names in zip(english_names, hebrew_names):
        rb_on_humash.append(create_book_node(en_names, he_names))
    return rb_on_humash


def create_book_node(en_dict, he_dict):
    book = SchemaNode()
    book.key = 'Sefer {}'.format(en_dict[0])
    book.add_title('Sefer {}'.format(en_dict[0]), 'en', primary=True)
    book.add_title(u'ספר {}'.format(he_dict[0]), 'he', primary=True)
    if en_dict[0] == u'Bereshit':
        book.append(create_intro_nodes())
    for en_name, he_name in zip(en_dict, he_dict):
        book.append(create_parsha_node(en_name, he_name))
    return book


def create_parsha_node(parhsa_name_en, parsha_name_he):
    parsha = SchemaNode()
    parsha.key = parhsa_name_en
    parsha.add_shared_term(parhsa_name_en)
    if parhsa_name_en is not u'Bereshit':
        parsha_one_intro_node = create_intro_nodes()
        parsha.append(parsha_one_intro_node)
    parsha_one_content_node = create_jagged_array_node()
    parsha.append(parsha_one_content_node)
    return parsha


def create_jagged_array_node():
    jagged_array_node = JaggedArrayNode()
    jagged_array_node.key = 'default'
    jagged_array_node.default = True
    jagged_array_node.depth = 1
    jagged_array_node.addressTypes = ["Integer"]
    jagged_array_node.sectionNames = ["Comment"]
    return jagged_array_node


def create_intro_nodes():
    intro_node = JaggedArrayNode()
    intro_node.add_title('Introduction', "en", primary=True)
    intro_node.add_title(u'הקדמה', "he", primary=True)
    intro_node.key = 'Introduction'
    intro_node.depth = 1
    intro_node.addressTypes = ["Integer"]
    intro_node.sectionNames = ["Comment"]
    return intro_node


def parse_and_post(rabbeinu_bahya_text_file):
    array_of_comments = []
    book_counter = -1
    parsha_counter = -1
    parsha_was_changed = False

    with codecs.open(rabbeinu_bahya_text_file, 'r', 'utf-8') as the_file:
        for each_line in the_file:
            if "@00" in each_line:
                post_the_text(array_of_comments, book_counter, parsha_counter)
                array_of_comments = []
                parsha_counter += 1
                parsha_was_changed = True

            elif "@22" in each_line and parsha_was_changed:
                post_the_text(array_of_comments, book_counter, parsha_counter, intro=True)
                array_of_comments = []
                parsha_was_changed = False

            elif "@99" in each_line:
                if book_counter == -1 and parsha_counter == -1:
                    introduction = True
                post_the_text(array_of_comments, book_counter, parsha_counter, introduction)
                introduction = False
                book_counter += 1
                parsha_counter = 0
                parsha_was_changed = True
                array_of_comments = []
                print('---------Getting thru books all day-----------')

            else:
                each_line = clean_up(each_line)
                array_of_comments.append(each_line)

    post_the_text(array_of_comments, book_counter, parsha_counter)


def clean_up(string):
    if "@05" in string:
        string += "</b>"

    string = add_bold(string, ["@05", "@11", "@66"], ["@33"])
    string = remove_tags(string, ["@44", "@55", "@22", "@01"])

    return string


def add_bold(string, list_of_opening_tags, list_of_closing_tags):
    for tag in list_of_opening_tags:
        string = string.replace(tag, '<b>')
    for tag in list_of_closing_tags:
        string = string.replace(tag, '</b>')
    return string


def remove_tags(string, list_of_tags):
    for tag in list_of_tags:
        string = string.replace(tag, '')
    return string


def post_the_text(jagged_array, book_number, parsha_number, intro=False):

    ref = create_ref(book_number, parsha_number, intro)
    text = create_text(jagged_array)

    #print ref
    # print text
    functions.post_text(ref, text)


def create_ref(book_number, parsha_number, intro):
    if intro:
        if book_number == -1 and parsha_number == -1:
            ref = 'Rabbeinu Bahya, Introduction'
        elif book_number == 0 and parsha_number == 0:
            ref = 'Rabbeinu Bahya, Sefer Bereshit, Introduction'
        else:
            ref = 'Rabbeinu Bahya, Sefer {}, {}, Introduction'.format(english_names[book_number][0], english_names[book_number][parsha_number])
    else:
        ref = 'Rabbeinu Bahya, Sefer {}, {}'.format(english_names[book_number][0], english_names[book_number][parsha_number])
    return ref


def create_text(jagged_array):
    return {
        "versionTitle": "Midrash Rabbeinu Bachya [ben Asher]. Warsaw, 1878",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001202474",
        "language": "he",
        "text": jagged_array
        }
