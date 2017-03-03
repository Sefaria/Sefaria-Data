# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
#from sefaria.model import *
from sources.functions import *
import re

#for posting commentary term for first time
term_obj = {
    "name": "Avi Ezer",
    "scheme": "commentary_works",
    "titles": [
        {
            "lang": "en",
            "text": "Avi Ezer",
            "primary": True
        },
        {
            "lang": "he",
            "text": u'אבי עזרי',
            "primary": True
        }
    ]
}
post_term(term_obj)

# create index record
record = SchemaNode()
record.add_title('Avi Ezer', 'en', primary=True, )
record.add_title(u'אבי עזרי', 'he', primary=True, )
record.key = 'Avi Ezer'

en_sefer_names = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy"]
he_sefer_names =  [u"בראשית",u"שמות" ,u"ויקרא",u"במדבר",u"דברים"]
for en_sefer, he_sefer in zip(en_sefer_names, he_sefer_names):
    sefer_node = JaggedArrayNode()
    sefer_node.add_title(en_sefer, 'en', primary=True, )
    sefer_node.add_title(he_sefer, 'he', primary=True, )
    sefer_node.key = en_sefer
    sefer_node.depth = 3
    sefer_node.toc_zoom = 2
    sefer_node.addressTypes = ['Integer', 'Integer','Integer']
    sefer_node.sectionNames = ['Chapter','Verse','Comment']
    record.append(sefer_node)

record.validate()

index = {
    "title":"Avi Ezer",
    "base_text_titles": [
       "Genesis","Exodus","Leviticus","Numbers","Deuteronomy"
    ],
    "dependence": "Commentary",
    "categories":['Tanakh','Commentary','Avi Ezer','Torah'],
    "schema": record.serialize()
}
post_index(index,weak_network=True)