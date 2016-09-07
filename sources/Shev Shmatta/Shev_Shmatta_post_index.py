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
"""
def numToHeb(engnum=""):
    engnum = str(engnum)
    numdig = len(engnum)
    hebnum = ""
    letters = [["" for i in range(3)] for j in range(10)]
    letters[0]=["", "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"]
    letters[1]=["", "י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ"]
    letters[2]=["", "ק", "ר", "ש", "ת", "תק", "תר", "תש", "תת", "תתק"]
    if (numdig > 3):
        print "We currently can't handle numbers larger than 999"
        exit()
    for count in range(numdig):
        hebnum += letters[numdig-count-1][int(engnum[count])]
    hebnum = re.sub('יה', 'טו', hebnum)
    hebnum = re.sub('יו', 'טז', hebnum)
    hebnum = hebnum.decode('utf-8')
    return hebnum
"""

# create index record
record = SchemaNode()
record.add_title('Shev Shmatta', 'en', primary=True, )
record.add_title(u'שב שמעתתא', 'he', primary=True, )
record.key = 'Shev Shmatta'

#add node for introduction
intro_node = JaggedArrayNode()
intro_node.add_title("Introduction", 'en', primary = True)
intro_node.add_title("הקדמה", 'he', primary = True)
intro_node.key = "Introduction"
intro_node.depth = 1
intro_node.addressTypes = ['Integer']
intro_node.sectionNames = ['Paragraph']
record.append(intro_node)

# add nodes for chapters
for index in range(1,8):
    #first we make node for Shmatta
    shmatta_node = SchemaNode()
    shmatta_node.add_title("Shmatta "+str(index), 'en', primary=True)
    shmatta_node.add_title(u"שמעתתא"+" "+numToHeb(index), 'he', primary=True)
    shmatta_node.key = "Shmatta "+str(index)

    #now we add subject node to Shmatta
    subject_node = JaggedArrayNode()
    subject_node.add_title("Subject", 'en', primary=True)
    subject_node.add_title("נושא", 'he', primary=True)
    subject_node.key = 'Subject'
    subject_node.depth = 1
    subject_node.addressTypes = ['Integer']
    subject_node.sectionNames = ['Paragraph']
    shmatta_node.append(subject_node)

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
    "categories": ["Halakhah"],
    "schema": record.serialize()
}
functions.post_index(index)