# -*- coding: utf-8 -*-

import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
import os
import re
import array
from bs4 import BeautifulSoup

def soup(filename):
        f = open(filename, "r")
        page = f.read()
        f.close()
        return BeautifulSoup(page)

def preprocess(filekey):
	linesout = []
	with open("source/" + filekey + ".html", 'rt') as lines:
		for line in lines:
			linesout.append(line)
			if '<body lang=EN-US' in line:
				 break;
		for line in lines:
			if "BODY_START" in line:
				linesout.append(line)
				break;
		for line in lines:
			linesout.append(line)
	
	with open("preprocess/" + filekey + ".html", 'wt') as out:
		out.writelines(linesout)

def parseText(filekey, ref, display=False):
	text = []
	chapter = []
	current_chapter = '' 
	s = soup("preprocess/" + filekey + ".html")
	pattern = re.compile("(.*)B(.*)-(.*)-{(.*)}")
	for a in s.find_all("a", attrs={"name":pattern}):
		match = re.match(pattern, a['name'])
		if match:
			book = match.group(1)
			chapter_num = match.group(3)
			verse = match.group(4)		
		pasuk = a.next_sibling.next_sibling.strip().strip(':')
		if(display):
			print book, chapter_num, verse, pasuk
		if not current_chapter:
			current_chapter = chapter_num
			
		if current_chapter != chapter_num:
			text.append(chapter)
			chapter = [] 
			current_chapter = chapter_num
			
		chapter.append(pasuk)
	text.append(chapter)
	
	text_whole = {
		"versionTitle": ref,
		"versionSource": "http://toratemetfreeware.com/",
		"language": "he",
		"text": text,
	}	
		
	f = open("json/" + ref + ".json", "w")
	json.dump(text_whole, f)
	return text_whole

def createBookRecord(server, apikey, ref, variant, category, oldTitle=''):
	index = {
		"title": ref,
		"titleVariants": [ref, variant],
		"sectionNames": ["Chapter", "Verse"],
		"categories": [category],
	}

	if(oldTitle):
		index['oldTitle'] = oldTitle

	url = 'http://' + server + '/api/index/' + index["title"].replace(" ", "_")
	indexJSON = json.dumps(index)
	values = {
		'json': indexJSON, 
		'apikey': apikey
	}
	data = urllib.urlencode(values)
	print url, data
	req = urllib2.Request(url, data)
	try:
		response = urllib2.urlopen(req)
		print response.read()
	except HTTPError, e:
		print 'Error code: ', e.code



def postText(server, apikey, ref, text):
	textJSON = json.dumps(text)
	ref = ref.replace(" ", "_")
	url = 'http://' + server + '/api/texts/%s?count_after=0&index_after=0' % ref
	print url
	values = {
		'json': textJSON, 
		'apikey': apikey
	}
	data = urllib.urlencode(values)
	req = urllib2.Request(url, data)
	try:
		response = urllib2.urlopen(req)
		print response.read()
	except HTTPError, e:
		print 'Error code: ', e.code
		print e.read()
		
