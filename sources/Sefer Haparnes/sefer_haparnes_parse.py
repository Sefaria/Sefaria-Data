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
import os

def parnes_index_post():
    record = JaggedArrayNode()
    record.add_title('Sefer HaParnas', 'en', primary=True, )
    record.add_title(u'ספר הפרנס', 'he', primary=True, )
    record.key = 'Sefer HaParnas'
    record.depth = 2
    record.addressTypes = ['Integer','Integer']
    record.sectionNames = ['Siman','Paragraph']    
    
    record.validate()

    index = {
        "title": 'Sefer HaParnas',
        "categories": ["Halakhah"],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def parnes_parse(posting=True):
    with open('ספר הפרנס מוכן.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    final_text = []
    for line in lines:
        if not_blank(line) and u'@22' not in line and u'@99' not in line and u"@00" not in line:
            final_text.append([parnes_clean(line)])
    """
    for siman in final_text:
        print siman
    """
    if posting:
        version = {
            'versionTitle': 'Sefer ha-Parnas, Vilna, 1891',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001225087',
            'language': 'he',
            'text': final_text
        }
        #post_text('Sheilat Shalom, Introduction', version,weak_network=True, skip_links=True, index_count="on")
        post_text_weak_connection('Sefer HaParnas', version)#,weak_network=True)#, skip_links=True,
    return final_text
def mool_index_post():
    record = JaggedArrayNode()
    record.add_title('Publisher\'s Haggahot on Sefer HaParnas', 'en', primary=True, )
    record.add_title(u'הגהות המו"ל על ספר הפרנס', 'he', primary=True, )
    record.key = 'Publisher\'s Haggahot on Sefer HaParnas'
    record.depth = 1
    record.addressTypes = ['Integer']
    record.sectionNames = ['Comment']    
    
    record.validate()

    index = {
        "title": 'Publisher\'s Haggahot on Sefer HaParnas',
        "categories": ["Halakhah","Commentary"],
        "base_text_titles": [
          'Sefer HaParnas'
        ],
        "dependence": "Commentary",
        "collective_title": "Publisher\'s Haggahot on Sefer HaParnas",
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def luria_index_post():
    record = JaggedArrayNode()
    record.add_title('Haggahot of R\' David Luria on Sefer HaParnas', 'en', primary=True, )
    record.add_title(u'הגהות הרד"ל על ספר הפרנס', 'he', primary=True, )
    record.key = 'Haggahot of R\' David Luria on Sefer HaParnas'
    record.depth = 2
    record.addressTypes = ['Integer','Integer']
    record.sectionNames = ['Siman','Comment']    
    
    record.validate()

    index = {
        "title": 'Haggahot of R\' David Luria on Sefer HaParnas',
        "categories": ["Halakhah","Commentary"],
        "base_text_titles": [
          'Sefer HaParnas'
        ],
        "dependence": "Commentary",
        "collective_title": "Haggahot of R\' David Luria on Sefer HaParnas",
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def mool_text_post():
    with open('ספר הפרנס הגהות המול מוכן.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    text = []
    for line in lines:
        if u"@00" not in line and u'@22' not in line and not_blank(line):
            text.append(comment_clean(line))
    """
    for line in text:
        print line
    """
    version = {
        'versionTitle': 'Sefer ha-Parnas, Vilna, 1891',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001225087',
        'language': 'he',
        'text': text
    }
    post_text_weak_connection('Publisher\'s Haggahot on Sefer HaParnas ', version)#,weak_network=True)#, skip_links=True, 
def luria_text_post():
    with open('ספר הפרנס הגהות רד לוריא מוכן.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    text = [[] for x in range(16)]
    
    current_siman = 0
    for line in lines:
        if u'@00הגהות וביאורים על ספר הפרנס מהגאון ר דוד לוריא ז"ל' not in line and not_blank(line) and u'@22' not in line:
            if u"@00" in line:
                current_siman = getGematria(line.replace(u'סימן',u''))
            else:
                print current_siman
                text[current_siman-1].append(comment_clean(line))
    """
    for sindex, siman in enumerate(text):
        for pindex, paragraph in enumerate(siman):
            print sindex, pindex, paragraph
    """
    version = {
        'versionTitle': 'Sefer ha-Parnas, Vilna, 1891',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001225087',
        'language': 'he',
        'text': text
    }
    post_text_weak_connection('Haggahot of R\' David Luria on Sefer HaParnas', version)#,weak_network=True)#, skip_links=True,
def link_comments():
    for siman, line in enumerate(parnes_parse()):
        for match in re.findall(ur'<.*?>',line[0]):
            if u'Publisher\'s Haggahot on Sefer HaParnas ' in match:
                print match
                data_order = re.search(ur'data-order=\"\d*',match).group().split(u'"')[1]
                link = (
                        {
                        "refs": [
                                 'Publisher\'s Haggahot on Sefer HaParnas , {}'.format(data_order),
                                 'Sefer HaParnas {}:1'.format(siman+1),
                                 ],
                        "type": "commentary",
                        'inline_reference': {
                            'data-commentator': "Publisher\'s Haggahot on Sefer HaParnas ",
                            'data-order': data_order,
                            },
                        "auto": True,
                        "generated_by": "sterling_Hagahot_HaMool_linker"
                        })
                post_link(link, weak_network=True)
            if u'Haggahot of R\' David Luria on Sefer HaParnas' in match:
                print match
                data_order = re.search(ur'data-order=\"\d*',match).group().split(u'"')[1]
                link = (
                        {
                        "refs": [
                                 'Haggahot of R\' David Luria on Sefer HaParnas, {}:{}'.format(siman+1,data_order),
                                 'Sefer HaParnas {}:1'.format(siman+1),
                                 ],
                        "type": "commentary",
                        'inline_reference': {
                            'data-commentator': "Haggahot of R\' David Luria on Sefer HaParnas",
                            'data-order': data_order,
                            },
                        "auto": True,
                        "generated_by": "sterling_Hagahot_Rav_Dovid_Luria_linker"
                        })
                post_link(link, weak_network=True)
def parnes_clean(s):
    s = s.replace(u'@11',u"<b>").replace(u'@33',u"</b>")
    for match in re.findall(ur'%.*?\)',s):
        s=s.replace(match,u"<i data-commentator=\"Publisher\'s Haggahot on Sefer HaParnas \" data-order=\""+str(getGematria(match))+"\"></i>")
    for match in re.findall(ur'#.*?\]',s):
        s=s.replace(match,u"<i data-commentator=\"Haggahot of R\' David Luria on Sefer HaParnas\" data-order=\""+str(getGematria(match))+"\"></i>")
    return s
def comment_clean(s):
    s = s.replace(u'@11',u"<b>").replace(u'@33',u"</b>")
    return s
def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def post_mool_term():
    term_obj = {
        "name": "Publisher\'s Haggahot on Sefer HaParnas ",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": 'Publisher\'s Haggahot on Sefer HaParnas',
                "primary": True
            },
            {
                "lang": "he",
                "text": u'הגהות המו"ל על ספר הפרנס',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
def post_luria_term():
    term_obj = {
        "name": 'Haggahot of R\' David Luria on Sefer HaParnas',
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": 'Haggahot of R\' David Luria on Sefer HaParnas',
                "primary": True
            },
            {
                "lang": "he",
                "text": u' הגהות הרד"ל על ספר הפרנס',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
#parnes_index_post()
parnes_parse()

#post_mool_term()
#mool_index_post()
#mool_text_post()

#post_luria_term()
#luria_index_post()
#luria_text_post()

link_comments()
#mool_text_post()
#luria_text_post()
# % is mool
# # is luria
#comment_file_dict={'Publisher\'s Haggahot on Sefer HaParnas ':{'file':'ספר הפרנס הגהות המול מוכן.txt','hebrew name':u'הגהות המו"ל על ספר הפרנס'},
#'Haggahot of R\' David Luria on Sefer HaParnas':'file':'ספר הפרנס הגהות רד לוריא מוכן.txt','hebrew name':u 'הגהות הרד"ל על ספר הפרנס'}