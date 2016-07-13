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



book_english_names = [u'Bereshit', u'Shemot', u'Vayikra', u'Bamidbar', u'Devarim']
pasuk_perek_number = regex.compile(u'\(?([\u05d0-\u05ea]{1,3})\)?([-_][\u05d0-\u05ea]{1,3})?\)?')


def create_rb_indices():
    rabbeinu_bahya_book = new_index()
    rabbeinu_bahya_book.validate()
    index = {
        "title": "Rabbeinu Bahya",
        "titleVariants": ["Rabbeinu Bechaye", "Rabbeinu Bahya ben Asher"],
        "categories": ["Commentary2", "Tanakh", "Rabbeinu Bahya"],
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
    #book_node.heSectionNames: [u"פרק", u"פסוק", u"פירוש"]
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

    book = []
    chapter = []
    verse = []
    titles = [u'Introduction', u'Bereshit', u'Shemot', u'Vayikra', u'Bamidbar', u'Devarim',]
    title_counter = 0
    most_recent_chapter = 1
    most_recent_verse = 1
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
                #if title_counter > 0:
                post_the_text(ja, titles[title_counter])
                title_counter += 1
                new_book = True
                book = []
                chapter = []
                verse = []
                most_recent_chapter = 1

            elif "@01" in each_line:

                if not new_book:
                    chapter.append(verse)
                    book.append(chapter)
                    chapter = []
                    verse = []
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
                most_recent_verse = 1



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



            else:
                each_line = clean_up(each_line)
                verse.append(each_line)

    chapter.append(verse)
    book.append(chapter)
    post_the_text(book, titles[title_counter])


def post_the_text(jagged_array, english_name):
    """
    create text
    create ref
    :return:
    """
    ref = create_ref(english_name)
    text = create_text(jagged_array)
    print(ref)
    # hello = codecs.open("hello.txt", 'w', 'utf-8')
    # util.jagged_array_to_file(hello, jagged_array, ['Chapter', 'Verse', 'Comment'])
    # hello.close()
    functions.post_text(ref, text)




def create_ref(name):
    ref = 'Rabbeinu Bahya, {}'.format(name)
    return ref


def create_text(jagged_array):
    return {
        "versionTitle": "Midrash Rabbeinu Bachya [ben Asher]. Warsaw, 1878",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001202474",
        "language": "he",
        "text": jagged_array
        }



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