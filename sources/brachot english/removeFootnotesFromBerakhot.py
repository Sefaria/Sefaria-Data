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


def post_text(ref, text):
    textJSON = json.dumps(text)
    ref = ref.replace(" ", "_")
    url = SEFARIA_SERVER+'/api/texts/'+ref
    values = {'json': textJSON, 'apikey': API_KEY}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        print response.read()
    except HTTPError, e:
        print 'Error code: ', e.code
        print e.read()

def get_text(ref):
 	ref = ref.replace(" ", "_")
 	url = SEFARIA_SERVER+'/api/texts/'+ref
 	req = urllib2.Request(url)
 	try:
 		response = urllib2.urlopen(req)
 		data = json.load(response)
 		return data
 	except: 
 		return 'Error'
 		
 		
for i in range(124):
	j = i + 3
	text = get_text("Berakhot."+AddressTalmud.toStr("en", j))['text']
	new_lines = []
	for line_n, line in enumerate(text):
		new_lines.append(re.sub(r'\[\d+\]', r'', line))
	send_text = {
				"versionTitle": "Tractate Berakot by A. Cohen, Cambridge University Press, 1921",
				"versionSource": "https://he.wikisource.org/wiki/תלמוד_בבלי",
				"language": "en",
				"text": new_lines,
				}
	post_text("Berakhot."+AddressTalmud.toStr("en", j), send_text)
