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

print len(heb_parshiot)
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
def highest_fuzz(input_list, input_item):
    highest_ratio = 0
    best_match = u''
    for item in input_list:
        if fuzz.ratio(input_item,item)>highest_ratio:
            best_match=item
            highest_ratio=fuzz.ratio(input_item,item)
    return best_match
def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
"""
for book in library.get_indexes_in_category("Torah"):
    i=library.get_index("Genesis")
    for parsha in library.get_index("Genesis").alt_structs["Parasha"]["nodes"]:
     print w["sharedTitle"]
"""
folders_in_order = ['בראשית','שמות','ויקרא','במדבר','דברים']
base_text_files = [u'שאילתות בראשית.txt',u'שאילתות שמות.txt',u'שאילתות ויקרא.txt',u'שאילתות במדבר.txt',u'שאילתות דברים.txt']
sheiltot = [[] for x in range(172)]
#parsha_range_table=[{} for x in range(55)]
parsha_range_table=[]
folder_names=[x[0]for x in os.walk("files")][1:]
last_parsha_index=999
current_sheilta = 0
for folder in folders_in_order:
    print "ORDER ", folder
for folder in folders_in_order:
    for _file in os.listdir('files/'+folder.decode('utf8')):
        if _file in base_text_files:
            _file=_file.encode('utf8')
            with open('files/'+folder+'/'+_file) as myfile:
                lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
            for line in lines:
                if u"@00" in line:
                    heb_parsha=line.replace(u"@00",u'').replace(u'פרשת',u'').strip()
                    if heb_parsha in heb_parshiot:
                        parsha_index = heb_parshiot.index(heb_parsha)
                        if len(parsha_range_table)>0:
                            parsha_range_table[-1]["End Index"]=current_sheilta
                        eng_parsha = eng_parshiot[parsha_index]
                        print "TEST ",eng_parsha,"LPI ",last_parsha_index,"CS ",current_sheilta
                        print eng_parsha, parsha_index
                        parsha_range_table.append({"Hebrew Parsha": heb_parsha,"English Parsha": eng_parsha, "Start Index": current_sheilta+1})
                        last_parsha_index=parsha_index
                        first_index=False
                    else:
                        sheiltot[current_sheilta].append(u'<b>'+line+u'</b>')
                elif u'@22' in line:
                    current_sheilta = getGematria(line)
                elif not_blank(line):
                    sheiltot[current_sheilta].append(line)
            #add index for last parsha
            parsha_range_table[-1]["End Index"]=current_sheilta
            
def fix_markers_sheiltot(s):
    return s
    
for parsha in parsha_range_table:
    print parsha

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
                


