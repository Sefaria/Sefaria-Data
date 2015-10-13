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

sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud	


root=JaggedArrayNode()
root.add_title(u"Abraham Cohen Footnotes on the English Translation of Masechet Berakhot", "en", primary=True)
root.add_title(u"הערות באנגלית של אברהם כהן על מסכת ברכות", "he", primary=True)
root.key = 'abrahamcohen'
root.sectionNames = ["Comment"]
root.depth = 1
root.addressTypes = ["Integer"]



root.validate()

index = {
    "title": "Abraham Cohen Footnotes on the English Translation of Masechet Berakhot",
    "categories": ["Modern Works"],
    "schema": root.serialize()
}

Index(index).save()
post_index(index)

