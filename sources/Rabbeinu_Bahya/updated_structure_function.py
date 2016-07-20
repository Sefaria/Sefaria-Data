# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
# from sources.Match import match_new
from sources.Match.match import Match
from sefaria.model.schema import AddressTalmud, SchemaNode, JaggedArrayNode
from fuzzywuzzy import fuzz
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
import pdb
import os
import sys

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

book_english_names = [u'Bereshit', u'Shemot', u'Vayikra', u'Bamidbar', u'Devarim']
pasuk_perek_number = regex.compile(u'\(?([\u05d0-\u05ea]{1,3})\)?([-_][\u05d0-\u05ea]{1,3})?\)?')


def create_rb_indices():
    structs = create_alternate_structs()
    rabbeinu_bahya_book = new_index()
    rabbeinu_bahya_book.validate()
    index = {
        "title": "Rabbeinu Bahya",
        "titleVariants": ["Rabbeinu Bechaye", "Rabbeinu Bahya ben Asher"],
        "categories": ["Commentary2", "Tanakh", "Rabbeinu Bahya"],
        "alt_structs": {"Parsha": structs.serialize()},
        "schema": rabbeinu_bahya_book.serialize()
    }
    return index


def new_index():
    rb_on_humash = SchemaNode()
    rb_on_humash.add_title('Rabbeinu Bahya', 'en', primary=True)
    rb_on_humash.add_title(u'רבינו בחיי', 'he', primary=True)
    rb_on_humash.key = 'Rabbeinu Bahya'
    rb_on_humash.append(create_intro_nodes())
    for book_name in book_english_names:
        rb_on_humash.append(create_book_ja_node(book_name))
    return rb_on_humash


def create_book_ja_node(book_name):
    book_node = JaggedArrayNode()
    book_node.add_shared_term(book_name)
    book_node.key = book_name
    book_node.depth = 3
    book_node.addressTypes = ["Integer", "Integer", "Integer"]
    book_node.sectionNames = ["Chapter", "Verse", "Comment"]
    return book_node


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
    book, chapter, verse = [], [], []
    title_counter = 0
    most_recent_chapter = 0
    most_recent_verse = 0
    new_book = False
    new_chapter = False
    with codecs.open(rabbeinu_bahya_text_file, 'r', 'utf-8') as the_file:
        for each_line in the_file:

            if "@99" in each_line:
                chapter.append(verse)
                book.append(chapter)
                ja = book
                if title_counter == 0:
                    ja = verse
                post_the_text(ja, title_counter)
                title_counter += 1
                new_book = True
                book, chapter, verse = [], [], []
                most_recent_chapter = 0

            elif "@01" in each_line:

                if not new_book:
                    chapter.append(verse)
                    book.append(chapter)
                    chapter, verse = [], []
                else:
                    new_book = False

                new_chapter = True

                matchObject = pasuk_perek_number.search(each_line)
                current_chapter = util.getGematria(matchObject.group(1))
                diff = current_chapter - most_recent_chapter
                while diff > 1:
                    book.append([[]])
                    diff -= 1

                most_recent_chapter = current_chapter
                most_recent_verse = 0

            elif "@22" in each_line:

                if not new_chapter:
                    chapter.append(verse)
                    verse = []
                else:
                    new_chapter = False

                matchObject = pasuk_perek_number.search(each_line)
                current_verse = util.getGematria(matchObject.group(1))
                diff = current_verse - most_recent_verse

                while diff > 1:
                        chapter.append([])
                        diff -= 1

                most_recent_verse = current_verse

            elif "@00" in each_line or "@77" in each_line:
                continue

            else:
                each_line = clean_up(each_line)
                verse.append(each_line)

    chapter.append(verse)
    book.append(chapter)
    post_the_text(book, title_counter)


def clean_up(string):
    if "@05" in string:
        string = amend_mishlei_verse(string)

    string = add_bold(string, ["@05", "@11", "@66"], ["@33"])
    string = remove_tags(string, ["@44", "@55", "@22", "@01", "@00"])

    return string


def amend_mishlei_verse(string):
    string = remove_tags(string, ['.', ':'])
    string = regex.sub(u'\(\u05de\u05e9\u05dc\u05d9\s[\u05d0-\u05ea]{1,3}\)', '', string)
    string = string.strip()
    string += u" \u2013 \u05de\u05e9\u05dc\u05d9</b>"
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


def post_the_text(jagged_array, title_counter):
    ref = create_ref(title_counter)
    text = create_text(jagged_array)
    functions.post_text(ref, text)
    if title_counter > 0:
        list_of_links = create_links(jagged_array, title_counter)
        print(list_of_links)
        functions.post_link(list_of_links)
    print ref


def create_ref(title_counter):
    titles = [u'Introduction', u'Bereshit', u'Shemot', u'Vayikra', u'Bamidbar', u'Devarim', ]
    ref = 'Rabbeinu Bahya, {}'.format(titles[title_counter])
    return ref


def create_text(jagged_array):
    return {
        "versionTitle": "Midrash Rabbeinu Bachya [ben Asher]. Warsaw, 1878",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001202474",
        "language": "he",
        "text": jagged_array
    }


def create_links(rb_ja, title_counter):
    titles = [u'Introduction', u'Bereshit', u'Shemot', u'Vayikra', u'Bamidbar', u'Devarim', ]
    list_of_links = []
    sefer_ja = TextChunk(Ref(titles[title_counter]), 'he', 'Tanach with Text Only').text
    proverbs = TextChunk(Ref('Proverbs'), 'he', 'Tanach with Text Only').text
    for perek_index, (perek_rb, perek_chumash) in enumerate(zip(rb_ja, sefer_ja)):
        for pasuk_index, (pasuk_rb, pasuk_chumash) in enumerate(zip(perek_rb, perek_chumash)):
            for comment_index, comment in enumerate(pasuk_rb):

                divrei_hamatchil = get_divrei_hamatchil(comment)
                if divrei_hamatchil:
                    rb_dictionary = create_rb_dict(titles[title_counter], perek_index+1, pasuk_index+1, comment_index+1)
                    if u'\u05de\u05e9\u05dc\u05d9' in divrei_hamatchil:
                        list_of_links.append(create_mishlei_link(divrei_hamatchil, proverbs, rb_dictionary))

                    elif divrei_hamatchil[-1] == '.':
                        list_of_links.append(create_the_link(rb_dictionary))

                    else:
                        divrei_hamatchil = reduce_it_to_letters(divrei_hamatchil)
                        pasuk_chumash = reduce_it_to_letters(pasuk_chumash)
                        if divrei_hamatchil in pasuk_chumash:
                            list_of_links.append(create_the_link(rb_dictionary))

    return list_of_links


def create_rb_dict(book, perek, pasuk, comment):
    return {
        "sefer": book,
        "perek": perek,
        "pasuk": pasuk,
        "comment": comment
    }


def get_divrei_hamatchil(comment):
    if not "<b>" in comment or not '</b>' in comment:
        return False
    divrei_hamatchil_start = comment.index('<b>') + len('<b>')
    divrei_hamatchil_end = comment.index('</b>')
    divrei_hamatchil = comment[divrei_hamatchil_start:divrei_hamatchil_end]
    divrei_hamatchil = divrei_hamatchil.strip()
    return divrei_hamatchil


def create_mishlei_link(divrei_hamatchil, proverbs, rb_dict):
    for mishlei_perek_index, perek in enumerate(proverbs):
        for mishlei_pasuk_index, pasuk in enumerate(perek):
            if fuzz.partial_ratio(divrei_hamatchil, pasuk) > 70:
                return create_mishlei_links(rb_dict, mishlei_perek_index+1, mishlei_pasuk_index+1)



def create_mishlei_links(rb_dict, proverbs_perek, proverb_pasuk):
    return {
                "refs": [
                        "Rabbeinu Bahya, {}.{}.{}.{}".format(rb_dict['sefer'], rb_dict['perek'], rb_dict['pasuk'], rb_dict['comment']),
                        "Proverbs.{}.{}".format(proverbs_perek, proverb_pasuk)
                    ],
                "type": "Commentary",
        }


def reduce_it_to_letters(full_string):
    just_hebrew_letters = regex.findall(u'[א-ת]', full_string)
    return ''.join(just_hebrew_letters)


def create_the_link(rb_dict):
    return {
                "refs": [
                        "Rabbeinu Bahya, {}.{}.{}.{}".format(rb_dict['sefer'], rb_dict['perek'], rb_dict['pasuk'], rb_dict['comment']),
                        "{}.{}.{}".format(rb_dict['sefer'], rb_dict['perek'], rb_dict['pasuk'])
                    ],
                "type": "Commentary",
        }


def create_alternate_structs():
    index = rabbeinu_bahya_index()
    return index


def rabbeinu_bahya_index():
    rb_on_humash = SchemaNode()
    rb_on_humash.append(create_alt_struct_intro_nodes('Rabbeinu_Bahya,_Introduction.1-5', include_section=False))
    for english_parsha_names, hebrew__parsha_names in zip(english_names, hebrew_names):
        rb_on_humash.append(create_book_node(english_parsha_names, hebrew__parsha_names))
    return rb_on_humash


def create_book_node(english_parsha_names, hebrew_parsha_names):
    book = SchemaNode()
    book.key = 'Sefer {}'.format(english_parsha_names[0])
    book.add_title('Sefer {}'.format(english_parsha_names[0]), 'en', primary=True)
    book.add_title(u'ספר {}'.format(hebrew_parsha_names[0]), 'he', primary=True)
    for en_name in english_parsha_names:
        book.append(create_parsha_node(en_name))
    return book


def create_parsha_node(english_parsha_name):
    dictionary = create_alt_struct_refs()
    parsha_node = SchemaNode()
    parsha_node.add_shared_term(english_parsha_name)
    parsha_node.key = english_parsha_name
    parsha_node.append(create_alt_struct_intro_nodes(dictionary[english_parsha_name]['intro']))
    parsha_node.append(create_jagged_array_node(english_parsha_name, dictionary[english_parsha_name]['comments']))
    return parsha_node


def create_jagged_array_node(en_parsha_name, whole_ref, include_section=True):
    ja_node = ArrayMapNode()
    ja_node.default = True
    ja_node.depth = 0
    ja_node.wholeRef = whole_ref
    ja_node.includeSections = include_section
    return ja_node


def create_alt_struct_intro_nodes(whole_ref, include_section=True):
    intro_node = ArrayMapNode()
    intro_node.add_title('Introduction', 'en', True)
    intro_node.add_title('הקדמה', 'he', True)
    intro_node.depth = 0
    intro_node.wholeRef = whole_ref
    intro_node.includeSections = include_section
    return intro_node


def create_alt_struct_refs():
    return {
            "Intro" : 'Rabbeinu_Bahya,_Introduction.1-5',
        "Bereshit" : {'intro': 'Rabbeinu_Bahya,_Bereshit.1.1.1-9', 'comments': 'Rabbeinu_Bahya,_Bereshit.1.1.10-6.8.1'},
        "Noach" : {'intro': 'Rabbeinu_Bahya,_Bereshit.6.9.1-2', 'comments': 'Rabbeinu_Bahya,_Bereshit.6.9.3-11.31.5'},
        "Lech Lecha" : {'intro': 'Rabbeinu_Bahya,_Bereshit.12.1.1-2', 'comments': 'Rabbeinu_Bahya,_Bereshit.12.2.1-17.17.6'},
        "Vayera" : {'intro': 'Rabbeinu_Bahya,_Bereshit.18.1.1-2', 'comments': 'Rabbeinu_Bahya,_Bereshit.18.1.3-22.20.1'},
        "Chayei Sara" : {'intro': 'Rabbeinu_Bahya,_Bereshit.23.1.1-6', 'comments': 'Rabbeinu_Bahya,_Bereshit.23.1.7-25.8.2'},
        "Toldot" : {'intro': 'Rabbeinu_Bahya,_Bereshit.25.19.1-3', 'comments': 'Rabbeinu_Bahya,_Bereshit.25.19.4-27.41.4'},
        "Vayetzei" : {'intro': 'Rabbeinu_Bahya,_Bereshit.28.10.1-4', 'comments': 'Rabbeinu_Bahya,_Bereshit.28.10.5-32.2.1'},
        "Vayishlach" : {'intro': 'Rabbeinu_Bahya,_Bereshit.32.3.1-10', 'comments': 'Rabbeinu_Bahya,_Bereshit.32.4.1-36.39.3'},
        "Vayeshev" : {'intro': 'Rabbeinu_Bahya,_Bereshit.37.1.1-2', 'comments': 'Rabbeinu_Bahya,_Bereshit.37.1.3-40.20.4'},
        "Miketz" : {'intro': 'Rabbeinu_Bahya,_Bereshit.41.1.1-5', 'comments': 'Rabbeinu_Bahya,_Bereshit.41.1.6-44.17.6'},
        "Vayigash" : {'intro': 'Rabbeinu_Bahya,_Bereshit.44.18.1-6', 'comments': 'Rabbeinu_Bahya,_Bereshit.44.18.7-47.27.4'},
        "Vayechi" : {'intro': 'Rabbeinu_Bahya,_Bereshit.47.28.1-2', 'comments': 'Rabbeinu_Bahya,_Bereshit.47.28.3-50.26.1'},
        "Shemot" : {'intro': 'Rabbeinu_Bahya,_Shemot.1.1.1-2', 'comments': 'Rabbeinu_Bahya,_Shemot.1.1.3-5.22.7'},
        "Vaera" : {'intro': 'Rabbeinu_Bahya,_Shemot.6.3.1-3', 'comments': 'Rabbeinu_Bahya,_Shemot.6.3.4-9.34.1'},
        "Bo" : {'intro': 'Rabbeinu_Bahya,_Shemot.10.1.1-2', 'comments': 'Rabbeinu_Bahya,_Shemot.10.1.3-13.16.6'},
        "Beshalach" : {'intro': 'Rabbeinu_Bahya,_Shemot.13.17.1-2', 'comments': 'Rabbeinu_Bahya,_Shemot.13.17.3-17.16.5'},
        "Yitro" : {'intro': 'Rabbeinu_Bahya,_Shemot.18.1.1-3', 'comments': 'Rabbeinu_Bahya,_Shemot.18.1.4-20.22.4'},
        "Mishpatim" : {'intro': 'Rabbeinu_Bahya,_Shemot.21.1.1-3', 'comments': 'Rabbeinu_Bahya,_Shemot.21.1.4-24.16.5'},
        "Terumah" : {'intro': 'Rabbeinu_Bahya,_Shemot.25.2.1-3', 'comments': 'Rabbeinu_Bahya,_Shemot.25.2.4-27.9.2'},
        "Tetzaveh" : {'intro': 'Rabbeinu_Bahya,_Shemot.27.20.1-4', 'comments': 'Rabbeinu_Bahya,_Shemot.27.20.5-30.9.2'},
        "Ki Tisa" : {'intro': 'Rabbeinu_Bahya,_Shemot.30.12.1-3', 'comments': 'Rabbeinu_Bahya,_Shemot.30.12.4-34.35.6'},
        "Vayakhel" : {'intro': 'Rabbeinu_Bahya,_Shemot.35.1.1-5', 'comments': 'Rabbeinu_Bahya,_Shemot.35.1.6-38.9.3'},
        "Pekudei" : {'intro': 'Rabbeinu_Bahya,_Shemot.38.21.1-6', 'comments': 'Rabbeinu_Bahya,_Shemot.38.21.7-40.38.4'},
        "Vayikra" : {'intro': 'Rabbeinu_Bahya,_Vayikra.1.1.1-3', 'comments': 'Rabbeinu_Bahya,_Vayikra.1.1.4-5.24.3'},
        "Tzav" : {'intro': 'Rabbeinu_Bahya,_Vayikra.6.2.1-4', 'comments': 'Rabbeinu_Bahya,_Vayikra.6.2.5-8.36.3'},
        "Shmini" : {'intro': 'Rabbeinu_Bahya,_Vayikra.9.1.1-4', 'comments': 'Rabbeinu_Bahya,_Vayikra.9.1.5-11.44.3'},
        "Tazria" : {'intro': 'Rabbeinu_Bahya,_Vayikra.12.2.1-4', 'comments': 'Rabbeinu_Bahya,_Vayikra.12.2.5-13.58.2'},
        "Metzora" : {'intro': 'Rabbeinu_Bahya,_Vayikra.14.2.1-2', 'comments': 'Rabbeinu_Bahya,_Vayikra.14.2.3-15.33.4'},
        "Achrei Mot" : {'intro': 'Rabbeinu_Bahya,_Vayikra.16.1.1-3', 'comments': 'Rabbeinu_Bahya,_Vayikra.16.1.4-18.29.9'},
        "Kedoshim" : {'intro': 'Rabbeinu_Bahya,_Vayikra.19.2.1-2', 'comments': 'Rabbeinu_Bahya,_Vayikra.19.2.3-20.26.2'},
        "Emor" : {'intro': 'Rabbeinu_Bahya,_Vayikra.21.1.1-3', 'comments': 'Rabbeinu_Bahya,_Vayikra.21.1.4-24.22.2'},
        "Behar" : {'intro': 'Rabbeinu_Bahya,_Vayikra.25.1.1-2', 'comments': 'Rabbeinu_Bahya,_Vayikra.25.1.3-26.2.2'},
        "Bechukotai" : {'intro': 'Rabbeinu_Bahya,_Vayikra.26.3.1-4', 'comments': 'Rabbeinu_Bahya,_Vayikra.26.3.5-27.34.1'},
        "Bamidbar" : {'intro': 'Rabbeinu_Bahya,_Bamidbar.1.1.1-3', 'comments': 'Rabbeinu_Bahya,_Bamidbar.1.1.4-4.20.4'},
        "Nasso" : {'intro': 'Rabbeinu_Bahya,_Bamidbar.4.22.1-3', 'comments': 'Rabbeinu_Bahya,_Bamidbar.4.22.4-7.89.1'},
        "Beha'alotcha" : {'intro': 'Rabbeinu_Bahya,_Bamidbar.8.2.1-2', 'comments': 'Rabbeinu_Bahya,_Bamidbar.8.2.3-12.15.1'},
        "Sh'lach" : {'intro': 'Rabbeinu_Bahya,_Bamidbar.13.2.1-2', 'comments': 'Rabbeinu_Bahya,_Bamidbar.13.2.3-15.41.2'},
        "Korach" : {'intro': 'Rabbeinu_Bahya,_Bamidbar.16.1.1-3', 'comments': 'Rabbeinu_Bahya,_Bamidbar.16.1.4-18.21.1'},
        "Chukat" : {'intro': 'Rabbeinu_Bahya,_Bamidbar.19.2.1-2', 'comments': 'Rabbeinu_Bahya,_Bamidbar.19.2.3-21.34.5'},
        "Balak" : {'intro': 'Rabbeinu_Bahya,_Bamidbar.22.2.1-2', 'comments': 'Rabbeinu_Bahya,_Bamidbar.22.2.3-25.7.1'},
        "Pinchas" : {'intro': 'Rabbeinu_Bahya,_Bamidbar.25.11.1-2', 'comments': 'Rabbeinu_Bahya,_Bamidbar.25.11.3-29.39.1'},
        "Matot" : {'intro': 'Rabbeinu_Bahya,_Bamidbar.30.2.1-2', 'comments': 'Rabbeinu_Bahya,_Bamidbar.30.2.3-32.42.1'},
        "Masei" : {'intro': 'Rabbeinu_Bahya,_Bamidbar.33.1.1-2', 'comments': 'Rabbeinu_Bahya,_Bamidbar.33.1.3-36.13.2'},
        "Devarim" : {'intro': 'Rabbeinu_Bahya,_Devarim.1.1.1-3', 'comments': 'Rabbeinu_Bahya,_Devarim.1.1.4-3.21.2'},
        "Vaetchanan" : {'intro': 'Rabbeinu_Bahya,_Devarim.3.23.1-2', 'comments': 'Rabbeinu_Bahya,_Devarim.3.23.3-7.11.1'},
        "Eikev" : {'intro': 'Rabbeinu_Bahya,_Devarim.7.12.1-2', 'comments': 'Rabbeinu_Bahya,_Devarim.7.12.3-11.25.1'},
        "Re'eh" : {'intro': 'Rabbeinu_Bahya,_Devarim.11.26.1-2', 'comments': 'Rabbeinu_Bahya,_Devarim.11.26.3-16.15.2'},
        "Shoftim" : {'intro': 'Rabbeinu_Bahya,_Devarim.16.18.1-2', 'comments': 'Rabbeinu_Bahya,_Devarim.16.18.3-21.9.2'},
        "Ki Teitzei" : {'intro': 'Rabbeinu_Bahya,_Devarim.21.10.1-2', 'comments': 'Rabbeinu_Bahya,_Devarim.21.10.3-25.19.3'},
        "Ki Tavo" : {'intro': 'Rabbeinu_Bahya,_Devarim.26.1.1-3', 'comments': 'Rabbeinu_Bahya,_Devarim.26.1.4-29.6.3'},
        "Nitzavim" : {'intro': 'Rabbeinu_Bahya,_Devarim.29.9.1-2', 'comments': 'Rabbeinu_Bahya,_Devarim.29.9.3-30.19.3'},
        "Vayeilech" : {'intro': 'Rabbeinu_Bahya,_Devarim.31.1.1-2', 'comments': 'Rabbeinu_Bahya,_Devarim.31.1.3-31.30.2'},
        "Ha'Azinu" : {'intro': 'Rabbeinu_Bahya,_Devarim.32.1.1-2', 'comments': 'Rabbeinu_Bahya,_Devarim.32.1.3-32.52.2'},
        "V'Zot HaBerachah" : {'intro': 'Rabbeinu_Bahya,_Devarim.33.1.1-4', 'comments': 'Rabbeinu_Bahya,_Devarim.33.1.5-34.12.5'}

    }


def create_parsha_refs():
    ts = TermSet({"scheme": "Parasha"})
    list_of_parsha_and_refs = [(t.name, t.ref) for t in ts]
    Bereshit, Shemot, Vayikra, Bamidbar, Devarim = [], [], [], [], []
    for Index in range(12):
        Bereshit.append(list_of_parsha_and_refs[Index])
    for Index in range(12, 23):
        Shemot.append(list_of_parsha_and_refs[Index])
    for Index in range(23, 33):
        Vayikra.append(list_of_parsha_and_refs[Index])
    for Index in range(33, 43):
        Bamidbar.append(list_of_parsha_and_refs[Index])
    for Index in range(43, 54):
        Devarim.append(list_of_parsha_and_refs[Index])
    parsha = [Bereshit, Shemot, Vayikra, Bamidbar, Devarim]
    return parsha


def create_alt_struct_dict(rabbeinu_bahya_text_file):
    first_perek, first_pasuk, current_perek, current_pasuk = 0, 0, 0, 0
    second_to_last_pasuk, second_to_last_comment_number = 0, 0
    first_comment_number, current_comment_number = 0, 0
    new_first_perek, new_first_pasuk, new_comment = True, True, True
    list_of_ranges = []

    with codecs.open(rabbeinu_bahya_text_file, 'r', 'utf-8') as the_file:
        for each_line in the_file:


            if "@99" in each_line:
                #list_of_ranges.append('{}.{}.{}-{}.{}.{}'.format(first_perek, first_pasuk, first_comment_number, current_perek, current_pasuk, current_comment_number))
                new_first_perek, new_first_pasuk, right_after_99 = True, True, True
                first_perek = 0

            elif "@00" in each_line:
                list_of_ranges.append('{}.{}.{}-{}.{}.{}'.format(first_perek, first_pasuk, first_comment_number, current_perek, current_pasuk, second_to_last_comment_number))
                new_first_perek, new_first_pasuk = True, True

            elif "@77" in each_line:
                list_of_ranges.append('{}.{}.{}-{}.{}.{}'.format(first_perek, first_pasuk, first_comment_number, current_perek, current_pasuk, second_to_last_comment_number))
                #new_first_perek, new_first_pasuk = True, True

            elif "@01" in each_line:

                matchObject = pasuk_perek_number.search(each_line)
                if new_first_perek:
                    matchObject = pasuk_perek_number.search(each_line)
                    first_perek = util.getGematria(matchObject.group(1))
                    new_first_perek = False
                current_perek = util.getGematria(matchObject.group(1))

            elif "@22" in each_line:

                matchObject = pasuk_perek_number.search(each_line)
                if new_first_pasuk:
                    matchObject = pasuk_perek_number.search(each_line)
                    first_pasuk = util.getGematria(matchObject.group(1))
                    new_first_pasuk = False
                    new_comment = True
                if new_comment:
                    first_comment_number = current_comment_number
                second_to_last_pasuk = current_pasuk
                current_pasuk = util.getGematria(matchObject.group(1))
                second_to_last_comment_number = current_comment_number
                current_comment_number = 0

            else:
                current_comment_number += 1

    return list_of_ranges
