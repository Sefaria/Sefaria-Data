# -*- coding: utf-8 -*-

import string
import json
import re
import urllib
import urllib2
import os
import local_settings

def numToHeb(engnum=""):
	engnum = str(engnum)
	numdig = len(engnum)
	hebnum = ""
	letters = [["" for i in range(3)] for j in range(10)]
	letters[0]=["", "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"]
	letters[1]=["", "י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ"]
	letters[2]=["", "ק", "ר", "ש", "ת", "תק", "תר", "תש", "תת", "תתק"]
	if (numdig > 3):
		print "We currently can't handle numbers larger than 999"
		exit()
	for count in range(numdig):
		hebnum += letters[numdig-count-1][int(engnum[count])]
	hebnum = re.sub('יה', 'טו', hebnum)
	hebnum = re.sub('יו', 'טז', hebnum)
	return hebnum

def unescape(s):
	s = s.replace("&lt;", "<")
	s = s.replace("&gt;", ">")
	s = s.replace("&quot;", "\"")
	s = s.replace("&amp;", "&")
	return s

def wikiGet(url, name):
	"""
	Takes a url and saves it to ./page/name
	"""

	ls = os.listdir("./pages")
	if name in ls:
		print "Already have %s" % (name)
		return
	print "Getting %s" % (name)
	
	request = urllib2.Request(url)
	request.add_header("User-Agent", "Ari Hebrew book grabber 1.0 ari@elias-bachrach.com") #wikimedia said to do this
	request.add_header("Host", "he.wikisource.org")
	request.add_header("Accept", "text/html,text/json")
	resp = urllib2.urlopen(request)

	f = open("./pages/%s" %(name), "w")
	f.write(resp.read())
	f.close()

def postText(filename):
	print 'now doing %s' % (filename)
	f = open("./parsed/%s" % (filename), "r")
	textJSON = f.read()
	f.close()
	errorLog = open("ERROR_LOG", "w")	
	url = 'http://dev.sefaria.org/api/texts/%s?count_after=0&index_after=0' % (filename)
	values = {'json': textJSON, 'apikey': local_settings.apikey}
	data = urllib.urlencode(values)
	req = urllib2.Request(url, data)
	try:
		response = urllib2.urlopen(req)
		#print response.read()
		if ("error" in response.read()):
			print "error occured - check log"
			errorLog.write(filename)
			errorLog.write(response.read())
	except urllib2.HTTPError, e:
		print "error occured - check log"
		errorLog.write(filename)
		errorLog.write('Error code: '+str(e.code))
		errorLog.write(e.read())
	errorLog.close()

def parse(filename):
	print filename
	f = open("%s" % (filename), "r")
	rawtext = f.read()
	f.close()
	finaltext = []

	rawtext = unescape(rawtext)	
	#remove header - find first </h3>
	rawtext = re.sub(re.compile('^.*?</h3>', re.DOTALL), '', rawtext)
	#remove footer
	rawtext = re.sub('<\/extract><\/page>.*', '', rawtext)
	#remove all line breaks
	rawtext = re.sub('\n', '', rawtext)
	#remove useless html
	'''
	Someone will I'm sure be wondering why on earth I've decided to remove HTML in
	this piecemeal fashion instead of using the single line here. The reason is
 	that I've found that many people like to add "fancy" things to wikisource
	like indexes, links to related documents, etc. While they're very nice, the only
	thing we want here in sefaria is the text. Lots of HTML is usually an indicator
	of someone having added one of these "fancy" things. Because I want to remove
	these things (when they occur), I only strip out the basic html that indicates
	minor formatting. Once I'm done parsing I manually grep through all the files for
	more HTML so I can find (and remove) other things people have added to the text 
	that we don't want.
	'''
	rawtext = re.sub('</?p>', '', rawtext)
	rawtext = re.sub('</?dd>', '', rawtext)
	rawtext = re.sub('</?dl>', '', rawtext)
	rawtext = re.sub('</?li?>', '', rawtext)
	rawtext = re.sub('</?[uo]l>', '', rawtext)
	rawtext = re.sub('</?font.*?>', '', rawtext)
	rawtext = re.sub('</?small>', '', rawtext)
	rawtext = re.sub('</?center>', '', rawtext)
	rawtext = re.sub('</?big>', '', rawtext)
	rawtext = re.sub('</?strong(\  class=\"selflink\")?>', '', rawtext)
	rawtext = re.sub('</?br?>', '', rawtext) #<b> and <br>
	#rawtext = re.sub('<.*?>', rawtext) # more forceful 
	#split into seifim
	p = re.compile('<h3>.*?</h3>', re.U)
	finaltext = p.split(rawtext)
	#print "found this many seifim: "+str(len(finaltext))

	parsed = {
		"versionTitle": "Wikisource Aruch HaShulchan",
		"versionSource": "http://he.wikisource.org/wiki/%D7%A2%D7%A8%D7%95%D7%9A_%D7%94%D7%A9%D7%95%D7%9C%D7%97%D7%9F_%D7%90%D7%95%D7%A8%D7%97_%D7%97%D7%99%D7%99%D7%9D",
		"heversionSource": "http://he.wikisource.org/wiki/%D7%A2%D7%A8%D7%95%D7%9A_%D7%94%D7%A9%D7%95%D7%9C%D7%97%D7%9F_%D7%90%D7%95%D7%A8%D7%97_%D7%97%D7%99%D7%99%D7%9D",
		"versionUrl": "http://he.wikisource.org/wiki/%D7%A2%D7%A8%D7%95%D7%9A_%D7%94%D7%A9%D7%95%D7%9C%D7%97%D7%9F",
	}
	#print rawtext
	parsed["language"] = "he"
	parsed["text"] = finaltext
	return parsed

def parseAll():
	ls = os.listdir("./pages")
	for filename in ls:
		#print filename
		#if not "." in filename or filename == ".DS_Store": continue
		parsed = parse("pages/%s" % (filename))
		
		if parsed:
			f = open("parsed/%s" % (filename), "w")
			json.dump(parsed, f, ensure_ascii=False, indent=4)
			f.close()
			#print "ok: found %d seifim" % len(parsed["text"])
		else:
			print "we had a problem with %s" % (filename)

def postAll(prefix=None):
	files = os.listdir("./parsed")
	total = len(files)
	filenum = 1 # progress counter
	for f in files:
		if "." in f:
			if not prefix or f.startswith(prefix):
				print "now starting file %d " % (filenum)
				parsed = postText(f)
				filenum += 1
		

