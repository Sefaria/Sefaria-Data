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
def get_perek(ref):
    range_dict = get_perek_ranges(ref.book)
    for chapter_range in range_dict.keys():
        if Ref(chapter_range).contains(ref):
            return range_dict[chapter_range]
def get_perek_ranges(tractate_name):
    return {node['wholeRef']:int(node['titles'][0]['text'].split()[1]) for node in library.get_index(tractate_name).alt_structs["Chapters"]['nodes']}


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
en_sefer_names = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy"]
he_sefer_names =  [u"בראשית",u"שמות" ,u"ויקרא",u"במדבר",u"דברים"]
#here we build dict to find parsha by perek and pasuk ref:
parsha_range_dict={}

for sefer in en_sefer_names:
    parsha_range_dict[sefer]={}
    for l in library.get_index(sefer).alt_structs['Parasha']['nodes']:
        parsha_range_dict[sefer][l['sharedTitle']]=l['wholeRef']
"""
for key in parsha_range_dict.keys():
    for pkey in parsha_range_dict[key].keys():
        print key, pkey, parsha_range_dict[key][pkey]
"""
def get_parsha_from_range(sefer, ref):
    for key in parsha_range_dict[sefer].keys():
        if Ref(parsha_range_dict[sefer][key]).contains(ref):
            return key
        
def ym_parse_text():
    with open('yismach moshe.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    for line in lines:
        if re.match(ur'[^\.]*@13\/\.', line):
            print "TRYING...",re.match(ur'[^\.]*@13\/\.', line).group()
            print re.search(ur'(?<=@12).*?(?=@13)',re.match(ur'[^\.]*@13\/\.', line).group()).group()
        #print line
def ym_post_index():
    # create index record
    record = SchemaNode()
    record.add_title('Yismach Moshe', 'en', primary=True, )
    record.add_title(u'ישמח משה', 'he', primary=True, )
    record.key = 'Yismach Moshe'

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
        "titleVariants": ["Yismach Moshe"],
        "alt_structs": {"Subject": alt_struct.serialize()},
        "categories": ["Halakhah"],
        "schema": record.serialize()
    }
    functions.post_index(index, weak_network = True)
ym_parse_text()
    