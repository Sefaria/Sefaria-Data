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
    return get_parsed_array()[0]
def get_parsha_index():
    return get_parsed_array()[1]
def get_parsed_array():
    parsha_count=0
    shaar_count = 0
    book_files = ["בראשית.txt","שמות.txt","ויקרא.txt","במדבר.txt","דברים.txt"]
    final_text = []
    parsha_index = []
    for index, file in enumerate(book_files):
        with open(file) as myfile:
            text = myfile.readlines()
        #first parse the shaarim, the most detailed level of structure:
        shaar_box = []
        for line in text:
            line = fix_bold_lines(line)
            if "@" in line:
                if "@22" in line and len(shaar_box)!=0:
                    final_text.append(shaar_box)
                    shaar_box = []
            else:
                shaar_box.append(line)
        final_text.append(shaar_box)
        #now make parsha index:
        for line in text:
            if "@22" in line:
                shaar_count+=1
            if "@11" in line:
                if len(parsha_index)>0:
                    parsha_index[-1].append(shaar_count-1)
                parsha_index.append([heb_parshiot[parsha_count],shaar_count])
                parsha_count+=1
                
        parsha_index[-1].append(shaar_count-1)
    return [final_text,parsha_index]
def fix_bold_lines(input_line):
    if "@01" in input_line:
        input_line = input_line.replace("@01","<b>")
        if "@02" in input_line:
            input_line= input_line.replace("@02","</b>")
        else:
            input_line+="</b>"
    input_line = input_line.replace("@05","<b>").replace("@03","</b>")
    return input_line
text = get_parsed_text()
for bindex, book in enumerate(text):
    for pindex, paragraph in enumerate(book):
        print str(bindex)+" "+str(pindex)+" "+paragraph
parshadex = get_parsha_index()
for parsha in parshadex:
    print parsha[0]+u" ",parsha[1]," ",parsha[2]," end"
#for b in get_parsed_text():
#    print "BOOK: "+b
"""
    @00 - Book
    @44 - Gate/Chapter (should be reorganized to sperate the two)
    @99 - Verse quote
    @22 @55 - Introductory Midrash
    @11 @33 - regular paragraph
    5<>6 bold
    * first level footnotes (we have them)
    **) second level footnotes (we haven't got them)
"""
#11:50 - 1:00
#1:40 - 3:42