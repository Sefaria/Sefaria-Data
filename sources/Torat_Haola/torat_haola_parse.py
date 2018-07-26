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
import pycurl
import cStringIO
from bs4 import BeautifulSoup
import urllib2
from fuzzywuzzy import fuzz
from num2words import num2words
start_cues=[u'תנן במסכת',u'כבר נתבאר',u'כבר נתבאר']
skip_these=[u'תוכן עניינים']
has_intro=[2,3]
def remove_extra_space(s):
    while u'  ' in s:
        s=s.replace(u'  ',u' ')
    s=s.replace(u' .',u'.').replace(u' ,',u',')
    return s
def make_files():
    chalakim=False
    if chalakim:
        chalek_links=['https://he.wikisource.org/wiki/%D7%AA%D7%95%D7%A8%D7%AA_%D7%94%D7%A2%D7%95%D7%9C%D7%94/%D7%97%D7%9C%D7%A7_%D7%90_(%D7%94%D7%9B%D7%9C)','https://he.wikisource.org/wiki/%D7%AA%D7%95%D7%A8%D7%AA_%D7%94%D7%A2%D7%95%D7%9C%D7%94/%D7%97%D7%9C%D7%A7_%D7%91_(%D7%94%D7%9B%D7%9C)','https://he.wikisource.org/wiki/%D7%AA%D7%95%D7%A8%D7%AA_%D7%94%D7%A2%D7%95%D7%9C%D7%94/%D7%97%D7%9C%D7%A7_%D7%92_(%D7%94%D7%9B%D7%9C)']
        for index, url in enumerate(chalek_links):
            response = urllib2.urlopen(url)
            with open('files/Part_{}.html'.format(index+1), 'w') as f:
                f.write(response.read())
    
    urls={"Index":'https://he.wikisource.org/wiki/%D7%AA%D7%95%D7%A8%D7%AA_%D7%94%D7%A2%D7%95%D7%9C%D7%94/%D7%9E%D7%A4%D7%AA%D7%97_%D7%A4%D7%A8%D7%A7%D7%99%D7%9D',
        "Intro":'https://he.wikisource.org/wiki/%D7%AA%D7%95%D7%A8%D7%AA_%D7%94%D7%A2%D7%95%D7%9C%D7%94/%D7%94%D7%A7%D7%93%D7%9E%D7%94',
        "Baruch_Sheamar":'https://he.wikisource.org/wiki/%D7%AA%D7%95%D7%A8%D7%AA_%D7%94%D7%A2%D7%95%D7%9C%D7%94/%D7%A4%D7%99%D7%A8%D7%95%D7%A9_%D7%9C%D7%91%D7%A8%D7%95%D7%9A_%D7%A9%D7%90%D7%9E%D7%A8',
        "Songs":'https://he.wikisource.org/wiki/%D7%AA%D7%95%D7%A8%D7%AA_%D7%94%D7%A2%D7%95%D7%9C%D7%94/%D7%A9%D7%99%D7%A8%D7%99_%D7%97%D7%AA%D7%99%D7%9E%D7%94'}
    
    urls={"Songs":'https://he.wikisource.org/wiki/%D7%AA%D7%95%D7%A8%D7%AA_%D7%94%D7%A2%D7%95%D7%9C%D7%94/%D7%A9%D7%99%D7%A8%D7%99_%D7%97%D7%AA%D7%99%D7%9E%D7%94'}
    
    for title in urls.keys():
        response = urllib2.urlopen(urls[title])
        with open('files/{}.html'.format(title), 'w') as f:
            f.write(response.read())
def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def not_note(s):
    if s not in skip_these and u'<<' not in s and u'>>' not in s and u'^' not in s:
        return True
    return False
def post_th_index():
    # create index record
    record = SchemaNode()
    record.add_title('Torat HaOlah', 'en', primary=True, )
    record.add_title(u'תורת העולה', 'he', primary=True, )
    record.key = 'Torat HaOlah'
    {'en':u'','he':u''}
    pre_text_titles=[{'en':u'Author\'s Introduction','he':u'הקדמת המחבר'}]
    post_text_titles=[{'en':u'Kabballic Commentary to Barukh SheAmar','he':u'פירוש לברוך שאמר'},{'en':u'Concluding Poems','he':u'שירי חתימה'}]
    
    for title in pre_text_titles:
        intro_node = JaggedArrayNode()
        intro_node.add_title(title['en'], 'en', primary = True)
        intro_node.add_title(title['he'], 'he', primary = True)
        intro_node.key = title['en']
        intro_node.depth = 1
        intro_node.addressTypes = ['Integer']
        intro_node.sectionNames = ['Paragraph']
        record.append(intro_node)
        
    index_node = JaggedArrayNode()
    index_node.add_title('Index', 'en', primary = True)
    index_node.add_title(u'מפתח', 'he', primary = True)
    index_node.key = 'Index'
    index_node.depth = 2
    index_node.addressTypes = ['Integer','Integer']
    index_node.sectionNames = ['Part','Paragraph']
    record.append(index_node)
    
    chelek_node = JaggedArrayNode()
    chelek_node.add_title("Part One", 'en', primary=True)
    chelek_node.add_title("חלק א", 'he', primary=True)
    chelek_node.key = 'Part One'
    chelek_node.depth = 2
    chelek_node.addressTypes = ['Integer','Integer']
    chelek_node.sectionNames = ['Chapter','Paragraph']
    record.append(chelek_node)
    
    titles=[[u'Part Two',u'חלק ב'],[u'Part Three',u'חלק ג']]
    # add nodes for chapters
    for title in titles:
        chelek_node = SchemaNode()
        chelek_node.add_title(title[0], 'en', primary=True)
        chelek_node.add_title(title[1], 'he', primary=True)
        chelek_node.key = title[0]

        intro_node = JaggedArrayNode()
        intro_node.add_title("Introduction", 'en', primary=True)
        intro_node.add_title(u"הקדמה", 'he', primary=True)
        intro_node.key = 'Introduction'
        intro_node.depth = 1
        intro_node.addressTypes = ['Integer']
        intro_node.sectionNames = ['Paragraph']
        chelek_node.append(intro_node)

        #now we add text node
        text_node = JaggedArrayNode()
        text_node.key = "default"
        text_node.default = True
        text_node.depth = 2
        text_node.addressTypes = ['Integer', 'Integer']
        text_node.sectionNames = ['Chapter','Paragraph']
        chelek_node.append(text_node)
    
        record.append(chelek_node)

    for title in post_text_titles:
        intro_node = JaggedArrayNode()
        intro_node.add_title(title['en'], 'en', primary = True)
        intro_node.add_title(title['he'], 'he', primary = True)
        intro_node.key = title['en']
        intro_node.depth = 1
        intro_node.addressTypes = ['Integer']
        intro_node.sectionNames = ['Paragraph']
        record.append(intro_node)

    record.validate()

    index = {
        "title": "Torat HaOlah",
        "categories": ["Philosophy"],
        "schema": record.serialize()
    }
    post_index(index)
def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def url_to_soup(url):
    chapter_buf = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    
    c.setopt(c.WRITEFUNCTION, chapter_buf.write)
    c.perform()
    soup = BeautifulSoup(chapter_buf.getvalue(), 'html.parser')
    return soup;
def clean_line(s):
    prag=u'פראג'
    mevarieg=u'מברג'
    am=u'עמ'
    s = re.sub(ur'<.*?>',u'',s)
    s= re.sub(ur'{}\'.*?{}'.format(am,prag),u'',s)
    s= re.sub(ur'{}\'.*?{}'.format(am,mevarieg),u'',s)
    s= re.sub(ur'\[\d*?\]',u'',s)
    s=remove_extra_space(s)
    return s
def post_chalakim():
    for index in range(1,4):
        soup = BeautifulSoup(open('files/Part_{}.html'.format(index)), "html.parser")
        prakim=[]
        perek_box=[]
        print "Posting Part",index
        for p in soup.findAll(class_='mw-body-content'):
            text = u''.join(p.findAll(text=True))
            lines=text.split('\n')
            for line in lines:
                if u'עריכה' in line: 
                    if u'מתוך' in line:
                        #print "BREAK"
                        prakim.append(perek_box)
                        perek_box=[]
                        title=line.split(u'/')[-1].split('(')[0]
                elif not re.findall(ur'[A-Za-z0-9]',line) and not_blank(line) and not_note(line):
                    perek_box.append(clean_line(line))
        #take out first one, since it's never part of parsing
        if len(perek_box)>0:
            prakim.append(perek_box)
        prakim=prakim[1:]
        #fill in missing chapts from part 3
        if index==3:
            for chapter in fill_missing_p3():
                prakim.append(chapter)
            #print "HEREP",u''.join(p.findAll(text=True))
        """
        for thing in soup.findAll(True):
            if thing.has_attr('id'):
                if u'פרק' in thing['id'] and len(perek_box)>0:
                    prakim.append(perek_box)                
            for p in thing.findAll('p'):
                perek_box.append(u''.join(thing.findAll(text=True)))
        prakim.append(perek_box)
        """
            
        """
        for pindex, perek in enumerate(prakim):
            for paindex, paragraph in enumerate(perek):
                print pindex, paindex, paragraph
        """
        if index in has_intro:
            version = {
                'versionTitle': 'Torat HaOlah, based on Prague, 1570 and Lemberg, 1858 editions',
                'versionSource': 'https://he.wikisource.org/wiki/%D7%AA%D7%95%D7%A8%D7%AA_%D7%94%D7%A2%D7%95%D7%9C%D7%94',
                'language': 'he',
                'text': prakim.pop(0)
            }
            post_text_weak_connection("Torat HaOlah, Part "+num2words(index).capitalize()+", Introduction", version)
        version = {
            'versionTitle': 'Torat HaOlah, based on Prague, 1570 and Lemberg, 1858 editions',
            'versionSource': 'https://he.wikisource.org/wiki/%D7%AA%D7%95%D7%A8%D7%AA_%D7%94%D7%A2%D7%95%D7%9C%D7%94',
            'language': 'he',
            'text': prakim
        }
        post_text_weak_connection("Torat HaOlah, Part "+num2words(index).capitalize(), version)
        #post_text("Malbim on Leviticus",  version,weak_network=True, skip_links=True, index_count="on")
def post_parts():
    intro=True
    index=False
    baruch=True
    songs=True
    
    
    intro_text=[]
    index_text=[]
    baruch_text=[]
    song_text=[]
    if intro:
        past_start=False
        soup = BeautifulSoup(open('files/Intro.html'), "html.parser")
        for p in soup.findAll(class_='mw-body-content'):
            text = u''.join(p.findAll(text=True))
            if u'וויקי' in text:
                lines=text.split('\n')
                for line in lines:
                    if u'מנחות' in line:
                        past_start=True
                    if u'New' in line:
                        break
                    if past_start and not_blank(line) and not_note(line):
                        intro_text.append(clean_line(line.replace(u'[עריכה]',u'')))
        version = {
            'versionTitle': 'Torat HaOlah, based on Prague, 1570 and Lemberg, 1858 editions',
            'versionSource': 'https://he.wikisource.org/wiki/%D7%AA%D7%95%D7%A8%D7%AA_%D7%94%D7%A2%D7%95%D7%9C%D7%94',
            'language': 'he',
            'text': intro_text
        }
        post_text_weak_connection("Torat HaOlah, Author's Introduction", version)
        #post_text("Malbim on Leviticus",  version,weak_network=True, skip_links=True, index_count="on")
    if index:
        past_start=False
        soup = BeautifulSoup(open('files/Index.html'), "html.parser")
        for line in u''.join(soup.findAll(class_='mw-body-content')[2].findAll(text=True)).split('\n'):
            if u'הקדמה' in line:
                past_start=True
            if u'New' in line:
                break
            if past_start and not_blank(line) and not_note(line):
                index_text.append(clean_line(line.replace(u'[עריכה]',u'')))
        final_index=[]
        part_box=[]
        for line in index_text:
            if u'חלק' in line and u'פרק' not in line and len(part_box)>0:
                final_index.append(part_box)
                part_box=[]
            part_box.append(line)
        if len(part_box)>0:
            final_index.append(part_box)
        """
        for pindex, part in enumerate(final_index):
            for paindex, paragraph in enumerate(part):
                print pindex, paindex, paragraph
        """
        
        version = {
            'versionTitle': 'Torat HaOlah, based on Prague, 1570 and Lemberg, 1858 editions',
            'versionSource': 'https://he.wikisource.org/wiki/%D7%AA%D7%95%D7%A8%D7%AA_%D7%94%D7%A2%D7%95%D7%9C%D7%94',
            'language': 'he',
            'text': final_index
        }
        post_text_weak_connection("Torat HaOlah, Index", version)
    if baruch:
        past_start=False
        soup = BeautifulSoup(open('files/Baruch_Sheamar.html'), "html.parser")
        for line in u''.join(soup.findAll(class_='mw-body-content')[2].findAll(text=True)).split('\n'):
            if u'המחבר' in line:
                past_start=True
            if u'קטע' in line:
                break
            if past_start and not_blank(line) and not_note(line):
                baruch_text.append(clean_line(line.replace(u'[עריכה]',u'')))
        """
        for line in baruch_text:
            print "TEXT:",line
        """
        version = {
            'versionTitle': 'Torat HaOlah, based on Prague, 1570 and Lemberg, 1858 editions',
            'versionSource': 'https://he.wikisource.org/wiki/%D7%AA%D7%95%D7%A8%D7%AA_%D7%94%D7%A2%D7%95%D7%9C%D7%94',
            'language': 'he',
            'text': baruch_text
        }
        post_text_weak_connection("Torat HaOlah, Kabballic Commentary to Barukh SheAmar", version)
    if songs:
        past_start=False
        soup = BeautifulSoup(open('files/Songs.html'), "html.parser")
        for line in u''.join(soup.findAll(class_='mw-body-content')[2].findAll(text=True)).split('\n'):
            #print line
            if u'עריכה' in line:
                past_start=True
            if u'New' in line:
                break
            if past_start and not_blank(line.replace(u'\xa0\xa0\xa0',u'')) and not_note(line):# and u'\xa0\xa0\xa0' not in line:
                song_text.append(clean_line(line.replace(u'[עריכה]',u'')))
        #1/0
        """
        for line in song_text:
            print "TEXT:",line
        """
        version = {
            'versionTitle': 'Torat HaOlah, based on Prague, 1570 and Lemberg, 1858 editions',
            'versionSource': 'https://he.wikisource.org/wiki/%D7%AA%D7%95%D7%A8%D7%AA_%D7%94%D7%A2%D7%95%D7%9C%D7%94',
            'language': 'he',
            'text': song_text
        }
        post_text_weak_connection("Torat HaOlah, Concluding Poems", version)
def fill_missing_p3():
    missing_chapts=[]
    chapt_box=[]
    soup=url_to_soup('https://he.wikisource.org/wiki/%D7%AA%D7%95%D7%A8%D7%AA_%D7%94%D7%A2%D7%95%D7%9C%D7%94/%D7%97%D7%9C%D7%A7_%D7%92')
    for index, link in enumerate(soup.findAll('p')[0]):
        if not link.find('a') and index>119:
            new_soup=url_to_soup('https://he.wikisource.org'+link['href'])
            for thing in new_soup.findAll('p'):
                text=remove_extra_space(u' '.join(thing.findAll(text=True))).replace(u'\n',u'')
                if not_blank(text) and not_note(text):
                    chapt_box.append(clean_line(text))
            missing_chapts.append(chapt_box)
            chapt_box=[]
    """
    for cindex, chapter in enumerate(missing_chapts):
        for pindex, paragraph in enumerate(chapter):
            print cindex, pindex, paragraph
    """
    return missing_chapts

        
#make_files()
#fill_missing_p3()


post_th_index()    
#post_parts()     
#post_chalakim()

#['p',{"class":'mw-headline'}]):
"""
        if p.has_attr('class'):
            print p['class']
            #print text
            if 'mw-body-content' in p['class']:
                print p
                text = u''.join(p.findAll(text=True))
                if u'מתוך:' in text and len(perek_box)>0:
                    prakim.append(perek_box)                
                    perek_box=[]
                elif not_blank(text):
"""