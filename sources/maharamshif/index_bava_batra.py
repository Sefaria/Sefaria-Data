# -*- coding: utf-8 -*-
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json 
import pdb
import os
import sys
from bs4 import BeautifulSoup
import re
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from sources.functions import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud	


root=JaggedArrayNode()
root.add_title(u"Maharam Shif on Eruvin", "en", primary=True)
root.add_title(u'מהר"ם שיף על ערובין', "he", primary=True)
root.key = 'maharam'
root.sectionNames = ["Daf", "Comment"]
root.depth = 2
root.addressTypes = ["Talmud", "Integer"]



root.validate()
index = {
    "title": "Maharam Shif on Eruvin",
    "categories": ["Talmud", "Bavli", "Commentary", "Maharam Shif", "Seder Moed"],
    "schema": root.serialize(),
    "dependence": "Commentary",
    "collective_title": "Maharam Shif",
    "base_text_titles": ["Eruvin"]
}

post_index(index, server=SEFARIA_SERVER)



root=JaggedArrayNode()
root.add_title(u"Maharam Shif on Rosh Hashanah", "en", primary=True)
root.add_title(u'מהר"ם שיף על ראש השנה', "he", primary=True)
root.key = 'maharam'
root.sectionNames = ["Daf", "Comment"]
root.depth = 2
root.addressTypes = ["Talmud", "Integer"]



root.validate()
index = {
    "title": "Maharam Shif on Rosh Hashanah",
    "categories": ["Talmud", "Bavli", "Commentary", "Maharam Shif", "Seder Moed"],
    "schema": root.serialize(),
    "dependence": "Commentary",
    "collective_title": "Maharam Shif",
    "base_text_titles": ["Rosh Hashanah"]
}

post_index(index, server=SEFARIA_SERVER)


root = JaggedArrayNode()
root.add_title(u"Chidushei Agadot on Tamid", "en", primary=True)
root.add_title(u'חידושי אגדות על תמיד', "he", primary=True)
root.key = 'chidushei_agadot'
root.sectionNames = ["Daf", "Comment"]
root.depth = 2
root.addressTypes = ["Talmud", "Integer"]



root.validate()
index = {
    "title": "Chidushei Agadot on Tamid",
    "categories": ["Talmud", "Bavli", "Commentary", "Chidushei Agadot", "Seder Kodashim"],
    "schema": root.serialize(),
    "dependence": "Commentary",
    "collective_title": "Chidushei Agadot",
    "base_text_titles": ["Tamid"]
}

post_index(index, server=SEFARIA_SERVER)



root=JaggedArrayNode()
root.add_title(u"Chidushei Agadot on Meilah", "en", primary=True)
root.add_title(u'חידושי אגדות על מעילה', "he", primary=True)
root.key = 'chidushei_agadot'
root.sectionNames = ["Daf", "Comment"]
root.depth = 2
root.addressTypes = ["Talmud", "Integer"]



root.validate()
index = {
    "title": "Chidushei Agadot on Meilah",
    "categories": ["Talmud", "Bavli", "Commentary", "Chidushei Agadot", "Seder Kodashim"],
    "schema": root.serialize(),
    "dependence": "Commentary",
    "collective_title": "Chidushei Agadot",
    "base_text_titles": ["Meilah"]
}

post_index(index, server=SEFARIA_SERVER)


