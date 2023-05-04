#encoding=utf-8
import django
django.setup()
import re
from sefaria.model import *
from bs4 import BeautifulSoup, element
from sources.functions import convertDictToArray, post_text, post_index
from parsing_utilities.XML_to_JaggedArray import int_to_roman, roman_to_int
import requests
import os


def get_ch_num(line):
    ch_num = line.split()[-1]
    ch_num = ch_num.replace(".", "")
    if ch_num.isdigit():
        ch_num = int(ch_num)
    else:
        ch_num = roman_to_int(str(ch_num))
    return ch_num

def render(p, ftnotes):
    running_str = u""
    for item in p.contents:
        if isinstance(item, element.NavigableString):
            running_str += unicode(item)
        elif item.name == "span":
            print "Ignored span"
            print item.text + "\n"
        elif item.name == "sup":
            assert item.attrs['class'] == ['reference']
            digit = re.compile(u".*?(\d+).*?").match(item.text).group(1)
            digit = int(digit)
            i_tag = u'<sup>{}</sup><i class="footnote">{}</i>'.format(digit, ftnotes[digit-1])
            i_tag = i_tag.replace(u"↑", u"").replace(u"^", u"").strip()
            running_str += i_tag
        else:
            pass
            running_str += str(item)
    return running_str


def get_ftnotes(soup):
    ftnotes = soup.find("ol", {"class": "references"})
    if not ftnotes:
        return []

    ftnotes_as_text = []
    for ftnote in ftnotes:
        if isinstance(ftnote, element.Tag):
            ftnotes_as_text.append(ftnote.text)

    #check that there are this many ftnotes
    actual_ftnotes = soup.find_all("sup", {"class": "reference"})
    assert len(actual_ftnotes) == len(ftnotes_as_text)
    return ftnotes_as_text



if __name__ == "__main__":
    # headers = {
    #     'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    # for i in range(1, 21):
    #     response = requests.get("https://en.wikisource.org/wiki/The_Antiquities_of_the_Jews/Book_{}".format(int_to_roman(i)), headers=headers)
    #     new_file = open("Antiquities_Book_{}".format(i), 'w')
    #     new_file.write(response.content)
    root = SchemaNode()
    root.add_primary_titles("The Antiquities of the Jews", u"קדמוניות היהודים")
    root.key = "antiquities"
    intro = JaggedArrayNode()
    intro.add_shared_term("Preface")
    intro.add_structure(["Paragraph"])
    intro.key = "preface"
    root.append(intro)
    default = JaggedArrayNode()
    default.default = True
    default.key = "default"
    default.add_structure(["Book", "Chapter", "Comment"])
    root.append(default)
    root.validate()
    index = {
        "schema": root.serialize(),
        "title": "The Antiquities of the Jews",
        "categories": ["Other"]

    }


    files = [f for f in os.listdir(".") if f.startswith("Antiquities_")]
    files = sorted(files, key=lambda x: int(x.split("_")[-1]))
    books = {}
    for count, f in enumerate(files):
        books[count+1] = []
        ch_num = ch_num_should_be = 0
        text = {}
        with open(f) as file:
            print f
            soup = BeautifulSoup(file, 'lxml')
            ftnotes = get_ftnotes(soup)
            lines = [render(p, ftnotes) for p in soup.find_all("p")]
            for line_n, line in enumerate(lines):
                if line.lower().startswith("chapter") and len(line.split()) == 2:
                    ch_num_should_be = get_ch_num(line)
                    ch_num += 1
                    if ch_num_should_be != ch_num:
                        print "{} vs {}".format(ch_num_should_be, ch_num)
                    text[ch_num_should_be] = []
                    continue
                elif ch_num == 0: #skip lines before Chapters start
                    continue
                if line.replace(" ", "") != "":
                    text[ch_num_should_be].append(line)
        text = convertDictToArray(text)
        books[count] = text
    books = convertDictToArray(books)
    send_text = {
        "text": books,
        "language": "en",
        "versionTitle": "Wikisource",
        "versionSource": "https://en.wikisource.org/wiki/The_Antiquities_of_the_Jews"
    }
    post_index(index, server="http://proto.sefaria.org")

    post_text("The Antiquities of the Jews", send_text, server="http://proto.sefaria.org")


