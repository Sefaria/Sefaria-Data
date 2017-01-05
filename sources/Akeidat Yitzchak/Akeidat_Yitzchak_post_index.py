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
from Akeidat_Yitzchak_parsepost import *
import re
import data_utilities
import codecs
from sources import functions


# create index record
record = SchemaNode()
record.add_title('Akeidat Yitzchak', 'en', primary=True, )
record.add_title(u'עקידת יצחק', 'he', primary=True, )
record.key = 'Akeidat Yitzchak'
pre_text_nodes = [["Index","מפתח"],["Author's Introduction","הקדמת המחבר"],["Mavo Shearim","מבוא שערים"]]
#add nodes for introduction
for node in pre_text_nodes:
    intro_node = JaggedArrayNode()
    intro_node.add_title(node[0], 'en', primary = True)
    intro_node.add_title(node[1], 'he', primary = True)
    intro_node.key = node[0]
    intro_node.depth = 1
    intro_node.addressTypes = ['Integer']
    intro_node.sectionNames = ['Paragraph']
    record.append(intro_node)
"""
    index_node = JaggedArrayNode()
    index_node.add_title("Index", 'en', primary = True)
    index_node.add_title("מפתח", 'he', primary = True)
    index_node.key = "Index"
    index_node.depth = 1
    index_node.addressTypes = ['Integer']
    index_node.sectionNames = ['Paragraph']
    record.append(index_node)
    
    mavo_node = JaggedArrayNode()
    intro_node.add_title("Author's Introduction", 'en', primary = True)
    intro_node.add_title("הקדמת המחבר", 'he', primary = True)
    intro_node.key = "Author's Introduction"
    intro_node.depth = 1
    intro_node.addressTypes = ['Integer']
    intro_node.sectionNames = ['Paragraph']
    record.append(intro_node)
    
    mavo_node = JaggedArrayNode()
    mavo_node.add_title("Mavo Shearim", 'en', primary = True)
    mavo_node.add_title("מבוא שערים", 'he', primary = True)
    mavo_node.key = "Mavo Shearim"
    mavo_node.depth = 1
    mavo_node.addressTypes = ['Integer']
    mavo_node.sectionNames = ['Paragraph']
    record.append(mavo_node)
"""
#now we add shaar struct:
shaar_struct = JaggedArrayNode()
shaar_struct.key = "default"
shaar_struct.default = True
shaar_struct.depth = 3
shaar_struct.addressTypes = ['Integer', 'Integer','Integer']
shaar_struct.sectionNames = ['Shaar','Chapter','Paragraph']
record.append(shaar_struct)

#now add node for neilas shaar:
neliah_node = JaggedArrayNode()
neliah_node.add_title("Neilat Shearim", 'en', primary = True)
neliah_node.add_title("נעילת שערים", 'he', primary = True)
neliah_node.key = "Neilat Shearim"
neliah_node.depth = 1
neliah_node.addressTypes = ['Integer']
neliah_node.sectionNames = ['Paragraph']
record.append(neliah_node)

#now we make alt structs
parsha_nodes = SchemaNode()
for index, parsha_index in enumerate(get_parsha_index()):
    parsha_node = ArrayMapNode()
    parsha_node.add_title(eng_parshiot[index], "en", primary=True)
    parsha_node.add_title(parsha_index[0], "he", primary=True)
    parsha_node.includeSections = True
    parsha_node.depth = 0
    parsha_node.wholeRef = "Akeidat Yitzchak, "+str(parsha_index[1])+"-"+str(parsha_index[2])
    parsha_nodes.append(parsha_node)

record.validate()

index = {
    "title": "Akeidat Yitzchak",
    "categories": ["Philosophy"],
    "alt_structs": {"Parsha": parsha_nodes.serialize()},
    "schema": record.serialize()
}
functions.post_index(index)