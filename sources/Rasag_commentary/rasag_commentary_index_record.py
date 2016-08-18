# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
# from sources.Match import match_new
from sources.Match.match import Match
from sefaria.model.schema import AddressTalmud, SchemaNode, JaggedArrayNode


def create_index():
    rav_perla = create_schema()
    rav_perla.validate()
    index = {
        "title": "Rav Perla on Sefer Hamitzvot of Rasag",
        "categories": ["Commentary2", "Sefer Hamitzvot of Rasag", "Rav Perla on Sefer Hamitzvot of Rasag"],
        "schema": rav_perla.serialize()
    }
    return index


def create_schema():
    rasag_commentary = SchemaNode()
    rasag_commentary.add_title('Rav Perla on Sefer Hamitzvot of Rasag', 'en', primary=True)
    rasag_commentary.add_title(u'רב פערלא על ספר מצות לרסג', 'he', primary=True)
    rasag_commentary.key = 'Rav Perla on Sefer Hamitzvot of Rasag'
    rasag_commentary.append(create_book_intro_node())
    rasag_commentary.append(create_positive_commandments_node())
    rasag_commentary.append(create_negative_commandments_node())
    rasag_commentary.append(create_onshim_node())
    rasag_commentary.append(create_communal_node())
    rasag_commentary.append(create_miluim_node())
    return rasag_commentary


def create_book_intro_node():
    intro_node = SchemaNode()
    intro_node.add_title('Introduction', "en", primary=True)
    intro_node.add_title(u'מבוא', "he", primary=True)
    intro_node.key = 'Introduction'
    for number in range(1, 7):
        intro_node.append(regular_chapter_nodes(number))
    intro_node.append(chapter_seven(7))
    intro_node.append(regular_chapter_nodes(8))
    intro_node.append(chapter_nine(9))
    for number in range(10, 13):
        intro_node.append(regular_chapter_nodes(number))
    return intro_node


def create_positive_commandments_node():
    positive_commandments = JaggedArrayNode()
    positive_commandments.add_title('Positive Commandments', 'en', primary=True)
    positive_commandments.add_title(u'מנין עשה', 'he', primary=True)
    positive_commandments.key = 'Positive Commandments'
    positive_commandments.depth = 2
    positive_commandments.addressTypes = ["Integer", "Integer"]
    positive_commandments.sectionNames = ["Mitzvah", "Comment"]
    return positive_commandments


def create_negative_commandments_node():
    negative_commandments = JaggedArrayNode()
    negative_commandments.add_title('Negative Commandments', 'en', primary=True)
    negative_commandments.add_title(u'מנין לא תעשה', 'he', primary=True)
    negative_commandments.key = 'Negative Commandments'
    negative_commandments.depth = 2
    negative_commandments.addressTypes = ["Integer", "Integer"]
    negative_commandments.sectionNames = ["Mitzvah", "Comment"]
    return negative_commandments


def create_onshim_node():
    onshim = SchemaNode()
    onshim.add_title('Laws of the Court', 'en', primary=True)
    onshim.add_title(u'מנין העונשין', 'he', primary=True)
    onshim.key = 'Laws of the Court'
    onshim.append(create_intro_nodes())
    onshim.append(create_default_nodes())
    return onshim


def create_communal_node():
    communal = SchemaNode()
    communal.add_title('Communal Laws', 'en', primary=True)
    communal.add_title(u'מנין הפרשיות', 'he', primary=True)
    communal.key = 'Communal Laws'
    communal.append(create_intro_nodes())
    communal.append(create_default_nodes())
    return communal


def create_miluim_node():
    miluim_node = SchemaNode()
    miluim_node.add_title('Appendix', "en", primary=True)
    miluim_node.add_title(u'מלואים', "he", primary=True)
    miluim_node.key = 'Appendix'
    miluim_node.append(create_intro_nodes())
    miluim_node.append(create_default_nodes())
    return miluim_node


def create_intro_nodes():
    intro_node = JaggedArrayNode()
    intro_node.add_title('Introduction', "en", primary=True)
    intro_node.add_title(u'הקדמה', "he", primary=True)
    intro_node.key = 'Introduction'
    intro_node.depth = 1
    intro_node.addressTypes = ["Integer"]
    intro_node.sectionNames = ["Comment"]
    return intro_node

def create_default_nodes():
    default = JaggedArrayNode()
    default.default = True
    default.key = 'default'
    default.depth = 2
    default.addressTypes = ["Integer", "Integer"]
    default.sectionNames = ["Mitzvah", "Comment"]
    return default


def regular_chapter_nodes(number):
    hebrew_letter = util.numToHeb(number)
    chapter = JaggedArrayNode()
    chapter.add_title('Chapter {}'.format(number), "en", primary=True)
    chapter.add_title(u'{} {}'.format(u'סימן',hebrew_letter), "he", primary=True)
    chapter.key = 'Chapter {}'.format(number)
    chapter.depth = 1
    chapter.addressTypes = ["Integer"]
    chapter.sectionNames = ["Comment"]
    return chapter


def chapter_seven(number):
    hebrew_letter = util.numToHeb(number)
    chapter = SchemaNode()
    chapter.add_title('Chapter {}'.format(number), "en", primary=True)
    chapter.add_title(u'{} {}'.format(u'סימן',hebrew_letter), "he", primary=True)
    chapter.key = 'Chapter {}'.format(number)
    chapter.append(create_intro_nodes())
    chapter.append(create_default_nodes())
    return chapter


def chapter_nine(number):
    hebrew_letter = util.numToHeb(number)
    chapter = JaggedArrayNode()
    chapter.add_title('Chapter {}'.format(number), "en", primary=True)
    chapter.add_title(u'{} {}'.format(u'סימן',hebrew_letter), "he", primary=True)
    chapter.key = 'Chapter {}'.format(number)
    chapter.depth = 2
    chapter.addressTypes = ["Integer", "Integer"]
    chapter.sectionNames = ["Section", "Mitzvah"]
    return chapter
