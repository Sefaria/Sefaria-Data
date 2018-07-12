# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.append("/Users/Eytan/Desktop/sefaria/Sefaria-Data/sources")

from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
#from sefaria.model import *

from functions import *
import re
import data_utilities
import codecs
from sources import functions

record = SchemaNode()
record.add_title('Sefer HaIkkarim', 'en', primary=True, )
record.add_title(u'ספר העקרים', 'he', primary=True, )
record.key = 'Sefer HaIkkarim'

#create title node
title_node = JaggedArrayNode()
title_node.add_title("Title", 'en', primary = True)
title_node.add_title("שער", 'he', primary = True)
title_node.key = "Title"
title_node.depth = 1
title_node.addressTypes = ['Integer']
title_node.sectionNames = ['Paragraph']
record.append(title_node)

#create "editor's introduction" node
ei_node = JaggedArrayNode()
ei_node.add_title("Editor's Introduction", 'en', primary = True)
ei_node.add_title("הקדמת העורך", 'he', primary = True)
ei_node.key = "Editor's Introduction"
ei_node.depth = 1
ei_node.addressTypes = ['Integer']
ei_node.sectionNames = ['Paragraph']
record.append(ei_node)

#create peticha node
peticha_node = JaggedArrayNode()
peticha_node.add_title("Forward", 'en', primary = True)
peticha_node.add_title("פתיחה", 'he', primary = True)
peticha_node.key = "Forward"
peticha_node.depth = 1
peticha_node.addressTypes = ['Integer']
peticha_node.sectionNames = ['Paragraph']
record.append(peticha_node)

#create Introduction Node
intro_node = JaggedArrayNode()
intro_node.add_title("Introduction", 'en', primary = True)
intro_node.add_title("הקדמה", 'he', primary = True)
intro_node.key = "Introduction"
intro_node.depth = 1
intro_node.addressTypes = ['Integer']
intro_node.sectionNames = ['Paragraph']
record.append(intro_node)

#create body node
for index in range(1,5):
    #first we make node for Maamar
    maamar_node = SchemaNode()
    maamar_node.add_title("Maamar "+str(index), 'en', primary=True)
    maamar_node.add_title(u"מאמר"+" "+numToHeb(index), 'he', primary=True)
    maamar_node.key = "Maamar "+str(index)
    
    #now we add introduction node to Maamar
    subject_node = JaggedArrayNode()
    subject_node.add_title("Introduction", 'en', primary=True)
    subject_node.add_title("הקדמה", 'he', primary=True)
    subject_node.key = 'Introduction'
    subject_node.depth = 1
    subject_node.addressTypes = ['Integer']
    subject_node.sectionNames = ['Paragraph']
    maamar_node.append(subject_node)
    
    #second maamar has a "haarah" after heading
    if index ==2:
        haarah_node = JaggedArrayNode()
        haarah_node.add_title("Observation", 'en', primary=True)
        haarah_node.add_title("הערה", 'he', primary=True)
        haarah_node.key = 'Observation'
        haarah_node.depth = 1
        haarah_node.addressTypes = ['Integer']
        haarah_node.sectionNames = ['Paragraph']
        maamar_node.append(haarah_node)
    
    #now we add text node
    text_node = JaggedArrayNode()
    text_node.key = "default"
    text_node.default = True
    text_node.depth = 2
    text_node.addressTypes = ['Integer', 'Integer']
    text_node.sectionNames = ['Chapter','Paragraph']
    maamar_node.append(text_node)
    
    #now we add this Shmatta's node to the root node
    record.append(maamar_node)


record.validate()

index = {
    "title": "Sefer HaIkkarim",
    "categories": ["Philosophy"],
    "schema": record.serialize()
}
functions.post_index(index)



