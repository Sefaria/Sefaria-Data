# -*- coding: utf-8 -*-
import pycurl
import cStringIO
import re
import codecs
from bs4 import BeautifulSoup

#returns parsed text with acrostic-adjusted index
def get_final_parsed_text():
    parsed_text = get_parsed_text()
    parsed_text[0] = make_intro_accrostic(parsed_text[0])
    return parsed_text;

#returns plain parsed text
def get_parsed_text():
    
    wiki_link = "https://he.wikisource.org/wiki/%D7%A9%D7%91_%D7%A9%D7%9E%D7%A2%D7%AA%D7%AA%D7%90"
    chapter_links = get_chapter_links(wiki_link)

    final_text= []
    chapter_content_list = []
    subchapter_content_list = []
    
    #first link is introduction, next seven respective sections of sefer. inroduction has no subchapters, so it must be implemented differently
    for intro_content in get_subchapter_content(chapter_links[0]):
        chapter_content_list.append(intro_content.strip())
    final_text.append(chapter_content_list)
    chapter_content_list = []

    #for rest of text
    for index in range(1,8):
        for subchapter_link in get_subchapter_links(chapter_links[index]):
            for subchapter_content in get_subchapter_content(subchapter_link):
                subchapter_content_list.append(subchapter_content)
            chapter_content_list.append(subchapter_content_list)
            subchapter_content_list = []
        final_text.append(chapter_content_list)
        chapter_content_list = []

    return final_text;

def make_intro_accrostic(intro):
    #intro startuing in the 3rd pararaph (index 2) is an acrostic (besides last paragraph), so we want to bold the first letter of those paragraphs. For last paragraph, acrostic includes
    #first two letters of the paragraph ("הן" in "הכהן")
    return_intro =[]
    for index, paragraph in enumerate(intro):
        return_intro.append( bold_letters(paragraph, 1) if index>2 and index<len(intro)-2 else paragraph if index!=len(intro)-2 else bold_letters(paragraph, 2) )



#intro[-1] = bold_letters(intro[-2],2)

    return return_intro;

def bold_letters(string, index):
    print type(string)
    string = string.decode('utf8')
    print type(string)
    string = u"<b><big>"+string[0:index]+u"</b></big>"+string[index:]
    string = string.encode('utf8')
    return string

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
    chapter_content = soup.find_all('p')
    
    return_array = []
    for index, chapter in enumerate(chapter_content):
        text = remove_html(str(chapter))
        if not_blank(text):
            return_array.append(text)
    
    
    return return_array;

#each shmatta has a subject line, which is most easiy accessed from the index page.
def get_chapter_subjects():
    soup = url_to_soup("https://he.wikisource.org/wiki/%D7%A9%D7%91_%D7%A9%D7%9E%D7%A2%D7%AA%D7%AA%D7%90")
    subject_elements = soup.find_all("small")
    return_array = []

    for subject_element in subject_elements:
        return_array.append(subject_element.contents[0])
    #assert isInstance(type(subject_element.contents[0]), unicode)

    return return_array;

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
    soup = BeautifulSoup(chapter_buf.getvalue(), 'html.parser')
    return soup;

text = get_final_parsed_text()

for index, paragraph in enumerate(text[0]):
    print str(index)+" "+paragraph
for chapter in text[1:]:
    for subchapter in chapter:
        for index, paragraph in enumerate(subchapter):
            print str(index) + " "+ paragraph


