# -*- coding: utf-8 -*-
#put dh into magen_text as bold
#deal with 

import pdb
import urllib
import urllib2
from urllib2 import URLError, HTTPError
from bs4 import BeautifulSoup
import json

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
    url = 'http://dev.sefaria.org/api/texts/'+ref
    values = {'json': textJSON, 'apikey': 'F4J2j3RF6fHWHLtmAtOTeZHE3MOIcsgvcgtYSwMzHtM'}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        print response.read()
    except HTTPError, e:
        print 'Error code: ', e.code
        print e.read()

def gematriaFromSiman(line):
	txt = line.split(" ")[1]
	index=0
	sum=0
	while index <= len(txt)-1:
		if txt[index:index+2] in gematria:
			sum += gematria[txt[index:index+2]]
		index+=1
	return sum-1 #adjust for fact that array starts at 0

def lineIntoDH(line):
	actual_dh = ""
	dh_and_comm = line.split(" - ")
	dh = dh_and_comm[0]
	comm = dh_and_comm[1]
	dh = dh.replace("""(פמ"ג)""", "")
	dh = dh.replace("""(מחה"ש)""", "")
	dh_array = dh.split(" ")
	for i in range(len(dh_array)):
		if i == len(dh_array)-1: #don't want to add an extra space 
			actual_dh += dh_array[i]
		elif i >= 1 and len(dh_array[i])>0:  #first option removes initial letter of seif and second option gets rid of emtpy spaces
			actual_dh += dh_array[i] + " "
	return comm, actual_dh

new_magen = open("new_magen", "r")
magen_text = []#open("magen_text", "w")
magen_dh = open("magen_dh", "w")
error_file = open('errors', 'w')
prev_line_status = ""
prev_line = ""
count = 0
current_siman = -1
simanim_gematria = {} #key is current_siman, value is equivalent of hebrew gematria
						#at end, go through this, posting magen_text[current_siman]
						#as the number which is the value of the hebrew gematria
current_line = ""
current_line_status = ""
for line in new_magen:
	prev_line_status = current_line_status
	count+=1
	if count > 2 and count < 7239: #ignore first two lines of file and last two lines
		siman = line.find("סימן") 
		len_line = len(line.split(" "))
		seif = line.find(" - ")
		if seif >= 0:
			if siman >= 0 and len_line < 5:
				error_file.write(str(line))
				error_file.write('\n')
			current_line_status = 'seif'
			comm, actual_dh = lineIntoDH(line)
			text_to_append = ""
			if prev_line_status == "neither": #prev line was a description of siman, not a seif
				print prev_line
				text_to_append = prev_line + "<br><b>" + str(actual_dh) + "</b>. "+str(comm)+"\n"
			else:
				text_to_append = "<b>" + str(actual_dh) + "</b>. "+str(comm)+"\n"
			magen_text[current_siman].append(text_to_append)
			magen_dh.write(actual_dh)
			magen_dh.write('\n')
		elif siman >= 0 and len_line == 3:
			current_line_status = 'siman'
			text_to_append = str(line)+"\n"
			magen_text.append([])
			current_siman += 1
			simanim_gematria[current_siman] = gematriaFromSiman(line)
			magen_dh.write(str(line))
			magen_dh.write('\n')
		else:
			current_line_status = "neither"
			prev_line = line

magen_dh.close()
error_file.close()		

#pdb.set_trace()

for key in simanim_gematria.keys():
	value = simanim_gematria[key]
	text = {
		"versionTitle": "Magen Avraham",
		"versionSource": "http://www.worldcat.org/oclc/232883774",
		"language": "he",
		"text": magen_text[key],
		}
	try:
		post_text("Magen Avraham "+str(value+1), text)
	except:
		pdb.set_trace()


