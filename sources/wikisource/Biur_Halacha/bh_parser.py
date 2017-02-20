# -*- coding: utf-8 -*-
import os, sys, re

import urllib2
from bs4 import BeautifulSoup

p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)

from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from sefaria.model import *

from sources.functions import numToHeb, getGematria, post_index, post_text
from sefaria.datatype import jagged_array
from data_utilities.util import ja_to_xml, traverse_ja

reload(sys)
sys.setdefaultencoding("utf-8")


simanim_ja = jagged_array.JaggedArray([[[]]]) #JA of Simanim[Seifim[comments]]]


def soupAndOpen(filename):
    with open(filename, "r") as file:
        page = file.read()
        return BeautifulSoup(page)

def is_titled_seif(tag):
    return tag.has_attr('title') and u"סעיף" in tag['title']


def getSeifNumber(txt):
    assert u"סעיף" in txt
    seif_number_he = txt.split(' ')[1]
    return getGematria(seif_number_he)


def isSeifTitle(comment):
    return len(comment.text) < 9 and u"סעיף" in comment.text \
           or comment.name == "h3" or comment.name == "h2" or comment.name == "script"


def regularParse(soup, siman_num):

    seif_titles = soup.find_all("span",
                               class_="mw-headline")

    for seif_title in seif_titles:

        seif_num = getSeifNumber(seif_title.text)

        seif = seif_title.parent

        comment_text = ""
        comments_text = []

        comments = seif.find_next_siblings()

        for comment in comments:

            if isSeifTitle(comment): break

            if comment.b:  # has a new comment with new dibur hamatchil

                if comment_text: comments_text.append(comment_text)

                comment_text = comment.text.strip()

            else:  # part of the previous comment
                comment_text += comment.text.strip()

        if comment_text: comments_text.append(comment_text.strip())

        simanim_ja.set_element([siman_num - 1, seif_num - 1], comments_text, [])



def outlierParse(soup, siman_num):

    content = soup.find("div", class_="mw-content-rtl")

    seif_titles = content.find_all_next("p")

    for seif_title in seif_titles:

        seif_num = getSeifNumber(seif_title.text)

        comments_text = []

        comments = seif_title.find_next('ul')

        for comment in comments.find_all("li"):
            comments_text.append(comment.text.strip())

        simanim_ja.set_element([siman_num - 1, seif_num - 1], comments_text, [])


opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]
page = opener.open("https://he.wikisource.org/w/index.php?title=%D7%91%D7%99%D7%90%D7%95%D7%A8_%D7%94%D7%9C%D7%9B%D7%94&printable=yes")
soup = BeautifulSoup(page)

sections = []
start = 1 # start of first section of halachot
end = 0 # end is added to start

section_titles = soup.find_all("span", class_="mw-headline")

for section_title in section_titles:

    section = section_title.parent
    siman_headers = section.find_next_sibling("p")

    if siman_headers:
        start = end + 1
        end = siman_headers.text.count("|") + start
        sections.append([section_title.text, start, end])


files = os.listdir("./pages")

for filename in files: #696 simanim in O.C.

    siman_num = int(filename.split('.')[1])  # get siman number from title

    if siman_num is 5 or siman_num is 6:
        print "not real", siman_num
        continue # 5 & 6 are simanim with no text but a page

    soup = soupAndOpen("./pages/%s" % (filename))

    if siman_num is 3 or siman_num is 4 or siman_num is 7: #siman numbers that did not conform to be able to parse
        print "outlier", siman_num
        outlierParse(soup, siman_num)

    else:
        print "regular", siman_num
        regularParse(soup, siman_num)


ja_to_xml(simanim_ja.array(), ["siman", "seif", "comment"])


links = []

for comment in traverse_ja(simanim_ja.array()):
    links.append({
        'refs':[
            'Shulchan_Arukh, Orach_Chayim.{}.{}'.format(comment['indices'][0] - 1, comment['indices'][1] - 1),
            'Biur Halacha.{}.{}.{}'.format(*[i - 1 for i in comment['indices']])
        ],
        'type': 'commentary',
        'auto': True,
        'generated_by': 'Biur Halacha linker'
    })

index_schema = JaggedArrayNode()
index_schema.add_primary_titles("Biur Halacha", u"ביאור הלכה")
index_schema.add_structure(["Siman", "Seif", "Comment"])
index_schema.validate()


alt_schema = SchemaNode()

for section in sections:
    map_node = ArrayMapNode()
    map_node.add_title(section[0], "he", True)
    map_node.add_title("temp", "en", True)
    map_node.wholeRef = "Biur Halacha.{}-{}".format(section[1], section[2])
    map_node.includeSections = True
    map_node.depth = 0
    map_node.validate()

    alt_schema.append(map_node)

index = {
    "title": "Biur Halacha",
    "base_text_mapping": "commentary_increment_base_text_depth",
    "dependence": "Commentary",
    "categories": ["Halakhah", "Commentary", "Shulchan Arukh"],
    "schema": index_schema.serialize(),
    "alt_structs": { "Categories": alt_schema.serialize() },
    "base_text_titles": ["Shulchan Arukh, Orach_Chayim"]
}


post_index(index)

text_version = {
    'versionTitle': "Biur Halacha",
    'versionSource': "https://he.wikisource.org/wiki/%D7%91%D7%99%D7%90%D7%95%D7%A8_%D7%94%D7%9C%D7%9B%D7%94",
    'language': 'he',
    'text': simanim_ja.array()
}

post_text("Biur Halacha", text_version, weak_network=True)
