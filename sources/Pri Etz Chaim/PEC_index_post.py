# -*- coding: utf-8 -*-
import sys
import os
import cStringIO
import pycurl
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.append("/Users/Eytan/Desktop/sefaria/Sefaria-Data/sources")

from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
#from sefaria.model import *

from functions import *
import re
import data_utilities
import codecs
from sources import functions
from bs4 import BeautifulSoup


def get_titles():
    soup = url_to_soup("http://www.hebrew.grimoar.cz/vital/pri_ec_chajim.htm")
    ps = soup.find('p')
    title_tags = soup.find_all('b')
    titles = []
    for t in title_tags:
        extracted_title = extract_title(t.find(text=True))
        if extracted_title not in titles and u"הקדמה" not in extracted_title:
            titles.append(extracted_title)
    titles = titles[2:]
    #the shaar of responding amen is mislables on the website, so it must be added in manually
    titles.insert(10, "שער כוונת אמן")
    return titles

def extract_title(line):
    return line.split("-")[0].replace(":","").replace("  "," ").strip()

def url_to_soup(url):
    chapter_buf = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    
    c.setopt(c.WRITEFUNCTION, chapter_buf.write)
    c.perform()
    soup = BeautifulSoup(chapter_buf.getvalue(), 'html.parser')
    return soup;


    
english_titles = ["Gate of Prayer", "Gate of Blessings","Gate of Fringes","Gate of Teffilin","Gate of the World of Action","Gate of the Holies","Gate of Songs","Gate of the Recitation of the Shema","Gate of the Silent Prayer","Gate of the Repetition of the Silent Prayer","Gate of Amen Intention","Gate of Confession","Gate of Putting Down the Head","Gate of Reading the Torah","Gate of the Afternoon and Evening Prayers","Gate of the Recitation of the Shema Before Retiring","Gate of the Midnight Prayer","Gate of Conduct While Learning","Gate of the Sabbath","Gate of The New Month, Chanukah, and Purim","Gate of Festival","Gate of Passover","Gate of the Omer Count","Gate of Shavuot","Gate of Rosh Hashana","Gate of the Prayers of Rosh Hashana","Gate of the Shofer","Gate of Yom Kippur","Gate of Sukkot","Gate of Lulav"]
for index, title in enumerate(get_titles()):
    print title + " "+english_titles[index]+str(index)
x=1/0
# create index record
record = SchemaNode()
record.add_title('Pri Etz Chaim', 'en', primary=True, )
record.add_title(u'פרי עץ חיים', 'he', primary=True, )
record.key = 'Pri Etz Chaim'

# add nodes for each shaar
for index, title in enumerate(get_titles()):
    #first we make node for each shaar
    shaar_node = SchemaNode()
    shaar_node.add_title(english_titles[index], 'en', primary=True)
    shaar_node.add_title(title, 'he', primary=True)
    shaar_node.key = english_titles[index]
    
    #now we add introduction node to certain gates that have them
    #for Shaar Hatfila, index 0, and Shaar Rosh Hashana, index 23 there is a depth-one introduction
    if index==0 or index==23:
        intro_node = JaggedArrayNode()
        intro_node.add_title("Introduction", 'en', primary=True)
        intro_node.add_title("הקדמה", 'he', primary=True)
        intro_node.key = 'Introduction'
        intro_node.depth = 1
        intro_node.addressTypes = ['Integer']
        intro_node.sectionNames = ['Paragraph']
        shaar_node.append(intro_node)
    #Shaar Shabbos, index 17, has a depth-2 introduction
    if index ==17:
        intro_node = JaggedArrayNode()
        intro_node.add_title("Introduction", 'en', primary=True)
        intro_node.add_title("הקדמה", 'he', primary=True)
        intro_node.key = 'Introduction'
        intro_node.depth = 2
        intro_node.addressTypes = ['Integer', 'Integer']
        intro_node.sectionNames = ['Chapter','Paragraph']
        shaar_node.append(intro_node)
    #Shaar Kaddishim has an addition from Second Printing
    if index == 5:
        mb_node = JaggedArrayNode()
        mb_node.add_title("From Second Edition", 'en', primary=True)
        mb_node.add_title("מהדורא בתרא", 'he', primary=True)
        mb_node.key = 'From Second Edition'
        mb_node.depth = 1
        mb_node.addressTypes = ['Integer']
        mb_node.sectionNames = ['Paragraph']
        shaar_node.append(mb_node)
    #now we add text node
    text_node = JaggedArrayNode()
    text_node.key = "default"
    text_node.default = True
    text_node.depth = 2
    text_node.addressTypes = ['Integer', 'Integer']
    text_node.sectionNames = ['Chapter','Paragraph']
    shaar_node.append(text_node)
    
    #now we add this Shaar's node to the root node
    record.append(shaar_node)



record.validate()

index = {
    "title": "Pri Etz Chaim",
    "categories": ["Kabbalah"],
    "schema": record.serialize()
}
functions.post_index(index)
