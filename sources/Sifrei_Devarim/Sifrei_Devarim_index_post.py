# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
#sys.path.append("/Users/Eytan/Desktop/sefaria/Sefaria-Data/sources")

from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
#from sefaria.model import *
from Sifrei_Devarim_post import *
from functions import *
import re
import data_utilities
import codecs
from sources import functions


# create index record
record = SchemaNode()
record.add_title('Sifrei Devarim', 'en', primary=True, )
record.add_title(u'ספרי דברים', 'he', primary=True, )
record.key = 'Sifrei Devarim'

# add nodes for chapters
for index in range(1,8):
    #first we make node for Shmatta
    shmatta_node = SchemaNode()
    shmatta_node.add_title("Shmatta "+str(index), 'en', primary=True)
    shmatta_node.add_title(u"שמעתתא"+" "+numToHeb(index), 'he', primary=True)
    shmatta_node.key = "Shmatta "+str(index)
    
    #now we add text node
    text_node = JaggedArrayNode()
    text_node.key = "default"
    text_node.default = True
    text_node.depth = 2
    text_node.addressTypes = ['Integer', 'Integer']
    text_node.sectionNames = ['Chapter','Paragraph']
    shmatta_node.append(text_node)
    
    #now we add this Shmatta's node to the root node
    record.append(shmatta_node)



record.validate()

index = {
    "title": "Shev Shmatta",
    "titleVariants": ["Shev Shmat’ta","Shev Shmatsa"],
    "categories": ["Halakhah"],
    "schema": record.serialize()
}
functions.post_index(index)