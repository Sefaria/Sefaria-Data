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
            
def fix_markers_sheiltot(sheilta):
    #we have to fix markers by sheilta, to properly address the i tags
    global shalom_current_order_number
    i_tag_table=[]
    return_array = []
    eimek_current_order_number = 1
    for p in sheilta:
        p = p.replace(u"@11",u"<b>").replace(u"@33",u"</b>")
        for eimek_match in re.findall(ur'@44(\*|\(.*?\))',p):
            #print eimek_match
            if getGematria(eimek_match)>0:
                eimek_current_order_number=getGematria(eimek_match)
            if u'*' in eimek_match:
                p=p.replace(eimek_match,u"<i data-commentator=\"Haamek Sheilah on Sheiltot d\'Rav Achai Gaon\" data-label=\"*\" data-order=\""+str(eimek_current_order_number)+"\"></i>")
            else:
                p=p.replace(eimek_match,u"<i data-commentator=\"Haamek Sheilah on Sheiltot d\'Rav Achai Gaon\" data-order=\""+str(eimek_current_order_number)+"\"></i>")
        for shalom_match in re.findall(ur'@55\S* ',p):
            #print shalom_match, getGematria(shalom_match)
            #print repr(shalom_match)
            if getGematria(shalom_match)>1:
                shalom_current_order_number=getGematria(shalom_match)
            if u'*' in shalom_match:
                p=p.replace(shalom_match,u"<i data-commentator=\"Sheilat Shalom on Sheiltot d\'Rav Achai Gaon\" data-label=\"*\" data-order=\""+str(shalom_current_order_number)+"\"></i> ")
            else:
                p=p.replace(shalom_match,u"<i data-commentator=\"Sheilat Shalom on Sheiltot d\'Rav Achai Gaon\" data-order=\""+str(shalom_current_order_number)+"\"></i> ")
        return_array.append(re.sub(ur"@\d{1,4}",u"",p))
    return return_array
    
sheiltot=sheiltot[1:]
shalom_current_order_number = 1
fixed_sheiltot=[]
for sheilta in sheiltot:
    fixed_sheiltot.append(fix_markers_sheiltot(sheilta))


"""
for sindex, sheilta in enumerate(fixed_sheiltot):
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
        "alt_structs": {"Parasha": parsha_nodes.serialize()},
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def post_eimek_index():
    # create index record
    record = SchemaNode()
    record.add_title('Haamek Sheilah on Sheiltot d\'Rav Achai Gaon', 'en', primary=True, )
    record.add_title(u'העמק שאלה על שאילתות דרב אחאי גאון', 'he', primary=True, )
    record.key = 'Haamek Sheilah on Sheiltot d\'Rav Achai Gaon'

    #add nodes for introductions
    intro_node = JaggedArrayNode()
    intro_node.add_title("Kidmat HaEmek", 'en', primary = True)
    intro_node.add_title(u'קדמת העמק', 'he', primary = True)
    intro_node.key = "Kidmat HaEmek"
    intro_node.depth = 2
    intro_node.addressTypes = ['Integer','Integer']
    intro_node.sectionNames = ['Chapter','Paragraph']
    record.append(intro_node)
    
    intro_node = JaggedArrayNode()
    intro_node.add_title("Petach HaEmek", 'en', primary = True)
    intro_node.add_title(u'פתח העמק', 'he', primary = True)
    intro_node.key = "Petach HaEmek"
    intro_node.depth = 2
    intro_node.addressTypes = ['Integer','Integer']
    intro_node.sectionNames = ['Chapter','Paragraph']
    record.append(intro_node)
    
    shetila_nodes = JaggedArrayNode()
    shetila_nodes.key = "default"
    shetila_nodes.default = True
    shetila_nodes.depth = 3
    shetila_nodes.addressTypes = ['Integer', 'Integer','Integer']
    shetila_nodes.sectionNames = ['Sheilta','Comment','Paragraph']
    shetila_nodes.toc_zoom=2

    record.append(shetila_nodes)
    
    record.validate()

    index = {
        "title": 'Haamek Sheilah on Sheiltot d\'Rav Achai Gaon',
        "categories": ["Halakhah","Commentary"],
        "dependence": "Commentary",
        "collective_title": "Haamek Sheilah",
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
def get_shalom_paragraph_table():
    #to properly link the i-tags we need to make a table
    #linking requires the sheilta-paragraph ref for the shelta side, and the comment ref for the shalom side.
    #there are a few '*' refs, and for those we tack onto the last order-number (or next, for the first ones)
    #the index position in the return array corresponds to the sheilta.
    #the array contains dictionaries, whose title is the pargraph number and contents are the order-numbers to be linked.
    #The order numbers correspond to the index position in the sheilat shalom as well.
    return_array=[{} for x in range(172)]
    for sindex, sheilta in enumerate(sheiltot):
        last_order_number=1
        for pindex, paragraph in enumerate(sheilta):
            for shalom_match in re.findall(ur'@55\S*?',paragraph):
                if getGematria(shalom_match)>0:
                    if pindex in return_array[sindex-1]:
                        return_array[sindex-1][pindex].append(getGematria(shalom_match))
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
    #some test runs
    no_eimek = [x for x in range(171)]
    highest_eimek = [0 for x in range(171)]
    for sindex, sheilta, in enumerate(fixed_sheiltot):
        for pindex, paragraph in enumerate(sheilta):
            for match in re.findall(ur'<.*?>',paragraph):
                if u'Haamek' in match:
                    if sindex in no_eimek:
                        no_eimek.remove(sindex)
                    #make sure eimek refs match by checking highest of each one
                    if int(re.search(ur'(?<=order=\")\d*',match).group())>highest_eimek[sindex]:
                        highest_eimek[sindex]=int(re.search(ur'(?<=order=\")\d*',match).group())
    final_text = [[] for x in range(171)]
    for folder in folders_in_order:
        for _file in os.listdir('files/'+folder.decode('utf8')):
            if u'עמק' in _file:
                if u'הקדמת' in _file:
                    pass
                #different sefarim are marked differently...
                elif u'בראשית' in _file:
                    _file=_file.encode('utf8')
                    with open('files/'+folder+'/'+_file) as myfile:
                        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
                    current_sheilta=-1
                    ref_box = []
                    for line in lines:
                        if u'(א)' in line:
                            if len(ref_box)>0:
                                final_text[current_sheilta].append(ref_box)
                                ref_box=[]
                            current_sheilta+=1
                        elif u'@22' in line and len(ref_box)>0:
                            final_text[current_sheilta].append(ref_box)
                            ref_box=[]
                        elif u"@00" not in line and not_blank(line) and u'@22' not in line and u'@88' not in line:
                            ref_box.append(fix_comment_markers(line))
                    if len(ref_box)>0:
                        final_text[current_sheilta].append(ref_box)
                elif u"דברים" in _file:
                    _file=_file.encode('utf8')
                    with open('files/'+folder+'/'+_file) as myfile:
                        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
                    #139 is last sheilta in Bamidbar, so we start from 140 (minus one for the 0th index and one for first label)
                    current_sheilta=138
                    ref_box = []
                    for line in lines:
                        if not_blank(line):
                            if u"@22" in line:
                                if len(ref_box)>0:
                                    final_text[current_sheilta].append(ref_box)
                                    ref_box=[]
                                if getGematria(line)==1:
                                    current_sheilta+=1
                                    while current_sheilta in no_eimek:
                                        current_sheilta+=1
                            elif u"@00" not in line:
                                ref_box.append(fix_comment_markers(line))
                    if len(ref_box)>0:
                        final_text[current_sheilta].append(ref_box)
                else:
                    _file=_file.encode('utf8')
                    with open('files/'+folder+'/'+_file) as myfile:
                        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
                    past_start=False
                    ref_box = []
                    for line in lines:
                        if not_blank(line):
                            if u"@88" in line:
                                past_start=True
                            if past_start:
                                if u'00השמטות' in line or 'BREAK' in line:
                                    break
                                if u"@88" in line:
                                    if len(ref_box)>0:
                                        final_text[current_sheilta-1].append(ref_box)
                                        ref_box=[]
                                    current_sheilta=getGematria(line)
                                elif u'@22' in line and u'@22(א)' not in line:
                                    if len(ref_box)>0:
                                        final_text[current_sheilta-1].append(ref_box)
                                        ref_box=[]
                                elif u"@00" not in line and u"@22" not in line:
                                    ref_box.append(fix_comment_markers(line))
                    if len(ref_box)>0:
                        final_text[current_sheilta-1].append(ref_box)
    final_text[170]=final_text[170][1:]
    """
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
    """
    
    for sindex, sheilta in enumerate(final_text):
        for rindex, ref in enumerate(sheilta):
            for pindex, paragraph in enumerate(ref):
                print sindex, rindex, pindex, paragraph
    for sindex, sheilta in enumerate(final_text):
        if len(sheilta)!=highest_eimek[sindex]:
            print "Sheilta", sindex+1, "Highest Ref:",highest_eimek[sindex],"Actual Eimek Notes:", len(sheilta) 
    
    version = {
        'versionTitle': 'Sheiltot d\'Rav Achai Gaon; Vilna, 1861',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001166995',
        'language': 'he',
        'text': final_text
    }
    post_text('Haamek Sheilah on Sheiltot d\'Rav Achai Gaon', version,weak_network=True, skip_links=True, index_count="on")
    #post_text_weak_connection('Haamek Sheilah on Sheiltot d\'Rav Achai Gaon', version)#,weak_network=True)#, skip_links=True,
def post_eimek_intros():
    with open('files/במדבר/שאילתות עמק השאלה במדבר.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    in_kidmat=False
    in_petach=False
    next_is_same=False
    kidmat_box=[]
    petach_box=[]
    for line in lines:
        if not_blank(line):
            in_kidmat=True
        if u'@00להכנס בדברים של גאון בעל השאלתות והביאורים בעזרת הנותן כח לאין אונים לחבר חבורים' in line:
            in_petach=True
        if u'@00פרשת במדבר' in line:
            break
        if in_petach:
            if next_is_same and len(petach_box)>0:
                petach_box[-1].append(clean_intro_line(line))
                next_is_same=False
            else:
                petach_box.append([clean_intro_line(line)])
        elif in_kidmat and u"@00פתח" not in line:
            if next_is_same and len(kidmat_box)>0:
                kidmat_box[-1].append(clean_intro_line(line))
                next_is_same=False
            else:
                kidmat_box.append([clean_intro_line(line)])
        if u'@00' in line:
            next_is_same=True
    """
    for cindex, chapter in enumerate(kidmat_box):
        for pindex, paragraph in enumerate(chapter):
            print "Kid",cindex, pindex, paragraph
    for cindex, chapter in enumerate(petach_box):
        for pindex, paragraph in enumerate(chapter):
            print "Pet",cindex, pindex, paragraph
    """

    version = {
        'versionTitle': 'Sheiltot d\'Rav Achai Gaon; Vilna, 1861',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001166995',
        'language': 'he',
        'text': kidmat_box
    }
    #post_text('Haamek Sheilah on Sheiltot d\'Rav Achai Gaon, Kidmat HaEmek', version,weak_network=True)#, skip_links=True, index_count="on")
    #post_text_weak_connection('Haamek Sheilah on Sheiltot d\'Rav Achai Gaon', version)#,weak_network=True)#, skip_links=True,
    
    version = {
        'versionTitle': 'Sheiltot d\'Rav Achai Gaon; Vilna, 1861',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001166995',
        'language': 'he',
        'text': petach_box
    }
    #post_text('Haamek Sheilah on Sheiltot d\'Rav Achai Gaon, Petach HaEmek', version,weak_network=True)#, skip_links=True, index_count="on")
    #post_text_weak_connection('Haamek Sheilah on Sheiltot d\'Rav Achai Gaon, Petach HaEmek', version)#,weak_network=True)#, skip_links=True,
def post_bereshit_eimek_intro():
    with open('files/בראשית/שאילתות הקדמת העמק שאלה.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    chapter_box=[]
    hakdama_box = []
    for line in lines:
        if not_blank(line) and u'קדמת העמק' not in line:
            if u'@22' in line:
                if u'@22א' not in line:
                    hakdama_box.append(chapter_box)
                    chapter_box=[]
            else:
                chapter_box.append(re.sub(ur"@\d{1,4}",u"",line))
    hakdama_box.append(chapter_box)
    
    """
    #print test
    for cindex, chapter in enumerate(hakdama_box):
        for pindex, paragraph in enumerate(chapter):
            print cindex, pindex, paragraph
    """
    
    version = {
        'versionTitle': 'Sheiltot d\'Rav Achai Gaon, Kidmat HaEmek, volume I, 1861-1867',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001166995',
        'language': 'he',
        'text': hakdama_box
    }
    post_text_weak_connection('Haamek Sheilah on Sheiltot d\'Rav Achai Gaon, Kidmat HaEmek', version)#,weak_network=True)#, skip_links=True,

def post_vayikra_eimek_intro():    
    with open('files/ויקרא/שאילתות עמק השאלה ויקרא.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    chapter_box = []
    kidmat_box=[]
    petach_box=[]
    in_kidmat=False
    in_petach=False
    for line in lines:
        if u'@00השמטות' in line:
            petach_box.append(chapter_box)
            break
        if not_blank(line):
            if u'@00פתח העמק' in line:
                in_petach=True
                kidmat_box.append(chapter_box)
                chapter_box=[]
            elif u'ספרים ראשונים להגבה מעלה. שהם חביון עוז כל דבר סגלה' in line:
                in_kidmat=True
            elif in_petach:
                if re.search(ur'@44[^@]*?\s',line):
                    petach_box.append(chapter_box)
                    chapter_box=[]
                    #print re.search(ur'@44[^@]*?\s',line).group()
                chapter_box.append(clean_intro_line(line))
            elif in_kidmat:
                if u'@11' in line:
                    kidmat_box.append(chapter_box)
                    chapter_box=[]
                chapter_box.append(clean_intro_line(line))
    version = {
        'versionTitle': 'Sheiltot d\'Rav Achai Gaon, Kidmat HaEmek, volume II, 1861-1867',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001166995',
        'language': 'he',
        'text': kidmat_box
    }
    post_text_weak_connection('Haamek Sheilah on Sheiltot d\'Rav Achai Gaon, Kidmat HaEmek', version)
    
    version = {
        'versionTitle': 'Sheiltot d\'Rav Achai Gaon, Kidmat HaEmek, volume II, 1861-1867',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001166995',
        'language': 'he',
        'text': petach_box
    }
    post_text_weak_connection('Haamek Sheilah on Sheiltot d\'Rav Achai Gaon, Petach HaEmek', version)
    
            

def clean_intro_line(s):
    s = re.sub(ur'\s@11',u'',s)
    if u"@33" in s:
        s = ' '.join(s.split()[1:])
    return re.sub(ur"@\d{1,4}",u"",s)
def link_eimek_text():
    for sindex, sheilta in enumerate(fixed_sheiltot):
        for pindex, paragraph in enumerate(sheilta):
            #print paragraph
            for match in re.findall(ur'<.*?>',paragraph):
                if 'Haamek' in match:
                    data_order = re.search(ur'data-order=\"\d*',match).group().split(u'"')[1]
                    if 'data-label' in match:
                        link = (
                                {
                                "refs": [
                                         Ref('Haamek Sheilah on Sheiltot d\'Rav Achai Gaon, {}:{}'.format(sindex+1,data_order)).as_ranged_segment_ref().normal(),
                                         'Sheiltot d\'Rav Achai Gaon {}:{}'.format(sindex+1, pindex+1),
                                         ],
                                "type": "commentary",
                                'inline_reference': {
                                    'data-commentator': "Haamek Sheilah on Sheiltot d\'Rav Achai Gaon",
                                    'data-order': data_order,
                                    'data-label': '*'
                                    },
                                "auto": True,
                                "generated_by": "sterling_Haamek_Sheilah_linker"
                                })
                    else:
                        link = (
                                {
                                "refs": [
                                         Ref('Haamek Sheilah on Sheiltot d\'Rav Achai Gaon, {}:{}'.format(sindex+1,data_order)).as_ranged_segment_ref().normal(),
                                         'Sheiltot d\'Rav Achai Gaon {}:{}'.format(sindex+1, pindex+1),
                                         ],
                                "type": "commentary",
                                'inline_reference': {
                                    'data-commentator': "Haamek Sheilah on Sheiltot d\'Rav Achai Gaon",
                                    'data-order': data_order
                                    },
                                "auto": True,
                                "generated_by": "sterling_Haamek_Sheilah_linker"
                                })
                    post_link(link, weak_network=True)
def post_shalom_index():
    # create index record
    record = SchemaNode()
    record.add_title('Sheilat Shalom on Sheiltot d\'Rav Achai Gaon', 'en', primary=True, )
    record.add_title(u'שאילת שלום על שאילתות דרב אחאי גאון', 'he', primary=True, )
    record.key = 'Sheilat Shalom on Sheiltot d\'Rav Achai Gaon'

    #add node for introduction
    intro_node = JaggedArrayNode()
    intro_node.add_title("Introduction", 'en', primary = True)
    intro_node.add_title("הקדמה", 'he', primary = True)
    intro_node.key = "Introduction"
    intro_node.depth = 1
    intro_node.addressTypes = ['Integer']
    intro_node.sectionNames = ['Paragraph']
    record.append(intro_node)
    
    comment_nodes = JaggedArrayNode()
    comment_nodes.key = "default"
    comment_nodes.default = True
    comment_nodes.depth = 2
    comment_nodes.addressTypes = ['Integer','Integer']
    comment_nodes.sectionNames = ['Comment','Paragraph']
    record.append(comment_nodes)
    
    record.validate()

    index = {
        "title": 'Sheilat Shalom on Sheiltot d\'Rav Achai Gaon',
        "categories": ["Halakhah","Commentary"],
        "dependence": "Commentary",
        "collective_title": "Sheilat Shalom",
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def post_shalom_text():
    #first post intro
    with open('files/'+'בראשית'+'/'+'שאלתות בראשית שאילת שלום.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    intro_box = []
    for line in lines:
        if u"@22" in line:
            break
        intro_box.append(re.sub(ur"@\d{1,4}",u"",line))
    final_text = [[] for x in range(153)]
    add_to_next=[]
    current_sheilta=1
    next_one_is_added=True
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
                        if u'@22' in line:
                            if u'*' not in line:
                                current_sheilta=getGematria(line)
                        elif not_blank(line):
                            #print current_sheilta, final_text[current_sheilta-1]
                            #if len(final_text[current_sheilta-1][-1])>0:
                            #    final_text[current_sheilta-1][-1]+=u'<br>'
                            final_text[current_sheilta-1].append(shalom_clean_line(line))
    """
    for cindex, comment in enumerate(final_text):
        for pindex, paragraph in enumerate(comment):
            print cindex, pindex, paragraph
    """
    version = {
        'versionTitle': 'Sheiltot d\'Rav Achai Gaon; Vilna, 1861',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001166995',
        'language': 'he',
        'text': intro_box
    }
    #post_text('Sheilat Shalom on Sheiltot d\'Rav Achai Gaon, Introduction', version,weak_network=True, skip_links=True, index_count="on")
    post_text_weak_connection('Sheilat Shalom on Sheiltot d\'Rav Achai Gaon, Introduction', version)#,weak_network=True)#, skip_links=True,    
    version = {
        'versionTitle': 'Sheiltot d\'Rav Achai Gaon; Vilna, 1861',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001166995',
        'language': 'he',
        'text': final_text
    }
    post_text_weak_connection('Sheilat Shalom on Sheiltot d\'Rav Achai Gaon', version)#,weak_network=True)#, skip_links=True,

def post_shalom_term():
    term_obj = {
        "name": "Sheilat Shalom",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Sheilat Shalom",
                "primary": True
            },
            {
                "lang": "he",
                "text": u'שאילת שלום',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
    
def post_eimek_term():
    term_obj = {
        "name": "Haamek Sheilah",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Haamek Sheilah",
                "primary": True
            },
            {
                "lang": "he",
                "text": u'העמק שאלה ב',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
def post_sheilta_term():
    term_obj = {
        "name": "Sheilta",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Sheilta",
                "primary": True
            },
            {
                "lang": "he",
                "text": u'שאילתא',
                "primary": True
            }
        ]
    }
    post_term(term_obj)                         
def shalom_link():
    #for linking we just link each ref (that isn't a *) to the first ref in that index location
    #except for the first one, where we link it to the third.
    #keeps track of how many matches we have for each shalom index
    shalom_index_array = [[] for x in range(153)]

    for sindex, sheilta in enumerate(fixed_sheiltot):
        for pindex, paragraph in enumerate(sheilta):
            #print paragraph
            for match in re.findall(ur'<.*?>',paragraph):
                if 'Sheilat' in match:
                    print match
                    data_order = re.search(ur'data-order=\"\d*',match).group().split(u'"')[1]
                    shalom_index_array[int(data_order)-1].append([])
                    #lenlen = len(shalom_index_array[int(data_order)-1])
                    if 'data-label' in match:
                        link = (
                                {
                                "refs": [
                                         'Sheilat Shalom on Sheiltot d\'Rav Achai Gaon, {}:{}'.format(data_order, len(shalom_index_array[int(data_order)-1])),
                                         'Sheiltot d\'Rav Achai Gaon {}:{}'.format(sindex+1, pindex+1),
                                         ],
                                "type": "commentary",
                                'inline_reference': {
                                    'data-commentator': "Sheilat Shalom on Sheiltot d\'Rav Achai Gaon",
                                    'data-order': data_order,
                                    'data-label': '*'
                                    },
                                "auto": True,
                                "generated_by": "sterling_sheilat_shalom_linker"
                                })
                    else:
                        link = (
                                {
                                "refs": [
                                         'Sheilat Shalom on Sheiltot d\'Rav Achai Gaon, {}:{}'.format(data_order, len(shalom_index_array[int(data_order)-1])),
                                         'Sheiltot d\'Rav Achai Gaon {}:{}'.format(sindex+1, pindex+1),
                                         ],
                                "type": "commentary",
                                'inline_reference': {
                                    'data-commentator': "Sheilat Shalom on Sheiltot d\'Rav Achai Gaon",
                                    'data-order': data_order
                                    },
                                "auto": True,
                                "generated_by": "sterling_sheilat_shalom_linker"
                                })
                    post_link(link, weak_network=True)
def shalom_clean_line(s):
    s = s.replace(u"@11",u"<b>").replace(u"@33",u"</b>")
    return re.sub(ur"@\d{1,4}",u"",s)          
def post_sra_text():
    """
    for sindex, sheilta in enumerate(fixed_sheiltot):
        for pindex, paragraph in enumerate(sheilta):
            print sindex, pindex, paragraph
    """
    version = {
        'versionTitle': 'Sheiltot d\'Rav Achai Gaon; Vilna, 1861',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001166995',
        'language': 'he',
        'text': fixed_sheiltot
    }
    #post_text('Sheiltot d\'Rav Achai Gaon', version,weak_network=True, skip_links=True, index_count="on")
    post_text_weak_connection('Sheiltot d\'Rav Achai Gaon', version)#,weak_network=True)#, skip_links=True, index_count="on")

#post_sheilta_term()

#post_sra_index()
#post_sra_text()

#post_eimek_term()
post_eimek_index()
post_bereshit_eimek_intro()
post_vayikra_eimek_intro()
post_eimek_intros()
post_eimek_text()
link_eimek_text()

#post_shalom_term()
post_shalom_index()
post_shalom_text()
shalom_link()
"""
keys:
Base Text:
@22- New Sheilta
@44- Eimek Note
@55- Sheilas Shalom Note
        
Eimek = 
@88- new sheilta
@22- new note
and 'order=\"1' in match

Intro names:
Kidmat HaEmek / קדמת העמק [Chapter, Paragrpah]
Petach HaEmek / פתח העמק [Chapter, Paragrpah]
"""

                


