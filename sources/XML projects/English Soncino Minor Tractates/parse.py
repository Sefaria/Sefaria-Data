# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sources.functions import *
from sefaria.model import *
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from sefaria.helper.schema import *
import bleach
import os
def reorder_modify(text):
    return bleach.clean(text, strip=True)

post_info = {}
post_info["language"] = "en"
post_info["server"] = "http://ste.sandbox.sefaria.org"
allowed_tags = ["book", "minor", "intro", "chapter", "bibl", "part", "p", "ftnote", "img", "title", "ol", "footnotes", "appendix", "h1"]
allowed_attributes = ["id", "src"]
p = re.compile("\d+a?\.")

files = [f for f in os.listdir(".") if f.endswith(".xml")]
for f in files:
    print(f)
    post_info["versionTitle"] = "Commentary on the Torah by Ramban (Nachmanides). Translated and annotated by Charles B. Chavel. New York, Shilo Pub. House, 1971-1976"
    post_info["versionSource"] = "https://www.nli.org.il/he/books/NNL_ALEPH002108945/NLI"
    title = f.replace("_", " ")[:-4]
    versionInfo = [["Index Title", title],
                   ["Version Title",
                    "The Minor Tractates of the Talmud, trans. A. Cohen, London: Soncino Press, 1965"],
                   ["Language", "he"],
                   ["Version Source", "https://www.nli.org.il/he/books/NNL_ALEPH002035163/NLI"],
                   ["Version Notes", ""]]
    books = {}
    curr = "Introduction"
    skip_next = False
    with open(f) as open_f:
        lines = list(open_f)
        for n, line in enumerate(lines):
            if skip_next:
                skip_next = False
            else:
                if line == "<book>\n":
                    if lines[n+1].startswith("<title>"):
                        curr = lines[n+1].replace("<title>", "").replace("</title>", "").strip()
                        skip_next = True
                    assert curr not in books
                    books[curr] = line
                elif line not in ["<minor>\n"]:
                    books[curr] += line
                elif line == "</book>\n":
                    books[curr] += line

    for curr, book in books.items():
        print(curr)
        before_words = bleach.clean(book, strip=True).count(" ")
        parser = XML_to_JaggedArray(curr, book, allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images",
                                    titled=True, print_bool=True, remove_chapter=False, versionInfo=versionInfo)
        parser.set_funcs(reorder_modify=reorder_modify)
        parser.run()
        after_words = parser.word_count
        print(after_words-before_words)
