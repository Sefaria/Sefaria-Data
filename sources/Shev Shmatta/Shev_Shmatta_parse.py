# -*- coding: utf-8 -*-
import pycurl
import cStringIO
import re
from bs4 import BeautifulSoup


#get section links from wikisource page
def get_chapter_links(url):
    soup = url_to_soup(url)
    chapters =  soup.find(id="mw-content-text").find_all("li")
    return_list = []
    for chapter in chapters:
        result = chapter.a['href']
        #so far we have relative url, so we append the first part
        return_list.append('https://he.wikisource.org'+result)
    return return_list;

def get_subchapter_links(url):
    soup = url_to_soup(url)
    subchapter_links = soup.find_all('p')[1].find_all('a')
    
    return_array = []
    
    for link in subchapter_links:
        return_array.append('https://he.wikisource.org'+link['href'])
    
    return return_array

def get_subchapter_content(url):
    soup = url_to_soup(url)
    #1st p element is blank
    chapter_content = soup.find_all('p')[1:]
    
    for index, chapter in enumerate(chapter_content):
        chapter_content[index] = clean_content(str(chapter))
    
    
    return chapter_content

def clean_content(s):
#take out english
#s= re.sub('<a href=\"/wiki/[a-zA-Z0-9%_//]*','',s)
    s = re.sub("<.*?>","",s)
    return s

#takes URL and return beautiful soup object
def url_to_soup(url):
    chapter_buf = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    
    c.setopt(c.WRITEFUNCTION, chapter_buf.write)
    c.perform()
    soup = BeautifulSoup(chapter_buf.getvalue(), 'html.parser', from_encoding="iso-8859-8")
    return soup;

wiki_link = "https://he.wikisource.org/wiki/%D7%A9%D7%91_%D7%A9%D7%9E%D7%A2%D7%AA%D7%AA%D7%90"
chapter_links = get_chapter_links(wiki_link)

final_text= []
chapter_content_list = []
#first link is introduction, next seven respective sections of sefer

#for rest of text
for index in range(1,8):
    for subchapter_link in get_subchapter_links(chapter_links[index]):
        for subchapter_content in get_subchapter_content(subchapter_link):
            chapter_content_list.append[subchapter_content]
    final_text.append[chapter_content]
