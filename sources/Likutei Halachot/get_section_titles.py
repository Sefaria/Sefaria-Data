# -*- coding: utf-8 -*-
import pycurl
import cStringIO
import re
import sys
import json
import urllib
import urllib2
from urllib2 import URLError, HTTPError
from bs4 import BeautifulSoup

reload(sys)
sys.setdefaultencoding("utf-8")

#takes URL and return beautiful soup object
def url_to_soup(url):
    chapter_buf = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)

    c.setopt(c.WRITEFUNCTION, chapter_buf.write)
    c.perform()
    soup = BeautifulSoup(chapter_buf.getvalue(), 'html.parser', from_encoding="iso-8859-8")
    return soup;

#get section links from wikisource page
def get_part_links(url):
    soup = url_to_soup(url)
    chapters =  soup.find(id="mw-content-text").find_all("li")
    return_list = []
    for chapter in chapters:
        result = chapter.a['href']
        #so far we have relative url, so we append the first part
        return_list.append('https://he.wikisource.org'+result)
    return return_list;

#gets section titles from rabenubooks orech chayim pages
def get_sections_oc():
    final_list = []
    #on rabenubooks, Likutei Halachot is split into three pages.
    #Here we iterate through each to get the titles.
    rabenu_urls = ['http://rabenubook.com/%D7%9C%D7%99%D7%A7%D7%95%D7%98%D7%99-%D7%94%D7%9C%D7%9B%D7%95%D7%AA-%D7%90%D7%95%D7%A8%D7%97-%D7%97%D7%99%D7%99%D7%9D-%D7%90-%D7%AA%D7%95%D7%9B%D7%9F-%D7%A2%D7%A0%D7%99%D7%99%D7%A0%D7%99%D7%9D/', 
        'http://rabenubook.com/%D7%9C%D7%99%D7%A7%D7%95%D7%98%D7%99-%D7%94%D7%9C%D7%9B%D7%95%D7%AA-%D7%90%D7%95%D7%A8%D7%97-%D7%97%D7%99%D7%99%D7%9D-%D7%91-%D7%AA%D7%95%D7%9B%D7%9F-%D7%A2%D7%A0%D7%99%D7%99%D7%A0%D7%99%D7%9D/',
        'http://rabenubook.com/%D7%9C%D7%99%D7%A7%D7%95%D7%98%D7%99-%D7%94%D7%9C%D7%9B%D7%95%D7%AA-%D7%90%D7%95%D7%A8%D7%97-%D7%97%D7%99%D7%99%D7%9D-%D7%92-%D7%AA%D7%95%D7%9B%D7%9F-%D7%A2%D7%A0%D7%99%D7%99%D7%A0%D7%99%D7%9D/']
    for url in rabenu_urls:
        soup = url_to_soup(url)
        chapters =  soup.find(id="lcp_instance_0").find_all("a")
        sec_names = []
        #here we take section titles and format for our purposes
        for index in range(len(chapters)):
            sec_names.append(chapters[index]['title'].split(" ")[6:])
        #here we take out letter section references, or else make a string out of the array of strings we have now
        for e in sec_names:
            if (len(e[len(e)-1])==1):
                string_title = ' '.join(e[:-1])
                if standardize_title(string_title) not in final_list:
                    final_list.append(standardize_title(string_title))
            else:
                final_list.append(standardize_title(' '.join(e)))
    
    return final_list;

#makes sure each title has "הלכות" written exactly once, unless it is an introduction
def standardize_title(title):
    title_array = title.split(" ")
    while title_array[0].replace(" ", "") =="":
        title_array.pop(0)
    while len(title_array)> 0 and title_array[len(title_array)-1].replace(" ", "") =="":
        title_array.pop(len(title_array)-1)
    if ("הלכה" in title_array):
        title_array.pop(title_array.index("הלכה"))
    if title_array[0]=="הלכות" or title_array[0]=="הקדמת":
        return ' '.join(title_array)
    else:
        return  "הלכות"+" "+' '.join(title_array);

#these next two methods scrape section titles from wikisource.
#require two methods as formatting on wikisource is not standardized
def get_sections_yd(url):
    soup = url_to_soup(url)
    return_list = []

    chapters =  soup.find(id="mw-content-text").find_all("li")
    for chapter in chapters:
        result = chapter.a['title']
        return_list.append(result.split("/")[2])
    return return_list;

def get_sections_eh(url):
    soup = url_to_soup(url)
    chapters =  soup.find('ul').find_all("li")
    return_list = []
    for chapter in chapters:
        result = chapter.a['title']
        #so far we have relative url, so we append the first part
        return_list.append(result.split("/")[2])
    return return_list;
def get_he_section_title_array():
    #stores section titles recieved on wikisource
    parts = get_part_links('https://he.wikisource.org/wiki/%D7%9C%D7%99%D7%A7%D7%95%D7%98%D7%99_%D7%94%D7%9C%D7%9B%D7%95%D7%AA')

    #within wikisource, each chalek is formatted differently and needs seperate attention
    sections = []
    #for orech chayim, we took from rabenubooks, which needs a designated method
    sections.append(get_sections_oc())
    #within wikisource, each chalek is formatted differently and needs seperate attention

    #for yoreh deah
    sections.append(get_sections_yd(parts[1]))
    #for even haeizer
    sections.append(get_sections_eh(parts[2]))
    #for chosen mishpat (same as yd)
    sections.append(get_sections_yd(parts[3]))
    return sections;

sections = get_he_section_title_array()
"""for section in sections:
    for title in section:
        print title"""
