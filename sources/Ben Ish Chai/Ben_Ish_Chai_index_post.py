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
from Ben_Ish_Chai_parse import *
#from sefaria.model import *

from functions import *
import re
import data_utilities
import codecs
from sources import functions
from Ben_Ish_Chai_parse import *
import pdb
# create index record
record = SchemaNode()
record.add_title('Ben Ish Chai', 'en', primary=True, )
record.add_title(u'בן איש חי', 'he', primary=True, )
record.key = 'Ben Ish Chai'

#add node for introduction
intro_node = JaggedArrayNode()
intro_node.add_title("Introduction", 'en', primary = True)
intro_node.add_title("הקדמה", 'he', primary = True)
intro_node.key = "Introduction"
intro_node.depth = 1
intro_node.addressTypes = ['Integer']
intro_node.sectionNames = ['Paragraph']
record.append(intro_node)
#at the same time, we're making an alt struct for the parshiot.
alt_struct = SchemaNode()
# add nodes for parsha sections:

no_shared_title = ["Hannakah"]
parsha_records = [get_parsed_drasha(),get_halachas_shana_1(),get_halachas_shana_2()]
parsha_sections = [ ["Drashot","דרשות"], ["Halachot Shana 1","הלכות שנה א"], ["Halachot Shana 2","הלכות ב"] ]
for index, section in enumerate(parsha_sections):
    section_node = SchemaNode()
    section_node.add_title(section[0],'en',primary=True)
    section_node.add_title(section[1], 'he', primary=True)
    section_node.key = section[0]
    
    alt_section_node = SchemaNode()
    alt_section_node.add_title(section[0],'en',primary=True)
    alt_section_node.add_title(section[1], 'he', primary=True)
        
    for parsha in parsha_records[index]:
        print section[0],parsha[0][1]
        
        #first, alt parsha struct:
        alt_parsha_node = ArrayMapNode()
        if Term().load({"name":parsha[0][1]}):
            alt_parsha_node.sharedTitle = parsha[0][1]
            alt_parsha_node.depth = 0
            alt_parsha_node.wholeRef = "Ben Ish Hai, "+section[0]+", "+parsha[0][1]
            alt_section_node.append(alt_parsha_node)
        
        else:
            no_shared_title.append(parsha[0][1])
            alt_parsha_node.add_title(parsha[0][1], 'en', primary=True)
            alt_parsha_node.add_title(parsha[0][0].replace(u"בא\"ח שנה שנייה",""), 'he', primary=True)
            alt_parsha_node.depth = 0
            alt_parsha_node.wholeRef = "Ben Ish Hai, "+section[0]+", "+parsha[0][1]
            alt_section_node.append(alt_parsha_node)
        
        #now, regular parsha struct. Drashot section has no intro, so it must be handled seperately
        if index!=0:
            parsha_node = SchemaNode()
            parsha_node.add_title(parsha[0][1], 'en', primary=True)
            parsha_node.add_title(parsha[0][0].replace(u"בא\"ח שנה שנייה",""), 'he', primary=True)
            parsha_node.key = parsha[0][1]
            
            #now we add intro node to Parsha for the Halachot 
            intro_node = JaggedArrayNode()
            intro_node.add_title("Introduction", 'en', primary=True)
            intro_node.add_title('פתיחה', 'he', primary=True)
            intro_node.key = 'Introduction'
            intro_node.depth = 1
            intro_node.addressTypes = ['Integer']
            intro_node.sectionNames = ['Paragraph']
            parsha_node.append(intro_node)
    
            #now we add text node
            text_node = JaggedArrayNode()
            text_node.key = "default"
            text_node.default = True
            text_node.depth = 2
            text_node.addressTypes = ['Integer', 'Integer']
            text_node.sectionNames = ['Chapter','Paragraph']
            parsha_node.append(text_node)
            section_node.append(parsha_node)
            
            
        else:
            parsha_node = JaggedArrayNode()
            parsha_node.add_title(parsha[0][1], 'en', primary=True)
            parsha_node.add_title(parsha[0][0], 'he', primary=True)
            parsha_node.key = parsha[0][1]
            parsha_node.depth = 1
            parsha_node.addressTypes = ['Integer']
            parsha_node.sectionNames = ['Paragraph']    
            section_node.append(parsha_node)
        
    alt_struct.append(alt_section_node)
    record.append(section_node)


record.validate()
print "these have noe shared title:"
for title in no_shared_title:
    print title
index = {
    "title": "Ben Ish Hai",
    "titleVariants": ["Ben Ish Chai"],
    "alt_structs": {"Parsha": alt_struct.serialize()},
    "categories": ["Halakhah"],
    "schema": record.serialize()
}
functions.post_index(index, weak_network = True)


