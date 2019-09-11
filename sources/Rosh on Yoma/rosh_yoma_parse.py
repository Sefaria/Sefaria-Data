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
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from data_utilities.dibur_hamatchil_matcher import *

daf_to_halacha_dict={}
heb_letters=[u'א',u'ב',u'ג',u'ד',u'ה',u'ו',u'ז',u'ח',u'ט',u'י',u'כ',u'ל',u'מ',u'נ',u'ס',u'ע',u'פ',u'צ',u'ק',u'ר',u'ש',u'ת']
def make_tractate_index():
    record = JaggedArrayNode()
    record.add_title('Rosh on Yoma', 'en', primary=True)
    record.add_title(u'פסקי הראש על יומא', 'he', primary=True)
    record.key = 'Rosh on Yoma'
    
    #now we add subject node to Shmatta
    avodah_node = JaggedArrayNode()
    avodah_node.add_title("Avodat Yom HaKippurim", 'en', primary=True)
    avodah_node.add_title(u'הלכות סדר עבודת יום הכפורים', 'he', primary=True)
    avodah_node.key = 'Avodat Yom HaKippurim'
    avodah_node.depth = 1
    avodah_node.addressTypes = ['Integer']
    avodah_node.sectionNames = ['Paragraph']
    record.append(avodah_node)

    #now we add text node
    text_node = JaggedArrayNode()
    text_node.key = "default"
    text_node.default = True
    text_node.depth = 3
    text_node.addressTypes = ['Integer', 'Integer', 'Integer']
    text_node.sectionNames = ['Chapter', 'Halacha', 'Paragraph']
    record.append(text_node)
    


    index = {
        "title":'Rosh on Yoma',
        "base_text_titles": [
           "Yoma"
        ],
        "collective_title":"Rosh",
        "dependence": "Commentary",
        "categories":["Talmud","Bavli","Commentary","Rosh", "Seder Moed"],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def post_rosh_text():
    in_avodah=True
    siman_box=[]
    avodah_box=[]
    shmini_box = []
    link_table=[]
    current_daf = 0
    current_amud='a'
    with open("ראש יומא.txt") as myFile:
        lines = list(map(lambda x: x.decode("utf-8",'replace'), myFile.readlines()))
    for line in lines:
        if u'פרק שמיני' in line:
            in_avodah=False
        elif in_avodah and u"@99" not in line:
            avodah_box.append([avodah_clean(line)])
        elif not in_avodah:
            if re.search(ur'\[דף.*?\]',line):
                match=re.search(ur'\[דף.*?\]',line).group()
                """
                if line.index(match)>20:
                    daf_to_halacha_dict[str(current_daf)+current_amud].append(len(shmini_box))
                """
                current_amud='a' if u'ע\"א' in line else 'b'
                current_daf = getGematria(match.replace(u'דף',u'').replace(u'ע\"א',u'').replace(u'ע\"ב',u''))
                print str(current_daf)+current_amud, match
                link_table.append([len(shmini_box)+1, current_daf, current_amud])
            if re.findall(ur'@22\S',line) and len(siman_box)>0:
                shmini_box.append(siman_box)
                siman_box=[]
            siman_box.append(shmini_clean(line))
    shmini_box.append(siman_box)

    halacha_simanim=[[] for x in range(7)]
    halacha_simanim.append(fix_rosh_perek(shmini_box))
    avodah_box=fix_rosh_perek(avodah_box)
    avodah_final=[]
    for p in avodah_box:
        avodah_final.append(p[0])
    """
    for sindex, siman in enumerate(avodah_box):
        for pindex, paragraph in enumerate(siman):
            print "ROSH", sindex, pindex, paragraph
    """
    """
    for sindex, siman in enumerate(halacha_simanim[-1]):
        for pindex, paragraph in enumerate(siman):
            print "ROSH", sindex, pindex, paragraph
    0/0
    """
    
    if False:
        version = {
            'versionTitle': 'Vilna Edition',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957',
            'language': 'he',
            'text': avodah_final
        }
        post_text_weak_connection('Rosh on Yoma, Avodat Yom HaKippurim', version)
        #post_text('Rosh on Yoma, Avodat Yom HaKippurim', version)
        version = {
            'versionTitle': 'Vilna Edition',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957',
            'language': 'he',
            'text': halacha_simanim
        }
        post_text_weak_connection('Rosh on Yoma', version)
        #post_text('Rosh on Yoma', version)    
    if True:
        for link in link_table:
            print link
            link_post = (
                    {
                    "refs": [
                             'Rosh on Yoma, 8:{}'.format(link[0]),
                             'Yoma {}{}'.format(link[1], link[2]),
                             ],
                    "type": "commentary",
                    "auto": True,
                    "generated_by": "sterling_Rosh_Yoma_linker"
                    })
            #post_link(link_post, weak_network=True)
    if True:
        link_perek_netanels(halacha_simanim[-1],'default')
        link_perek_netanels(avodah_box,'')
def link_perek_netanels(perek_text, section):
    for sindex, siman in enumerate(perek_text):
        for pindex, paragraph in enumerate(siman):
            for match in re.findall(ur'<i.*?>',paragraph):
                dataOrder= re.search(ur'(?<=data-order=\")\d+',match).group()
                dataLabel= re.search(ur'(?<=data-label=\")[^\"]+',match).group()
                print 'Korban Netanel on Yoma, 8.{}.{}'.format(sindex+1,dataOrder)
                print 'Rosh on Yoma 8:{}:{}'.format(sindex+1, pindex+1),
                if 'default' in section:
                    link = (
                            {
                            "refs": [
                                     'Korban Netanel on Yoma, 8.{}.{}'.format(sindex+1,dataOrder),
                                     'Rosh on Yoma 8:{}:{}'.format(sindex+1, pindex+1),
                                     ],
                            "type": "commentary",
                            'inline_reference': {
                                'data-commentator': "Korban Netanel",
                                'data-order': dataOrder,
                                'data-label': dataLabel
                                },
                            "auto": True,
                            "generated_by": "sterling_karbon_netanel_linker"
                            })
                else:
                    link = (
                            {
                            "refs": [
                                     'Korban Netanel on Yoma, Avodat Yom HaKippurim, {}.{}'.format(sindex+1,dataOrder),
                                     'Rosh on Yoma, Avodat Yom HaKippurim, {}'.format(sindex+1),
                                     ],
                            "type": "commentary",
                            'inline_reference': {
                                'data-commentator': "Korban Netanel",
                                'data-order': dataOrder,
                                'data-label': dataLabel
                                },
                            "auto": True,
                            "generated_by": "sterling_karbon_netanel_linker"
                            })
                post_link(link, weak_network=True)
    
        
def avodah_clean(s):
    s =re.sub(ur'\[?#\]?',u'',s)
    return re.sub(ur"@\d{1,4}",u"",s)
def shmini_clean(s):
    s =re.sub(ur'\[?#\]?',u'',s)
    s = re.sub(ur'@22\S*',u'',s)
    return re.sub(ur"@\d{1,4}",u"",s)
def kn_index_post():
    record = JaggedArrayNode()
    record.add_title('Korban Netanel on Yoma', 'en', primary=True)
    record.add_title(u'קרבן נתנאל על יומא', 'he', primary=True)
    record.key = 'Korban Netanel on Yoma'
    
    #now we add subject node to Shmatta
    avodah_node = JaggedArrayNode()
    avodah_node.add_title("Avodat Yom HaKippurim", 'en', primary=True)
    avodah_node.add_title(u'הלכות סדר עבודת יום הכפורים', 'he', primary=True)
    avodah_node.key = 'Avodat Yom HaKippurim'
    avodah_node.depth = 2
    avodah_node.addressTypes = ['Integer','Integer']
    avodah_node.sectionNames = ['Paragraph','Comment']
    record.append(avodah_node)

    #now we add text node
    text_node = JaggedArrayNode()
    text_node.key = "default"
    text_node.default = True
    text_node.depth = 3
    text_node.addressTypes = ['Integer', 'Integer', 'Integer']
    text_node.sectionNames = ['Chapter', 'Halacha', 'Comment']
    record.append(text_node)
    


    index = {
        "title":'Korban Netanel on Yoma',
        "base_text_titles": [
           "Rosh on Yoma"
        ],
        "collective_title":"Korban Netanel",
        "dependence": "Commentary",
        "categories":["Talmud","Bavli","Commentary","Korban Netanel", "Seder Moed"],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def kn_parse():
    prakim=[[] for x in range(7)]
    shmini_final=[]
    avoda_final=[]
    with open("קרבן נתנאל יומא עם אותיות מוכן(1).txt") as myFile:
        lines = list(map(lambda x: x.decode("utf-8",'replace'), myFile.readlines()))
    kn_box=[]
    for line in lines:
        if u'$' in line:
            avoda_box=kn_box
            kn_box=[]
        elif u'[' in line:
            kn_box.append(clean_kn(line))
    siman_counts=get_kn_count_per_siman()
    so_far=0
    for perek_count in siman_counts[0]:
        avoda_final.append([avoda_box[so_far:so_far+perek_count]][0])
        so_far+=perek_count
    """
    for sindex, siman in enumerate(avoda_final):
        for cindex, comment in enumerate(siman):
            print sindex, cindex, comment
    """
    so_far=0
    for perek_count in siman_counts[1]:
        shmini_final.append([kn_box[so_far:so_far+perek_count]][0])
        so_far+=perek_count  
    """
    for sindex, siman in enumerate(shmini_final):
        for cindex, comment in enumerate(siman):
            print sindex, cindex, comment
    #"""
    #1/0
    prakim.append(shmini_final)
    version = {
        'versionTitle': 'Vilna Edition',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957',
        'language': 'he',
        'text': avoda_final
    }
    #post_text('Korban Netanel on Yoma, Avodat Yom HaKippurim', version)
    post_text_weak_connection('Korban Netanel on Yoma, Avodat Yom HaKippurim', version)
    version = {
        'versionTitle': 'Vilna Edition',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957',
        'language': 'he',
        'text': prakim
    }
    #post_text('Korban Netanel on Yoma', version)
    post_text_weak_connection('Korban Netanel on Yoma', version)
def post_ts_index():
    record = JaggedArrayNode()
    record.add_title("Tiferet Shmuel on Yoma", 'en', primary=True)
    record.add_title(u"תפארת שמואל על יומא", 'he', primary=True)
    record.key = "Tiferet Shmuel on Yoma"
    record.depth = 1
    record.addressTypes = ['Integer']
    record.sectionNames = ['Comment']
    record.validate()
    
    index = {
        "title": "Tiferet Shmuel on Yoma",
        "base_text_titles": [
           "Rosh on Yoma"
        ],
        "collective_title":"Tiferet Shmuel",
        "dependence": "Commentary",
        "categories":["Talmud","Bavli","Commentary","Tiferet Shmuel", "Seder Moed"],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def get_kn_count_per_siman():
    return_list=[]
    count_box=[]
    siman_count=0
    with open("ראש יומא.txt") as myFile:
        lines = list(map(lambda x: x.decode("utf-8",'replace'), myFile.readlines()))
    for line in lines:
        if u"@99" in line and len(count_box)>0:
            #count_box.append(siman_count)
            return_list.append(count_box)
            count_box=[]
            siman_count=0
        elif (len(return_list)<1 and not (siman_count==0 and len(count_box)<1)) or (re.search(ur'@22\S',line) and not (siman_count==0 and len(count_box)<1)):
            count_box.append(siman_count)
            siman_count=0
        siman_count+=line.count('[*]')
    count_box.append(siman_count)
    return_list.append(count_box)
    #"""
    for pindex, perek in enumerate(return_list):
        for nindex, number in enumerate(perek):
            print pindex, nindex, number
    #"""
    return return_list   
def clean_kn(s):
    s = re.sub(ur'\[.*@11',u'<b>',s)
    if '.' in s:
        s=s.replace(u'.',u'.</b>')
        s=re.sub(ur'@22',u'',s)
    else:
        s = re.sub(ur'@22',u'</b>',s)
    return s
def fix_rosh_perek(perek):
    return_perek=[]
    siman_box=[]
    letter_num=0
    for siman in perek:
        siman_box=[]
        siman_num=1
        for paragraph in siman:
            temp=paragraph
            #print paragraph
            for match in re.findall(ur'\[\*\]', temp):
                temp=temp.replace(match,u"""<i data-commentator="Korban Netanel" data-label="{}" data-order="{}"></i>""".format(heb_letters[letter_num], siman_num),1)
                letter_num+=1
                if letter_num==22:
                    letter_num=0
                siman_num+=1
            siman_box.append(temp)
        return_perek.append(siman_box)
    return return_perek
        
#make_tractate_index()
post_rosh_text()
#kn_index_post()            
#kn_parse()
#post_ts_index()
#get_kn_count_per_siman()