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

heb_parshiot = [u"בראשית",u"נח", u"לך לך", u"וירא", u"חיי שרה", u"תולדות", u"ויצא", u"וישלח", u"וישב", u"מקץ",
u"ויגש", u"ויחי", u"שמות", u"וארא", u"בא", u"בשלח", u"יתרו", u"משפטים", u"תרומה", u"תצוה", u"כי תשא",
u"ויקהל", u"פקודי", u"ויקרא", u"צו", u"שמיני", u"תזריע", u"מצרע", u"אחרי מות", u"קדשים", u"אמר", u"בהר",
u"בחקתי", u"במדבר", u"נשא", u"בהעלתך", u"שלח לך", u"קרח", u"חקת", u"בלק", u"פינחס", u"מטות",
u"מסעי", u"דברים", u"ואתחנן", u"עקב", u"ראה", u"שפטים", u"כי תצא", u"כי תבוא", u"נצבים",
u"וילך", u"האזינו", u"וזאת הברכה"]

eng_parshiot = ["Bereshit", "Noach", "Lech Lecha", "Vayera", "Chayei Sara", "Toldot", "Vayetzei", "Vayishlach",
"Vayeshev", "Miketz", "Vayigash", "Vayechi", "Shemot", "Vaera", "Bo", "Beshalach", "Yitro",
"Mishpatim", "Terumah", "Tetzaveh", "Ki Tisa", "Vayakhel", "Pekudei", "Vayikra", "Tzav", "Shmini",
"Tazria", "Metzora", "Achrei Mot", "Kedoshim", "Emor", "Behar", "Bechukotai", "Bamidbar", "Nasso",
"Beha'alotcha", "Sh'lach", "Korach", "Chukat", "Balak", "Pinchas", "Matot", "Masei",
"Devarim", "Vaetchanan", "Eikev", "Re'eh", "Shoftim", "Ki Teitzei", "Ki Tavo", "Nitzavim", "Vayeilech", "Ha'Azinu",
"V'Zot HaBerachah"]

def get_parsha_index():
    parsha_count=0
    shaar_count = 0
    book_files = ["בראשית.txt","שמות.txt","ויקרא.txt","במדבר.txt","דברים.txt"]
    parsha_index = []
    for index, file in enumerate(book_files):
        with open(file) as myfile:
            text = myfile.readlines()
        for line in text:
            if "IGNORE" not in line:
                if "@22" in line:
                    shaar_count+=1
                if "@11" in line:
                    if len(parsha_index)>0:
                        parsha_index[-1].append(shaar_count-1 if parsha_index[-1][-1]!=shaar_count else shaar_count)
                    parsha_index.append([heb_parshiot[parsha_count],shaar_count])
                    parsha_count+=1
                #introduction to parshas shemos requires it's own implementation, since it breaks from the parsha pattern
                if "@232" in line:
                    parsha_index[-1].append(shaar_count-1)
                    parsha_index.append([u"הקדמת ספר שמות",shaar_count])
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
            if "@77נעילת שערים" in line:
                break
            line = remove_unused_tags(line)
            if "IGNORE" not in line:
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
def remove_unused_tags(s):
    unused_tags = ["@05","**","@01","@02","@04","@03"]
    for tag in unused_tags:
        s = s.replace(tag,"")
    return s
def remove_unused_tags_intro(s):
    unused_tags = ["@11","22","@66","@77","@88","@44","@55","@99","@"]
    for tag in unused_tags:
        s = s.replace(tag,"")
    return s
def bold_intro_lines(s):
    return s.replace("@33","<b>").replace("@43","</b>")
def get_parsed_intro():
    with open("הקדמה עקידת יצחק.txt") as myfile:
        lines = myfile.readlines()
    final_intro = []
    section_box = []
    for line in lines:
        #line=line.replace("@66","<b>").replace("@77","</b>")
        #line = re.sub("@[")
        if "@00" in line and len(section_box)!=0:
            final_intro.append(section_box)
            section_box = []
        else:
            line = remove_unused_tags_intro(bold_intro_lines(line))
            #some paragraphs end in the wrong place, so we make sure each paragraph ends with a ":"
            if len(section_box)>0:
                if ":" not in section_box[-1]:
                    section_box[-1] = (section_box[-1]+line).replace("\n","")
                else:
                    section_box.append(line)
            else:
                section_box.append(line)
    final_intro.append(section_box)
    return final_intro[1:]
def get_parsed_neilah():
    with open("דברים.txt") as myfile:
        lines = myfile.readlines()
    neilah_index=0
    for index, line in enumerate(lines):
        if "@77נעילת שערים" in line:
            break
        neilah_index+=1
    neilah_return = []
    for line in lines[neilah_index+1:]:
        line = re.sub("@[\d]+","",line)
        line = line.replace("**","")
        neilah_return.append(line)
    return neilah_return
        
    

def fix_bold_lines(input_line):
    #we decided later not to bold these tags
    """
    if "@01" in input_line:
        input_line = input_line.replace("@01","<b>")
        if "@02" in input_line:
            input_line= input_line.replace("@02","</b>")
        else:
            input_line+="</b>"
    input_line = input_line.replace("@04","<b>").replace("@03","</b>")
    """
    if "@44" in input_line:
        input_line = "<b>"+input_line.replace("@44","")+"</b>"
    return input_line
def main():
    pass
if __name__ == "__main__":
    
    #for MAIN TEXT
    text = get_parsed_text()
    for bindex, book in enumerate(text):
        for cindex,chapter in enumerate(book):
            for pindex, paragraph in enumerate(chapter):
                print str(bindex)+" "+str(cindex)+" "+str(pindex)+" "+paragraph
    version = {
        'versionTitle': 'Akeidat Yitzchak, Pressburg 1849',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002034858',
        'language': 'he',
        'text': text
    }

    post_text('Akeidat Yitzchak', version, weak_network=True)
    
    """
    #for INTROS
    print "this is an intro"
    for sindex, section in enumerate(get_parsed_intro()):
        for pindex, paragraph in enumerate( section):
            print str(sindex)+" "+str(pindex)+" "+paragraph
    
    parshadex = get_parsha_index()
    for parsha in parshadex:
        print parsha[0]+u" ",parsha[1]," ",parsha[2]," end"
    intro_titles = ["Index","Author's Introduction","Mavo Shearim"]
    for index, title in enumerate(intro_titles):
        
    main()
    """
    
    """
    #for NEILAH
    n = get_parsed_neilah()
    for line in n:
        print line
    version = {
        'versionTitle': 'Akeidat Yitzchak, Pressburg 1849',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002034858',
        'language': 'he',
        'text': n
    }

    post_text('Akeidat Yitzchak, Neilat Shearim', version, weak_network=True)
    """
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