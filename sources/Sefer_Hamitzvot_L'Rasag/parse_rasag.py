# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
# from sources.Match import match_new
from sources.Match.match import Match
from sefaria.model.schema import AddressTalmud, SchemaNode, JaggedArrayNode


"""
Create and upload index record
create text version with blank lists
"""

def create_index():
    rasag = create_schema()
    rasag.validate()
    index = {
        "title": "Sefer Hamitzvot of Rasag",
        "categories": ["Halakhah"],
        "schema": rasag.serialize()
    }
    return index


def create_schema():
    rasag = SchemaNode()
    rasag.add_title('Sefer Hamitzvot of Rasag', 'en', primary=True)
    rasag.add_title(u'ספר המצוות לרס"ג', 'he', primary=True)
    rasag.key = 'Sefer Hamitzvot of Rasag'
    rasag.append(create_positive_node())
    rasag.append(create_negative_node())
    rasag.append(create_laws_of_the_court_node())
    rasag.append(create_communal_laws_nodes())
    return rasag


def create_positive_node():
    positive_node = SchemaNode()
    positive_node.add_title('Positive Commandments', "en", primary=True)
    positive_node.add_title(u'מצות עשה', "he", primary=True)
    positive_node.key = 'Positive Commandments'
    positive_node.append(create_default_nodes())
    return positive_node


def create_negative_node():
    negative_node = SchemaNode()
    negative_node.add_title('Negative Commandments', "en", primary=True)
    negative_node.add_title(u'מצות לא תעשה', "he", primary=True)
    negative_node.key = 'Negative Commandments'
    negative_node.append(create_intro_nodes())
    negative_node.append(create_default_nodes())
    return negative_node

def create_laws_of_the_court_node():
    law_of_court = SchemaNode()
    law_of_court.add_title('Laws of the Courts', "en", primary=True)
    law_of_court.add_title(u'עונשים', "he", primary=True)
    law_of_court.key = 'Laws of the Courts'
    law_of_court.append(create_intro_nodes())
    law_of_court.append(create_default_nodes())
    return law_of_court

def create_communal_laws_nodes():
    communal_laws = SchemaNode()
    communal_laws.add_title('Communal Laws', "en", primary=True)
    communal_laws.add_title(u'פרשיות ציבור', "he", primary=True)
    communal_laws.key = 'Communal Laws'
    communal_laws.append(create_intro_nodes())
    communal_laws.append(create_default_nodes())
    return communal_laws

def create_intro_nodes():
    intro_node = JaggedArrayNode()
    intro_node.add_title('Introduction', "en", primary=True)
    intro_node.add_title(u'פתיחה', "he", primary=True)
    intro_node.key = 'Introduction'
    intro_node.depth = 1
    intro_node.addressTypes = ["Integer"]
    intro_node.sectionNames = ["Comment"]
    return intro_node

def create_default_nodes():
    default_node = JaggedArrayNode()
    default_node.key = 'default'
    default_node.default = True
    default_node.depth = 1
    default_node.addressTypes = ["Integer"]
    default_node.sectionNames = ["Comment"]
    return default_node


"""
Sefer Hamitzvot of Rasag, Positive Commandments
Sefer Hamitzvot of Rasag, Negative Commandments, Introduction
Sefer Hamitzvot of Rasag, Negative Commandments
Sefer Hamitzvot of Rasag, Laws of the Courts, Introduction
Sefer Hamitzvot of Rasag, Laws of the Courts
Sefer Hamitzvot of Rasag, Communal Laws, Introduction
Sefer Hamitzvot of Rasag, Communal Laws
"""


def create_ref(section_name, intro=False):
    ref = 'Sefer Hamitzvot of Rasag, {}'.format(section_name)
    if intro:
        ref += ', Introduction'
    return ref


def create_text():
    return {
        "versionTitle": "Sefer Hamitzvot L'Rasag, Warsaw, 1914",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002027638",
        "language": "he",
        "text": [' ']
    }


index = create_index()
functions.post_index(index)

for number in xrange(7):
   section_names = ['Positive Commandments','Negative Commandments','Negative Commandments','Laws of the Courts','Laws of the Courts','Communal Laws','Communal Laws']
   intro = number % 2 != 0
   ref = create_ref(section_names[number], intro)
   text = create_text()
   functions.post_text(ref, text)

