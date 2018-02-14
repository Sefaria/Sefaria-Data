# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
import re
from sources.functions import *
from sefaria.model import *
from codecs import *

server = "http://proto.sefaria.org"

def get_text(file):
    lines = ""
    for line in file:
        things_to_replace = {
            u'\xa0': u'',
            u'\u015b': u's',
            u'\u2018': u"'",
            u'\u2019': u"'",
            u'\u2013': u"-",
            u'\u201c': u'"',
            u'\u201d': u'"'
        }
        for thing in things_to_replace:
            line = line.replace(thing, things_to_replace[thing])
        lines += line

    groups = lines.split("@")
    groups = groups[1:]

    text = {}
    for group in groups:
        segments = group.split("\r\n")
        link = u"Arpillei Tohar Commentary {}".format(segments[0])
        assert segments[-1] == ""
        segments = segments[1:-1]
        text[link] = []
        for segment in segments:
            match = re.compile(u"\(\d+\)\s(.*)").match(segment)
            if match:
                text[link].append(match.group(1))
            else:
                len_text = len(text[link]) - 1
                text[link][len_text] += segment

    return text


def create_schema():
    root = JaggedArrayNode()
    root.add_primary_titles("Arpillei Tohar Commentary", u"ביאורים לערפילי טוהר")
    root.add_structure(["Kovetz", "Comment", "Paragraph"])

    index = {
        "schema": root.serialize(),
        "title": "Arpillei Tohar Commentary",
        "dependence": "Commentary",
        "base_text_titles": ["Shmonah Kvatzim"],
        "base_text_mapping": "many_to_one",
        "categories": ["Philosophy", "Commentary"]
    }
    post_index(index, server=server)


if __name__ == "__main__":
    create_schema()
    text = get_text(codecs.open("arpillei tohar.txt", 'rb', 'cp1252'))
    for ref in text:
        send_text = {
            "text": text[ref],
            "language": "en",
            "versionTitle": "Selected Paragraphs from Arfilei Tohar, comm. Pinchas Polonsky",
            "versionSource": "http://orot-yerushalaim.org/books/Arfilei_Tohar.pdf"
        }
        post_text(ref, send_text, server=server)

    pass