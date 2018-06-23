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
from Sifrei_Devarim_en_post import *
import re
import data_utilities
import codecs
from sources import functions


# create index record
record = SchemaNode()
record.add_title('Sifrei Devarim', 'en', primary=True, )
record.add_title(u'ספרי דברים', 'he', primary=True, )
record.key = 'Sifrei Devarim'

#now we add Piska struct:
piska_struct = JaggedArrayNode()
piska_struct.key = "default"
piska_struct.default = True
piska_struct.depth = 2
piska_struct.addressTypes = ['Integer', 'Integer']
piska_struct.sectionNames = ['Piska','Paragraph']
record.append(piska_struct)

#now we make alt structs
perek_nodes = SchemaNode()
for perek_index in get_perek_index():
    perek_node = ArrayMapNode()
    perek_node.add_title("Chapter "+str(perek_index[0]), "en", primary=True)
    perek_node.add_title(u"פרק"+" "+numToHeb(int(perek_index[0])), "he", primary=True)
    perek_node.includeSections = True
    perek_node.depth = 0
    perek_node.wholeRef = "Sifrei Devarim, "+str(perek_index[1])+"-"+str(perek_index[2])
    perek_nodes.append(perek_node)

parsha_nodes = SchemaNode()
for parsha_index in get_parsha_index():
    parsha_node = ArrayMapNode()
    parsha_node.add_title(parsha_index[0], "en", primary=True)
    parsha_node.add_title(heb_parshiot[eng_parshiot.index(parsha_index[0])], "he", primary=True)
    parsha_node.includeSections = True
    parsha_node.depth = 0
    parsha_node.wholeRef = "Sifrei Devarim, "+str(parsha_index[1])+"-"+str(parsha_index[2])
    parsha_nodes.append(parsha_node)



record.validate()

index = {
    "title": "Sifrei Devarim",
    "categories": ["Midrash", "Halachic Midrash"],
    "alt_structs": {"Parsha": parsha_nodes.serialize(),"Chapters": perek_nodes.serialize()},
    "default_struct": "Chapters",
    "schema": record.serialize()
}
functions.post_index(index,weak_network=True)