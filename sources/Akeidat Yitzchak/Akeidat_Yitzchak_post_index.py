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
record.add_title('Akeidat Yitzchak', 'en', primary=True, )
record.add_title(u'עקידת יצחק', 'he', primary=True, )
record.key = 'Akeidat Yitzchak'

#add node for introduction
intro_node = JaggedArrayNode()
intro_node.add_title("Introduction", 'en', primary = True)
intro_node.add_title("הקדמה", 'he', primary = True)
intro_node.key = "Introduction"
intro_node.depth = 1
intro_node.addressTypes = ['Integer']
intro_node.sectionNames = ['Paragraph']
record.append(intro_node)

#now we add shaar struct:
shaar_struct = JaggedArrayNode()
shaar_struct.key = "default"
shaar_struct.default = True
shaar_struct.depth = 3
shaar_struct.addressTypes = ['Integer', 'Integer','Integer']
shaar_struct.sectionNames = ['Shaar','Chapter','Paragraph']
record.append(shaar_struct)

#now we make alt structs
parsha_nodes = SchemaNode()
for index, parsha_index in enumerate(get_parsha_index()):
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
functions.post_index(index)