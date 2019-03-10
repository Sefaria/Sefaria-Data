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
note_seferim=["Genesis","Exodus"]
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
def get_intro():
    returning=[]
    with open("final_text_files/הקדמה.txt") as myFile:
        lines = list(map(lambda x: x.decode("utf-8",'replace'), myFile.readlines()))
    for line in lines:
        if not_blank(line):
            returning.append(clean_intro_line(line))
    return returning
def clean_intro_line(s):
    s=s.replace(u'@11', u'<b>').replace(u'@22', u'</b>')
    for match in re.findall(ur'@45.*?@46',s):
        s=s.replace(match, u'&1.{}'.format(getGematria(match)))
    return s
def clean_mlt_line(s):
    s=re.sub(ur"@\d{1,4}",u"",s)
    if len(s.split(u' '))>14:
        if u'.' in ''.join(s.split(u' ')[:14]):
            s=u'<b>'+s[:s.index(u'.')+1]+u'</b>'+s[s.index(u'.')+1:]
    s=s.replace(u'\\uXXXX',u'')
    return s
def clean_mlt_perek(perek, sefer, chapter):
    matched=[]
    returning=make_perek_array(sefer)[chapter]
    for pindex, pasuk in enumerate(perek):
        for s in pasuk:
            for match in re.findall(ur'&[\d\.]*',s):
                if match not in matched:
                    s=s.replace(match, u"""<i data-commentator="Notes and Corrections on Midrash Lekach Tov" data-order="{}"></i>""".format(match.split(u'.')[1]), 1)
                else:
                    s=s.replace(match, u'({})'.format(match.split(u'.')[1]), 1)
                matched.append(match)
                    
            for match in re.findall(ur'~.*?\.\d+',s):
                if match not in matched:
                    s=s.replace(match, u"""<i data-commentator="Beur HaRe\'em on Midrash Lekach Tov" data-order="{}"></i>""".format(match.split(u'.')[1]), 1)
                else:
                    s=s.replace(match, u'({})'.format(match.split(u'.')[1]), 1)
                matched.append(match)
                
            returning[pindex].append(clean_mlt_line(s))
    return returning
def not_blank(s):
    while u" " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def post_lekach_tov_text(posting=True):
    mlt_file_names=['Genesis_LT_edited.tsv','Exodus_LT_edited.tsv','Leviticus_LT_edited.tsv','Numbers_LT_edited.tsv','Deuteronomy_LT_edited.tsv']
    return_array=[]
    for index, _file in enumerate(mlt_file_names):
        sefer=u''
        for sefer_name in en_sefer_names:
            if sefer_name in _file:
                sefer = sefer_name
        if True:#"Deu" in sefer:
            print "PARSING SEFER",sefer
            text_array= make_perek_array(sefer)
            current_perek=0
            current_pasuk=1
            with open('final_text_files/{}'.format(_file),'rb') as tsvin:
                tsvin = csv.reader(tsvin, delimiter='\t')
                for row in tsvin:
                    if len(row)>0:
                        current_perek=int(re.sub(r'[^\d]','',row[0].split(':')[0]))
                        current_pasuk=int(re.sub(r'[^\d]','',row[0].split(':')[1]))
                        text_array[current_perek-1][current_pasuk-1].append(row[1].decode('utf8','replace'))
            if "Gen" in sefer:
                intro=get_intro()
                for x in range(0,len(intro)):
                    text_array[0][0].insert(0,intro.pop())

            final_array=[]
            for pindex, perek in enumerate(text_array):
                final_array.append(clean_mlt_perek(perek, sefer, pindex))
            """
            for pindex, perek in enumerate(final_array):
                for vindex, verse in enumerate(perek):
                    for mindex, midrash in enumerate(verse):
                        print sefer,pindex, vindex, mindex, midrash
            """
            return_array.append(final_array)
            version = {
                'versionTitle': 'Midrash Lekach Tov on Torah, Vilna 1884',
                'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001922206',
                'language': 'he',
                'text': final_array
            }
            if posting and "Gen" not in sefer and "Ex" not in sefer:
                if SEFARIA_SERVER == "http://localhost:8000":
                    post_text('Midrash Lekach Tov on Torah, '+sefer,  version,weak_network=True, skip_links=True, index_count="on")
                else:
                    #post_text('Midrash Lekach Tov on Torah, '+sefer,  version,weak_network=True)#, skip_links=True, index_count="on")
                    post_text_weak_connection('Midrash Lekach Tov on Torah, '+sefer, version)
    return return_array
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
        sefer_node.sectionNames = ['Chapter','Verse','Midrash']
        record.append(sefer_node)
    
    #alt struct for parasha
    parsha_nodes =SchemaNode()
    for sefer in en_sefer_names: 
        for parsha in library.get_index(sefer).alt_structs['Parasha']['nodes']:
            #print parsha['sharedTitle']
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
        "collective_title": "Midrash Lekach Tov",
        "dependence": "Commentary",
        "alt_structs": {"Parasha": parsha_nodes.serialize()},
        "categories": ["Midrash","Aggadic Midrash","Midrash Lekach Tov"],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def link_nc():
    for sindex, sefer in enumerate(post_lekach_tov_text(False)):
        sefer_name = en_sefer_names[sindex]
        if sefer_name in note_seferim:
            for cindex, chapter in enumerate(sefer):
                for vindex, verse in enumerate(chapter):
                    for mindex, midrash in enumerate(verse):
                        for match in re.findall(ur'<i[^/]*?>',midrash):
                            data_order = re.findall(ur'data-order=\"\d*',match)[0].split(u'"')[1]
                            print sefer_name, cindex, "NOTE:", data_order
                            link = (
                                    {
                                    "refs": [
                                             'Notes and Corrections on Midrash Lekach Tov, {}, {}:{}'.format(sefer_name,cindex+1,data_order),
                                             'Midrash Lekach Tov on Torah, {}, {}:{}:{}'.format(sefer_name,cindex+1,vindex+1,mindex+1),
                                             ],
                                    "type": "commentary",
                                    'inline_reference': {
                                        'data-commentator': "Notes and Corrections on Midrash Lekach Tov",
                                        'data-order': data_order,
                                        },
                                    "auto": True,
                                    "generated_by": "sterling_mlt_linker"
                                    })
                            post_link(link, weak_network=True)
        else:
            parsha_count=-1
            for cindex, chapter in enumerate(sefer):
                for vindex, verse in enumerate(chapter):
                    for mindex, midrash in enumerate(verse):
                        for match in re.findall(ur'<i[^/]*?>',midrash):
                            data_order = re.findall(ur'data-order=\"\d*',match)[0].split(u'"')[1]
                            if int(data_order)==1:
                                parsha_count+=1
                            print sefer_name, eng_parshiot_dict[sefer_name][parsha_count], "NOTE:", data_order
                            
                            link = (
                                    {
                                    "refs": [
                                             'Beur HaRe\'em on Midrash Lekach Tov, {}, {}, {}'.format(sefer_name,eng_parshiot_dict[sefer_name][parsha_count],data_order),
                                             'Midrash Lekach Tov on Torah, {}, {}:{}:{}'.format(sefer_name,cindex+1,vindex+1,mindex+1),
                                             ],
                                    "type": "commentary",
                                    'inline_reference': {
                                        'data-commentator': "Beur HaRe\'em on Midrash Lekach Tov",
                                        'data-order': data_order,
                                        },
                                    "auto": True,
                                    "generated_by": "sterling_mlt_linker"
                                    })
                            post_link(link, weak_network=True)
def link_mlt_to_text():
    for sindex, sefer in enumerate(post_lekach_tov_text(False)):
        if sindex>1:
            for cindex, chapter in enumerate(sefer):
                if True:
                    for vindex, verse in enumerate(chapter):
                        print "LINKING {} {}:{}".format(en_sefer_names[sindex], cindex+1, vindex+1)
                        for mindex, midrash in enumerate(verse):
                            link = (
                                    {
                                    "refs": [
                                             'Midrash Lekach Tov on Torah, {}, {}:{}:{}'.format(en_sefer_names[sindex], cindex+1, vindex+1, mindex+1),
                                             '{} {}:{}'.format(en_sefer_names[sindex], cindex+1, vindex+1),
                                             ],
                                    "type": "commentary",
                                    "auto": True,
                                    "generated_by": "sterling_Midrash_Lekach_Tov_linker"
                                    })
                            post_link(link, weak_network=True)
def parse_new_notes():
    nac_files=['Genesis_notes_and_comments_edited - w greek.tsv','Exodus_notes_and_comments_edited - w greek.tsv']
    for index, _file in enumerate(nac_files):
        sefer = en_sefer_names[index]
        tc = TextChunk(Ref(sefer), "he")
        sefer_index = []
        for x in range(len(tc.text)):
            sefer_index.append([])
        with open('final_text_files/{}'.format(_file),'rb') as tsvin:
            tsvin = csv.reader(tsvin, delimiter='\t')
            for row in tsvin:
                current_chapter=int(row[0].split(':')[0])
                current_note=int(row[0].split(':')[1])
                while len(sefer_index[current_chapter-1])<current_note-1:                    
                    sefer_index[current_chapter-1].append([])
                if len(sefer_index[current_chapter-1])==current_note:
                    sefer_index[current_chapter-1][-1]=sefer_index[current_chapter-1][-1]+'\n'+row[1]
                else:
                    sefer_index[current_chapter-1].append(row[1])
        """
        for pindex, perek in enumerate(sefer_index):
            for cindex, comment in enumerate(perek):
                print sefer, pindex, cindex, comment
        """
        version = {
            'versionTitle': 'Midrash Lekach Tov on Torah, Vilna 1884',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001922206',
            'language': 'he',
            'text': sefer_index
        }
        post_text_weak_connection('Notes and Corrections on Midrash Lekach Tov, '+sefer, version)
                
                            
#post_lekach_tov_index()
#post_lekach_tov_text()
#parse_new_notes()
#link_nc()
link_mlt_to_text()    