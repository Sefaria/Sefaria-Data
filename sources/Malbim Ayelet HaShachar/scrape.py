#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from sources.functions import *
import requests
import bleach
from bs4 import BeautifulSoup, Tag
first_half = "https://he.wikisource.org/wiki/%D7%90%D7%99%D7%9C%D7%AA_%D7%94%D7%A9%D7%97%D7%A8_(%D7%9E%D7%9C%D7%91%D7%99%22%D7%9D)/%D7%A4%D7%A8%D7%A7%D7%99%D7%9D_%D7%90_-_%D7%9C"
second_half = "https://he.wikisource.org/wiki/%D7%90%D7%99%D7%9C%D7%AA_%D7%94%D7%A9%D7%97%D7%A8_(%D7%9E%D7%9C%D7%91%D7%99%22%D7%9D)/%D7%A4%D7%A8%D7%A7%D7%99%D7%9D_%D7%9C%D7%90_-_%D7%A0%D7%93"
text = {}
perakim = {}
old_perek = curr_perek = None
curr_klal = None

def get_formatted_element(el):
    return bleach.clean(str(el), tags=["b"], strip=True)

def get_li_elements(el):
    li_elements = []
    for li in el:
        if li != "\n":
            li_elements.append(get_formatted_element(li))
    return li_elements

for url in [first_half, second_half]:
    request = requests.get(url, headers=headers).content
    soup = BeautifulSoup(request, features='lxml')
    output = soup.find("div", {"class": "mw-parser-output"})
    for el in output:
        if not isinstance(el, Tag):
            pass
        elif el.name == "p" and curr_klal:
            text[curr_klal].append(get_formatted_element(el))
        elif el.name == "ul" and curr_klal:
            text[curr_klal] += get_li_elements(el)
        elif el.name == "h2":
            #we find a new perek, then below if new perek, we
            old_perek = curr_perek
            if old_perek and len(perakim[old_perek]) is 1:
                perakim[old_perek].append(curr_klal)
            curr_perek = getGematria(el.text.split()[-1])
            perakim[curr_perek] = []
        elif el.name == "h3":
            curr_klal = getGematria(el.text.split()[-1])
            assert curr_klal not in text
            text[curr_klal] = []
            if perakim[curr_perek] == []:
                perakim[curr_perek].append(curr_klal)
perakim[curr_perek].append(613)
print len(text)
text = convertDictToArray(text)
print text[0]
print text[20]
print text[500]
root = JaggedArrayNode()
root.depth = 2
root.add_primary_titles("Malbim Ayelet HaShachar", u"""אילת השחר (מלבי"ם)""")
root.add_structure(["Klal", "Paragraph"])
root.validate()
indx = {
    "schema": root.serialize(),
    "categories": ["Tanakh", "Commentary"],
    "title": "Malbim Ayelet HaShachar"
}
post_index(indx)
send_text = {
    "text": text,
    "language": "he",
    "versionTitle": "WikiSource",
    "versionSource": "https://he.wikisource.org/wiki/%D7%90%D7%99%D7%9C%D7%AA_%D7%94%D7%A9%D7%97%D7%A8_(%D7%9E%D7%9C%D7%91%D7%99%22%D7%9D)"
}
post_text("Malbim Ayelet HaShachar", send_text)
post_text("Malbim Ayelet HaShachar", send_text, server="http://localhost:8000")