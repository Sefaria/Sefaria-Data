# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
import re
from sources.functions import *
from sefaria.model import *
from codecs import *

headers = headers = """A person may not allow one’s fear of heaven to override his natural morality





Just as [we] must elevate [our] fallen thoughts and traits



The insolence at the time preceding the Messiah comes about










The essence of learning Torah for its own sake


There are various causes of depression





Two levels of Divine Providence








The rectification of the political state as a whole









The nefesh of the sinners of Israel in the era preceding the coming of the Messiah



















The more a person loves people



There is no room to ask about the source of a person’s knowledge of supernal information


It is the yearnings that transcend the entire world that give the world life and happiness




At times, when there is a need to disregard words of Torah









Holy people must truly be natural people

A person’s instinct is swifter and more exact than his or her intellectual recognition

Just as supernal holy people have no connection to mundane and trivial concerns / In the days preceding the coming of the Messiah, whoever connects










Torah sages are perfected by means of the unlearned masses



Impurities in understanding of divinity






I love all




Consciousness of God flees a blemished, splintered, and incomplete life for a life that is whole, outstanding, and full







Understanding of divinity at the level of zeir anpin and arikh anpin





When a person sins, that person is in the world of separation




The insolence at the time preceding the Messiah is a diminution of light / Without the insolence preceding the Messiah, it would be impossible to explain secrets of the Torah







The feeling of love must develop in all of its details




To provide a contrast to those studious people who are scrupulous about constant perseverance


When set against the supernal, divine truth, there is no difference whatsoever between imagined faith and heresy







When [our] divine enlightenment is small







It is proper to yearn to be bound to the entire nation of Israel



A great soul yearns to spread over everything







Morality will not stand without its source








There is a quality within the particular individuality of every person that is higher and more elevated than [the quality] of the communal nature that exists in the nation


Our temporary existence is a single spark of eternal existence, of the splendor of the utterly eternal




All descents of supernal tzadikim from their glory



The essence of hearing the voice of God is that we take heed of the entire process of the ways of life


When people think about divinity, at times their thought proceeds in a form that negates the world



At times, a person cannot engage in learning Torah




Trivial matters can be elevated only by means of the revelation of secrets of Torah






When a person suffers from a smallness of faith






There are certain rectifications of the world that cannot be accomplished by tzadikim


Spiritual rebellion will take place in the land of Israel
















Faith with which intellect does not agree arouses anger and cruelty








When one truly looks at the good aspect of every individual


Heresy’s spirit of smashing through barriers purifies all of the infection


“I am in the midst of the exile”















There are three stages upon which the individual and collective perfection of Israel must be based





As the spirit of freedom grows more at home in the world""".splitlines()
headers = [h.strip() for h in headers if h.strip()]
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
    links = []
    for group in groups:
        segments = group.split("\r\n")
        segments[0] = segments[0].replace(".", ":")
        link = u"Commentary on Selected Paragraphs of Arpilei Tohar {}".format(segments[0])
        assert segments[-1] == ""
        text[link] = []
        for i, segment in enumerate(segments[1:-1]):
            match = re.compile(u"\(\d+\)\s(.*)").match(segment)
            if match:
                text[link].append(match.group(1))
                links.append({"type": "Commentary", "auto": True, "generated_by": "arpilei_to_shmoneh",
                              "refs": ["{}:{}".format(link, i + 1), "Shmonah Kvatzim {}:1".format(segments[0])]})
            else:
                len_text = len(text[link]) - 1
                text[link][len_text] += "<br><br>"+segment
    post_link(links)
    return text


def create_schema():
    root = JaggedArrayNode()
    en, he = """Commentary on Selected Paragraphs of Arpilei Tohar / ביאורים על קטעים נבחרים מתוך ערפילי טוהר""".split(" / ")
    root.add_primary_titles(en, he)
    root.add_structure(["Kovetz", "Comment", "Paragraph"])

    index = {
        "schema": root.serialize(),
        "title": en,
        "dependence": "Commentary",
        "base_text_titles": ["Shmonah Kvatzim"],
        "categories": ["Philosophy", "Commentary"]
    }
    post_index(index)


if __name__ == "__main__":
    create_schema()
    text = get_text(codecs.open("arpillei tohar.txt", 'rb', 'cp1252'))
    for ref, header in list(zip(text.keys(), headers)):
        text[ref][0] = "<b>{}</b><br>".format(header) + text[ref][0]
        send_text = {
            "text": text[ref],
            "language": "en",
            "versionTitle": "Selected Paragraphs from Arfilei Tohar, comm. Pinchas Polonsky",
            "versionSource": "http://orot-yerushalaim.org/books/Arfilei_Tohar.pdf"
        }
        post_text(ref, send_text)

    pass