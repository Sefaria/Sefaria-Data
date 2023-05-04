# -*- coding: utf-8 -*-
import sys
import os
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from sources.functions import *
import re
import linking_utilities
import codecs
from sources import functions
from Shaarei_Orah_parse import *

english_titles= ["Introduction","First Gate, Tenth Sefirah","Second Gate, Ninth Sefirah","Third and Fourth Gates, Seventh and Eight Sefirah","Fifth Gate, Sixth Sefirah","Sixth Gate, Fifth Sefirah","Seventh Gate, Fourth Sefirah","Eight Gate, Third Sefirah","Ninth Gate, Second Sefirah","Tenth Gate, First Sefirah"]
titles = get_titles()
text = get_parsed_text()
# create index record
record = SchemaNode()
record.add_title('Shaarei Orah', 'en', primary=True, )
record.add_title(u'שערי אורה', 'he', primary=True, )
record.key = 'Shaarei Orah'

# add nodes for chapters
for index, section in enumerate(titles):
    #first we make node for Shmatta
    section_node = JaggedArrayNode()
    section_node.add_title(english_titles[index], 'en', primary=True)
    section_node.add_title(section, 'he', primary=True)
    section_node.key = english_titles[index]
    section_node.depth = 1
    section_node.addressTypes = ['Integer']
    section_node.sectionNames = ['Paragraph']
    record.append(section_node)


record.validate()

index = {
    "title": "Shaarei Orah",
    "categories": ["Kabbalah"],
    "schema": record.serialize()
}
functions.post_index(index,weak_network=True)