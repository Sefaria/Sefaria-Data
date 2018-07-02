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
import re
import codecs

def get_parsed_text():
    with open('Sifrei_Devarim_reparse_text.txt') as my_file:
        lines = my_file.readlines()
    piska_box = []
    final_text = []
    oops = []
    empty = []
    missing_piskas = [i for i in range(1,358)]
    last_piska=0
    for line in lines:
        if "Piska" in line:
            piska_num = int(re.search(r"\d+",line).group())
            if len(piska_box)!=0 or piska_num!=1:
                final_text.append(piska_box)
                piska_box = []
            else:
                empty.append(piska_num-1)
            missing_piskas.remove(piska_num)
            if piska_num-last_piska!=1:
                oops.append([line,piska_num-last_piska])
                last_piska+=1
                while(last_piska!=piska_num):
                    final_text.append([''])
                    last_piska+=1
            last_piska=piska_num
        else:
            piska_box.append(line)
    final_text.append(piska_box)
    for oop in oops:
        print "OOps! "+oop[0]+" "+str(oop[1])
    print "There are piskas: "+str(len(final_text))
    print "These are missing..."
    for piska in missing_piskas:
        print piska
    print "These are empty..."
    for piska in empty:
            print piska
    return final_text
def main():
    pass
if __name__ == "__main__":
    version = {
        'versionTitle': 'Sifrei Devarim, Hebrew',
        'versionSource': 'https://he.wikisource.org/wiki/%D7%A1%D7%A4%D7%A8%D7%99_%D7%A2%D7%9C_%D7%93%D7%91%D7%A8%D7%99%D7%9D',
        'language': 'he',
        'text': get_parsed_text()
    }
    post_text('Sifrei Devarim', version,weak_network=True)
    main()
