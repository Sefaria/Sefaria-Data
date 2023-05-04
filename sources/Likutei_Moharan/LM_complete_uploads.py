# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.append("/Users/Eytan/Desktop/sefaria/Sefaria-Data/sources")

from local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from functions import *
import re
import linking_utilities
import codecs
import cStringIO
import pycurl
from bs4 import BeautifulSoup
from sources import functions

reload(sys)
sys.setdefaultencoding("utf-8")

def get_content_array(chapter_url):
    buf = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, chapter_url)
    c.setopt(c.WRITEFUNCTION, buf.write)
    c.perform()
    content_array = []
    
    soup = BeautifulSoup(buf.getvalue(), 'html.parser', from_encoding="iso-8859-8")
    
    for child in soup.find("div", class_ = "entry-content" ).descendants:
        if unicode(child)[0] !="<" and unicode(child)[0] !="i" and len(unicode(child)) !=1:
            content_array.append(child)
    #print "child " + child[:5]
    buf.close()
    content_array =  aggregate_chapters(content_array[:-1])
    return content_array

def aggregate_chapters(list):
    return_box = []
    p_box = []
    for p in list:
        first_word = p.strip().split(" ")[0]
        #don't want to make new ote for aleph, since we want to combine intro with first paragraph.
        if first_word=="א":
            p_box.append(' '.join(p.strip().split(" ")))
        elif False == wordHasNekudot(first_word) and "(" not in first_word:
            return_box.append('<br>'.join(p_box))
            p_box = []
            #skip first word, since it is the chapter header
            p_box.append(' '.join(p.strip().split(" ")))
        elif len(removeExtraSpaces(p)) != 0:
            p_box.append(p)
    return_box.append('<br>'.join(p_box))
    return return_box if len(return_box)>1 else list

def remove_br(p):
    if p[0]=="<":
        p = p[:4]
    if p[-1]==">":
        p = p[:-4]
    return p


chapter_buf = cStringIO.StringIO()
c = pycurl.Curl()
c.setopt(c.URL, 'http://rabenubook.com/%D7%9C%D7%99%D7%A7%D7%95%D7%98%D7%99-%D7%9E%D7%95%D7%94%D7%A8%D7%B4%D7%9F-%D7%AA%D7%95%D7%9B%D7%9F-%D7%A2%D7%A0%D7%99%D7%99%D7%A0%D7%99%D7%9D/')

c.setopt(c.WRITEFUNCTION, chapter_buf.write)
c.perform()
soup = BeautifulSoup(chapter_buf.getvalue(), 'html.parser', from_encoding="iso-8859-8")

chapters =  soup.find(id="lcp_instance_0").find_all("a")

final_list = []
max_list = 0
for index in range(len(chapters)):
    print "this is Torah "+str(index)
    torah = get_content_array(chapters[index]['href'])
    if len(torah)>max_list:
        max_list = len(torah)
                              
    final_list.append(torah)

print "uploading..."
print "max list: "+ str(max_list)

text_version = {
    'versionTitle': "Likutei Moharan - rabenubook.com",
    'versionSource': "http://rabenubook.com/%D7%9C%D7%99%D7%A7%D7%95%D7%98%D7%99-%D7%9E%D7%95%D7%94%D7%A8%D7%B4%D7%9F-%D7%90/",
    'language': 'he',
    'text': final_list
}

post_text_weak_connection("Likutei Moharan", text_version)


chapter_buf.close()
