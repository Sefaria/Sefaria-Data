# -*- coding: utf-8 -*-
"""
ditch regex in DM
BS chidlren cycle thru html elements or navstring to construct segments
issues:
- how to deal with intro/outro of mishnah commentary i.e. 1:5

key:
new mishnah: p class: u"_-המשנה-בירוק-שורה-1"
lines of mishnah: p class: u"_-המשנה-בירוק"
running text: p class: u"_טקסט-רץ"
mishnah in commentary: span class: u"_-פירוש-בירוק"
:: after mishnah: span class: u"_-"
dashes in commentary: span class: u"CharOverride-25"
green headlines: p class u"_-כותרת-ירוקה"
perek/amud: p class: u"_-מספר-עמוד ParaOverride-9"
page number: p class: u"_-מספר-עמוד"
pic info: p class: u"__כיתוב-לתמונה"
          p class: u"_-שם-התמונה"

DM:
DMs = p.find_all('span', {"class": u"_-פירוש-בירוק"})
for DM in DMs:
    if DMs.index(DM) < len(DMs) - 2:
        if re.search(u'{} :: (.*){} ::'.format(DM.text, DMs[DMs.index(DM) + 1].text), soup.text):
            text = re.search(u'{} :: (.*){} ::'.format(DM.text, DMs[DMs.index(DM) + 1].text), soup.text).group(1)
        else:
            DMs[DMs.index(DM) + 1].replace_with(DM.text + DMs[DMs.index(DM) + 1].text)
            continue
    else:
        try:
            text = re.search(u'{} :: (.*)'.format(DM.text), soup.text).group(1)
        except AttributeError:
            print DM.text
    segments.append(u'<b>{}</b> {}'.format(DM.text, text))

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
            chunk = p.text.strip()
            segments.append(chunk)
        elif contains_mishna(p):
            chunk = u''
            for child in p.children:
                if not child.name:
                    chunk += unicode(child)
                    continue
                if child["class"][0] is u"_-פירוש-בירוק":
                    if chunk:
                        segments.append(chunk)
                    if child.next_sibling["class"][0] is u"_-פירוש-בירוק":
                        chunk = next(child).text.replace(child.text, u'<b>' + child.previous_sibling.text + child.text + u'.</b>')
                    else:
                        chunk = child.text.replace(child.text, u'<b>' + child.text + u'.</b>')
                if child["class"][0] is u"_-":
                    continue
                if child["class"][0] is u"CharOverride-25":
                    chunk += child.text
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

    schema = JaggedArrayNode()
    schema.add_primary_titles(u'', u'')
    schema.add_structure(["Chapter", "Verse", "Comment"])
    schema.validate()

    index = {
        "title": "",
        "categories": [],
        "schema": schema.serialize()
    }

    return index

def upload_text(parsed_text):

    version = {
            "versionTitle": "",
            "versionSource": "",
            "language": 'he',
            "text": parsed_text
        }
    functions.post_text("", version, index_count='on')

def build_links(parsed_text):
    pass


html_path = u'/Users/joelbemis/Documents/programming/Sefaria-Data/sources/Shinan/Avot_71.html'
csv_path = u'/Users/joelbemis/Documents/programming/Sefaria-Data/sources/Shinan/map.csv'


if __name__ == '__main__':
    jagged_array = parse(html_path, csv_path)
    util.ja_to_xml(jagged_array, ['Chapter', 'Verse', 'Commentary'])
    #functions.post_index(build_index())
    #upload_text(jagged_array)
    #functions.post_link(build_links(jagged_array))
