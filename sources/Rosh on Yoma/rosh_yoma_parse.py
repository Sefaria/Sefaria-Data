# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from sources.functions import *
import codecs
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from data_utilities.dibur_hamatchil_matcher import *
import re

daf_to_halacha_dict={}
def make_tractate_index():
    record = JaggedArrayNode()
    record.add_title('Rosh on Yoma', 'en', primary=True)
    record.add_title(u'פסקי הראש על יומא', 'he', primary=True)
    record.key = 'Rosh on Yoma'
    
    #now we add subject node to Shmatta
    avodah_node = JaggedArrayNode()
    avodah_node.add_title("Avoday Yom HaKippurim", 'en', primary=True)
    avodah_node.add_title(u'הלכות סדר עבודת יום הכפורים', 'he', primary=True)
    avodah_node.key = 'Avoday Yom HaKippurim'
    avodah_node.depth = 1
    avodah_node.addressTypes = ['Integer']
    avodah_node.sectionNames = ['Paragraph']
    record.append(avodah_node)

    #now we add text node
    text_node = JaggedArrayNode()
    text_node.key = "default"
    text_node.default = True
    text_node.depth = 1
    text_node.addressTypes = ['Integer']
    text_node.sectionNames = ['Halakhah']
    record.append(text_node)
    


    index = {
        "title":'Rosh on Yoma',
        "base_text_titles": [
           "Yoma"
        ],
        "collective_title":"Rosh",
        "dependence": "Commentary",
        "categories":["Talmud","Bavli","Commentary","Rosh", "Seder Moed"],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def post_rosh_text():
    in_avodah=True
    avodah_box=[]
    shmini_box = []
    current_daf = 0
    current_amud='a'
    with open("ראש יומא.txt") as myFile:
        lines = list(map(lambda x: x.decode("utf-8",'replace'), myFile.readlines()))
    for line in lines:
        if u'פרק שמיני' in line:
            in_avodah=False
        elif in_avodah and u"@99" not in line:
            avodah_box.append(avodah_clean(line))
        elif not in_avodah:
            if re.search(ur'\[דף.*?\]',line):
                match=re.search(ur'\[דף.*?\]',line).group()
                """
                if line.index(match)>20:
                    daf_to_halacha_dict[str(current_daf)+current_amud].append(len(shmini_box))
                """
                current_amud='a' if u'ע\"א' in line else 'b'
                current_daf = getGematria(match.replace(u'דף',u'').replace(u'ע\"א',u'').replace(u'ע\"ב',u''))
                print str(current_daf)+current_amud, match
            shmini_box.append(shmini_clean(line))
    version = {
        'versionTitle': 'VERSION TITLE',
        'versionSource': 'VERSION SOURCE',
        'language': 'he',
        'text': avodah_box
    }
    post_text_weak_connection('Rosh on Yoma, Avoday Yom HaKippurim', version)
    
    version = {
        'versionTitle': 'VERSION TITLE',
        'versionSource': 'VERSION SOURCE',
        'language': 'he',
        'text': shmini_box
    }
    post_text_weak_connection('Rosh on Yoma', version)

def avodah_clean(s):
    return re.sub(ur"@\d{1,4}",u"",s)
def shmini_clean(s):
    s = re.sub(ur'@22\S*',u'',s)
    return re.sub(ur"@\d{1,4}",u"",s)

#make_tractate_index()
post_rosh_text()            
            