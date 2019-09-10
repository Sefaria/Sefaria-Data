import django
django.setup()
from sources.functions import getGematria, headers
from sefaria.model import *
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import Tag

soup_input = requests.get("https://he.wikisource.org/wiki/%D7%9E%D7%A2%D7%A9%D7%94_%D7%A8%D7%91").content
soup = BeautifulSoup(soup_input, features='lxml')
nodes = soup.find_all("div", {"class": "mw-parser-output"})[0].contents[6].contents
wiki_url = "https://he.wikisource.org"
page_dict = {}
for node in nodes:
    if node == "\n":
        continue
    intro = None
    curr_daf = None
    node_url = wiki_url+node.contents[0]["href"]
    request = requests.get(node_url)
    node_soup = BeautifulSoup(request.content, features='lxml')
    pages = node_soup.find("div", {"class": "mw-parser-output"})
    for n, element in enumerate(pages):
        if not isinstance(element, Tag):
            pass
        elif element.name == "p":
            if not curr_daf:
                intro = element.text
            else:
                if intro:
                    page_dict[curr_daf] += intro + "\n"
                    intro = ""
                page_dict[curr_daf] += element.text + "\n"
        elif element.name.startswith("h"):
            curr_daf = getGematria(element.contents[1].text)
            page_dict[curr_daf] = ""



