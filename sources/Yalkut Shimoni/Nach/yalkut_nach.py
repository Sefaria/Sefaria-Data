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
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)

from sefaria.model import *

gematria = {}
gematria['א'] = 1
gematria['ב'] = 2
gematria['ג'] = 3
gematria['ד'] = 4
gematria['ה'] = 5
gematria['ו'] = 6
gematria['ז'] = 7
gematria['ח'] = 8
gematria['ט'] = 9
gematria['י'] = 10
gematria['כ'] = 20
gematria['ל'] = 30
gematria['מ'] = 40
gematria['נ'] = 50
gematria['ס'] = 60
gematria['ע'] = 70
gematria['פ'] = 80
gematria['צ'] = 90
gematria['ק'] = 100
gematria['ר'] = 200
gematria['ש'] = 300
gematria['ת'] = 400


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

def gematriaFromSiman(line):
	arr = line.split(" ")
	txt = arr[len(arr)-1]
	index=0
	sum=0
	while index <= len(txt)-1:
		if txt[index:index+2] in gematria:
			sum += gematria[txt[index:index+2]]
		index+=1
	return sum


whichYalkut = "Yalkut Shimoni on Nach" #as opposed to "Yalkut Shimoni on Nach"


parsha = ""

parsha = str(sys.argv[1])
if len(sys.argv) > 2:
	parsha += " "+sys.argv[2]
parshiot = [parsha]

#each time we find a new perek, we record the current remez and current paragraph

current_perek = 1
current_remez = 596
prev_perek = 1
prev_remez = current_remez
text=[]
para_n = 0
prev_parsha = ""
last_log = ""
if os.path.exists("perek_"+parsha+".txt") == True:
	os.remove("perek_"+parsha+".txt")	
perek_file = open('perek_'+parsha+'.txt', 'w')
if os.path.exists("parsha_"+parsha+".txt") == True:
	os.remove("parsha_"+parsha+".txt")
parsha_file = open("parsha_"+parsha+".txt", 'w')
prev_line = ""
perek_file.write(str(current_perek)+","+str(current_remez)+","+str(para_n+1)+"\n")
last_file = len(parshiot)-1
for parsha_count, parsha in enumerate(parshiot):
	first_line = True
	f = open(parsha+".txt", "r")
	for line in f:
		line = line.replace("\n", "")
		nothing = line.replace(" ", "")
		if len(nothing) > 0:
			header = max(line.find("H1"), line.find("h1"))
			if header >= 0:
				continuation = line.find("המשך")
				line = line.replace("המשך", "")
				line = line.replace("</H1>", "")
				line = line.replace("</h1>", "")
				h1_start = re.compile('<h1.*?>')
				match = re.search(h1_start, line)
				while match:
					text_to_replace = match.group(0)
					line = line.replace(text_to_replace, '')
					match = re.search(h1_start, line)
				H1_start = re.compile('<H1.*?>')
				match = re.search(H1_start, line)
				while match:
					text_to_replace = match.group(0)
					line = line.replace(text_to_replace, '')
					match = re.search(H1_start, line)
				book = line.split(" - ")[0]
				perek = line.split(" - ")[1]
				remez = line.split(" - ")[2]
				current_remez = gematriaFromSiman(remez)
				current_perek = gematriaFromSiman(perek)
				new_perek = False
				if prev_perek != current_perek:
					perek_file.write(str(prev_perek)+","+str(prev_remez) + ","+str(para_n)+"\n") 
					new_perek = True
				prev_perek = current_perek
				if continuation >= 0:
					if first_line == True:
						parsha_file.write(parsha+","+str(current_remez)+","+str(para_n+1)+"\n")
						first_line=False
					if new_perek:
						perek_file.write(str(current_perek)+","+str(current_remez)+","+str(para_n+1)+"\n")
					continuation = -1
					continue
				if first_line == True:
					parsha_file.write(parsha+","+str(current_remez)+",1\n")
					first_line=False
				if new_perek:
					perek_file.write(str(current_perek)+","+str(current_remez)+",1\n")
				if len(text)>0:
					send_text = {
					"versionTitle": whichYalkut,
					"versionSource": "http://www.tsel.org/torah/yalkutsh/",
					"language": "he",
					"text": text,
					}
					post_text(whichYalkut+"."+str(prev_remez), send_text)	
					text = []	
					para_n = 0
				prev_remez = current_remez
				prev_parsha = parsha
				new_perek = False
				prev_line = line
			else:
				if first_line == True:
					parsha_file.write(parsha+","+str(current_remez)+","+str(para_n+1)+"\n")
					first_line = False
				if line.find("<P>")>=0 and line.find("</P>")>=0:
					line = line.replace("<P>", "")
					line = line.replace("</P>", "")
				text.append(line)
				para_n += 1
				prev_line = line
				


	last_log = str(current_perek)+","+str(current_remez)+","+str(para_n)+"\n"
	if last_file==parsha_count:
		send_text = {
					"versionTitle": whichYalkut,
					"versionSource": "http://www.tsel.org/torah/yalkutsh/",
					"language": "he",
					"text": text,
					}
		post_text(whichYalkut+"."+str(prev_remez), send_text)
		perek_file.write(last_log)
	parsha_file.write(parsha+","+str(current_remez)+","+str(para_n)+"\n")
perek_file.close()
parsha_file.close()
