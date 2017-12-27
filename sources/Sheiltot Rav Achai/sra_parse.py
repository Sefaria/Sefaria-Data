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
                        #print "TEST ",eng_parsha,"LPI ",last_parsha_index,"CS ",current_sheilta
                        #print eng_parsha, parsha_index
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
sheiltot=sheiltot[1:]
def fix_markers_sheiltot(sheilta):
    #we have to fix markers by sheilta, to properly address the i tags
    i_tag_table=[]
    return_array = []
    eimek_current_order_number = 1
    shalom_current_order_number = 1
    for p in sheilta:
        p = p.replace(u"@11",u"<b>").replace(u"@33",u"</b>")
        for eimek_match in re.findall(ur'@44\(.*?\)',p):
            if getGematria(eimek_match)>0:
                eimek_current_order_number=getGematria(eimek_match)
            if u'*' in eimek_match:
                p=p.replace(eimek_match,u"<i data-commentator=\"Haamek Sheilah\" data-label=\"*\" data-order=\""+str(eimek_current_order_number)+"\"></i>")
            else:
                p=p.replace(eimek_match,u"<i data-commentator=\"Haamek Sheilah\" data-order=\""+str(eimek_current_order_number)+"\"></i>")
        for shalom_match in re.findall(ur'@55\S*?',p):
            if getGematria(shalom_match)>0:
                shalom_current_order_number=getGematria(shalom_match)
            if u'*' in shalom_match:
                p=p.replace(shalom_match,u"<i data-commentator=\"Sheilat Shalom\" data-label=\"*\" data-order=\""+str(shalom_current_order_number)+"\"></i>")
            else:
                p=p.replace(shalom_match,u"<i data-commentator=\"Sheilat Shalom\" data-order=\""+str(shalom_current_order_number)+"\"></i>")
        return_array.append(re.sub(ur"@\d{1,4}",u"",p))
    return return_array
"""
for sindex, sheilta in enumerate(sheiltot):
    for pindex, paragraph in enumerate(sheilta):
        print sindex, pindex, paragraph
"""
def post_sra_index():
    # create index record
    record = JaggedArrayNode()
    record.add_title('Sheiltot d\'Rav Achai Gaon', 'en', primary=True, )
    record.add_title(u'שאילתות דרב אחאי גאון', 'he', primary=True, )
    record.key = 'Sheiltot d\'Rav Achai Gaon'
    record.depth = 2
    record.addressTypes = ['Integer','Integer']
    record.sectionNames = ['Sheilta','Paragraph']
    
    #now we make alt structs
    parsha_nodes =SchemaNode()
    for parsha in parsha_range_table:
        parsha_node = ArrayMapNode()
        parsha_node.includeSections = True
        parsha_node.depth = 0
        parsha_node.wholeRef = "Sheiltot d'Rav Achai Gaon, "+str(parsha['Start Index'])+"-"+str(parsha['End Index'])
        parsha_node.key = parsha['English Parsha']
        parsha_node.add_shared_term(parsha['English Parsha'])
        parsha_nodes.append(parsha_node)
        
    record.validate()

    index = {
        "title": "Sheiltot d'Rav Achai Gaon",
        "categories": ["Halakhah"],
        "alt_structs": {"Parshas": parsha_nodes.serialize()},
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def post_eimek_index():
    # create index record
    record = SchemaNode()
    record.add_title('Haamek Sheilah', 'en', primary=True, )
    record.add_title(u'העמק שאלה', 'he', primary=True, )
    record.key = 'Haamek Sheilah'

    #add node for introduction
    intro_node = JaggedArrayNode()
    intro_node.add_title("Introduction", 'en', primary = True)
    intro_node.add_title("הקדמה", 'he', primary = True)
    intro_node.key = "Introduction"
    intro_node.depth = 2
    intro_node.addressTypes = ['Integer','Integer']
    intro_node.sectionNames = ['Section','Paragraph']
    record.append(intro_node)
    
    shetila_nodes = JaggedArrayNode()
    shetila_nodes.key = "default"
    shetila_nodes.default = True
    shetila_nodes.depth = 2
    shetila_nodes.addressTypes = ['Integer', 'Integer']
    shetila_nodes.sectionNames = ['Sheilta','Comment']
    record.append(shetila_nodes)
    
    record.validate()

    index = {
        "title": 'Haamek Sheilah',
        "categories": ["Halakhah","Commentary"],
        "dependence": "Commentary",
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def get_eimek_paragraph_table():
    #check for extra Shalom tags...
    """
    for sindex, sheilta in enumerate(sheiltot):
        last_order_number=0
        for pindex, paragraph in enumerate(sheilta):
            for eimek_match in re.findall(ur'@55\S*?',paragraph):
                print "SHALOM!", eimek_match
                #print sindex, eimek_match
                print "THE ADDITION: ",getGematria(eimek_match)-last_order_number
                if getGematria(eimek_match)-last_order_number>1:
                    for x in range(1,getGematria(eimek_match)-last_order_number):
                        print "SHALOM!",last_order_number+x,'from',sindex+1
                last_order_number=getGematria(eimek_match)
    """
    #check for extra Eimek tags...
    """
    for sindex, sheilta in enumerate(sheiltot):
        last_order_number=0
        for pindex, paragraph in enumerate(sheilta):
            for eimek_match in re.findall(ur'@44\(.*?\)',paragraph):
                #print sindex, eimek_match
                if getGematria(eimek_match)-last_order_number>1:
                    for x in range(1,getGematria(eimek_match)-last_order_number):
                        print last_order_number+x,'from',sindex+1
                last_order_number=getGematria(eimek_match)
                return_array[sindex].append(pindex)
    """
    return_array=[[] for x in range(172)]
    return return_array
get_shalom_paragraph_table():
    #to properly link the i-tags we need to make a table
    #linking requires the sheilta-paragraph ref for the shelta side, and the sheilta-comment ref for the shalom side.
    #for this text, the index order will always be the same as the paragraph in the shalom side.
    #the sheilta will correspond to the first list position.
    #so each position will be a dictionary containing order-number and text-paragraph.
    return_array=[[] for x in range(172)]
    for sindex, sheilta in enumerate(sheiltot):
        last_order_number=0
        for pindex, paragraph in enumerate(sheilta):
            for shalom_match in re.findall(ur'@55\S*?',paragraph):
                return_array[sindex].append({})
                return_array[sindex][-1]['sheilta_paragraph']=pindex
                if getGematria(shalom_match)>0:
                    return_array[sindex][-1]["order-number"]= getGematria(shalom_match)
                    last_order_number=getGematria(shalom_match)
                else:
                    return_array[sindex][-1]["order-number"]= 0
    return return_array
def fix_comment_markers(s):
    return re.sub(ur"@\d{1,4}",u"",s.replace(u"@11",u"<b>").replace(u"@33",u"</b>").replace(u'ADDTONEXT',u''))
def post_eimek_text():    
    final_text = [[] for x in range(172)]
    add_to_next=[]
    for folder in folders_in_order:
        for _file in os.listdir('files/'+folder.decode('utf8')):
            if u'העמק' in _file:
                if u'הקדמת' in _file:
                    pass
                #different sefarim are marked differently...
                elif u'בראשית' in _file:
                    _file=_file.encode('utf8')
                    with open('files/'+folder+'/'+_file) as myfile:
                        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
                    current_sheilta=-1
                    for line in lines:
                        if u'@88' in line:
                            current_sheilta+=1
                        #we added a tag to handle this exception
                        elif u"ADDTONEXT" in line:
                            add_to_next.append(line)
                        if u'@22' not in line and u"@00" not in line and u"@88" not in line and not_blank(line):
                            while len(add_to_next)>0:
                                line = add_to_next.pop()+u'<br>'+line
                            final_text[current_sheilta].append(fix_comment_markers(line))
                elif u"דברים" in _file:
                    _file=_file.encode('utf8')
                    with open('files/'+folder+'/'+_file) as myfile:
                        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
                    #139 is last sheilta in Bamidbar, so we start from 140 (minus one for the 0th index and one for first label)
                    current_sheilta=138
                    for line in lines:
                        if u"@22" in line and getGematria(line)==1:
                            current_sheilta+=1
                        elif u"@22" not in line and u"@00" not in line and not_blank(line):
                            final_text[current_sheilta].append(fix_comment_markers(line))
                else:
                    with open('files/'+folder+'/'+_file) as myfile:
                        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
                    past_start=False
                    for line in lines:
                        if u"@88" in line:
                            past_start=True
                        if past_start:
                            if u"@88" in line:
                                current_sheilta=getGematria(line)
                            elif u"@00" not in line and not_blank(line):
                                final_text[current_sheilta].append(line)
    #now check numbers:
    copy_paragraph_array = [row[:] for row in get_eimek_paragraph_table()]
    for sindex, sheilta in enumerate(final_text):
        for pindex, paragraph in enumerate(sheilta):
            print "SHEILTA COUNT:",len(final_text[sindex])
            print "ORDER NUM COUNT:", len(copy_paragraph_array[sindex])
            print "SHEILTA:",sindex,pindex, paragraph
            copy_paragraph_array[sindex].pop()
        if len(copy_paragraph_array[sindex])>0:
            print "There's too many notes!"

                            
def post_eimek_index():
    # create index record
    record = SchemaNode()
    record.add_title('Sheilat Shalom', 'en', primary=True, )
    record.add_title(u'שאילת שלום', 'he', primary=True, )
    record.key = 'Sheilat Shalom'

    #add node for introduction
    intro_node = JaggedArrayNode()
    intro_node.add_title("Introduction", 'en', primary = True)
    intro_node.add_title("הקדמה", 'he', primary = True)
    intro_node.key = "Introduction"
    intro_node.depth = 2
    intro_node.addressTypes = ['Integer','Integer']
    intro_node.sectionNames = ['Section','Paragraph']
    record.append(intro_node)
    
    shetila_nodes = JaggedArrayNode()
    shetila_nodes.key = "default"
    shetila_nodes.default = True
    shetila_nodes.depth = 2
    shetila_nodes.addressTypes = ['Integer', 'Integer']
    shetila_nodes.sectionNames = ['Sheilta','Comment']
    record.append(shetila_nodes)
    
    record.validate()

    index = {
        "title": 'Sheilat Shalom',
        "categories": ["Halakhah","Commentary"],
        "dependence": "Commentary",
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def post_shalom_text():
    final_text = [[] for x in range(172)]
    add_to_next=[]
    for folder in folders_in_order:
        for _file in os.listdir('files/'+folder.decode('utf8')):
            if u'שלום' in _file:
                _file=_file.encode('utf8')
                with open('files/'+folder+'/'+_file) as myfile:
                    lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
                past_start=False
                for line in lines:
                    if u'@22' in line:
                        past_start=True
                    if past_start:
                        
def post_sra_text():
    to_post=[]
    for sheilta in sheiltot:
        to_post.append(fix_markers_sheiltot(sheilta))
    for sindex, sheilta in enumerate(to_post):
        for pindex, paragraph in enumerate(sheilta):
            print sindex, pindex, paragraph
    version = {
        'versionTitle': 'Sheiltot d\'Rav Achai Gaon; Vilna, 1861',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001166995',
        'language': 'he',
        'text': sheiltot[1:]
    }
    #post_text('Sheiltot d\'Rav Achai Gaon', version,weak_network=True, skip_links=True, index_count="on")
    ##post_text_weak_connection('Sheiltot d\'Rav Achai Gaon', version)#,weak_network=True)#, skip_links=True, index_count="on")
#post_sra_index()
post_eimek_text()
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
                


