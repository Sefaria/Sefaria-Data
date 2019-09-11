# -*- coding: utf-8 -*-
import os
import re
import sys
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
import django
django.setup()
from sources.functions import *

heb_parshiot = [u"בראשית",u"נח", u"לך לך", u"וירא", u"חיי שרה", u"תולדות", u"ויצא", u"וישלח", u"וישב", u"מקץ",
u"ויגש", u"ויחי", u"שמות", u"וארא", u"בא", u"בשלח", u"יתרו", u"משפטים", u"תרומה", u"תצוה", u"כי תשא",
u"ויקהל", u"פקודי", u"ויקרא", u"צו", u"שמיני", u"תזריע", u"מצורע", u"אחרי מות", u"קדושים", u"אמור", u"בהר",
u"בחוקתי", u"במדבר", u"נשא", u"בהעלותך", u"שלח לך", u"קרח", u"חקת", u"בלק", u"פינחס", u"מטות",
u"מסעי", u"דברים", u"ואתחנן", u"עקב", u"ראה", u"שופטים", u"כי תצא", u"כי תבוא", u"נצבים",
u"וילך", u"האזינו", u"וזאת הברכה"]

eng_parshiot = ["Bereshit", "Noach", "Lech Lecha", "Vayera", "Chayei Sara", "Toldot", "Vayetzei", "Vayishlach",
"Vayeshev", "Miketz", "Vayigash", "Vayechi", "Shemot", "Vaera", "Bo", "Beshalach", "Yitro",
"Mishpatim", "Terumah", "Tetzaveh", "Ki Tisa", "Vayakhel", "Pekudei", "Vayikra", "Tzav", "Shmini",
"Tazria", "Metzora", "Achrei Mot", "Kedoshim", "Emor", "Behar", "Bechukotai", "Bamidbar", "Nasso",
"Beha'alotcha", "Sh'lach", "Korach", "Chukat", "Balak", "Pinchas", "Matot", "Masei",
"Devarim", "Vaetchanan", "Eikev", "Re'eh", "Shoftim", "Ki Teitzei", "Ki Tavo", "Nitzavim", "Vayeilech", "Ha'Azinu",
"V'Zot HaBerachah"]

heb_sections = [u"בראשית",u"נח", u"לך לך", u"וירא", u"חיי שרה", u"תולדות", u"ויצא", u"וישלח", u"וישב", u"מקץ",
u"ויגש", u"ויחי", u"שמות", u"וארא", u"בא", u"בשלח", u"יתרו", u"משפטים", u"תרומה", u"תצוה", u"כי תשא",
u"ויקהל",u'הגדה של פסח', u"פקודי", u"ויקרא", u"צו", u"שמיני", u"תזריע", u"מצורע", u"אחרי מות", u"קדושים", u"אמור", u"בהר",
u"בחוקתי", u"במדבר", u"נשא", u"בהעלותך", u"שלח", u"קרח", u"חקת", u"בלק", u"פנחס", u"מטות",
u"מסעי", u"דברים", u"ואתחנן", u"עקב", u"ראה", u"שופטים", u"כי תצא", u"כי תבוא", u"נצבים",
u"וילך", u"האזינו", u"וזאת הברכה",u'הפטורה לפרשת זכור',u'שיר השירים',u'רות',u'יהושע',u'מלכים א',u'ישעיה',
u'יחזקאל',u'הושע',u'תהלים',u'איוב',u'לקוטים על מאמרי חז"ל',u'השמטות']

eng_sections = ["Bereshit", "Noach", "Lech Lecha", "Vayera", "Chayei Sara", "Toldot", "Vayetzei", "Vayishlach",
"Vayeshev", "Miketz", "Vayigash", "Vayechi", "Shemot", "Vaera", "Bo", "Beshalach", "Yitro",
"Mishpatim", "Terumah", "Tetzaveh", "Ki Tisa", "Vayakhel","Pesach Haggadah", "Pekudei", "Vayikra", "Tzav", "Shmini",
"Tazria", "Metzora", "Achrei Mot", "Kedoshim", "Emor", "Behar", "Bechukotai", "Bamidbar", "Nasso",
"Beha'alotcha", "Sh'lach", "Korach", "Chukat", "Balak", "Pinchas", "Matot", "Masei",
"Devarim", "Vaetchanan", "Eikev", "Re'eh", "Shoftim", "Ki Teitzei", "Ki Tavo", "Nitzavim", "Vayeilech", "Ha'Azinu",
"V'Zot HaBerachah","Haftarah for Zachor","Song of Songs","Ruth","Joshua","I Kings","Isaiah","Ezekiel","Hosea",
"Psalms","Job","Miscellany","Addenda"]
def ch_index_post():
    record = JaggedArrayNode()
    record.add_title('Chanukat HaTorah', 'en', primary=True, )
    record.add_title(u"חנוכת התורה", 'he', primary=True, )
    record.key = 'Chanukat HaTorah'
    record.depth = 2
    record.addressTypes = ['Integer','Integer']
    record.sectionNames = ['Siman','Paragraph']    
    
    #now we make alt struct
    parsha_nodes =SchemaNode()
    for parsha in get_alt_struct():
        en_title=eng_sections[heb_sections.index(parsha[0])]
        
        parsha_node = ArrayMapNode()
        parsha_node.includeSections = True
        parsha_node.depth = 0
        parsha_node.wholeRef = "Chanukat HaTorah {}-{}".format(parsha[1],parsha[2])
        parsha_node.key = en_title
        if Term().load({"name":en_title}):
             parsha_node.add_shared_term(en_title)
        else:
             parsha_node.add_title(en_title, 'en', primary=True)
             parsha_node.add_title(parsha[0], 'he', primary=True)
        parsha_nodes.append(parsha_node)
    record.validate()

    index = {
        "title": 'Chanukat HaTorah',
        "categories": ["Tanakh","Commentary"],
        "dependence": "Commentary",
        "alt_structs": {"Parasha": parsha_nodes.serialize()},
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def is_text(s):
    if u'@55' not in s and u'@00' not in s:
        return True
    return False
def parse_text():
    with open("ספר חנוכת התורה מקורי.txt") as myFile:
        lines = list(map(lambda x: x.decode("utf-8",'replace'), myFile.readlines()))
    all_simanim=[]
    siman_box=[]
    goes_in_next=[]
    for line in lines:
        if u'@22' in line:
            if len(siman_box)>0:
                all_simanim.append(siman_box)
                siman_box=[]
        elif u'@00' in line or u'@55' in line:
            goes_in_next.append(u'<b>{}</b>'.format(line.replace(u'IGNORE',u'').replace(u'@00',u'').replace(u'\n',u'')))
        elif is_text(line):
            final_line=clean_line(line)
            while len(goes_in_next)>0:
                final_line=goes_in_next.pop()+u'<br>'+final_line
                print "NABD",final_line
            siman_box.append(final_line)
    all_simanim.append(siman_box)
    
    #"""
    for sindex, siman in enumerate(all_simanim):
        for pindex, paragraph in enumerate(siman):
            print sindex, pindex, paragraph
    #"""
    #0/0
    version = {
        'versionTitle': "Piotrków, 1900",
        'versionSource': 'http://beta.nli.org.il/he/books/NNL_ALEPH001091549/NLI',
        'language': 'he',
        'text': all_simanim
    }
    #post_text("Ahavat Chesed, "+key, version, weak_network=True)
    post_text_weak_connection("Chanukat HaTorah", version)
def get_alt_struct():
    siman_count=0
    with open("ספר חנוכת התורה.txt") as myFile:
        lines = list(map(lambda x: x.decode("utf-8",'replace'), myFile.readlines()))
    alt_refs=[]

    for line in lines:
        if u'@22' in line and "IGNORE" not in line:
            siman_count+=1
        elif u'@00' in line and u'IGNORE' not in line:
            #print u"'{}'".format(line.replace(u'@00',u'').replace(u'\n',u'').strip())
            if len(alt_refs)>0:
                alt_refs[-1].append(siman_count)
            if u'זכור' not in line:
                alt_refs.append([line.replace(u'@00',u'').replace(u'\n',u'').replace(u'פרשת',u'').strip(),siman_count+1])
            else:
                alt_refs.append([line.replace(u'@00',u'').replace(u'\n',u'').strip(),siman_count+1])
                
    alt_refs[-1].append(227)
    """
    for ref in alt_refs:
        print ref[0]
        print ref[1],ref[2]
    """
    return alt_refs
def clean_line(s):
    s=s.replace(u'@11',u'<b>').replace(u'@33',u'</b>')
    return re.sub(ur"@\d{1,4}",u"",s)
ch_index_post()
#parse_text()
#get_alt_struct()