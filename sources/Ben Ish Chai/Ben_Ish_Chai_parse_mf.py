# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
#from sefaria.model import *
from sources.functions import *
import re
import data_utilities
import codecs
import pycurl
import cStringIO
from bs4 import BeautifulSoup
from data_utilities.dibur_hamatchil_matcher import match_text

eng_parshiot = ["Bereshit", "Noach", "Lech Lecha", "Vayera", "Chayei Sara", "Toldot", "Vayetzei", "Vayishlach",
"Vayeshev", "Miketz", "Vayigash", "Vayechi", "Shemot", "Vaera", "Bo", "Beshalach", "Yitro",
"Mishpatim", "Terumah", "Tetzaveh", "Ki Tisa", "Vayakhel", "Pekudei", "Vayikra", "Tzav", "Shmini",
"Tazria", "Metzora", "Achrei Mot", "Kedoshim", "Emor", "Behar", "Bechukotai", "Bamidbar", "Nasso",
"Beha'alotcha", "Sh'lach", "Korach", "Chukat", "Balak", "Pinchas", "Matot", "Masei",
"Devarim", "Vaetchanan", "Eikev", "Re'eh", "Shoftim", "Ki Teitzei", "Ki Tavo", "Nitzavim", "Vayeilech", "Ha'Azinu",
"V'Zot HaBerachah"]

eng_bereishit = ["Bereshit", "Noach", "Lech Lecha", "Vayera", "Chayei Sara", "Toldot", "Vayetzei", "Vayishlach","Vayeshev","Chanukah", "Miketz", "Vayigash", "Vayechi"]
eng_shemot = ["Shemot", "Vaera", "Bo", "Beshalach", "Yitro","Mishpatim", "Terumah", "Tetzaveh", "Ki Tisa", "Vayakhel", "Pekudei"]
eng_vayikra = ["Vayikra", "Tzav", "Shmini","Tazria Metzora","Achrei Mot Kedoshim", "Emor", "Behar Bechukotai",]
eng_bamidbar = ["Bamidbar", "Nasso","Beha'alotcha", "Sh'lach", "Korach", "Chukat", "Balak", "Pinchas", "Matot", "Masei"]
eng_devarim = ["Devarim", "Vaetchanan", "Eikev", "Re'eh", "Shoftim", "Ki Teitzei", "Ki Tavo", "Nitzavim", "Vayeilech", "Ha'Azinu",
"V'Zot HaBerachah"]
all_parshas = [eng_bereishit,eng_shemot,eng_vayikra,eng_bamidbar,eng_devarim]
eng_bereishit2 = ["Bereshit", "Noach", "Lech Lecha", "Vayera", "Chayei Sara", "Toldot", "Vayetzei", "Vayishlach", "Miketz", "Vayigash", "Vayechi"]
eng_shemot2 = ["Shemot", "Vaera", "Bo", "Beshalach", "Yitro","Mishpatim", "Terumah", "Tetzaveh", "Ki Tisa", "Vayakhel", "Pekudei"]
eng_vayikra2 = ["Vayikra", "Tzav", "Shmini","Tazria", "Metzora", "Achrei Mot", "Kedoshim", "Emor", "Behar Bechukotai"]
eng_bamidbar2 = ["Nasso","Beha'alotcha", "Sh'lach", "Korach", "Chukat", "Balak", "Pinchas", "Matot", "Masei"]
eng_devarim2 = ["Vaetchanan", "Eikev", "Re'eh", "Shoftim", "Ki Teitzei", "Ki Tavo"]
all_parshas2 = [eng_bereishit2,eng_shemot2,eng_vayikra2,eng_bamidbar2,eng_devarim2]

eng_parshas=[ all_parshas, all_parshas2]
def get_parsed_drasha():
    parsha_titles = get_intro_parshas()
    return_list = []
    for index, parsha in enumerate(get_drasha_text()):
        return_list.append([[parsha_titles[index].replace("\n","").strip(),eng_parshiot[index]],parsha])
    return return_list
def get_drasha_text():
    with open('בן איש חי דרשות.txt') as myfile:
        ascii_lines = myfile.readlines()
    lines = list(map(lambda(x): x.decode('utf_8','replace'),ascii_lines))
    parsha_box = []
    all_parshas = []
    for line in lines:
        if "@02" in line:
            all_parshas.append(parsha_box)
            parsha_box = []
        parsha_box.append(re.sub(ur"@\d+",u"",line).replace(u"T",""))
    all_parshas.append(parsha_box)
    return all_parshas[2:]
def _filter(some_string):
    if re.search(ur'<b>(.*?)</b>', some_string) is None:
        return False
    else:
        return True

def _dh_extract_method(some_string):
    if re.search(ur'כו '+ur"[\. \']", some_string):
        return re.search(ur'כו '+ur"[\. \']", some_string).group()
    else:
        return u' '.join(some_string.split(" ")[:4])
def base_tokenizer(some_string):
    return some_string.split()
def post_drasha_links(drasha_text):
    total =0.0
    matched = 0.0
    for parsha in drasha_text:
        base_text = TextChunk(Ref(parsha[0][1]),"he").text
        for perek_index, perek in enumerate(base_text):
            bih_matches = match_text(perek,parsha[1],dh_extract_method=_dh_extract_method)
            for match_pair in bih_matches["matches"]:
                print match_pair
                """
                print link.get('refs')
                if base:
                    link = (
                            {
                            "refs": [
                                     base.normal(),
                                     comment.normal(),
                                     ],
                            "type": "commentary",
                            "auto": True,
                            "generated_by": "sterling_avi_ezer_ibn_ezra_linker"
                            })
                    #post_link(link, weak_network=True)    
                    matched+=1
                else:
                    print "NOBASE"
                total+=1
                """
    print "Ratio: "+str(matched/total)
def get_halachas_shana_1():
    return get_parsed_halachas(1)
def get_halachas_shana_2():
    return get_parsed_halachas(2)
def get_parsed_halachas(shana_num):
    soup = url_to_soup("https://he.wikisource.org/wiki/%D7%91%D7%9F_%D7%90%D7%99%D7%A9_%D7%97%D7%99")
    links = soup.find_all('ul')
    #links = filter(lambda(x):x('li'),links)
    #for index, li in enumerate(links[1:3]):
    sefer_links = []
    for a in links[shana_num].find_all('a'):
        sefer_links.append('https://he.wikisource.org'+a['href'])
    complete_year = []
    for sefer_index, sefer_link in enumerate(sefer_links):
        #sefer_parshas contains each parsha, and each parsha contains 1 title, 1 intro and 1 2D list of sections
        parsha_count = -1
        sefer_soup=url_to_soup(sefer_link)
        for index, li in enumerate(sefer_soup.find_all('li')):
            try:
                if u"פרשת" in ''.join(li.find_all(text=True)) or u"פרשיות" in ''.join(li.find_all(text=True)) or u"חנוכה" in ''.join(li.find_all(text=True)):
                    parsha_box = []
                    parsha_soup = url_to_soup('https://he.wikisource.org'+li.find('a')['href'])
                    parsha_count+=1
                    parsha_box.append([''.join(li.find_all(text=True)),eng_parshas[shana_num-1][sefer_index][parsha_count] ])
                    if shana_num == 2:
                        print parsha_box[0][0],parsha_box[0][1],parsha_count
                    intro_box = []
                    first_headline_box =[]
                    for headline in parsha_soup.find_all(class_="mw-headline"):
                        if ''.join(headline.find_all(text=True)).strip()==u"פתיחה":
                            first_headline_box.append(headline)
                    first_headline = first_headline_box[0]
                    text_start_index = 0
                    start_index =  parsha_soup(True).index(first_headline)
                    for item in parsha_soup(True)[start_index:]:
                        if not item.has_attr('class') and not item.has_attr('href') and not item.has_attr('size') and item.name!="b":
                            if ''.join(item.find_all(text=True)).strip()==ur"הלכות[עריכה]":
                                text_start_index = parsha_soup(True).index(item)
                                break
                            intro_box.append(''.join(item.find_all(text=True)).strip())
                    parsha_box.append(intro_box)
                    #load in text of halachot
                    section_box = []
                    halacha_box = []
                    for item in parsha_soup(True)[text_start_index:]:
                        if item.name == "p":
                            section_box.append(''.join(item.find_all(text=True)).strip())
                        else:
                            if len(section_box)>0:
                                halacha_box.append(section_box)
                                section_box=[]
                    parsha_box.append(halacha_box)
                    complete_year.append(parsha_box)
            except:
                q=0
    return complete_year
    
    
def get_parsed_intro():
    with open('בן איש חי דרשות.txt') as myfile:
        ascii_lines = myfile.readlines()
    lines = list(map(lambda(x): x.decode('utf_8','replace'),ascii_lines))
    section_box = []
    for line in lines:
        section_box.append(re.sub(ur"@\d+",u"",line).replace(u"T",""))
        if "@00" in line:
            section_box = []
        if u"@01ספר בראשית" in line:
            break
    return section_box
def get_intro_parshas():
    with open('בן איש חי דרשות.txt') as myfile:
        ascii_lines = myfile.readlines()
    lines = list(map(lambda(x): x.decode('utf_8','replace'),ascii_lines))
    parshas = []
    for line in lines:
        if u"@02" in line:
            parshas.append(re.sub(ur"@\d+",u"",line).replace(u"T",""))
    return parshas[1:]
def url_to_soup(url):
    chapter_buf = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    
    c.setopt(c.WRITEFUNCTION, chapter_buf.write)
    c.perform()
    soup = BeautifulSoup(chapter_buf.getvalue(), 'html.parser')
    return soup;
def not_blank(s):
    while " " in s:
        s = s.replace(" ","")
    return (len(s.replace("\n","").replace("\r","").replace("\t",""))!=0);
def print_text():
    with open('בן איש חי דרשות.txt') as myfile:
        ascii_lines = myfile.readlines()
    lines = list(map(lambda(x): x.decode('utf_8','replace'),ascii_lines))
    for line in lines:
        print line
def main():
    pass
if __name__ == "__main__":
    """
    #post intro:
    version = {
        'versionTitle': 'Ben Ish Chai; Jerusalem, 1898',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001933796',
        'language': 'he',
        'text': get_parsed_intro()
    }
    post_text_weak_connection('Ben Ish Hai, Introduction', version)
    #post all text
    
    parsha_sections = ["Drashot","Halachot 1st Year","Halachot 2nd Year"]
    parsha_content = [get_parsed_drasha(), get_halachas_shana_1(), get_halachas_shana_2()]
    primo_link = 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001933796'
    wiki_link = 'https://he.wikisource.org/wiki/%D7%91%D7%9F_%D7%90%D7%99%D7%A9_%D7%97%D7%99'
    section_index_info = [['Ben Ish Hai -- Wikisource',wiki_link],['Ben Ish Chai; Jerusalem, 1898',primo_link],['Ben Ish Chai; Jerusalem, 1898',primo_link]]
    
    for section_name, section_content, section_version in zip(parsha_sections,parsha_content,section_index_info):
        for parsha in section_content:
            #add intro if not drashot:
            if "Drashot" not in section_name:
                version = {
                    'versionTitle': section_version[0],
                    'versionSource': section_version[1],
                    'language': 'he',
                    'text': parsha[1] 
                }
                print "posting "+section_name+", "+parsha[0][1]+", Introduction"
                post_text_weak_connection('Ben Ish Hai, '+section_name+", "+parsha[0][1]+", Introduction", version)
    
                version = {
                    'versionTitle': section_version[0],
                    'versionSource': section_version[1],
                    'language': 'he',
                    'text': parsha[1] if "Drashot" in section_name else parsha[2]
                }
                print "posting "+section_name+", "+parsha[0][1]
                post_text_weak_connection('Ben Ish Hai, '+section_name+", "+parsha[0][1], version)
    """
    post_drasha_links(get_parsed_drasha())
    """
    
    #print parsha titles
    """
    """ 
    print "Drasha"
    for paindex, parsha in enumerate(get_parsed_drasha()):
        print parsha[0][0]
        print parsha[0][1]
    
    print "Shana 1"
    for paindex, parsha in enumerate(get_halachas_shana_1()):
        print parsha[0][0]
        print parsha[0][1]
    
    print "Shana 2"
    for paindex, parsha in enumerate(get_halachas_shana_2()):
        print parsha[0][0]
        print parsha[0][1]
        print parsha[2][0]
        #for parsha in sefer:
           # print "TITLE: "+parsha[0][0]+" "+parsha[0][1]
       
    
        print "INTRO:"
        for p in parsha[1]:
            print p
        print "HALACHOT:"
        for sindex, sec in enumerate(parsha[2]):
            for pindex, pa in enumerate(sec):
                print str(sindex)+" "+str(pindex)+" "+pa
    """
    """
    for section in get_parsed_drashas():
        print "SECTION:"
        for line in section:
            print line
    """
    """
    text = get_halachas_shana_2()
    for parsha in text:
        print "Parsha:"
        print parsha[0][0],parsha[0][1]
        print "Intro:"
        for index, p in enumerate(parsha[1]):
            print str(index),p
        print "body:"
        for index2, p2 in enumerate(parsha[2]):
            print index2, p2
        
    main()
    """