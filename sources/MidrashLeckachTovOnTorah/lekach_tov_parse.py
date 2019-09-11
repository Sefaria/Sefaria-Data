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
import re
import csv
#from fuzzywuzzy import fuzz
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

eng_parshiot_dict={
    "Leviticus":["Vayikra", "Tzav", "Shmini",
"Tazria", "Metzora", "Achrei Mot", "Kedoshim", "Emor", "Behar", "Bechukotai"],
    "Numbers":["Bamidbar", "Nasso",
"Beha'alotcha", "Sh'lach", "Korach", "Chukat", "Balak", "Pinchas", "Matot", "Masei"],
    "Deuteronomy":["Devarim", "Vaetchanan", "Eikev", "Re'eh", "Shoftim", "Ki Teitzei", "Ki Tavo", "Nitzavim", "Vayeilech", "Ha'Azinu",
"V'Zot HaBerachah"]
}

en_sefer_names = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy"]
he_sefer_names =  [u"בראשית",u"שמות" ,u"ויקרא",u"במדבר",u"דברים"]
def make_perek_array(book):
    tc = TextChunk(Ref(book), "he")
    return_array = []
    for x in range(len(tc.text)):
        return_array.append([])
    for index, perek in enumerate(return_array):
        tc = TextChunk(Ref(book+" "+str(index+1)), "he")
        for x in range(len(tc.text)):
            return_array[index].append([])
    return return_array
def is_csv_file(s):
    return ".csv" in s
def is_txt_file(s):
    return ".txt" in s
def not_blank(s):
    while u" " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def not_a_csv_null(s):
    s=re.sub(ur'@\d*',u'',s)
    s.replace(u',',u'')
    return len(s)>0
def post_lekach_tov_index():
    # create index record
    record = SchemaNode()
    record.add_title('Midrash Lekach Tov on Torah', 'en', primary=True, )
    record.add_title(u'מדרש לקח טוב על תורה', 'he', primary=True, )
    record.key = 'Midrash Lekach Tov on Torah'


    for en_sefer, he_sefer in zip(en_sefer_names, he_sefer_names):
        sefer_node = JaggedArrayNode()
        sefer_node.add_title(en_sefer, 'en', primary=True, )
        sefer_node.add_title(he_sefer, 'he', primary=True, )
        sefer_node.key = en_sefer
        sefer_node.depth = 3
        sefer_node.toc_zoom = 2
        sefer_node.addressTypes = ['Integer', 'Integer','Integer']
        sefer_node.sectionNames = ['Chapter','Verse','Comment']
        record.append(sefer_node)
    
    #alt struct for parasha
    parsha_nodes =SchemaNode()
    for sefer in en_sefer_names: 
        for parsha in library.get_index(sefer).alt_structs['Parasha']['nodes']:
            print parsha['sharedTitle']
            parsha_node = ArrayMapNode()
            parsha_node.wholeRef = "Midrash Lekach Tov on Torah, {}".format(parsha['wholeRef'])
            parsha_node.key = parsha['sharedTitle']
            parsha_node.depth=0
            parsha_node.add_shared_term(parsha['sharedTitle'])
            parsha_nodes.append(parsha_node)
    record.validate()

    index = {
        "title":"Midrash Lekach Tov on Torah",
        "base_text_titles": [
           "Genesis","Exodus","Leviticus","Numbers","Deuteronomy"
        ],
        "dependence": "Commentary",
        "alt_structs": {"Parasha": parsha_nodes.serialize()},
        "categories":['Midrash', 'Aggadic Midrash','Midrash Lekach Tov'],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def fix_ocr_errs(last_matched, current_match, next_match=None):
    #print "In OCR fix, HAVE {} {} {}".format(last_matched, current_match, next_match)
    if next_match and last_matched+2==next_match and current_match!=last_matched:
        #print "DID 3"
        return last_matched+1
    if last_matched%10==7 and current_match%10==5:
        #print "DID 7 8"
        return current_match-current_match%10+8
    if last_matched%10==8 and current_match%10==5:
        #print "DID 8 8"
        return last_matched
    if last_matched%10==2 and current_match%10!=3 and current_match!=1:
        #print "DID 2 3"
        #print "return ",last_matched+1
        return last_matched+1
    if last_matched%10==5 and current_match%10==0:
        #print "DID 5 0"
        return last_matched+1
    #print "DID NOTHING"
    return current_match

def clean_csv_sefer(sefer, sefer_name):
    return_array=[]
    for cindex, chapter in enumerate(sefer):
        return_array.append([[] for x in range(len(chapter))])
    matched_list=[]
    num_1_count=0
    ref_num=False
    for cindex, chapter in enumerate(sefer):
        for vindex, verse in enumerate(chapter):
            for mindex, midrash in enumerate(verse):
                for match in re.findall(ur'@45.*?@46',midrash):
                    matched_list.append(getGematria(match))
    match_count=0
    ref_num=False
    last_matched=False
    vayikra_exception=True
    overriding=False
    for cindex, chapter in enumerate(sefer):
        for vindex, verse in enumerate(chapter):
            for mindex, midrash in enumerate(verse):
                s = midrash
                for match in re.findall(ur'@45.*?@46',midrash):
                    if "IG" not in match:
                        if overriding and getGematria(match)==1:
                            overriding=False
                        if overriding:
                            ref_num+=1
                            #print "OVERRIDING",ref_num
                        elif getGematria(match)==1 and match_count>0 and "Lev" in sefer_name and vayikra_exception:
                            overriding=True
                            vayikra_exception=False
                            ref_num+=1
                        elif ref_num and len(matched_list)>match_count+1:
                            ref_num=fix_ocr_errs(last_matched, matched_list[match_count], matched_list[match_count+1])
                        elif ref_num:
                            ref_num=fix_ocr_errs(last_matched, matched_list[match_count])
                        else:
                            ref_num=getGematria(match)
                        if ref_num==1:
                            num_1_count+=1
                        #print "RN",ref_num
                        if last_matched:
                            if last_matched>ref_num and ref_num!=1 and "IG" not in match:
                                print "Error",sefer_name, last_matched, ref_num
                                print "BEFORE...", last_p
                                print midrash
                                0/0
                        last_matched=ref_num
                    match_count+=1
                    last_p=midrash
                    s=s.replace(match, u'~{}.{}'.format(eng_parshiot_dict[sefer_name][num_1_count-1].replace(u' ',u'_'),ref_num), 1)
                return_array[cindex][vindex].append(s)
    """
    for cindex, chapter in enumerate(return_array):
        for vindex, verse in enumerate(chapter):
            for mindex, midrash in enumerate(verse):
                print sefer_name, cindex, vindex, mindex, midrash
    """
    return return_array
def clean_txt_perek(p, perek_six=False, perek_one=False, perek_num=False):
    if perek_six:
        print "PEREK SIX"
    matched_list=[]
    return_array=[[] for x in range(len(p))]
    last_matched=0
    ref_num=None
    match_count=0
    matches_in_perek=[]
    last_found=None
    for pindex, pasuk in enumerate(p):
        for s in pasuk:
            for match in re.findall(ur'@45.*?@46',s):
                if "IGNORE" not in match:
                    matches_in_perek.append(getGematria(match))
    for pindex, pasuk in enumerate(p):
        for s in pasuk:
            if u'@11' in s:
                s = s[s.index(u'@11')+3:].strip()
                #if u'.' in s:
                #    s = u'<b>'+s[:s.index(u'.')+1]+u'</b>'+s[s.index(u'.')+1:]
            for match in re.findall(ur'@45.*?@46',s):
                if "IGNORE" not in match:
                    if ref_num:
                        if perek_six and fix_ocr_errs(ref_num,getGematria(match))<ref_num:
                            print "DID PS"
                            ref_num+=1
                        elif match_count<len(matches_in_perek)-1:
                            ref_num=fix_ocr_errs(last_matched, matches_in_perek[match_count], matches_in_perek[match_count+1])
                        else:
                            ref_num=fix_ocr_errs(last_matched, matches_in_perek[match_count])
                        if perek_six:
                            print "RN", ref_num
                    else:
                        ref_num=getGematria(match)
                    if ref_num>200:
                        print "TOO HIGH"
                        print match
                    if ref_num<last_matched and ref_num!=1 and not perek_one:
                        print "S",s
                        print "M",match
                        print last_matched, ref_num
                        print "LAST FOUND ",last_found
                        0/0
                    match_count+=1
                    if ref_num not in matched_list:
                        #s=s.replace(match, u"""<i data-commentator="Notes and Corrections on Midrash Lekach Tov" data-order="{}"></i>""".format(ref_num), 1)
                        s=s.replace(match, u'~{}.{}'.format(ref_num, perek_num),1)
                        matched_list.append(ref_num)
                    else:
                        s=s.replace(match, u'~{}.{}'.format(ref_num, perek_num), 1)
                    last_matched=ref_num
                    last_found=match
            #s=re.sub(ur"@\d{1,4}",u"",s)
            if s[-1]==u'.' or s[-1]==u':':
                return_array[pindex].append(s)
            else:
                return_array[pindex].append(s+u'.')
    
    for pindex, p in enumerate(return_array):
        for paindex, pa in enumerate(p):
            print "IN CLEAN",perek_num,pindex, paindex, pa
    
    return return_array
def parse_mlt_csvs(parsing=True):
    return_list=[]
    csv_files=['lekach_tov_link_-_Leviticus_corrected.csv','lekach_tov_link_-_Numbers_corrected.csv','lekach_tov_link_-_Deuteronomy_corrected.csv']
    for file in csv_files:
        last_perek=0
        last_pasuk=0
        past_start=False
        sefer = re.findall(ur'(?<=_-_).*(?=_)',file)[0]
        print "parsing", sefer
        text_array= make_perek_array(sefer)
        with open('lekach_tov_link_-_manually_corrected/'+file, 'rb') as f:
            reader = csv.reader(f)
            for row in reader:
                if '@88' in row[0]:
                    past_start=True
                elif past_start and 'Lek' not in row[0] and '@88' not in row[0]:
                    ref_pair=row[1].split(u':')
                    
                    if ref_pair[0]<last_perek:
                        print "BAD PEREK",sefer,ref_pair[0],last_perek
                        print row[0]
                        1/0
                    if ref_pair[0]!=last_perek:
                        last_perek=int(ref_pair[0])
                        last_pasuk=0
                        
                    if ref_pair[1]<last_pasuk:
                        print "BAD PASUK",sefer, ref_pair[1], last_pasuk
                        print row[0]
                        1/0
                    last_pasuk=int(ref_pair[1])
                    #print sefer, row[1], row[0]
                    text_array[int(ref_pair[0])-1][int(ref_pair[1])-1].append(row[0].decode('utf8','replace'))
        #final_text_array=[]
        #for perek in text_array:
        #    final_text_array.append(clean_csv_perek(perek, sefer))
        final_text_array=clean_csv_sefer(text_array, sefer)
        return_list.append(final_text_array)
        version = {
            'versionTitle': 'Midrash Lekach Tov on Torah, Vilna 1884',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001922206',
            'language': 'he',
            'text': final_text_array
        }
        if parsing:
            if SEFARIA_SERVER == "http://localhost:8000":
                post_text('Midrash Lekach Tov on Torah, '+sefer,  version,weak_network=True, skip_links=True, index_count="on")
            else:
                post_text_weak_connection('Midrash Lekach Tov on Torah, '+sefer, version)
    return return_list
def parse_mlt_txts(posting=True):
    exceptions={"Genesis":[[2,12]], "Exodus":[[26,10]]}
    return_array=[]
    txt_files=['לקח טוב בראשית.txt','לקח טוב שמות.txt']
    for file in filter(is_txt_file,os.listdir("files")):
        if file in txt_files:
            with open("files/"+file) as myFile:
                lines = list(map(lambda x: x.decode("utf-8",'replace'), myFile.readlines()))
            sefer=u''
            for sefer_name in he_sefer_names:
                if sefer_name in file.decode('utf8','replace'):
                    sefer = en_sefer_names[he_sefer_names.index(sefer_name)]
            print "PARSING SEFER",sefer
            text_array= make_perek_array(sefer)
            current_perek=0
            current_pasuk=1
            past_start=False
            new_perek=False
            for chunk in lines:
                for line in chunk.split(u':'):
                    if "BEGIN" in line:
                        past_start=True
                    elif past_start: 
                        if u'@99' in line:
                            if getGematria(re.findall(ur'@99\S*', line)[0])!=current_perek+1:
                                print "BAD PEREK", line, sefer
                                1/0
                            print "NEW PEREK", getGematria(re.findall(ur'@99\S*', line)[0])
                            current_perek=getGematria(re.findall(ur'@99\S*', line)[0])
                            current_pasuk=1
                            new_perek=True
                        if u'@55' in line:
                            if current_pasuk>fix_ocr_errs(current_pasuk,getGematria(re.findall(ur'@55.*?\)', line)[0])) and not new_perek and [current_perek, current_pasuk] not in exceptions[sefer]:
                                print "BAD PASUK", line, sefer
                                print current_perek, current_pasuk
                                1/0
                            new_perek=False
                            print "PASUK LINE",line
                            current_pasuk=fix_ocr_errs(current_pasuk,getGematria(re.findall(ur'@55.*?\)', line)[0]))
                        if not_blank(line):
                            #print sefer, current_perek, current_pasuk
                            text_array[current_perek-1][current_pasuk-1].append(line)
            final_text_array=[]
            for pindex, perek in enumerate(text_array):
                if pindex==5 and u'Gen' in sefer:
                    final_text_array.append(clean_txt_perek(perek, perek_six=True, perek_num=pindex+1))
                elif pindex==0 and u'Ex' in sefer:
                    final_text_array.append(clean_txt_perek(perek, perek_one=True, perek_num=pindex+1))
                else:
                    final_text_array.append(clean_txt_perek(perek, perek_num=pindex+1))
            return_array.append(final_text_array)
            version = {
                'versionTitle': 'Midrash Lekach Tov on Torah, Vilna 1884',
                'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001922206',
                'language': 'he',
                'text': final_text_array
            }
            if posting:
                if SEFARIA_SERVER == "http://localhost:8000":
                    post_text('Midrash Lekach Tov on Torah, '+sefer,  version,weak_network=True, skip_links=True, index_count="on")
                else:
                    post_text_weak_connection('Midrash Lekach Tov on Torah, '+sefer, version)
    return return_array
def post_notes_and_comments_index():
    # create index record
    record = SchemaNode()
    record.add_title('Notes and Corrections on Midrash Lekach Tov on Torah', 'en', primary=True, )
    record.add_title(u'הערות ותיקונים על מדרש לקח טוב על תורה', 'he', primary=True, )
    record.key = 'Notes and Corrections on Midrash Lekach Tov on Torah'

    en_sefer_names = ["Genesis","Exodus"]
    he_sefer_names =  [u"בראשית",u"שמות"]
    for en_sefer, he_sefer in zip(en_sefer_names, he_sefer_names):
        sefer_node = JaggedArrayNode()
        sefer_node.add_title(en_sefer, 'en', primary=True, )
        sefer_node.add_title(he_sefer, 'he', primary=True, )
        sefer_node.key = en_sefer
        sefer_node.depth = 2
        sefer_node.addressTypes = ['Integer', 'Integer']
        sefer_node.sectionNames = ['Chapter','Comment']
        record.append(sefer_node)

    index = {
        "title":'Notes and Corrections on Midrash Lekach Tov on Torah',
        "base_text_titles": [
           "Midrash Lekach Tov on Torah"
        ],
        "dependence": "Commentary",
        "categories":['Midrash', 'Aggadic Midrash',"Midrash Lekach Tov"],
        "collective_title": "Notes and Corrections on Midrash Lekach Tov",
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def parse_notes_and_comments(posting=True):
    return_list=[]
    writing_report=True
    #nac_files = ['הערות_ותיקונים_-_בראשית.csv','הערות_ותיקונים_-_שמות .csv']
    nac_files=['Genesis_notes_and_comments_edited - w greek.tsv','Exodus_notes_and_comments_edited - w greek.tsv']
    for index, _file in enumerate(nac_files):
        sefer = en_sefer_names[index]
        print sefer
        if True:#"Ex" in sefer:
            tc = TextChunk(Ref(sefer), "he")
            sefer_index = []
            for x in range(len(tc.text)):
                sefer_index.append([])
            current_perek=0
            current_ref_num=0
            with open("notes_csv_files/"+_file, 'rb') as f:
                reader = csv.reader(f)
                for row in reader:
                    if not_blank(row[2].decode('utf8','replace')):
                        if len(row[0])>0:
                            current_perek=getGematria(row[0])
                            print "NEW NOTE CHAPTER",row[0]
                            overriding=False
                        if overriding:
                            current_ref_num+=1
                            print "overriden", current_ref_num
                            print "have ",len(sefer_index[current_perek-1])
                        elif getGematria(row[1])==current_ref_num:
                            sefer_index[current_perek-1][-1]+=u'<br>{}'.format(row[2])
                        elif len(sefer_index[current_perek-1])>fix_ocr_errs(current_ref_num,getGematria(row[1])) and current_perek==6:
                            current_ref_num+=1
                            print "6 was overriden", current_ref_num
                            print "have ",len(sefer_index[current_perek-1])
                            overriding=True
                        else:
                            current_ref_num=fix_ocr_errs(current_ref_num,getGematria(row[1]))
                    
                        if len(sefer_index[current_perek-1])>current_ref_num-1:# and current_perek!=6:
                            print "PEREK LEN", len(sefer_index[current_perek-1])
                            print current_ref_num
                            print "FIXIT ",row[2]
                            1/0
                        while len(sefer_index[current_perek-1])<current_ref_num-1:
                            print "there ain't no ", current_perek, len(sefer_index[current_perek-1])+1
                            sefer_index[current_perek-1].append([])
                        sefer_index[current_perek-1].append(row[2])
                        print "On to next note, now length ",len(sefer_index[current_perek-1])
            for pindex, perek in enumerate(sefer_index):
                for cindex, comment in enumerate(perek):
                    print sefer, pindex, cindex, comment
            
            return_list.append(sefer_index)
            version = {
                'versionTitle': 'Midrash Lekach Tov on Torah, Vilna 1884',
                'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001922206',
                'language': 'he',
                'text': sefer_index
            }
            if posting:
                post_text_weak_connection('Notes and Corrections on Midrash Lekach Tov on Torah, '+sefer, version)
    return return_list
def post_biur_index():
    # create index record
    record = SchemaNode()
    record.add_title('Beur HaRe\'em on Midrash Lekach Tov on Torah', 'en', primary=True, )
    record.add_title(u'באור הרא"ם על מדרש לקח טוב על תורה', 'he', primary=True, )
    record.key = 'Beur HaRe\'em on Midrash Lekach Tov on Torah'

    en_sefer_names = ["Leviticus","Numbers","Deuteronomy"]
    he_sefer_names =  [u"ויקרא",u"במדבר",u"דברים"]
    for en_sefer, he_sefer in zip(en_sefer_names, he_sefer_names):
        sefer_node = SchemaNode()
        sefer_node.add_title(en_sefer, 'en', primary=True, )
        sefer_node.add_title(he_sefer, 'he', primary=True, )
        sefer_node.key = en_sefer
        for pindex, parsha in enumerate(eng_parshiot_dict[en_sefer]):
            parsha_node = JaggedArrayNode()
            parsha_node.add_title(parsha, 'en', primary=True, )
            parsha_node.add_title(heb_parshiot[eng_parshiot.index(parsha)], 'he', primary=True, )
            parsha_node.key = parsha
            parsha_node.depth = 1
            parsha_node.addressTypes = ['Integer']
            parsha_node.sectionNames = ['Comment']
            sefer_node.append(parsha_node)
        record.append(sefer_node)

    index = {
        "title":'Beur HaRe\'em on Midrash Lekach Tov on Torah',
        "base_text_titles": [
           "Midrash Lekach Tov on Torah"
        ],
        "dependence": "Commentary",
        "collective_title": "Beur HaRe\'em on Midrash Lekach Tov",
        "categories":['Midrash', 'Aggadic Midrash',"Midrash Lekach Tov"],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def parse_beur_reim(posting=True):
    vayikra_exception=False
    return_list=[]
    br_file_names=['לקח_טוב_-_באור_הראם_ויקרא.csv','לקח_טוב_-_באור_הראם_במדבר.csv','לקח_טוב_-_באור_הראם_דברים.csv']
    for index, _file in enumerate(br_file_names):
        sefer = en_sefer_names[index+2]
        override=False
        if index==0:
            vayikra_exception=True
        #sefer_index=[[] for x in range(len(TextChunk(Ref(sefer), "he").text))]
        sefer_parshiot=[]
        with open("beur_files/"+_file, 'rb') as f:
            reader = csv.reader(f)
            #current_perek=0
            parsha_box=[]
            current_ref_num=0
            for row in reader:
                #print row[0]
                if fix_ocr_errs(current_ref_num,getGematria(row[0]))==current_ref_num:
                    parsha_box[-1]+='<br>'+row[1]
                else:
                    if override and getGematria(row[0])!=1:
                        current_ref_num+=1
                    else:
                        current_ref_num=fix_ocr_errs(current_ref_num,getGematria(row[0]))
                    #print current_ref_num, type(current_ref_num)
                    if current_ref_num==1 and len(parsha_box)>0:
                        if vayikra_exception:
                            vayikra_exception=False
                            override=True
                            current_ref_num=195
                        else:
                            override=False
                            sefer_parshiot.append(parsha_box)
                            parsha_box=[]
                            current_ref_num=1
                    while len(parsha_box)<current_ref_num-1:
                        parsha_box.append([])
                    parsha_box.append(row[1])
            if len(parsha_box)>0:
                sefer_parshiot.append(parsha_box)
            """
            for pindex, parsha in enumerate(sefer_parshiot):
                for cindex, comment in enumerate(parsha):
                    if len(eng_parshiot_dict[sefer])>pindex:
                        print eng_parshiot_dict[sefer][pindex],cindex, comment
                    else:
                        print "Out of Index", cindex, comment
            #1/0
            """
            return_list.append(sefer_parshiot)
            
            for pindex, parsha in enumerate(sefer_parshiot):
                print "Posting {}...".format(eng_parshiot_dict[sefer][pindex])
                version = {
                    'versionTitle': 'Midrash Lekach Tov on Torah, Vilna 1884',
                    'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001922206',
                    'language': 'he',
                    'text': parsha
                }
                if posting:
                    post_text_weak_connection('Beur HaRe\'em on Midrash Lekach Tov on Torah, {}, {}'.format(sefer, eng_parshiot_dict[sefer][pindex]), version)
    return return_list
def get_intro():
    returning=[]
    with open("final_text_files/הקדמה.txt") as myFile:
        lines = list(map(lambda x: x.decode("utf-8",'replace'), myFile.readlines()))
    for line in lines:
        if not_blank(line):
            print "INTRO LINE",line
            returning.append(clean_intro_line(line))
    return returning
def clean_intro_line(s):
    s=s.replace(u'@11', u'<b>').replace(u'@22', u'</b>')
    for match in re.findall(ur'@45.*?@46',s):
        s=s.replace(match, u'&1.{}'.format(getGematria(match)))
    return s
def parse_new_be_files(posting=False):
    files=['Genesis_LT_edited.tsv','Exodus_LT_edited.tsv']
    return_array=[]
    for findex, file in enumerate(files):
        sefer=u''
        for sefer_name in en_sefer_names:
            if sefer_name in file:
                sefer = sefer_name
        print "PARSING SEFER",sefer
        text_array= make_perek_array(sefer)
        current_perek=0
        current_pasuk=1
        with open('final_text_files/{}'.format(file),'rb') as tsvin:
            tsvin = csv.reader(tsvin, delimiter='\t')
            for row in tsvin:
                print "ROW 0", row[0]
                print "ROW 1", row[1]
                current_perek=int(re.sub(r'[^\d]','',row[0].split(':')[0]))
                current_pasuk=int(re.sub(r'[^\d]','',row[0].split(':')[1]))
                text_array[current_perek-1][current_pasuk-1].append(row[1])
        if "Gen" in sefer:
            intro=get_intro()
            for x in range(0,len(intro)):
                text_array[0][0].insert(0,intro.pop())
        for pindex, perek in enumerate(text_array):
            for vindex, verse in enumerate(perek):
                for mindex, midrash in enumerate(verse):
                    print sefer,pindex, vindex, mindex, midrash
        return_array.append(text_array)
        version = {
            'versionTitle': 'Midrash Lekach Tov on Torah, Vilna 1884',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001922206',
            'language': 'he',
            'text': text_array
        }
        if posting:
            if SEFARIA_SERVER == "http://localhost:8000":
                post_text('Midrash Lekach Tov on Torah, '+sefer,  version,weak_network=True, skip_links=True, index_count="on")
            else:
                post_text_weak_connection('Midrash Lekach Tov on Torah, '+sefer, version)
    return return_array

def check_notes():
    texts=parse_new_be_files(False)
    for index, sefer in enumerate(parse_notes_and_comments(False)):
        #lt_text=TextChunk(Ref('Midrash Lekach Tov on Torah, {}'.format(en_sefer_names[index])), 'he').text
        lt_text=texts[index]
        for pindex, perek in enumerate(lt_text):
            check_box=[]
            miss_box=[]
            for psindex, pasuk in enumerate(perek):
                for paindex, paragraph in enumerate(pasuk):
                    for match in re.findall(ur'(?<=&)\d+\.\d+', paragraph):
                        check_box.append(int(match.split('.')[1]))
            if pindex>=len(sefer):
                print "NO PEREK {} IN {} BASE".format(cindex+1, en_sefer_names[index])
            else:
                for cindex, comment in enumerate(sefer[pindex]):
                
                    if len(comment)>0:
                        if cindex+1 in check_box:
                            check_box.remove(cindex+1)
                        else:
                            miss_box.append(cindex+1)
            check_string=''
            while len(check_box)>0:
                check_string+='{} '.format(check_box.pop(0))
            if check_string!='':
                print "These are in the SOURCE {} {} but not the notes:".format(en_sefer_names[index], pindex+1)
                print check_string
            check_string=''
            while len(miss_box)>0:
                check_string+='{} '.format(miss_box.pop(0))
            if check_string!='':
                print "These are in the NOTES {} {} but not the SOURCE:".format(en_sefer_names[index], pindex+1)
                print check_string
def generate_ge_txt_files():
    #texts=parse_mlt_txts(False)
    texts=parse_mlt_csvs(False)
    for tindex, text in enumerate(texts):
        with open('new_text_files/{}_LT_edited.tsv'.format(en_sefer_names[tindex+2]),'w') as myFile:
            for pindex, perek in enumerate(text):
                for paindex, pasuk in enumerate(perek):
                    for mindex, midrash in enumerate(pasuk):
                        myFile.write('{}:{}\t{}\n'.format(pindex+1,paindex+1,midrash.encode('utf8','replace')))
                        
def generate_nc_txt_files():
    texts=parse_notes_and_comments(False)
    for tindex, text in enumerate(texts):
        with open('new_text_files/{}_notes_and_comments_edited.tsv'.format(en_sefer_names[tindex]),'w') as myFile:
            for pindex, perek in enumerate(text):
                for cindex, comment in enumerate(perek):
                    print "COMMENT", type(comment), comment
                    myFile.write('{}:{}\t{}\n'.format(pindex+1,cindex+1,comment))
def generate_biur_files():
    for tindex, text in enumerate(parse_beur_reim(False)):
        with open('new_text_files/{}_biur_edited.tsv'.format(en_sefer_names[tindex+2]),'w') as myFile:
            for pindex, perek in enumerate(text):
                for cindex, comment in enumerate(perek):
                    myFile.write('{}:{}\t{}\n'.format(eng_parshiot_dict[en_sefer_names[tindex+2]][pindex],cindex+1,comment))

def check_beur():
    base_miss_list=[]
    comment_miss_list=[]
    match_list=[]
    bases=parse_mlt_csvs(False)
    for index, biur in enumerate(parse_beur_reim(False)):
        misscount=0
        lt_text=bases[index]
        for pindex, perek in enumerate(lt_text):
            for psindex, pasuk in enumerate(perek):
                for paindex, paragraph in enumerate(pasuk):
                    #print "we're matching these",paragraph
                    for match in re.findall(ur'(?<=~)\d+', paragraph):
                        match_list.append([int(match), '{}:{}:{}'.format(pindex+1, psindex+1,paindex)])
        for pindex, perek in enumerate(biur):
            while match_list[0][0]!=1:
                #print "we're in base  751 {} {} note {} and missed".format(en_sefer_names[index+2], pindex, match_list[0][0])
                
                base_miss_list.append(match_list.pop(0))
                
            for cindex, comment in enumerate(perek):
                if match_list[0][0]==1 and cindex!=0:
                   # print "CHECKING {}:{}".format(match_list[0][0],cindex)
                    #print "we're in notes 757 {} {}:{} and missed".format(en_sefer_names[index+2], pindex, cindex)
                    comment_miss_list.append('{}:{}'.format(eng_parshiot_dict[en_sefer_names[index+2]][pindex], cindex+1))
                else:
                    while cindex+1>match_list[0][0]:
                        #print "we're in base 761 {} {} note {} and missed".format(en_sefer_names[index+2], pindex, match_list[0][0])
                        base_miss_list.append(match_list.pop(0))
                    if cindex+1<match_list[0][0]:
                        #print "we're in notes 764 {} {}:{} and missed".format(en_sefer_names[index+2], pindex, cindex)
                        comment_miss_list.append('{}:{}'.format(eng_parshiot_dict[en_sefer_names[index+2]][pindex], cindex+1))
                if match_list[0][0]==cindex+1:
                    match_list.pop(0)
        prints=''
        for match in base_miss_list:
            prints+='{} in {}\n'.format(match[0],match[1])
        print "These references are in the base but not the notes:"
        print prints
        
        prints=''
        for match in comment_miss_list:
            prints+='{}\n'.format(match)
        print "These references are in the notes but not the base:"
        print prints
                        

#post_lekach_tov_index()
post_notes_and_comments_index()
#parse_notes_and_comments()
post_biur_index()
#parse_beur_reim()
#parse_mlt_csvs(False)
#parse_mlt_txts()
#check_beur()
#generate_ge_txt_files()
#generate_nc_txt_files()
#check_notes()
#get_intro()
#parse_new_be_files()
#generate_biur_files()
"""
2:9
7:14

1842 misses in Leviticus
1269 misses in Numbers
1578 misses in Deuteronomy


print "found",match
if not not_blank(sefer[pindex][int(match)].decode('utf8','replace')):
  print en_sefer_names[index], pindex, match, "MISSING"
  0/0
else:
  print "{}, {}, Matched".format(en_sefer_names[index], pindex)



            for match in re.findall(ur'@45.*?@46',s):
                matches_in_perek.append(getGematria(match))
            for x in range(1,len(matches_in_perek)):
                matches_in_perek[x]=fix_ocr_errs(matches_in_perek[x-1],matches_in_perek[x])
            if len(matches_in_perek)>=3:
                for x in range(0, len(matches_in_perek)-2):
                    if matches_in_perek[x]==matches_in_perek[x+2]+2:
                        matches_in_perek[x+1]=x+2
114 35 23 mlt
45 23 115
"""