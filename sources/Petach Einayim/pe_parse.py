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
import codecs
from fuzzywuzzy import fuzz

seders = {'Seder Zeraim':u'סדר זרעים','Seder Moed':u'סדר מועד','Seder Nashim':u'סדר נשים','Seder Nezikin':u'סדר נזיקין','Seder Kodashim':u'סדר קדשים','Seder Tahorot':u'סדר טהרות'}
vechu = u'וכו\''

mishnah_titles = {}
for tractate_title in library.get_indexes_in_category("Mishnah"):
    he_title = library.get_index(tractate_title).get_title("he")
    mishnah_titles[he_title]=tractate_title

talmud_titles = {}
for tractate_title in library.get_indexes_in_category("Talmud"):
    he_title = library.get_index(tractate_title).get_title("he")
    talmud_titles[he_title]=tractate_title
class Mishnah_Tractate:
    def __init__(self, he_title, tractate_dict):
        self.he_title = he_title
        self.en_title = mishnah_titles[he_title]
        self.text = tractate_dict['Text']
        self.version = tractate_dict['Version']
        
    def pe_post_index(self):   
        record = JaggedArrayNode()
        record.add_title('Petach Einayim on '+self.en_title, 'en', primary=True)
        record.add_title(u'פתח עינים על'+' '+self.he_title, 'he', primary=True)
        record.key = 'Petach Einayim on '+self.en_title
        record.depth = 3
        record.addressTypes = ["Integer", "Integer", "Integer"]
        record.sectionNames = ["Perek", "Mishnah", "Comment"]
        record.toc_zoom = 2
        record.validate()
        
        index = {
            "title":'Petach Einayim on '+self.en_title,
            "base_text_titles": [
              self.en_title
            ],
            "dependence": "Commentary",
            "collective_title":"Petach Einayim",
            "categories":["Mishnah","Commentary","Petach Einayim",get_mishnah_seder(self.en_title)],
            "schema": record.serialize()
        }
        post_index(index,weak_network=True)
    
    def pe_post_text(self):
        parsed_text = make_mishnah_perek_array(self.en_title)
        current_chapter = 0
        current_mishnah = 0
        for line in self.text:
            if u"@99" in line:
                current_mishnah = getGematria(re.match(ur"@99.*?"+ur"@11",line.replace(u"יו\"ד",u"י")).group().replace(u'משנה',u''))
            elif u"@11משנה" in line:
                current_mishnah = getGematria(re.match(ur"@11משנה.*?"+ur"@33",line.replace(u"יו\"ד",u"י")).group().replace(u'משנה',u''))
                #line = line.replace(re.match(ur"@11משנה.*?"+ur"@33",line),'')
                #current_chapter= getGematria(re.search(ur'\'\S*',line).groups()[0].replace(u"פרק",u""))
            if u"@22" in line:
                current_chapter= getGematria(line.replace(u"יו\"ד",u"י").replace(u"פרק",u""))
            elif u"@88" in line:
                current_chapter= getGematria(re.search(ur'פרק'+ur' \S*',line.replace(u"יו\"ד",u"י")).group().replace(u"פרק",u""))
            elif not_blank(line):
                parsed_text[current_chapter-1][current_mishnah-1].append(fix_mishnah_markers(line, self.version))
        """
        for pindex, perek in enumerate(parsed_text):
            for mindex, mishnah in enumerate(perek):
                for cindex, comment in enumerate(mishnah):
                    print self.en_title, pindex, mindex, cindex, comment
        """
        version = {
            'versionTitle': 'Petach Einayim, Jerusalem 1959',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001157028',
            'language': 'he',
            'text': parsed_text
        }
        post_text_weak_connection('Petach Einayim on '+self.en_title, version)
    def pe_post_links(self):
        pe_text = TextChunk(Ref('Petach Einayim on '+self.en_title),"he").text
        for perek_index,perek in enumerate(pe_text):
            for mishna_index, mishna in enumerate(perek):
                for comment_index, comment in enumerate(mishna):
                    link = (
                            {
                            "refs": [
                                     'Petach Einayim on {}, {}:{}:{}'.format(self.en_title, perek_index+1, mishna_index+1, comment_index+1),
                                     '{} {}:{}'.format(self.en_title,perek_index+1, mishna_index+1),
                                     ],
                            "type": "commentary",
                            "auto": True,
                            "generated_by": 'sterling_Petach_Einayim_{}_linker'.format(self.en_title.replace(u" ",u"_"))
                            })
                    print link.get('refs')
                    post_link(link, weak_network=True)
        
class Talmud_Tractate:
    def __init__(self, he_title, tractate_dict):
        self.he_title = he_title
        self.en_title = talmud_titles[he_title]
        self.text = tractate_dict['Text']
        self.version = tractate_dict['Version']
    def pe_post_index(self):
        en_title = self.en_title
        he_title = self.he_title
        record = JaggedArrayNode()
        record.add_title('Petach Einayim on '+en_title, 'en', primary=True)
        record.add_title(u'פתח עינים על'+u" "+he_title, 'he', primary=True)
        record.key = 'Petach Einayim on '+en_title
        record.depth = 2
        record.addressTypes = ['Talmud', 'Integer']
        record.sectionNames = ['Daf','Comment']
        record.validate()

        index = {
            "title":'Petach Einayim on '+en_title,
            "base_text_titles": [
               en_title
            ],
            "collective_title":"Petach Einayim",
            "dependence": "Commentary",
            "categories":["Talmud","Bavli","Commentary","Petach Einayim",get_mishnah_seder(self.en_title)],
            "schema": record.serialize()
        }
        post_index(index,weak_network=True)
    def pe_post_text(self):
        #dict contains daf and amud
        current_daf_ref = {}
        #subtract 2 since we start at 0, add one since range's range is non-inclusive
        final_list = [[] for x in range(len(TextChunk(Ref(self.en_title),"he").text))]
        current_daf = 0
        current_amud = ''
        amud_aleph_string = u"ע\"א"
        amud_bet_string = u"ע\"ב"
        for line in self.text:
            #print line, self.en_title
            if u"@22" not in line and u"@88" not in line:
                #print "past 147!"
                if u"@99" in line and u"@11" in line:
                    print 'past 149!'
                    ref_extract = re.match(ur"@99.*?@11",line).group()
                    if re.search(ur'דף .*?,',ref_extract):
                        current_daf=getGematria(re.search(ur'דף .*?,',ref_extract).group().replace(u'דף',u'').replace(u'יוד',u'י'))
                        current_amud='a'
                    if u", א]" in ref_extract:
                        current_amud='a'
                    if u", ב]" in ref_extract or amud_bet_string in line:
                        current_amud='b'
                if u"@99" in line and u"@11" not in line:
                    #print 'past 159!'
                    if u"ע\"ב" in line:
                        current_amud="b"
                    else:
                        current_amud='a'
                    if u"דף" in line:
                        if line.count(amud_aleph_string)==2: 
                            current_daf = 71
                        if line.count(amud_bet_string)==2: 
                            current_daf = 72
                        else:
                            current_daf = getGematria(line.replace(u"דף",u'').replace(u"ע\"א",u'').replace(u"ע\"ב",u''))
                            
                    #print "NEW INDEX:", current_daf, current_amud                    
                elif not_blank(line):
                    #print self.en_title
                    #print "RANGE: ", len(final_list)
                    #print "CURRENT DAF: ",current_daf
                    #print "CURRENT AMUD", current_amud
                    #print "THEY SAY", get_page(current_daf,current_amud)+2
                    if self.version == 'NEW' and u'@23' not in line and len(final_list[get_page(current_daf,current_amud)+1])>0:
                        final_list[get_page(current_daf,current_amud)+1][-1]+=u'<br>'+fix_talmud_markers(line, self.version).strip()
                    elif self.version==2:
                        #for version 2 (file 2), we combine not-dh lines with previous:
                        if u'@23' not in line and len(final_list[get_page(current_daf,current_amud)+1])>0:
                            final_list[get_page(current_daf,current_amud)+1][-1]+=u'<br>'+fix_talmud_markers(line, self.version).strip()
                        else:
                            final_list[get_page(current_daf,current_amud)+1].append(fix_talmud_markers(line, self.version).strip())
                    else:
                        final_list[get_page(current_daf,current_amud)+1].append(fix_talmud_markers(line, self.version).strip())
        #final_list.insert(0,[])
        
        for aindex, amud in enumerate(final_list):
            for cindex, comment in enumerate(amud):
                print self.en_title, len(final_list), aindex, cindex, comment
        
        version = {
            'versionTitle': 'Petach Einayim, Jerusalem 1959',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001157028',
            'language': 'he',
            'text': final_list
        }
        post_text_weak_connection('Petach Einayim on '+self.en_title, version)
    def link_tos(self):

        for amud_index in range(1,len(TextChunk(Ref(self.en_title)).text)-1):
            try:
                tos_chunk = TextChunk(Ref('Tosafot_on_'+self.en_title+"."+get_daf_en(amud_index)),"he")
                pe_chunk = TextChunk(Ref("Petach Einayim on "+self.en_title+"."+get_daf_en(amud_index)),"he")
            except:
                break
            """
            for line in tos_chunk.text:
                for comment in line:
                    print comment
            """
            """
            for comment in pe_chunk.text:
                if tos_filter(comment):
                    print re.split(ur'(\.|</b>|'+vechu+ur'|'+cosvu+ur')',re.sub(ur'^\s*\.',u'',comment))[0].replace(u'ד"ה ',u'').replace(u'תוס\' ',u'').replace(u'<b>',u'')
            """
            #"""
            matches = match_ref(tos_chunk,pe_chunk,
                tos_base_tokenizer,dh_extract_method=pe_tos_dh_extract,rashi_filter=tos_filter,verbose=True)
            if "comment_refs" in matches:
                for link_index, (base, comment) in enumerate(zip(matches["matches"],matches["comment_refs"])):
                    print "B",base,"C", comment
                    if base:
                        link = (
                                {
                                "refs": [
                                         base.normal(),
                                         comment.normal(),
                                         ],
                                "type": "commentary",
                                "auto": True,
                                "generated_by": "sterling_petach_einayim_"+self.en_title.replace(" ","_")+"_linker"
                                })
                        #post_link(link, weak_network=True)    
            #"""
    def pe_link(self):
        print "Linking "+self.en_title
        matched = 0.00
        total = 0.00
        last_not_matched=[]
        for amud_index in range(1,len(TextChunk(Ref(self.en_title)).text)-1):
            tractate_chunk = TextChunk(Ref(self.en_title+"."+get_daf_en(amud_index)),"he")
            last_matched = Ref(self.en_title+'.'+get_daf_en(amud_index)+'.1')
            if amud_index>0:
                try:
                    pe_chunk = TextChunk(Ref("Petach Einayim on "+self.en_title+"."+get_daf_en(amud_index)),"he")
                except:
                    continue
                if len(pe_chunk.text)<1:
                    continue
                matches = match_ref(tractate_chunk,pe_chunk,
                    base_tokenizer,dh_extract_method=dh_extract_method,rashi_filter=pe_filter,verbose=True)
                if "comment_refs" in matches:
                    for link_index, (base, comment) in enumerate(zip(matches["matches"],matches["comment_refs"])):
                        total+=1
                        print "B",base,"C", comment
                        if base:
                            link = (
                                    {
                                    "refs": [
                                             base.normal(),
                                             comment.normal(),
                                             ],
                                    "type": "commentary",
                                    "auto": True,
                                    "generated_by": "sterling_petach_einayim_"+self.en_title.replace(" ","_")+"_linker"
                                    })
                            post_link(link, weak_network=True)    
                            matched+=1
            
                            while len(last_not_matched)>0:
                                print "we had ", last_matched.normal()
                                print "we have ", base.normal()
                                print "so, we'll do ",last_matched.normal()+"-"+base.ending_ref().normal_last_section()
                                link = (
                                        {
                                        "refs": [
                                                 last_matched.normal()+"-"+base.ending_ref().normal_last_section(),
                                                 last_not_matched.pop().normal(),
                                                 ],
                                        "type": "commentary",
                                        "auto": True,
                                        "generated_by": "sterling_petach_einayim_"+self.en_title.replace(" ","_")+"_linker"
                                        })
                                post_link(link, weak_network=True)
                                matched+=1
                
                            last_matched=base
               
                        else:
                            last_not_matched.append(comment.starting_ref())
                            if link_index==len(matches["matches"])-1:
                                print "NO LINKS LEFT!"
                                start_ref = last_matched.normal().split('-')[0] if '-' in last_matched.normal() else last_matched.normal()
                                print "we had ", last_matched.normal()
                                print "so, we'll do ",start_ref+"-"+str(len(tractate_chunk.text))
                                while len(last_not_matched)>0:
                                    link = (
                                            {
                                            "refs": [
                                                     start_ref+"-"+str(len(tractate_chunk.text)),
                                                     last_not_matched.pop().normal(),
                                                     ],
                                            "type": "commentary",
                                            "auto": True,
                                            "generated_by": "sterling_petach_einayim_"+self.en_title.replace(" ","_")+"_linker"
                                            })
                                    post_link(link, weak_network=True)
                                    matched+=1                                   
                elif len(pe_chunk.text)>0:
                    link = (
                            {
                            "refs": [
                                     Ref(self.en_title+"."+get_daf_en(amud_index)).as_ranged_segment_ref().normal(),
                                     Ref("Petach Einayim on "+self.en_title+"."+get_daf_en(amud_index)).normal(),
                                     ],
                            "type": "commentary",
                            "auto": True,
                            "generated_by": "sterling_petach_einayim_"+self.en_title.replace(" ","_")+"_linker"
                            })
                    post_link(link, weak_network=True)

def get_tractate_texts():
    return_list = {"Mishnah":{},"Talmud":{}}
    for pe_file in os.listdir('files'):
        if ".txt" in pe_file:
            with open('files/'+pe_file) as myfile:
                lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
            tractate_box = []
            current_tractate=u"BLANK_ENTRY"
            parse_here = False
            for line in lines:
                if u"START" in line:
                    parse_here=True
                elif u"SKIP" in line:
                    parse_here=False
                elif parse_here:
                    if u"@00" in line:
                        if len(tractate_box)>0:
                            #sort by Mishna/Talmud
                            if current_tractate[5:] in talmud_titles.keys():
                                return_list["Talmud"][current_tractate[5:]]={}
                                return_list["Talmud"][current_tractate[5:]]["Text"]=tractate_box
                                return_list["Talmud"][current_tractate[5:]]["Version"]= 1 if '1' in pe_file else 2
                            elif u"BLANK" not in current_tractate:
                                return_list["Mishnah"][current_tractate]={}
                                return_list["Mishnah"][current_tractate]["Text"]=tractate_box
                                return_list["Mishnah"][current_tractate]["Version"]= 1 if '1' in pe_file else 2
                                
                        current_tractate=highest_fuzz(mishnah_titles.keys(), line)
                        tractate_box=[]
                    else:
                        tractate_box.append(line)
            if current_tractate[5:] in talmud_titles.keys():
                return_list["Talmud"][current_tractate[5:]]={}
                return_list["Talmud"][current_tractate[5:]]["Text"]=tractate_box
                return_list["Talmud"][current_tractate[5:]]["Version"]= 1 if '1' in pe_file else 2
            elif u"BLANK" not in current_tractate:
                return_list["Mishnah"][current_tractate]={}
                return_list["Mishnah"][current_tractate]["Text"]=tractate_box
                return_list["Mishnah"][current_tractate]["Version"]= 1 if '1' in pe_file else 2
    return return_list
#needed to redo this since the file got reparsed...
def get_tractate_texts_v2():
    return_list = {"Mishnah":{},"Talmud":{}}
    with open('files/Petach Enayim 1.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    tractate_box = []
    current_tractate=u"BLANK_ENTRY"
    parse_here = True
    for line in lines:
        if u"START" in line:
            parse_here=True
        elif u"SKIP" in line:
            parse_here=False
        elif parse_here:
            if u"@00" in line:
                if len(tractate_box)>0:
                    #sort by Mishna/Talmud
                    if current_tractate[5:] in talmud_titles.keys():
                        return_list["Talmud"][current_tractate[5:]]={}
                        return_list["Talmud"][current_tractate[5:]]["Text"]=tractate_box
                        return_list["Talmud"][current_tractate[5:]]["Version"]= 'NEW'
                    elif u"BLANK" not in current_tractate:
                        return_list["Mishnah"][current_tractate]={}
                        return_list["Mishnah"][current_tractate]["Text"]=tractate_box
                        return_list["Mishnah"][current_tractate]["Version"]= 'NEW'
                        
                current_tractate=highest_fuzz(mishnah_titles.keys(), line)
                tractate_box=[]
            else:
                tractate_box.append(line)
    if current_tractate[5:] in talmud_titles.keys():
        return_list["Talmud"][current_tractate[5:]]={}
        return_list["Talmud"][current_tractate[5:]]["Text"]=tractate_box
        return_list["Talmud"][current_tractate[5:]]["Version"]= 'NEW'
    elif u"BLANK" not in current_tractate:
        return_list["Mishnah"][current_tractate]={}
        return_list["Mishnah"][current_tractate]["Text"]=tractate_box
        return_list["Mishnah"][current_tractate]["Version"]= 'NEW'
    return return_list
def post_mishnah_categories():
    add_category('Petach Einayim', ["Mishnah","Commentary",'Petach Einayim'],u'פתח עינים')
    for seder in seders.keys():
        add_category(seder, ["Mishnah","Commentary",'Petach Einayim',seder], seders[seder])
def post_talmud_categories():
    print "Added PE"
    #def add_category(en_title, path, he_title=None, server=SEFARIA_SERVER):
    add_category('Petach Einayim', ["Talmud","Bavli","Commentary",'Petach Einayim'], u'פתח עינים')
    for seder in seders.keys():
        add_category(seder, ["Talmud","Bavli","Commentary",'Petach Einayim',seder], seders[seder])
        print "ADDED ",seder
def post_pe_term():
    term_obj = {
        "name": 'Petach Einayim',
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": 'Petach Einayim',
                "primary": True
            },
            {
                "lang": "he",
                "text": u'פתח עינים',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
def base_tokenizer(some_string):
    #print "STRING: ",some_string
    print 'some_string',some_string
    some_string = remove_extra_space(some_string)#.replace("<b>","").replace("</b>","").replace(":","")
    return filter(not_blank,some_string.split(" "))
def tos_base_tokenizer(some_string):
    if u'.' in some_string:
        some_string= some_string.split(u'.')[0].replace(u'כו\'',u'')
    elif u'-' in some_string:
        some_string= some_string.split(u'-')[0].replace(u'כו\'',u'')
    #else:
    #    print "NO PERIOD OR -:",some_string
    some_string = remove_extra_space(some_string)#.replace("<b>","").replace("</b>","").replace(":","")
    print "THIS WAS THE STRING:", filter(not_blank,some_string.split(" ")), some_string
    return filter(not_blank,some_string.split(" "))
def dh_extract_method(some_string):
    print some_string, 'this gets dh'
    return re.search(ur"(?<=<b>).*?(?=</b>)",some_string).group()
def pe_filter(some_string):
    #asssume every piece of text has a DH
    return re.match(ur"<b>.*</b>",some_string)
def tos_filter(some_string):
    return u'תוס' in re.match(ur"<b>.*?</b>",some_string).group()
def fix_mishnah_markers(s, version):
    if version==2:
        s=re.sub(ur"@99.*?"+ur"משנה"+ur".*?@11",u'',s)
        if u"@23" in s:
            s=u"<b>"+s.replace(u"@23",u"</b>")
    else:
        s=re.sub(ur"@11.*?"+ur"משנה"+ur".*?@33",u'',s)
        if vechu in s:
            if s.index(vechu)<30:
                s=u'<b>'+s.replace(vechu, vechu+u"</b>")
    s= re.sub(ur"@\d{1,3}",u"",s)
    
    """
    s= s.replace(u"@11",u"<b>").replace(u"@33",u"</b>").replace(u"@23",u"</b>")
    if u"</b>" in s and u"<b>" not in s:
        s = u"<b>"+s
    
    if re.match(ur".*?\.",s):
        splits["period_split"]= re.match(ur".*?\.",s).group()
    if re.match(ur".*?"+ur"כו"+ur"'", s):
        splits["chulai_split"]= re.match(ur".*?"+ur"כו"+ur"'", s).group()
    choice = ''
    for split in splits.keys():
        if len(choice)==0:
            choice = splits[split]
        elif len(splits[split])<choice:
            choice = splits[split]
    if len(choice)>0:
        print "TADA ",choice
        return u"<b>"+choice+u"</b>"+s[len(choice):]
    """
    return s
def fix_talmud_markers(s, version):
    #s= s.replace(u"@11",u"<b>").replace(u"@33",u"</b>")
    begin_bold=[u'@11',u'@66']
    end_bold=[u'@33',u'@23',u'@77']
    for mark in begin_bold:
        s=s.replace(mark, u'<b>')
    for mark in end_bold:
        s=s.replace(mark, u'</b>')
    """
    if u'.' not in s[:s.index(u'</b>')+1]:
        s=s.replace(u'</b>',u'.</b>')
    """
    return re.sub(ur"@\d{1,3}",u"",s)
    
    """
    splits={}
    if re.match(ur"@99\[.*?\]",s):
        s=s.replace(re.match(ur"@99\[.*?\]",s).group(),u'')
    choice = ''
    if version==2:
        if u"@23" in s:
            s = s.replace(u"@11",u"<b>").replace(u"@23",u"</b>")
        if u'<b>' not in s:
            s = u'<b>'+s[:s.index(u' ')]+u'</b>'+s[s.index(u' '):]
        return re.sub(ur"@\d{1,3}",u"",s)
    else: 
        if re.match(ur".*?\.",s):
            splits["period_split"]= re.match(ur".*?\.",s).group()
        if re.match(ur".*?"+ur"כו"+ur"'", s):
            splits["chulai_split"]= re.match(ur".*?"+ur"כו"+ur"'", s).group()
        for split in splits.keys():
            if len(choice)==0:
                choice = splits[split]
            elif len(splits[split])<choice:
                choice = splits[split]
        if len(choice.split(u' '))>15 and re.match(ur".*?@33",s):
            choice = re.match(ur".*?@33",s).group()
    if len(choice)>0:
        return re.sub(ur"@\d{1,3}",u"",u"<b>"+choice+u"</b>"+s[len(choice):])
    return re.sub(ur"@\d{1,3}",u"",s)

        
        
    
    chulai_split = s.split(u"וכו'")
    threethree_split = s.split(u"@33")
    
    return re.sub(ur"@\d{1,3}",u"",s)
    """
def pe_tos_dh_extract(s):
    vechu = u'וכו'
    cosvu = u'כתבו'
    return re.split(ur'(\.|</b>|'+vechu+ur'|'+cosvu+ur')',re.sub(ur'^\s*\.',u'',s))[0].replace(u'ד"ה ',u'').replace(u'תוס\' ',u'').replace(u'<b>',u'')
def highest_fuzz(input_list, input_item):
    highest_ratio = 0
    best_match = u''
    for item in input_list:
        if fuzz.ratio(input_item,item)>highest_ratio:
            best_match=item
            highest_ratio=fuzz.ratio(input_item,item)
    return best_match
def make_mishnah_perek_array(book):
    #hit a bug with Pesach, fixed since then
    tc = TextChunk(Ref(book), "he") if "Pesac" not in book else TextChunk(Ref(book), "en")
    return_array = []
    for x in range(len(tc.text)):
        return_array.append([])
    for index, perek in enumerate(return_array):
        tc = TextChunk(Ref(book+" "+str(index+1)), "he") if "Pesac" not in book else TextChunk(Ref(book+" "+str(index+1)), "en")
        for x in range(len(tc.text)):
            return_array[index].append([])
    return return_array
def make_talmud_array(book):
    tc = TextChunk(Ref(book), "he")
    return_array = []
    for x in range(len(tc.text)):
        return_array.append([])
    for index, perek in enumerate(return_array):
        tc2 = tc.text[index]
        for x in range(len(tc.text)):
            return_array[index].append([])
    return return_array
def get_mishnah_seder(mishnah_title):
    if u"Mishnah" not in mishnah_title:
        mishnah_title="Mishnah "+mishnah_title
    for seder in seders.keys():
        indices = library.get_indexes_in_category(seder)
        if mishnah_title in indices:
            return seder
    return None
def remove_extra_space(string):
    while u"  " in string:
        string = string.replace(u"  ",u" ")
    return string    
def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def get_daf_en(num):

    if num % 2 == 1:
        num = num / 2 + 2
        return str(num)+"a"

    else:
        num = num / 2 + 1
        return str(num)+"b"               
#tractate_texts=get_tractate_texts()
tractate_texts=get_tractate_texts_v2()
posting_term = False
if posting_term:
    post_pe_term()
"""
#for Mishna:
posting_categories = True
posting_indices = True
posting_texts = True
linking = True
admin_links = []
site_links = []
if posting_categories:
    post_mishnah_categories()
for key in tractate_texts["Mishnah"]:
    mishna_object = Mishnah_Tractate(key, tractate_texts["Mishnah"][key])
    admin_links.append(SEFARIA_SERVER+"/admin/reset/Petach_Einayim_on_"+mishna_object.en_title.replace(u" ",u"_"))
    site_links.append(SEFARIA_SERVER+"/Petach_Einayim_on_"+mishna_object.en_title.replace(u" ",u"_"))
    if posting_indices:
        print "posting "+key+" index..."
        mishna_object.pe_post_index()
    if posting_texts:
        print "posting "+key+" text..."
        mishna_object.pe_post_text()
    if linking:
        mishna_object.pe_post_links()

print "Admin Links:"
for link in admin_links:
    print link
print "Site Links:"
for link in site_links:
    print link
"""
#for Talmud
posting_categories = False
posting_indices = True
posting_texts = True
linking = True
linking_tos=False
if posting_categories:
    post_talmud_categories()
admin_links = []
site_links = []
results={}
did_one = False
past_last=False
for key in tractate_texts["Talmud"]:
    t_o = Talmud_Tractate(key, tractate_texts["Talmud"][key])
    if "Kidd" in t_o.en_title:
        past_last=True
    if past_last:#t_o.version==2 and not did_one:# and past_last:# and not did_one:
        admin_links.append(SEFARIA_SERVER+"/admin/reset/Petach_Einayim_on_"+t_o.en_title.replace(u" ",u"_"))
        site_links.append(SEFARIA_SERVER+"/Petach_Einayim_on_"+t_o.en_title.replace(u" ",u"_"))
        if posting_indices:
            t_o.pe_post_index()
        if posting_texts:
            t_o.pe_post_text()
        if linking:
            t_o.pe_link()
        if linking_tos:
            t_o.link_tos()
        #did_one=True
print "Admin Links:"
for link in admin_links:
    print link
print "Site Links:"
for link in site_links:
    print link
for key in results.keys():
    print key, results[key]
