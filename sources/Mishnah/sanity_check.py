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
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.insert(0, '../Match/')
from match import Match
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *
import glob

sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud


#checked Mishnayot for Pereks being in order and within each perek each comment is in order
#checked Boaz for Pereks being in order but DID NOT check that each comment within each perek is in order

# dont_count=['פ"', 'פרק ', 'בבא','פ', 'מעשר', 'פתח']

count=0
for file in glob.glob(u"*.txt"):
    file = file.replace(u"\u200f", u"")
    if file.split(" ")[0] == u"משניות":
        count += 1
        print file
        in_order(file, tag="@22", reset_tag="@00", increment_by=1)
