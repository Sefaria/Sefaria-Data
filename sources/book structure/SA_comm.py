# -*- coding: utf-8 -*-
#put dh into SA_comm_text as bold
#deal with 

import pdb
import urllib
import urllib2
from urllib2 import URLError, HTTPError
from bs4 import BeautifulSoup
import json
import os
import sys

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

max = 3574
comm_file = "chelkat"
dh_file = "chelkat_dh"
title = "Chelkat Mechokek"
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

if os.path.exists(dh_file) == True:
	os.remove(dh_file)	
SA_comm = open(comm_file, "r")
SA_comm_text = []#open("SA_comm_text", "w")
SA_comm_dh = open(dh_file, "w")
error_file = open('errors', 'w')
prev_line_status = ""
prev_line = ""
count = 0
current_siman = -1
simanim_gematria = {} #key is current_siman, value is equivalent of hebrew gematria
						#at end, go through this, posting SA_comm_text[current_siman]
						#as the number which is the value of the hebrew gematria
current_line = ""
current_line_status = ""
for line in SA_comm:
	prev_line_status = current_line_status
	count+=1
	if count > 2 and count < max: #ignore first two lines of file and last two lines
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
			SA_comm_text[current_siman].append(text_to_append)
			SA_comm_dh.write(actual_dh)
			SA_comm_dh.write('\n')
		elif siman >= 0 and len_line == 3:
			current_line_status = 'siman'
			text_to_append = str(line)+"\n"
			SA_comm_text.append([])
			current_siman += 1
			simanim_gematria[current_siman] = gematriaFromSiman(line)
			SA_comm_dh.write(str(line))
			SA_comm_dh.write('\n')
		else:
			current_line_status = "neither"
			prev_line = line

SA_comm_dh.close()
error_file.close()		

		
intro_text = []
intro_file = open("beit_shmuel_addition_intro.txt", "r")
for line in intro_file:
	line = line.replace("\n", "")
	blank = line.replace(" ", "")
	if len(blank) > 0:
		intro_text.append(line)


men_text = []
men_file = open("beit_shmuel_addition_men.txt", "r")
for line in men_file:
	line = line.replace("\n", "")
	blank = line.replace(" ", "")
	if len(blank) > 0:
		men_text.append(line)
	
women_text = []
women_file = open("beit_shmuel_addition_women.txt", "r")
for line in women_file:
	line = line.replace("\n", "")
	blank = line.replace(" ", "")
	if len(blank) > 0:
		women_text.append(line)
	
rivers_text = []
rivers_file = open("beit_shmuel_addition_rivers.txt", "r")
for line in rivers_file:
	line = line.replace("\n", "")
	blank = line.replace(" ", "")
	if len(blank) > 0:
		rivers_text.append(line)
	
final_text = []
final_file = open("beit_shmuel_addition_final.txt", "r")
for line in final_file:
	line = line.replace("\n", "")
	blank = line.replace(" ", "")
	if len(blank) > 0:
		final_text.append(line)
intro_text = {
		"versionTitle": title,
		"versionSource": "http://www.worldcat.org/oclc/232883774",
		"language": "he",
		"text": intro_text,
		}
		
men_text = {
		"versionTitle": title,
		"versionSource": "http://www.worldcat.org/oclc/232883774",
		"language": "he",
		"text": men_text,
		}
		
women_text = {
		"versionTitle": title,
		"versionSource": "http://www.worldcat.org/oclc/232883774",
		"language": "he",
		"text": women_text,
		}

rivers_text = {
		"versionTitle": title,
		"versionSource": "http://www.worldcat.org/oclc/232883774",
		"language": "he",
		"text": rivers_text,
		}
final_text = {
		"versionTitle": title,
		"versionSource": "http://www.worldcat.org/oclc/232883774",
		"language": "he",
		"text": final_text,
		}

post_text(title + ", Introduction to Section on Names", intro_text)
post_text(title + ", Beit Shmuel on Names for Men", men_text)
post_text(title + ", Beit Shmuel on Names for Women", women_text)
post_text(title + ", Beit Shmuel on Names of Rivers", rivers_text)
post_text(title + ", Beit Shmuel on Names", final_text)


for key in simanim_gematria.keys():
	value = simanim_gematria[key]
	text = {
		"versionTitle": title,
		"versionSource": "http://www.worldcat.org/oclc/232883774",
		"language": "he",
		"text": SA_comm_text[key],
		}
	try:
		post_text(title + " "+str(value+1), text)
	except:
		pdb.set_trace()
		



