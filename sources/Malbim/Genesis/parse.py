import re
import os
import sys
import argparse
import unicodecsv
import local_settings
from bs4 import BeautifulSoup, element
from sefaria.model.text import library
from sefaria.datatype.jagged_array import JaggedArray
from sefaria.utils.talmud import daf_to_section, section_to_daf
from sefaria.utils.hebrew import decode_hebrew_numeral as gematria
from sefaria.utils.hebrew import decompose_presentation_forms_in_str as normalize_he

def createIndex(enTitle):
    heTitle = getHebrewTitle(enTitle)

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
        "base_text_titles": [enTitle],
        "collective_title": "",
        "dependence": "",

    }

    post_index(index)


def parseChapter(name):
'''
:param:
:url: url of malbim html to parse
return: jagged array
'''

    f = open("./pages/%s" % (name), "r")
    page = f.read()
    f.close()

    soup = BeautifulSoup(page)

    pz = soup.find_all('p')

    Malbim = JaggedArray([[]])

    parsed = {
		"language": "he",
		"versionTitle": "Malbim on Genesis -- Wikisource ",
		"versionUrl": "https://he.wikisource.org/wiki/%D7%9E%D7%9C%D7%91%D7%99%22%D7%9D_%D7%A2%D7%9C_%D7%91%D7%A8%D7%90%D7%A9%D7%99%D7%AA",
		"text": []
	}

	for i in range(len(pz)):
		line = ""
		next = pz[i].nextSibling
		while next:
            if next is question:
                line += "<b>" next.text.encode("utf-8")
            if next is commentary:
                DM(next)
                line += next.text.encode("utf-8")



def parseAll():
	files = os.listdir("./pages")

	for f in files:
		print "parsing %s" % f
		parsed = parseChapter(f)
		f = open("./parsed/%s" %(f), "w")
		f.write(json.dumps(parsed, indent=4))
		f.close()
