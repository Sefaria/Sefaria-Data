# -*- coding: utf-8 -*-
import os
import re
import sys
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from sources.functions import *
import re
import codecs
from fuzzywuzzy import fuzz
import os
parsha_dict = {}
for book in library.get_indexes_in_category("Torah"):
    i=library.get_index("Genesis")
    for parsha in library.get_index("Genesis").alt_structs["Parasha"]["nodes"]:
     print w["sharedTitle"]
folders_in_order = ['בראשית','שמות','ויקרא','במדבר','דברים']
base_text_files = ['שאילתות בראשית.txt','שאילתות שמות.txt','שאילתות ויקרא.txt','שאילתות במדבר.txt','שאילתות דברים.txt']
sheiltot = [[] for x in range(172)]
parsha_range_table=[]
folder_names=[x[0]for x in os.walk("files")][1:]
for folder in folder_names:
    for _file in os.listdir(folder):
        print _file
        if _file in base_text_files:
            current_sheilta = 0
            with open(folder+'/'+_file) as myfile:
                lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
            for line in lines:
                if u"@00" in line:
                    if len(parsha_range_table)>0:
                        parsha_range_table[-1]["End Index"]=current_sheilta
                    parsha_range_table.append({"Hebrew Parsha": line.replace(u"@00",u''), "Start Index": current_sheilta+1})
                elif u'@22' in line:
                    current_sheilta = getGematria(line)
                    print line
                else:
                    print current_sheilta
                    sheiltot[current_sheilta].append(line)
for sindex, sheilta in enumerate(sheiltot):
    for pindex, paragraph in enumerate(sheilta):
        print sindex, pindex, paragraph
    
"""
keys:
Base Text:
@22- New Sheilta
@44- Eimek Note
@55- Sheilas Shalom Note
        
Eimek = 
@88- new sheilta
@22- new note
"""
                


