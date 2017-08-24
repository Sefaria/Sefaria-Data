# -*- coding: utf-8 -*-
"""
issues:
- fix problematic entries
    - what if 3 perush ha mishna in a row? (<span class="_-פירוש-בירוק">וְהַמִּכְתָּב</span>)
- linking (only running commentary, but not just dibbur mathils)

ranged:

פרק ב      משניות י-יא (doesn't matter)
פרק ג      משניות יא-יב (doesn't matter)
x פרק ד      משניות ט
x פרק ד      משניות י
פרק ד      משניות כו-כז  (doesn't matter)
פרק ה      משניות ב-ג (doesn't matter)
פרק ה      משניות ה-ו (doesn't matter)
x פרק ה      משניות יד-טו
x פרק ה      משניות יז-יח
x פרק ה      משניות כה-כו
x פרק ו     משניות א-ג
x פרק ו     משניות ד-ו
x פרק ו     משניות ז-י
x פרק ו      משניות י-יא

"""
import re
import csv
import os
import io
import sys
import pdb
import codecs
from bs4 import BeautifulSoup
from bs4.element import NavigableString
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from data_utilities import util
from sources.local_settings import *
from sources import functions
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.datatype.jagged_array import JaggedArray
from sefaria.utils.hebrew import decode_hebrew_numeral as gematria

def parse(html_page, csv_page):

    def useless(html_fragment):
        soup = html_fragment
        if soup["class"][0] == u'_-המשנה-בירוק' or u"_-שם-התמונה" or u"__כיתוב-לתמונה":
            return True
        return False


    def end_of_irrelevant(html_fragment):
        soup = html_fragment
        if soup["class"][0] == u"_-המשנה-בירוק-שורה-1":
            return True
        return False


    def contains_loc(html_fragment):
        soup = html_fragment
        if soup["class"][0] == u"_-מספר-עמוד" and re.match(u'פרק', soup.text):
            return True
        return False


    def contains_range(html_fragment):
        soup = html_fragment
        if re.search(u'משניות', soup.text):
            return True
        return False


    def contains_headline(html_fragment):
        soup = html_fragment
        if soup["class"][0] == u"_-כותרת-ירוקה":
            return True
        return False


    def contains_mishna(html_fragment):
        soup = html_fragment
        if soup.find('span', {"class": u"_-פירוש-בירוק"}):
            return True
        return False


    def contains_commentary(html_fragment):
        soup = html_fragment
        if soup["class"][0] == u"_טקסט-רץ":
            return True
        return False


    def get_chapter(html_fragment):
        soup = html_fragment
        return str(gematria(re.search(u'פרק (.)', soup.text).group(1)))

    def get_mishna(html_fragment):
        soup = html_fragment
        if contains_range(soup):
            return str(gematria(re.search(u'משניות (.*)-.*', soup.text).group(1)))
        return str(gematria(re.search(u'משנה (.*)', soup.text).group(1)))


    def get_loc(html_fragment):
        soup = html_fragment
        location = {
            'map': get_chapter(soup) + u':' + get_mishna(soup),
            'ch': get_chapter(soup),
            'mishna': get_mishna(soup)
        }
        return location


    def convert_to_vilna(vilna_string):
        location = {
            'map': vilna_string,
            'ch': vilna_string[:1],
            'mishna': re.search(u':(.*)', vilna_string).group(1)
        }
        return location

    tracker = False
    chapters, mishnayot, segments = {}, {}, []
    cur_loc = {'map': '1:1', 'ch': '1', 'mishna': '1'}

    infile = io.open(csv_page, 'r')
    reader = csv.reader(infile)
    mishna_map = dict((row[0], row[1]) for row in reader)
    infile.close()

    infile = io.open(html_page, 'r')
    soup = BeautifulSoup(infile, 'html5lib')
    infile.close()

    for p in soup.find_all('p'):
        if tracker == False:
            if end_of_irrelevant(p):
                tracker = True
            else:
                continue

        if contains_loc(p):
            new_loc = get_loc(p)

            # reconcile clashes between shinan / vilna strutures
            if mishna_map[new_loc['map']] != new_loc['map']:
                new_loc = convert_to_vilna(mishna_map[new_loc['map']])

            # store previous mishna
            if cur_loc['mishna'] != new_loc['mishna'] and segments:
                mishnayot[int(cur_loc['mishna'])] = segments
                segments = []

            # store previous chapter
            if cur_loc['ch'] != new_loc['ch'] and mishnayot:
                chapters[int(cur_loc['ch'])] = mishnayot
                mishnayot = {}

            cur_loc = new_loc

        if contains_headline(p):
            chunk = p.text.replace(p.text, u"<b>" + p.text.strip() + "</b>")
            segments.append(chunk)
        elif contains_mishna(p):
            for child in p.children:
                if isinstance(child, NavigableString):
                    if child == u' ' or child == u'.':
                        p.contents[p.index(child) - 1].append(child)
            chunk = u''
            for child in p.children:
                if isinstance(child, NavigableString):
                    chunk += unicode(child)
                elif child["class"][0] == u"CharOverride-25":
                    chunk += child.text
                elif child["class"][0] == u"_-פירוש-בירוק":
                    if child.text == u' ' or child.text == u'.':
                        continue
                    if child.previous_sibling is None:
                        if isinstance(child.next_sibling, NavigableString):
                            chunk = child.text.replace(child.text, u'<b>' + child.text.strip() + u'.</b>')
                        elif child.next_sibling["class"][0] == u'_-':
                            chunk = child.text.replace(child.text, u'<b>' + child.text.strip() + u'.</b>')
                        elif child.next_sibling["class"][0] == u'_-פירוש-בירוק':
                            chunk = child.text.replace(child.text, u'<b>' + child.text.strip() + child.next_sibling.text.strip() + u'.</b>')
                    elif isinstance(child.previous_sibling, NavigableString):
                        segments.append(chunk)
                        if isinstance(child.next_sibling, NavigableString):
                            print(child)
                            continue
                        elif child.next_sibling["class"][0] == u'_-':
                            chunk = child.text.replace(child.text, u'<b>' + child.text.strip() + u'.</b>')
                        elif child.next_sibling["class"][0] == u'_-פירוש-בירוק':
                            chunk = child.text.replace(child.text, u'<b>' + child.text.strip() + child.next_sibling.text.strip() + u'.</b>')
                    elif child.previous_sibling["class"][0] == u'_-פירוש-בירוק':
                        continue
            else:
                segments.append(chunk)
        elif contains_commentary(p):
            chunk = p.text.strip()
            segments.append(chunk)
    else:
        mishnayot[int(cur_loc['mishna'])] = segments
        chapters[int(cur_loc['ch'])] = mishnayot


    for chapter in chapters.keys():
        chapters[chapter] = util.convert_dict_to_array(chapters[chapter])
    chapters = util.convert_dict_to_array(chapters)
    return chapters


def build_index():

    root = SchemaNode()
    root.add_primary_titles(u"פירוש ישראלי חדש על פרקי אבות", "A New Israeli Commentary on Pirkei Avot")
    leaf = JaggedArrayNode()
    leaf.add_primary_titles("Introduction")
    leaf.add_structure(["Paragraph"])
    root.append(leaf)
    defaultLeaf = JaggedArrayNode()
    defaultLeaf.add_structure(["Chapter", "Mishnah", "Commentary"])
    defaultLeaf.key = "default"
    defaultLeaf.default = True
    root.validate()

    index = {
        "title": "A New Israeli Commentary on Pirkei Avot",
        "categories": ["Mishnah", "Seder Nezikin", "Commentary"],
        "schema": root.serialize()
    }

    return index

def upload_text(parsed_text):

    intro = {
        "versionTitle": "Pirke Avot, a New Israeli Commentary, by Avigdor Shinan; Jerusalem, 2009",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002690779",
        "language": 'he',
        "text": parsed_intro
    }
    content = {
        "versionTitle": "Pirke Avot, a New Israeli Commentary, by Avigdor Shinan; Jerusalem, 2009",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002690779",
        "language": 'he',
        "text": parsed_text
    }
    functions.post_text("A New Israeli Commentary on Pirkei Avot, Introduction", intro)
    functions.post_text("A New Israeli Commentary on Pirkei Avot", content, index_count='on')

def build_links(parsed_text):
    pass


html_path = u'/Users/joelbemis/Documents/programming/Sefaria-Data/sources/Shinan/Avot_71.html'
csv_path = u'/Users/joelbemis/Documents/programming/Sefaria-Data/sources/Shinan/map.csv'


if __name__ == '__main__':
    jagged_array = parse(html_path, csv_path)
    util.ja_to_xml(jagged_array, ['Chapter', 'Mishnah', 'Comment'])
    #functions.post_index(build_index())
    #upload_text(jagged_array)
    #functions.post_link(build_links(jagged_array))
