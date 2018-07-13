# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
#sys.path.append("/Users/Eytan/Desktop/sefaria/Sefaria-Data/sources")

from sources.local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
#from sefaria.model import *

from sources.functions import *
import re
import data_utilities
import codecs
from sources import functions


# create index record
record = SchemaNode()
record.add_title('Shaarei Kedusha', 'en', primary=True, )
record.add_title(u'שערי קדושה', 'he', primary=True, )
record.key = 'Shaarei Kedusha'

#add node for introduction
intro_node = JaggedArrayNode()
intro_node.add_title("Introduction", 'en', primary = True)
intro_node.add_title("הקדמה", 'he', primary = True)
intro_node.key = "Introduction"
intro_node.depth = 1
intro_node.addressTypes = ['Integer']
intro_node.sectionNames = ['Paragraph']
record.append(intro_node)

chalakim = JaggedArrayNode()
# add nodes for chapters
for index in range(1,5):
    #first we make node for Shmatta
    chelek_node = SchemaNode()
    chelek_node.add_title("Part "+str(index), 'en', primary=True)
    chelek_node.add_title(u"חלק"+" "+numToHeb(index), 'he', primary=True)
    chelek_node.key = "Part "+str(index)
    #now we add text node
    text_node = JaggedArrayNode()
    text_node.key = "default"
    text_node.default = True
    text_node.depth = 2
    text_node.addressTypes = ['Integer', 'Integer']
    text_node.sectionNames = ['Shaar','Paragraph']
    chelek_node.append(text_node)
    
    #now we add this Shmatta's node to the root node
    record.append(chelek_node)



record.validate()

index = {
    "title": "Shaarei Kedusha",
    "categories": ["Kabbalah"],
    "schema": record.serialize()
}
functions.post_index(index,weak_network=True)