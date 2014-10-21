# -*- coding: utf-8 -*-

import string
import json
import re
import urllib
import urllib2
import os
import local_settings

def postText(filename):
	print 'now doing %s' % (filename)
	f = open("parsed/%s" % (filename), "r")
	textJSON = f.read()
	f.close()
	errorLog = open("ERROR_LOG", "w")	
	url = 'http://www.sefaria.org/api/texts/%s?count_after=0&index_after=0' % (filename)
	values = {'json': textJSON, 'apikey': local_settings.apikey}
	data = urllib.urlencode(values)
	req = urllib2.Request(url, data)
	try:
		response = urllib2.urlopen(req)
		print "response is " + response.read()
		if ("error" in response.read()):
			print "error occured - check log"
			errorLog.append("error occured - check log")
			errorLog.append(filename)
			errorLog.append(response.read())
			print response.read()
	except urllib2.HTTPError, e:
		print "error occured - check log X"
		#errorLog.write(filename)
		#errorLog.write('Error code: '+str(e.code))
		#errorLog.write(e.read())
		print e.read()
	#errorLog.close()

def parse(filename):
	print "parsing" +filename
	f = open("%s" % (filename), "r")
	intext = f.read()
	f.close()

	intext = re.sub('<title>.*</title>', '', intext)
	intext = re.sub('\n', '', intext)
	
	ss = re.split('<line>\d*</line>', intext)

	n = len(ss)
	finaltext = [["" for x in xrange(15)] for x in xrange(n-1)]
	for i in range (0, n):
		if ss[i]:
			block = ss[i]
			block = re.sub('<bold>', '<b>', block)  #DBH
			block = re.sub('</bold>', '</b> - ', block) #DBH
			block = re.sub('<text>', '', block) #continue
			block = block.rstrip('</text>')
			qwert = re.split('</text>', block) #end of comment
			finaltext[i-1] = qwert

	parsed = {
		"versionTitle": "R. David Kimhi on the first book of Psalms, Translated by R.G. Finch, London, 1919",
		"versionSource": "http://www.worldcat.org/title/longer-commentary-on-the-first-book-of-psalms-i-x-xv-xvii-xix-xxii-xxiv/oclc/3364330",
		"versionUrl": "http://www.worldcat.org/title/longer-commentary-on-the-first-book-of-psalms-i-x-xv-xvii-xix-xxii-xxiv/oclc/3364330",
	}
	#print finaltext
	parsed["language"] = "en"
	parsed["text"] = finaltext
	return parsed

def parseAll():
	ls = os.listdir("./text")
	for filename in ls:
		#print filename
		parsed = parse("text/%s" % (filename))
		
		if parsed:
			f = open("parsed/Radak_on_%s" % (filename), "w")
			json.dump(parsed, f, ensure_ascii=False, indent=4)
			f.close()
		else:
			print "we had a problem with %s" % (filename)

def postAll(prefix=None):
	files = os.listdir("./parsed")
	total = len(files)
	filenum = 1 # progress counter
	for f in files:
		if "." in f:
			if not prefix or f.startswith(prefix):
				print "now posting file %d " % (filenum)
				parsed = postText(f)
				filenum += 1
		

parseAll()
postAll()
