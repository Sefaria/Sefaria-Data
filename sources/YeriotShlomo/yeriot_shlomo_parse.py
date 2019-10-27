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

en_sefer_names = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy"]

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

vechu=u'כו\''
def not_blank(s):
    while u" " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);

def get_parsha_ranges():
    return_dict={}
    for sefer in en_sefer_names:
        for node in library.get_index(sefer).alt_structs['Parasha']['nodes']:
            return_dict[node['sharedTitle']]=node['wholeRef']                
    return return_dict
    
def post_index_ys():
    # create index record
    record = SchemaNode()
    record.add_title('Yeriot Shlomo on Torah', 'en', primary =True, )
    record.add_title(u'יריעות שלמה על תורה', 'he',primary= True, )
    record.key = 'Yeriot Shlomo on Torah'
    
    #now for sefer nodes:
    for parsha in eng_parshiot:
        parsha_node = JaggedArrayNode()
        if Term().load({"name":parsha}):
            parsha_node.add_shared_term(parsha)
        else:
             print parsha
             0/0
        parsha_node.key = parsha
        parsha_node.depth = 1
        parsha_node.addressTypes = ['Integer']
        parsha_node.sectionNames = ['Comment']
        record.append(parsha_node)

    record.validate()

    index = {
        "title": 'Yeriot Shlomo on Torah',
        "categories": ["Tanakh","Commentary"],
        "schema": record.serialize()
    }
    post_index(index)
    
    
def parse_text():
    with open("יריעות שלמה.txt") as myFile:
        lines = list(map(lambda x: x.decode("utf-8",'replace'), myFile.readlines()))
    parsha_list=[]
    parsha_box=[]
    past_start=False
    just_passed_sefer=False
    for line in lines:
        if u'פרשת' in line:
            past_start=True
        if past_start:
            if u'@88' in line:
                if len(parsha_box)>0:
                    parsha_list.append(parsha_box)
                    parsha_box=[]
            elif not_blank(line):
                parsha_box.append(line)
    parsha_list.append(parsha_box)
    #"""
    for pindex, parsha in enumerate(parsha_list):
        for lindex, line in enumerate(parsha):
            print eng_parshiot[pindex], lindex, line
    #"""
    #0/0
    for pindex, parsha in enumerate(parsha_list):
        version = {
            'versionTitle': "Yeriot Shelomo, Prague 1609",
            'versionSource': 'http://primo.nli.org.il/primo-explore/fulldisplay?vid=NLI&docid=NNL_ALEPH001978635&context=L',
            'language': 'he',
            'text': parsha
        }
        #post_text("Ahavat Chesed, "+key, version, weak_network=True)
        #post_text("Toledot Yitzchak, {}".format(eng_parshiot[pindex]),  version,weak_network=True, skip_links=True, index_count="on")
        post_text_weak_connection("Yeriot Shlomo on Torah, {}".format(eng_parshiot[pindex]),  version)

def produce_link_sheets():
    parsha_ranges=get_parsha_ranges()
    for sefer_name in en_sefer_names:
        if "Deu" not in sefer_name:
            with open('Yeriot_Shlomo_{}_links.tsv'.format(sefer_name),'w') as record_file:
                for node in library.get_index(sefer_name).alt_structs['Parasha']['nodes']:
                    parsha_name=node['sharedTitle']
                    print "linking...",parsha_name
                    ys_text=TextChunk(Ref('Yeriot Shlomo on Torah, '+parsha_name),'he').text
                    print '{}, {}'.format(sefer_name, parsha_name)
                    print 'Mizrachi, {}, {}'.format(sefer_name, parsha_ranges[parsha_name].split(u' ')[1])
                    base_chunk = TextChunk(Ref('Mizrachi, {}, {}'.format(sefer_name, parsha_ranges[parsha_name].split(u' ')[1])),"he")
                    com_chunk = TextChunk(Ref('Yeriot Shlomo on Torah, {}'.format(parsha_name)),"he")
                    ch_links = match_ref(base_chunk,com_chunk,base_tokenizer,dh_extract_method=dh_extract_method,rashi_filter=_filter)
                    for link_index, (base, comment) in enumerate(zip(ch_links["matches"],ch_links["comment_refs"])):
                        if base:
                            print "B",base,"C", comment
                            if "Yeri" in base.normal():
                                ty=base.normal()
                                pasuk=comment.normal()
                            else:
                                ty=comment.normal()
                                pasuk=base.normal()
                            record_file.write('{}\t{}\t{}\n'.format(ty,TextChunk(Ref(ty),'he').text.replace(u'\n',u'').encode('utf','replace'), Ref(pasuk).normal()))
                            last_matched=base
                        else:
                            record_file.write('{}\t{}\tNULL\n'.format(comment.normal(),TextChunk(Ref(comment.normal()),'he').text.replace(u'\n',u'').encode('utf','replace')))
                
def _filter(some_string):
    return True
    return u'<b>' in some_string

def dh_extract_method(some_string):
    print "DH FINDING...",some_string
    if u'@11' in some_string and u'@22' in some_string:
        return re.search(ur'(?<=@11).*?(?=\.?\s*@22)', some_string).group().split(vechu)[0].replace(u'בד"ה',u'')
    return some_string

def base_tokenizer(some_string):
    print "THE STRING",some_string
    if u'<b>' in some_string:
        return filter(lambda(x): x!=u'',remove_extra_spaces(re.search(ur'(?<=<b>).*?(?=\.?\s*</b>)', some_string).group()).split(u' '))
    else:
        return some_string
def remove_extra_spaces(string):
    string = re.sub(ur"\. $",u".",string)
    while u"  " in string:
        string=string.replace(u"  ",u" ")
    return string             
#post_index_ys()
#parse_text()
produce_link_sheets()