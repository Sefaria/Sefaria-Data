#notes:
    # emulate Ruth
    # use bs + collections to better understand the data you're working with
    # parse by line / feed line into soup
    # switch to line by line, then feed through bs
# assumptions:
    #question: contains reference, don't repeat
    #commentary: contains <br />, reference, if commentary contains range, repeats
#fix manually:
    # 2:1-3 only question contains reference, and repeats, but only twice
        #delete second iteration
    # 2:16-17 repeats
        #delelete second occurrence
    # 2:21-25 repeats, but only twice
        #delete second occurrence
    # pasukim in question with ' and " at 8:7
#questions:
    # can we have line breaks within array
    # remove references in she'elot?
        # if range should it link to range of psukim or only first?
    # footnotes as footnotes
import re
import os
import sys
import argparse
import unicodecsv
import local_settings
from bs4 import BeautifulSoup, element
from sefaria.model.text import library
from sefaria.datatype.jagged_array import JaggedArray
from sefaria.utils.hebrew import decode_hebrew_numeral as gematria
from sefaria.utils.hebrew import decompose_presentation_forms_in_str as normalize_he

def get_lines(page):
    with codecs.open(page, 'r', 'utf-8') as infile:
        return infile.readlines()

def get_data(page): # returns object with chapter and verses

    soup = BeautifulSoup(page, 'html5lib')

    chapter = gematria(soup.find('h1').text.strip().rsplit(' ', 1)[1])

    verses = []
    for tag in soup.find_all('a', class_='mw-redirect', string=u'כל הפסוק'):
            verses.append(gematria(p[0].get('title').rsplit(' ', 1)[1]))

    return metadata

def parse(ja, lines, data): # returns jagged array populated with data
    for tag in soup.find_all('h2'):
        if len(list(tag.next_siblings)) > 5):
            if question: (len(list(tag.next_siblings)) > 9)(div containing h3 and p) or search('&#160;&#160;')
                list.append('<b>שאלות: </b>' + p.text)
            if commentary (contains <br />):
                remove (pasuk) from text
                bold DH (span with class_=pasuq )
                if footnote:
                    add into text at
                list.append(pasuk + text)

    for tag in soup.find_all('h2'): # and text != 'תוכן עניינים'
        verse = gematria(tag.child.text.rsplit(' ', 1)[1])
        h3

    chapt = data.perek
    enumerate(verse) = data.pasuk
    for line in lines:
        questions
        commentary
        footnotes
        mal = questions + commentary + footnotes
        ja.set_element([chapt, verse], mal)

        #p's that are sibling of that h2 contain the text i want
        ids = []
        for i in range(len(pz)):
        	line = ""
        	next = pz[i].nextSibling
    		while next:
                if next is question:
                    line += "<b>" next.text.encode("utf-8")
                if next is commentary:
                    DM(next)
                    line += next.text.encode("utf-8")

    print len(soup.find_all('div', style=None, class_=None, id=None))
    divs = soup.find_all('div', style=None, class_=None, id=None)
    for div in divs:
        #skip first
        print len(list(div.children))
        for child in div.children:
            if child.name=='p':
                print child.string


def posterize(text):
    parsed = {
		"language": "he",
		"versionTitle": "Malbim on Genesis -- Wikisource ",
		"versionUrl": "https://he.wikisource.org/wiki/%D7%9E%D7%9C%D7%91%D7%99%22%D7%9D_%D7%A2%D7%9C_%D7%91%D7%A8%D7%90%D7%A9%D7%99%D7%AA",
		"text": text
	}
    heTitle = getHebrewTitle("Malbim")

    root = JaggedArrayNode()
    root.add_title("Malbim on Genesis", "en", primary=True)
    root.add_title(u'מלבי״ם על בראשית', "he", primary=True)
    root.key = "MalbimGenesis"
    root.sectionNames = ["", ""]
    root.depth = 2
    root.addressTypes = ["", ""]


    root.validate()

    index = {
        "title": "Malbim on Genesis",
        "categories": [],
        "schema": root.serialize(),
        "base_text_titles": ['Genesis'],
        "collective_title": "Malbim",
        "dependence": "Commentary",

    }
    #post_index(index)
    #post_text()
    #post_links()

if __name__ == '__main__':
    createIndex()
    malbim = JaggedArray([[]])
    files = os.listdir("./pages")
    for f in files:
        print "parsing %s" % f
        text = get_lines(f)
        important_data = get_data(f)
        parse(malbim, text, important_data)
    posterize(malbim)
