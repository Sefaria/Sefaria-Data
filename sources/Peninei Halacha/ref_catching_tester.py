# -*- coding: utf-8 -*-
import django
django.setup()
from sefaria.model import *
from sources.functions import *

VERSION_TITLE = "NOAH"
VERSION_SOURCE = "RAPOPORT"
ma_re = re.compile(u"\((?<!\u05e8)\u05de\"\u05d0 .*\)")

def parse():
    text = [[u"(ערוך השולחן, אורח חיים רס, ו)",
             u"(בראשית א, א)",
             u"(רמב\"ם, הלכות שבת ל, ז)",
             u"""(רש"י שם; רמב"ן על שמות כ, ח).""",
             u"""(מ"א רמב, א)""",
             u"""(רמ"א רמב, א)"""]]

    for n, t in enumerate(text[0]):
        match = re.search(ma_re, t)
        if match:
            text[0][n] = t.replace(match.group(), match.group().replace(u"\u05de\"\u05d0 ",
                                                                         u"\u05de\u05d2\u05df \u05d0\u05d1\u05e8\u05d4\u05dd "))
    return text

def post_index_to_server(en, he):
    root = JaggedArrayNode()
    comm_en = "Noah Rapoport on {}".format(en)
    comm_he = u"נח על {}".format(he)
    root.add_primary_titles(comm_en, comm_he)
    root.add_structure(["Chapter","Paragraph"])
    root.validate()
    index = {
        "dependence": "Commentary",
        "title": comm_en,
        "collective_title": "Noah Rapoport",
        "schema": root.serialize(),
        "categories": ["Halakhah"]
    }
    post_index(index, server=SEFARIA_SERVER)


def post_text_to_server(text, en):
    send_text = {
        "text": text,
        "versionTitle": VERSION_TITLE,
        "versionSource": VERSION_SOURCE,
        "language": "he"
    }
    post_text("Noah Rapoport on {}".format(en), send_text, server=SEFARIA_SERVER)


if __name__ == "__main__":
    text = parse()
    # add_term("Noah Rapoport", u"נח רפפורט")

    post_index_to_server("Noah's Book", u"ספר נח")
    post_text_to_server(text, "Noah's Book")