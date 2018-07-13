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
import csv
from functions import *
import re
import data_utilities
import codecs
from sources import functions
from Ben_Ish_Chai_parse import *
import pdb
#prepare lists of titles for Halachot Indices
import csv

with open('Halachot_Year_1.csv', 'rb') as f:
    reader = csv.reader(f)
    Y1_titles = list(reader)
with open('Halachot_Year_2.csv', 'rb') as f:
    reader = csv.reader(f)
    Y2_titles = list(reader)

def fix_parsha_title(s):
    #need to handle double parshas seperately...
    if u"אחרי" in s and u"קדושים" in s:
        return u"אחרי קדושים"
    if u"בהר" in s and u"בחוקותי" in s:
            return u"בהר בחוקותי"
    return s.replace(u"בא\"ח שנה שנייה",u"").split(u"-")[0].replace(u"פרשת",u"").replace(u"פרשיות",u"")
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

parsha_records = [get_parsed_drasha(),get_halachas_shana_1(),get_halachas_shana_2()]
parsha_sections = [ ["Drashot","דרשות"], ["Halachot 1st Year","הלכות שנה א"], ["Halachot 2nd Year","הלכות ב"] ]
for index, section in enumerate(parsha_sections):
    section_node = SchemaNode()
    section_node.add_title(section[0],'en',primary=True)
    section_node.add_title(section[1], 'he', primary=True)
    section_node.key = section[0]
    #only Halacha sections have alt structs
    if index!=0:
        alt_section_node = SchemaNode()
        alt_section_node.add_title(section[0],'en',primary=True)
        alt_section_node.add_title(section[1], 'he', primary=True)
    
        
    for parsha_index,parsha in enumerate(parsha_records[index]):
        print section[0],parsha[0][1]
        
        #Drashot section has no intro or alt struct, so it must be handled seperately
        if index!=0:
            #only Halachot Section has an alt struct
            alt_parsha_titles = Y1_titles[parsha_index] if index==1 else Y2_titles[parsha_index]
            print "alt sec titles: "+alt_parsha_titles[0]+" "+alt_parsha_titles[1]
            alt_parsha_node = ArrayMapNode()
            alt_parsha_node.add_title(re.sub(r" *- *",": ",alt_parsha_titles[0].strip()), 'en', primary=True)
            alt_parsha_node.add_title(alt_parsha_titles[1].strip(), 'he', primary=True)
            alt_parsha_node.depth = 0
            alt_parsha_node.wholeRef = "Ben Ish Hai, "+section[0]+", "+parsha[0][1]
            alt_section_node.append(alt_parsha_node)
            
            #now regular struct node:
            parsha_node = SchemaNode()
            parsha_node.key = parsha[0][1]
            if Term().load({"name":parsha[0][1]}):
                parsha_node.add_shared_term(parsha[0][1])
            else:
                parsha_node.add_title(parsha[0][1], 'en', primary=True)
                parsha_node.add_title(fix_parsha_title(parsha[0][0]), 'he', primary=True)
            #now we add intro node to Parsha for the Halachot 
            intro_node = JaggedArrayNode()
            intro_node.add_title("Introduction", 'en', primary=True)
            intro_node.add_title('פתיחה', 'he', primary=True)
            intro_node.key = 'Introduction'
            intro_node.depth = 1
            intro_node.addressTypes = ['Integer']
            intro_node.sectionNames = ['Paragraph']
            parsha_node.append(intro_node)
                        
            text_node = JaggedArrayNode()
            text_node.key = "default"
            text_node.default = True
            text_node.addressTypes = ['Integer', 'Integer']
            text_node.sectionNames = ['Chapter','Paragraph']
            text_node.depth = 2    
            parsha_node.append(text_node)
            
            section_node.append(parsha_node)
            #Parshat Vayeishev for Shana 2 needs special treatment, since its text is omitted from wikisource and must be added manually
            if index==2 and parsha_index==7:
                vayeshev_parsha_titles = ["Vayeshev","וישב"]
                parsha_node = SchemaNode()
                parsha_node.key = vayeshev_parsha_titles[0]
                parsha_node.add_shared_term(vayeshev_parsha_titles[0])
                        
                text_node = JaggedArrayNode()
                text_node.key = "default"
                text_node.default = True
                text_node.addressTypes = ['Integer', 'Integer']
                text_node.sectionNames = ['Chapter','Paragraph']
                text_node.depth = 2    
                parsha_node.append(text_node)
            
                section_node.append(parsha_node)
                
        #for the Drashot...
        else:
            parsha_node = JaggedArrayNode()
            if Term().load({"name":parsha[0][1]}):
                 parsha_node.add_shared_term(parsha[0][1])
            else:
                 parsha_node.add_title(parsha[0][1], 'en', primary=True)
                 parsha_node.add_title(fix_parsha_title(parsha[0][0]), 'he', primary=True)
            parsha_node.key = parsha[0][1]
            parsha_node.depth = 1
            parsha_node.addressTypes = ['Integer']
            parsha_node.sectionNames = ['Paragraph']    
            section_node.append(parsha_node)
    if index!=0:
        alt_struct.append(alt_section_node)    
    record.append(section_node)


record.validate()
index = {
    "title": "Ben Ish Hai",
    "titleVariants": ["Ben Ish Chai"],
    "alt_structs": {"Subject": alt_struct.serialize()},
    "categories": ["Halakhah"],
    "schema": record.serialize()
}
functions.post_index(index, weak_network = True)


