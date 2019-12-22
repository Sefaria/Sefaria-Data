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

DOMAIN_LANGUAGES={}
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

parsha_by_sefer={'Genesis':["Bereshit", "Noach", "Lech Lecha", "Vayera", "Chayei Sara", "Toldot", "Vayetzei", "Vayishlach",
"Vayeshev", "Miketz", "Vayigash", "Vayechi"],
"Exodus":["Shemot", "Vaera", "Bo", "Beshalach", "Yitro",
"Mishpatim", "Terumah", "Tetzaveh", "Ki Tisa", "Vayakhel", "Pekudei"],
"Leviticus":["Vayikra", "Tzav", "Shmini",
"Tazria", "Metzora", "Achrei Mot", "Kedoshim", "Emor", "Behar", "Bechukotai"],
"Numbers":["Bamidbar", "Nasso",
"Beha'alotcha", "Sh'lach", "Korach", "Chukat", "Balak", "Pinchas", "Matot", "Masei"],
"Deuteronomy":["Devarim", "Vaetchanan", "Eikev", "Re'eh", "Shoftim", "Ki Teitzei", "Ki Tavo", "Nitzavim", "Vayeilech", "Ha'Azinu",
"V'Zot HaBerachah"],
}
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
        if Ref(parsha_range_dict[sefer][key]).contains(Ref(sefer+' '+ref)):
            return key
def get_sefer_from_parsha(parsha):
    for key in parsha_by_sefer.keys():
        for parsha_title in parsha_by_sefer[key]:
            if parsha==parsha_title:
                return key
    return None
def ym_parse_text(posting=True):
    with open('yismach moshe.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    parsha_dict = {}
    intro_box = []
    last_parsha = 'Bereshit'
    in_text=False
    past_intro=False
    for line in lines:
        if u'10פתחו שערים' in line:
            in_text=True
        if u'@01ח"א ג/א@02' in line:
            past_intro=True
        if not past_intro and in_text:
            intro_box.append(remove_markers(line))
        elif in_text:
            if not_blank(line):
                if u'@10פרשת' in line:
                    last_parsha= eng_parshiot[heb_parshiot.index(highest_fuzz(heb_parshiot, line.replace(u'פרשת',u'')))]
                    parsha_dict[last_parsha]=[[]]
                
                elif re.match(ur'[^\.]*@13\/\.', line):
                    #print "TRYING...",re.match(ur'[^\.]*@13\/\.', line).group()
                    #print re.search(ur'(?<=@12).*?(?=@13)',re.match(ur'[^\.]*@13\/\.', line).group()).group()
                    if extact_ref(re.search(ur'(?<=@12).*?(?=@13)',re.match(ur'[^\.]*@13\/\.', line).group()).group()):
                        dicti = extact_ref(re.search(ur'(?<=@12).*?(?=@13)',re.match(ur'[^\.]*@13\/\.', line).group()).group())
                        parsha_result = get_parsha_from_range(en_sefer_names[he_sefer_names.index(dicti['Sefer'])],str(dicti['Perek'])+':'+str(dicti['Pasuk']))
                        if parsha_result and abs(eng_parshiot.index(parsha_result)-eng_parshiot.index(last_parsha))<2:
                            last_parsha=parsha_result
                            if last_parsha in parsha_dict:
                                parsha_dict[last_parsha].append([remove_markers(line)])
                            else:
                                parsha_dict[last_parsha]=[[remove_markers(line)]]
                        else:
                            parsha_dict[last_parsha].append([remove_markers(line)])
                            #parsha_dict[last_parsha][-1].append(remove_markers(line))
                    else:
                        parsha_dict[last_parsha][-1].append(remove_markers(line))
                elif re.search(ur'[^\.,]*@13\/\,',line) or u'@10בהפטורה' in line:
                    parsha_dict[last_parsha].append([remove_markers(line)])
                else:
                    parsha_dict[last_parsha][-1].append(remove_markers(line))
    for parsha in parsha_dict.keys():
        if len(parsha_dict[parsha][0])<1:
            parsha_dict[parsha]=parsha_dict[parsha][1:]
    if posting:
        version = {
            'versionTitle': 'VERSION TITLE',
            'versionSource': 'VERSION SOURCE',
            'language': 'he',
            'text': intro_box
        }
        #post_text('Yismach Moshe, Introduction', version,weak_network=True, skip_links=True, index_count="on")
        post_text_weak_connection('Yismach Moshe, Introduction', version)
        for key in parsha_dict.keys():
            version = {
                'versionTitle': 'VERSION TITLE',
                'versionSource': 'VERSION SOURCE',
                'language': 'he',
                'text': parsha_dict[key]
            }
            #post_text('Yismach Moshe, '+get_sefer_from_parsha(key)+', '+key, version,weak_network=True, skip_links=True, index_count="on")
            post_text_weak_connection('Yismach Moshe, '+key, version)
        
        """
        for cindex, comment in enumerate(parsha_dict[key]):
            for pindex, paragraph in enumerate(comment):
                print key, get_sefer_from_parsha(key), cindex, pindex, paragraph
        for pindex, paragraph in enumerate(intro_box):
            print "INTRO:",pindex, paragraph
        """
    return parsha_dict
def extact_ref(s):
    s = s.replace(u'(',u'').replace(u')',u'')
    sefer=u''
    for sefer_name in he_sefer_names:
        if sefer_name in s:
            sefer=sefer_name
    if sefer==u'':
        return None
    perek = getGematria(s.split(u' ')[1])
    pasuk = getGematria(s.split(u' ')[2])
    return{'Sefer':sefer, 'Perek':perek, 'Pasuk':pasuk}
def remove_markers(s):
    s=s.replace(u'/',u' ')
    while u'  ' in s:
        s=s.replace(u'  ',u' ')
    s = re.sub(ur'@01.*?@02',u'',s)
    s = re.sub(ur' (?=[\.,\]\)])',u'',s)
    s = re.sub(ur'(?<=[\[\(]) ',u'',s)
    return re.sub(ur"@\d{1,4}",u"",s)
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
    
    #now for sefer nodes:
    for parsha in eng_parshiot:
        parsha_node = JaggedArrayNode()
        parsha_node.add_shared_term(parsha)
        parsha_node.key = parsha
        parsha_node.depth = 2
        parsha_node.addressTypes = ['Integer', 'Integer']
        parsha_node.sectionNames = ['Comment','Paragraph']
        record.append(parsha_node)

    record.validate()
    index = {
        "title": "Yismach Moshe",
        "categories": ["Chasidut"],
        "schema": record.serialize()
    }
    post_index(index, weak_network = True)
def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def ym_link():
    text = ym_parse_text(False)
    for key in text.keys():
        for sindex, section in enumerate(text[key]):
            for pindex, paragraph in enumerate(section):
                if paragraph.split(u'.')[0][-1]==u')':
                    ref=Ref('Yismach Moshe, {}, {}'.format(key, sindex+1))
                    #print 'Yismach Moshe, {}, {}:{}-{}'.format(key, sindex+1, pindex+1,len(ref.text('he').text)),
                    if extract_ref(paragraph):
                        link = (
                                {
                                "refs": [
                                         'Yismach Moshe, {}, {}:{}-{}'.format(key, sindex+1, pindex+1,len(ref.text('he').text)),
                                         extract_ref(paragraph),
                                         ],
                                "type": "commentary",
                                "auto": True,
                                "generated_by": "sterling_yismach_moshe_linker"
                                })
                        post_link(link, weak_network=True)
                    
def extract_ref(s):
    ref_dict={}
    s = s.split(u'.')[0].split('(')[-1]
    for sefer in he_sefer_names:
        if sefer in s and len(s[s.rfind(sefer):].split())==3:
            s = s[s.rfind(sefer):]
            return en_sefer_names[he_sefer_names.index(sefer)]+' '+str(getGematria(s.split()[1]))+':'+str(getGematria(s.split()[2]))
    return False
def highest_fuzz(input_list, input_item):
    highest_ratio = 0
    best_match = u''
    for item in input_list:
        if fuzz.ratio(input_item,item)>highest_ratio:
            best_match=item
            highest_ratio=fuzz.ratio(input_item,item)
    return best_match           
def ym_post_term():
    term_obj = {
        "name": "Yismach Moshe",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Yismach Moshe",
                "primary": True
            },
            {
                "lang": "he",
                "text": u'ישמח משה',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
#ym_parse_text()
#ym_post_term()
#ym_post_index()
#ym_parse_text()    
ym_link()