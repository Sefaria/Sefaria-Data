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
import data_utilities
import codecs
import pycurl
import cStringIO
from bs4 import BeautifulSoup
import urllib2
from fuzzywuzzy import fuzz

aleph_to_nun=u'[א-נ]'

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
    
vayikra=u'ויקרא'

exceptions=[]
full_malbim_by_perek=make_perek_array('Leviticus')

#make a dictionary of terms for Sifra
sifra_term_dict = {}
for item in library.get_index('Sifra').schema.items()[0][1]:
     if 'titles' in item.keys():
         #print item['titles'][0]['text']
         #print item['titles'][1]['text']
         sifra_term_dict[item['titles'][1]['text']]=item['titles'][0]['text']
     else:
         #print item['sharedTitle']
        hebrew_title=u''
        for title in Term().load({"name":item['sharedTitle']}).titles:
            if 'primary' in title and title['lang']=='he':
                hebrew_title= title['text']
        sifra_term_dict[hebrew_title]=item['sharedTitle']
"""
for key in sifra_term_dict.keys():
    print key, sifra_term_dict[key]
"""
def remove_extra_spaces(string):
    string = re.sub(ur"\. $",u".",string)
    while u"  " in string:
        string=string.replace(u"  ",u" ")
    return string
def highest_fuzz(input_list, input_item):
    highest_ratio = 0
    best_match = u''
    for item in input_list:
        if fuzz.ratio(input_item,item)>highest_ratio:
            best_match=item
            highest_ratio=fuzz.ratio(input_item,item)
    return best_match
def post_malbim_index():
    # create index record
    record = JaggedArrayNode()
    record.add_title('Malbim on Leviticus', 'en', primary=True, )
    record.add_title(u'מלבי"ם על ויקרא"', 'he', primary=True, )
    record.key = 'Malbim on Leviticus'
    record.depth = 3
    record.toc_zoom =2
    record.addressTypes = ['Integer','Integer','Integer']
    record.sectionNames = ['Chapter','Verse','Comment']
    
    record.validate()

    index = {
        "title": "Malbim on Leviticus",
        "base_text_titles": [
          "Leviticus"
        ],
        "dependence": "Commentary",
        "collective_title": "Malbim",
        "categories": ['Tanakh','Commentary','Malbim','Torah'],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)

def make_malbim_files():
    all_simanim=[]
    link_list=[]
    soup = url_to_soup("https://he.wikisource.org/wiki/%D7%A7%D7%98%D7%92%D7%95%D7%A8%D7%99%D7%94:%D7%94%D7%AA%D7%95%D7%A8%D7%94_%D7%95%D7%94%D7%9E%D7%A6%D7%95%D7%94_%D7%A2%D7%9C_%D7%95%D7%99%D7%A7%D7%A8%D7%90")
    for link in soup.find_all('ul')[1]:
        if not_blank(link.string):
            #print link
            #print link.find('a')['href']
            url = 'https://he.wikisource.org'+link.find('a')['href']
            response = urllib2.urlopen(url)
            with open('files/'+link.find('a')['title']+'.html', 'w') as f:
                f.write(response.read())
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
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def remove_all_space(s):
    while u' ' in s:
        s=s.replace(u' ',u'')
    s=s.replace(u' .',u'.').replace(u' ,',u',')
    return s
def post_malbim_text(linking=False):
    page_list=[]
    global full_malbim_by_perek
    
    soup = url_to_soup("https://he.wikisource.org/wiki/%D7%A7%D7%98%D7%92%D7%95%D7%A8%D7%99%D7%94:%D7%94%D7%AA%D7%95%D7%A8%D7%94_%D7%95%D7%94%D7%9E%D7%A6%D7%95%D7%94_%D7%A2%D7%9C_%D7%95%D7%99%D7%A7%D7%A8%D7%90")
    #print soup
    for link in soup.find_all('ul')[1]:
        if not_blank(link.string):
            #print link
            #print link.find('a')['href']
            page_list.append(link.find('a')['title'])

    page_list = [u'התורה והמצוה ויקרא טו ג' if x==u'התורה והמצוה ויקרא ט:כב - י:ז' else x for x in page_list]
    page_list = sorted(page_list, key=lambda x: tuple([getGematria(x.split()[3]),getGematria(x.split()[4].split(u'-')[0])]))

    for page_name in page_list:
        print "PARSING PAGE:",page_name
        perek=getGematria(page_name.split()[3])
        pasuk = getGematria(page_name.split()[4].split(u'-')[0])# if u'-' not in ps else [getGematria(ps.split(u'-')[0]),getGematria(ps.split(u'-')[1])]

        soup = BeautifulSoup(open('files/'+page_name+'.html'), "html.parser")

        take_out_text=[]
        sifra_paragraph_link_list=[]
        link_box=[]
        siman_box=[]
        simanim=[]
        past_start=False

        for item in soup.find_all('div'):
            if item.has_attr('style'):
                if item['style']=='font-weight:bold':
                    for text in ''.join(item.find_all(text=True)).split(u'\n'):
                        take_out_text.append(text)

        for text in ''.join(soup.find_all(text=True)).split(u'\n'):
            #for typo...
            text = text.replace(u'o',u'ם')
            if re.search(ur'קטע[\s]+',text):
                if u'סימן' in text and len(text.split())<8:
                    text = text.split(u'קטע')[0]
                else:
                    continue
            if text not in take_out_text:
                if u'עריכה' in text:
                    past_start=True
                if past_start and not_blank(text):
                    if re.search(ur'[A-Za-z]{1}',text):
                        break
                    if re.search(ur'[\[ ]+עריכה[\]]+',text) and u'מאת המלבי"ם' not in text and len(siman_box)>0 and u'נר' not in text and u'קטע' not in text and u'ביאור משנה' not in text and u'באור משנה' not in text:
                        simanim.append(siman_box)
                        siman_box=[]
                        if len(link_box)>0:
                            sifra_paragraph_link_list.append(link_box)
                        elif len(sifra_paragraph_link_list)>0:
                            sifra_paragraph_link_list.append(sifra_paragraph_link_list[-1])
                        link_box=[]
                    siman_box.append(remove_extra_spaces(text))
            else:
                for match in re.findall(ur'\[[א-נ]{1,3}\]',text):
                    link_box.append(getGematria(match))
        if len(link_box)>0:
            sifra_paragraph_link_list.append(link_box)
        elif len(sifra_paragraph_link_list)>0:
            sifra_paragraph_link_list.append(sifra_paragraph_link_list[-1])       
        simanim.append(siman_box)

        final_text=[]
        siman_box=[]
        break_=False
        
        """
        for sindex, siman in enumerate(simanim):
            for pindex, paragraph in enumerate(siman):
                print sindex, pindex, paragraph
        """


        for sindex, siman in enumerate(simanim):
            if len(filter(lambda(x): not_blank(x), siman))>0:
                print page_name, sindex
                siman_letter=u'['+remove_all_space(siman.pop(0).replace(u'סימן',u'').replace(u'עריכה',u'').replace(u'[]',u''))+u']'
                if u'ספרא' not in siman[0]:
                    #this page doesn't fit template...
                    if u'התורה והמצוה ויקרא ה ד (המשך' in page_name:
                        siman.pop(0)
                        pasuk=4#,u'ה',u'יג']
                        perek=5
                        sifra_ref='Vayikra Dibbura d\'Chovah, Chapter 17'
                    else:
                        pasuk_ref=siman.pop(0)
                        print pasuk_ref
                        if u'וְאִם נֶפֶשׁ כִּי תֶחֱטָא וְעָשְׂתָה אַחַת מִכָּל מִצְו‍ֹת יְהוָה אֲשֶׁר לֹא תֵעָשֶׂינָה וְלֹא יָדַע וְאָשֵׁם וְנָשָׂא עֲו‍ֹנוֹ' in pasuk_ref:
                            pasuk=17
                            perek=5
                        elif vayikra in pasuk_ref:
                            pasuk=getGematria((pasuk_ref.split()[2].split(u'-')[0]))
                            perek=getGematria(pasuk_ref.split()[1])
                        sifra_ref=''
                        while u'ספרא' not in sifra_ref:
                            sifra_ref = siman.pop(0)
                        normal_sifra_ref= extract_sifra_ref(sifra_ref)
                        ##print siman_letter
                        print pasuk, perek
                
                else:
                    sifra_ref=''
                    while u'ספרא' not in sifra_ref:
                        sifra_ref = siman.pop(0)
                    normal_sifra_ref= extract_sifra_ref(sifra_ref)
                    #print siman_letter, page_name
                    #use pasuk ref from last time...
                #print perek, pasuk and len(siman)>0
                if perek and pasuk:
                    full_malbim_by_perek[perek-1][pasuk-1].append(u'<b>'+siman_letter+u'</b> '+siman.pop(0))
                    first_index = len(full_malbim_by_perek[perek-1][pasuk-1])
                    for comment in siman:
                        full_malbim_by_perek[perek-1][pasuk-1].append(comment)
                    last_index = len(full_malbim_by_perek[perek-1][pasuk-1])
                    if linking and u'התורה והמצוה ויקרא ה ד (המשך' not in page_name:#linking:
                        #for link_letter in sifra_paragraph_link_list.pop(0):
                        link = (
                                {
                                "refs": [
                                         'Sifra, {}, {}-{}'.format(normal_sifra_ref, sifra_paragraph_link_list[sindex][0], sifra_paragraph_link_list[sindex][-1]),
                                         'Malbim on Leviticus {}:{}:{}-{}'.format(perek, pasuk, first_index, last_index),
                                         ],
                                "type": "commentary",
                                "auto": True,
                                "generated_by": "sterling_Malbim_Sifra_linker"
                                })
                        post_link(link, weak_network=True)
                        link = (
                                {
                                "refs": [
                                         'Leviticus {}:{}'.format(perek, pasuk),
                                         'Malbim on Leviticus {}:{}:{}-{}'.format(perek, pasuk, first_index, last_index),
                                         ],
                                "type": "commentary",
                                "auto": True,
                                "generated_by": "sterling_Malbim_Vayikra_linker"
                                })
                        post_link(link, weak_network=True)
    """
    for pindex, perek in enumerate(full_malbim_by_perek):
        for paindex, pasuk in enumerate(perek):
            for cindex, comment in enumerate(pasuk):
                print pindex, paindex, cindex, comment
    """
    if not linking:
        version = {
            'versionTitle': 'VERSION',
            'versionSource': 'https://he.wikisource.org/wiki/%D7%A7%D7%98%D7%92%D7%95%D7%A8%D7%99%D7%94:%D7%94%D7%AA%D7%95%D7%A8%D7%94_%D7%95%D7%94%D7%9E%D7%A6%D7%95%D7%94_%D7%A2%D7%9C_%D7%95%D7%99%D7%A7%D7%A8%D7%90',
            'language': 'he',
            'text': full_malbim_by_perek
        }
        post_text_weak_connection("Malbim on Leviticus", version)
    #post_text("Malbim on Leviticus",  version,weak_network=True, skip_links=True, index_count="on")
    
        
def malbim_post_category():
    add_category("Torah", ["Tanakh","Commentary","Malbim","Torah"],u"תורה")
def extract_sifra_ref(s):
    addon=u''
    if u'פרק' in s:
        #print "AFTER",title[title.index(u'פרשת')+5:title.index(u'פרק')]
        if u'פרק'+u' ' in s:
            addon=', Chapter '+str(getGematria(re.findall(ur'(?<=פרק) \S+',s)[0]))
        else:
            addon=', Chapter '+str(getGematria(re.findall(ur'(?<=פרקים) \S+',s)[0]))
            
        s=s[s.index(u'פרשת')+5:s.index(u'פרק')]
    elif u'פרשה' in s:
        #print "AFTER",title[title.index(u'פרשת')+5:title.index(u'פרשה')]
        addon=', Section '+str(getGematria(re.findall(ur'(?<=פרשה) '+aleph_to_nun+'+',s)[0]))
        exceptions.append(s)
        s=s[s.index(u'פרשת')+5:s.index(u'פרשה')]
    else:
        #print "AFTERAFTER",title[title.index(u'פרשת')+5:]
        if u'ספרא (מלבי"ם) פרשת צו' in s:
            addon=', Mechilta d\'Miluim 1'
        elif u'ספרא (מלבי"ם) פרשת שמיני מכילתא' in s:
            addon= ', Mechilta d\'Miluim 2'
        else:
            addon='Notin'
        s= s[s.index(u'פרשת')+5:].replace(u'מכילתא דמלואים',u'')
    current_title=sifra_term_dict[highest_fuzz(sifra_term_dict.keys(),s)]+addon
    
    return current_title
#malbim_post_category()
#post_malbim_index()
#make_malbim_files()
#post_malbim_index()
#post_malbim_text()
post_malbim_text(True)