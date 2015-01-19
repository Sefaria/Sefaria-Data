# -*- coding: utf-8 -*-

import argparse
import sys
import helperFunctions as Helper
from helperFunctions import run_once
import json
import re
import os, errno
import os.path


try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import pprint
import itertools
import difflib

#ur"[\u0591-\u05c7\s]
#leaves only consonantal text
strip_cantillation_vowel_regex = re.compile(ur"[\u0591-\u05bd\u05bf-\u05c5\u05c7]|\([\u0590-\u05ea]\)", re.UNICODE)
#leaves only vowel text
strip_cantillation_regex = re.compile(ur"[\u0591-\u05af\u05bd\u05bf\u05c0\u05c4\u05c5]|\([\u0590-\u05ea]\)", re.UNICODE)


#======================== PARSING ==============================#

def parse_first(func):
    def wrapper(*args, **kwargs):
        if len(os.listdir('preprocess_json')) < 39: #make sure the parser already ran.
            run_parser()
        return func(*args, **kwargs)
    return wrapper

def run_parser():
    for filename in os.listdir('source/books'):
        json_text = process_book_file(filename)
        text_whole = {
            "title": json_text['title'],
            "versionTitle": "Tanach with Ta'amei Hamikra",
            "versionSource": "http://www.tanach.us/Tanach.xml",
            "language": "he",
            "text": json_text['text'],
        }
        save_parsed_text(text_whole)

def process_book_file(filename):
    print filename
    book_xml = ET.parse('source/books/'+filename)
    book_xml_r = book_xml.getroot().find('./tanach/book')
    canonical_book_name = book_xml_r.find('./names/name').text
    #print book_xml_r
    book_text = []

    for chap_num, chapter_node in enumerate(book_xml_r.findall('c'),1):
        #print "chapter ", chap_num, ": ", chapter_node.get('n').encode('utf-8')
        chapter_text = []
        book_text.append(chapter_text)
        for v_num,verse_node in enumerate(chapter_node.findall('v'),1):
            #print "verse ", v_num, ": ", verse_node.get('n').encode('utf-8')
            verse_text = verse_parsing_func(verse_node)
            chapter_text.append(verse_text)
    return {'title': canonical_book_name, 'text' :book_text}

def verse_parsing_func(verse_xml):
    verse_words_arr = []
    for child in verse_xml:
        word_str = xml_node_convert(child)
        if word_str is not None:
            verse_words_arr.append(word_str)
    return re.sub(ur"\u05be\s", ur"\u05be", " ".join(verse_words_arr))



def xml_node_convert(word_xml):
    if word_xml.tag == 'w': #normal word node
        return strip_wlc_morph_notation(join_irregular_letters(word_xml))
    elif word_xml.tag == 'k': #ketib
        return strip_wlc_morph_notation(join_irregular_letters(word_xml))
    elif word_xml.tag == 'q': #qere
        return "[" + strip_wlc_morph_notation(join_irregular_letters(word_xml)) + "]"
    elif word_xml.tag == 'reversednun':
        return "(" + u'\u05C6' + ")"
    elif word_xml.tag == 'samekh':
        return u"(ס)"
    elif word_xml.tag == 'pe':
        return u"(פ)"
    else:
        pass #ignore any other possible nodes like 'x' that denotes a textual note on wlc

def strip_wlc_morph_notation(word):
    #strip the slash that denotes a morphological separator
    return re.sub(ur"\u002f", "", word)

def join_irregular_letters(word_xml):
    word_str = word_xml.text if word_xml.text else ''
    word_str += ''.join(s.text for s in word_xml.findall('s'))
    word_str += word_xml[-1].tail if len(list(word_xml)) and word_xml[-1].tail else ''
    return word_str

def save_parsed_text(text, sub_directory=None):
    directory = "preprocess_json/%s" % sub_directory if sub_directory else "preprocess_json"
    Helper.mkdir_p(directory)
    with open(directory + "/" + text['title'] + ".json", 'w') as out:
        json.dump(text, out)

@parse_first
def parse_derived_text_versions():
    wlc_index_xml = ET.parse('source/TanachIndex.xml') #this lists num of chapters and verses for all books in the WLC
    books_xml_r = wlc_index_xml.getroot().find('tanach')
    for book in books_xml_r.findall('book'):
        canonical_name = book.find('./names/name').text
        print canonical_name
        with open("preprocess_json/%s.json" % canonical_name, 'r') as filep:
            book_text = json.load(filep)['text']

        vowel_text = make_vowel_text(book_text)
        vowel_whole = {
            "title": canonical_name,
            "versionTitle": "Tanach with Nikkud",
            "versionSource": "http://www.tanach.us/Tanach.xml",
            "language": "he",
            "text": vowel_text,
        }
        save_parsed_text(vowel_whole, 'vowels')

        consonant_text =  make_consonantal_text(book_text)
        consonant_whole = {
            "title": canonical_name,
            "versionTitle": "Tanach with Text Only",
            "versionSource": "http://www.tanach.us/Tanach.xml",
            "language": "he",
            "text": consonant_text,
        }
        save_parsed_text(consonant_whole, 'consonants')


def make_consonantal_text(book_text):
    return make_derived_text(book_text, strip_cantillation_vowel_regex)

def make_vowel_text(book_text):
    return make_derived_text(book_text, strip_cantillation_regex)

def make_derived_text(book_text, regex):
    return [[re.sub(ur"\s{2,}", ur" ", regex.sub('', verse)).strip() for verse in chapter] for chapter in book_text]

def flatten_text(book_text):
    result = []
    for chnum, chapter in enumerate(book_text,1):
        result.append("%s" % chnum)
        result.extend(["%s. %s" % (num, verse) for num, verse in enumerate(chapter,1)])
    return result


#======================== COMPARING ==============================#


@parse_first
def run_compare():
    Helper.mkdir_p('results')
    open("results/length_comparison.txt", 'wb+').close() #just create it for now.
    wlc_index_xml = ET.parse('source/TanachIndex.xml') #this lists num of chapters and verses for all books in the WLC
    books_xml_r = wlc_index_xml.getroot().find('tanach')
    for book in books_xml_r.findall('book'):
        do_book_comparison(book)



def do_book_comparison(book_index_xml):
    #check number of chapters.
    #compare to the parsed Leningrad itself
    #compare to the current sefaria versions.


    canonical_name = book_index_xml.find('./names/name').text
    print canonical_name
    diff_file = open("results/%s_wlc_koren.html" % canonical_name, 'wb+')
    length_results = open("results/length_comparison.txt", 'ab+')

    wlc_chapter_count = int(book_index_xml.find('./cs').text) #listed length of the leningrad chapters
    with open("preprocess_json/%s.json" % canonical_name, 'r') as filep:
        wlc_text = json.load(filep)['text']
    wlc_real_chapter_count = len(wlc_text) #physical length of the parsed leningrad chapters

    sefaria_book = Helper.getKnownTexts(canonical_name)
    sefria_chapter_count = sefaria_book['lengths'][0]
    sefaria_text = Helper.api_get_text("%s 1-%s" % (sefaria_book['title'], sefria_chapter_count), 'he', "Tanach with Ta'amei Hamikra")['he']
    if sefria_chapter_count == 1:
        sefaria_text = [sefaria_text]
    sefaria_real_chapter_count = len(sefaria_text)

    if not all_same([wlc_chapter_count, wlc_real_chapter_count, sefria_chapter_count, sefaria_real_chapter_count]):
        ch_res_str = "%s: Leningrad has %s chapters listed and %s chapters in text. Sefaria version has %s chapters listed and %s chapters in text\n" % (canonical_name.encode('utf-8'), wlc_chapter_count, wlc_real_chapter_count, sefria_chapter_count, sefaria_real_chapter_count)
        length_results.write(ch_res_str)

    for chapter in book_index_xml.findall('c'):
        ch_num = int(chapter.get('n'))
        wlc_verse_count = int(chapter.find('vs').text)
        wlc_real_verse_count = len(wlc_text[ch_num - 1])
        sefaria_real_verse_count = len(sefaria_text[ch_num-1])
        if not all_same([wlc_verse_count, wlc_real_verse_count, sefaria_real_verse_count]):
            v_res_str = "%s:%s Leningrad has %s verses listed and %s verses in text. Sefaria version has %s verses\n" % (canonical_name.encode('utf-8'), ch_num, wlc_verse_count, wlc_real_verse_count, sefaria_real_verse_count)
            length_results.write(v_res_str)

    html_diff = difflib.HtmlDiff().make_file(flatten_text(make_consonantal_text(wlc_text)), flatten_text(make_consonantal_text(sefaria_text)), 'Leningrad Codex', 'Sefaria/Koren')
    html_diff = html_diff.replace('charset=ISO-8859-1','charset=utf-8')
    diff_file.write(html_diff.encode('utf-8'))

    length_results.close()
    diff_file.close()


def all_same(items):
    #print items
    return all(x == items[0] for x in items)


#======================== POSTING ==========================05C6====#

@parse_first
def run_post_to_api(sub_directory=None):
    directory = "preprocess_json/%s" % sub_directory if sub_directory else "preprocess_json"
    wlc_index_xml = ET.parse('source/TanachIndex.xml') #this lists num of chapters and verses for all books in the WLC
    books_xml_r = wlc_index_xml.getroot().find('tanach')
    for book in books_xml_r.findall('book'):
        canonical_name = book.find('./names/name').text
        print canonical_name
        with open("%s/%s.json" % (directory,canonical_name), 'r') as filep:
            file_text = filep.read()
        sefaria_book = Helper.getKnownTexts(canonical_name)
        Helper.postText(sefaria_book['title'], file_text, False)


def post_derived_text_versions():
    source = 'consonants'
    run_post_to_api(source)
    source = 'vowels'
    run_post_to_api(source)






#========================================================================================================#


""" The main function, runs when called from the CLI"""
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--preprocess", help="Perform the preprocess and parse the files but do not post them to the db", action="store_true")
    parser.add_argument("-d", "--derive", help="derive other text versions from the original", action="store_true")
    parser.add_argument("-a", "--postapi", help="post data to API", action="store_true")
    parser.add_argument("-c", "--compare", help="compare the codex to prev sefaria version", action="store_true")
    args = parser.parse_args()
    #Map command line arguments to function arguments.
    if args.preprocess:
        print "processing"
        run_parser()
    if args.derive:
        print "making other version"
        parse_derived_text_versions()
    if args.compare:
        print "comparing"
        run_compare()
    if args.postapi:
        print "posting to api"
        run_post_to_api()
        if args.derive:
            post_derived_text_versions()

