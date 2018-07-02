# -*- coding: utf-8 -*-
import pycurl
import cStringIO
import re
import codecs
from bs4 import BeautifulSoup
import sys
import os
from Sifrei_Devarim_en_post import get_perek_index
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
sys.path.insert(0, SEFARIA_DATA_PATH)
from data_utilities.util import ja_to_xml
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from functions import *

perek_index = get_perek_index()

def get_piska_text():
    wiki_link = "https://he.wikisource.org/wiki/%D7%A1%D7%A4%D7%A8%D7%99_%D7%A2%D7%9C_%D7%93%D7%91%D7%A8%D7%99%D7%9D#.D7.A4.D7.A8.D7.A9.D7.AA_.D7.93.D7.91.D7.A8.D7.99.D7.9D"
    soup = url_to_soup(wiki_link)
    piska_link = soup.select('b a')[1:117]
    piska_complete = []
    for index, a in enumerate(piska_link):
        piska_ps = url_to_soup('https://he.wikisource.org'+a['href']).find_all('p')
        p_box = []
        for p in piska_ps:
            if p.a:
                for pa in p.find_all('a'):
                    pa.string = "("+pa.string+")"
                    pa.string = pa.string.replace("((","(").replace("))",")")
            line = ''.join(p.find_all(text=True))
            if not_blank(line):
                p_box.append(line)
        piska_complete.append(p_box)
    return piska_complete
#returns plain parsed text
def get_perek_text():
    wiki_link = "https://he.wikisource.org/wiki/%D7%A1%D7%A4%D7%A8%D7%99_%D7%A2%D7%9C_%D7%93%D7%91%D7%A8%D7%99%D7%9D#.D7.A4.D7.A8.D7.A9.D7.AA_.D7.93.D7.91.D7.A8.D7.99.D7.9D"
    parsed_chapter_numbers = []
    complete_text = []
    chapter_links = get_chapter_links(wiki_link)
    for chapter in chapter_links:
        chapter_number = get_chapter_number(chapter[0])
        print "This is CHHAPTER! "+str(chapter_number)
        if chapter_number not in parsed_chapter_numbers:
            parsed_chapter_numbers.append(get_chapter_number(chapter[0]))
            soup = url_to_soup(chapter[1])
            for pa in soup.find_all('a'):
                if pa.string:
                    pa.string = "("+pa.string+")"
                    pa.string = pa.string.replace("((","(").replace("))",")")
            lines = soup.find_all(text=True)
            text_lines = []
            final_lines = []
            for line in lines:
                text_lines.append(line.replace('\n','NEWLINE').replace(u"(כל הפרק)(כל הפסוק)",""))
            for text_line in re.split(ur"\u05e4\u05e1\u05d5\u05e7",''.join(text_lines))[1:]: #first item is not part of txt
                text_line = remove_nontext(text_line)
                if not_blank(text_line):
                    if len(text_line.split(u"\u05e2\u05e8\u05d9\u05db\u05d4"))>1:
                        try:
                            final_lines.append(remove_web_script(remove_extra_newlines(text_line)).replace('NEWLINE','\n').split(u"\u05e2\u05e8\u05d9\u05db\u05d4")[1])
                        except:
                            final_lines.append(remove_web_script(remove_extra_newlines(text_line)).replace('NEWLINE','\n'))
                    else:
                        final_lines.append(remove_extra_newlines(text_line).replace('NEWLINE','\n'))
            #take out text at the beggining
            final_lines = final_lines[get_end_index(final_lines):]
            #for pair in make_pasuk_index(final_lines):
            #print "THIS IS CHAPTER"+str(chapter_number)+" THIS IS PASUK: "+str(pair[0])+" "+pair[1]
            complete_text.append([chapter_number,make_pasuk_index(final_lines)])
    return complete_text
def remove_web_script(line):
    while len(line.split(u"<<"))>1:
        line = line.split(u"<<")[0]
    while len(line.split(u">>"))>1:
        line = line.split(u">>")[0]
    return line
def remove_nontext(s):
    s = s.split("Saved")[0]
    s = re.split("\S*_\S*",s)[0]
    good_string=[]
    """
    for line in s.split("\n"):
        if "%" not in line:
            good_string.append(line)
    s = '\n'.join(good_string)
    """
    return s
def remove_extra_newlines(s):
    return re.sub("(NEWLINE){2,}","NEWLINE",s)
def get_chapter_number(s):
    return getGematria(s.replace(u"פרק",u""))
def make_pasuk_index(text):
    return_list = []
    errors = []
    for line in text:
        if u"(כל הפרק)" in line:
            return_list.append([getGematria(line.split(" ")[1]),""])
        else:
            try:
                return_list[-1][1]+=line
            except:
               errors.append(line)
    for error in errors:
        x=0
    return return_list

def get_end_index(lines):
    for item in lines:
        if re.match(ur'\)\n$', item):
            return lines.index(item)+1
    return -1
def add_period_at_end_of_paragraph(s):
    s = s.replace(":",".")
    return s+"." if s.strip()[-1] != "." else s

#get section links from wikisource page
def get_chapter_links(url):
    soup = url_to_soup(url)
    chapters =  soup.find_all("li")
    return_list = []
    for chapter in chapters[13:40]:
        return_list.append([chapter.find(text=True),'https://he.wikisource.org'+chapter.find_all("a")[0]['href']])
    return return_list;

def remove_html(s):
    #take out html script
    s = re.sub("<.*?>","",s)
    s = re.sub("[.*?]","",s)
    return s;

def not_blank(s):
    return (len(s.replace(" ","").replace("\n","").replace("\r","").replace("\t",""))!=0);

#takes URL and return beautiful soup object
def url_to_soup(url):
    chapter_buf = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    
    c.setopt(c.WRITEFUNCTION, chapter_buf.write)
    c.perform()
    #print re.sub(r"(?<=>)(.*)(?=<\/a)",r"(\1)",chapter_buf.getvalue())
    soup = BeautifulSoup(chapter_buf.getvalue(), 'html.parser')
    return soup;
def get_start_piska(chapter):
    for index in perek_index:
        if chapter==index[0]:
            return index[1]
    if chapter == 31:
        return 307
    print "MISSING "+str(chapter)
    return None
def combine_perek(perek_pasuk_pairs):
    return_string = ""
    for pasuk_pair in perek_pasuk_pairs:
        return_string+=u"פסוק"+" "+numToHeb(pasuk_pair[0])+u"<br>"+pasuk_pair[1][1:]+u"<br>"
    return return_string[:-6]

"""useful print method to test output
   
"""
def get_parsed_text():
    piskas = [[""] for x in range(358)]
    piska_text = get_piska_text()
    print str(len(piska_text))+" PISKAS!"
    for index, piska in enumerate(get_piska_text()):
        print index
        print len(piskas)
        piskas[index]=piska
    prakim = get_perek_text()[8:]
    #first perek asssigned manually, so as not to overwrite piskas
    piskas[116]=[combine_perek(prakim[0][1])]
    for perek in prakim[1:]:
        #give them the chapter number and find correct piska, assign perek string
        piskas[get_start_piska(perek[0])-1]=[combine_perek(perek[1])]
    return piskas
def main():
    pass

if __name__ == "__main__":
    piskas = get_parsed_text()
    for pindex, piska in enumerate(piskas):
        for paindex, para in enumerate(piska):
            print str(pindex)+" "+str(paindex)+" "+para

    version = {
        'versionTitle': 'Sifrei Devarim, Hebrew',
        'versionSource': 'https://he.wikisource.org/wiki/%D7%A1%D7%A4%D7%A8%D7%99_%D7%A2%D7%9C_%D7%93%D7%91%D7%A8%D7%99%D7%9D',
        'language': 'he',
        'text': piskas
        }
    post_text('Sifrei Devarim', version,weak_network=True)
    main()
