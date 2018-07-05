#encoding=utf-8
import django
django.setup()
import requests
from sources.functions import convertDictToArray, post_text, post_index
from bs4 import BeautifulSoup, element
from sefaria.model import *
from data_utilities.XML_to_JaggedArray import roman_to_int
import re

def create_index():
    root = SchemaNode()
    root.add_primary_titles("The War of the Jews", u"מלחמת היהודים")
    preface = JaggedArrayNode()
    preface.add_structure(["Paragraph"])
    preface.add_shared_term("Preface")
    preface.key = "preface"
    content = JaggedArrayNode()
    content.default = True
    content.key = "default"
    content.add_structure(["Book", "Chapter", "Paragraph"])
    root.append(preface)
    root.append(content)
    root.validate()
    index = {
        "title": "The War of the Jews",
        "schema": root.serialize(),
        "categories": ["Other"]
    }
    post_index(index, "http://proto.sefaria.org")


def check_for_footnote(text, footnotes):
    if len(text.contents) > 1: #has footnote
        new_line = ""
        for line in text.contents:
            if type(line) is element.NavigableString:
                new_line += line + " "
            else:
                new_line = new_line.strip()
                num_in_footnote = re.compile("\[(\d+)\]").match(line.text).group(1)
                num_in_footnote = int(num_in_footnote)
                ftnote = footnotes[num_in_footnote-1].replace(u"↑", u"").replace(u"^", u"").strip()
                ftnote = u"<sup>{}</sup><i class='footnote'>{}</i>".format(num_in_footnote, ftnote)
                new_line += ftnote

        new_line = new_line.strip()
        return_text = new_line
    else:
        return_text = text.text
    return return_text


if __name__ == "__main__":
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    books = ["I", "II", "III", "IV", "V", "VI", "VII"]
    relevant_text = lambda x: x if type(x) is element.NavigableString else x.text
    text = {}
    footnotes = {}
    for book_n, book in enumerate(books):
        # should have dictionary that stores footnotes, and dictionary that stores text
        text[book_n] = {}
        footnotes[book_n] = []
        title = "Book_{}".format(book)
        with open(title) as f:
        # site = requests.get("http://en.wikisource.org/wiki/The_War_of_the_Jews/Book_{}".format(book), headers=headers).content
        # title = "http://en.wikisource.org/wiki/The_War_of_the_Jews/Book_{}".format(book).rsplit("/", 1)[1]
        # with open(title, 'w') as f:
        #     f.write(site)
            soup = BeautifulSoup(f, "lxml")
            chapter_headers = [poss for poss in soup.find_all("h2") if len(poss.contents) > 1]
            chapter_content = soup.find_all("ol")
            footnote_ch = chapter_content[-1]
            [footnotes[book_n].append(line.text) for line in footnote_ch.contents if line != "\n"]
            for ch_num, chapter in enumerate(chapter_content):
                #look for header which is just above the chapter itself
                print ch_num+1
                previous = chapter.previous
                while len(previous) < 7: #don't include "[edit]"...looking for actual header
                    previous = previous.previous
                header = previous
                chapter_header = unicode(header)

                #now look for "Chapter 1" or "Footnotes" which is above header
                title = header
                while not relevant_text(title).startswith("Chapter") and not relevant_text(title) == "Footnotes":
                    title = title.previous

                if title.startswith("Chapter"):
                    roman_num = title.split()[-1]
                    if not roman_num.isdigit():
                        roman_num = roman_to_int(roman_num.encode('utf-8'))
                    else:
                        roman_num = int(roman_num)
                    if roman_num != ch_num+1:
                        text[book_n] = "Error at Chapter {}".format(roman_num)
                        continue

                    lines = [check_for_footnote(line, footnotes[book_n]) for line_n, line in enumerate(chapter.contents) if line != "\n"]
                    lines = [(str(i+1) + ". " + line) for i, line in enumerate(lines)]
                    text[book_n][roman_num] = lines
                    first_line = text[book_n][roman_num][0]
                    text[book_n][roman_num][0] = u"<b>"+chapter_header+u"</b><br/><br/>"+first_line
            text[book_n] = convertDictToArray(text[book_n])

    create_index()
    text = convertDictToArray(text)

    body_text = {
        "text": text,
        "language": "en",
        "versionTitle": "The War of the Jews, translated by William Whiston",
        "versionSource": "https://en.wikisource.org/wiki/The_War_of_the_Jews"
    }
    post_text("The War of the Jews", body_text, server="http://proto.sefaria.org")
