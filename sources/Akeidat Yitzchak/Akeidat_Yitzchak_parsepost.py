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

def get_parsha_index():
    parsha_count=0
    shaar_count = 0
    book_files = ["בראשית.txt","שמות.txt","ויקרא.txt","במדבר.txt","דברים.txt"]
    parsha_index = []
    for index, file in enumerate(book_files):
        with open(file) as myfile:
            text = myfile.readlines()
        if index!=0:
            shaar_count-=1
        for line in text:
            if "@22" in line:
                shaar_count+=1
            if "@11" in line:
                if len(parsha_index)>0:
                    parsha_index[-1].append(shaar_count-1)
                parsha_index.append([heb_parshiot[parsha_count],shaar_count])
                parsha_count+=1
    parsha_index[-1].append(shaar_count)
    return parsha_index
def get_parsed_text():
    book_files = ["בראשית.txt","שמות.txt","ויקרא.txt","במדבר.txt","דברים.txt"]
    final_text = []
    parsha_index = []
    for index, file in enumerate(book_files):
        with open(file) as myfile:
            text = myfile.readlines()
        #first parse the shaarim, the most detailed level of structure:
        shaar_box = []
        chapter_box=[]
        mistakes =[]
        for line in text:
            line = fix_bold_lines(line)
            line = line.replace("@05","").replace("**","")
            if "@" in line:
                if "@22" in line and len(chapter_box)!=0:
                    shaar_box.append(chapter_box)
                    chapter_box=[]
                    final_text.append(shaar_box)
                    shaar_box = []
                elif "@33" in line and len(chapter_box)!=0:
                    shaar_box.append(chapter_box)
                    chapter_box=[]
                elif "@11" not in line and "@00" not in line:
                    mistakes.append(file+" EXTRA@ "+ line)
            else:
                if "השער" in line and len(line)<50:
                    mistakes.append(file+" SHAAR "+line)
                chapter_box.append(line)
    shaar_box.append(chapter_box)
    final_text.append(shaar_box)
    for mistake in mistakes:
        print mistake
    return final_text
"""
def get_parsed_intro():
    with open("הקדמה עקידת יצחק.txt") as myfile:
        lines = myfile.readlines()
    final_intro = []
    section_box = []
    for line in lines:
        line = line.replace("@22","").replace("@11","")
        line=line.replace("@66","<b>").replace("@77","</b>")
        line = re.sub("@[")
        if "@" in line:
            if "@00" in line and len(section_box)!=0:
                final_intro.append(section_box)
                section_box = []
        else:
            section_box.append(line)
    final_intro.append(section_box)
    return final_intro
    """


def fix_bold_lines(input_line):
    if "@01" in input_line:
        input_line = input_line.replace("@01","<b>")
        if "@02" in input_line:
            input_line= input_line.replace("@02","</b>")
        else:
            input_line+="</b>"
    if "@44" in input_line:
        input_line = "<b>"+input_line.replace("@44","")+"</b>"
    input_line = input_line.replace("@04","<b>").replace("@03","</b>")
    return input_line
text = get_parsed_text()
for bindex, book in enumerate(text):
    for cindex,chapter in enumerate(book):
        for pindex, paragraph in enumerate(chapter):
            print str(bindex)+" "+str(cindex)+" "+str(pindex)+" "+paragraph
parshadex = get_parsha_index()
for parsha in parshadex:
    print parsha[0]+u" ",parsha[1]," ",parsha[2]," end"
"""
for index, section in enumerate(get_parsed_intro()):
    for paragraph in section:
        print str(index)+" "+paragraph
        """
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