# -*- coding: utf-8 -*-

import urllib
import urllib2
import json
import os
import re
import sys
from hebnum import *
from BeautifulSoup import BeautifulSoup


def soup(filename):
	f = open(filename, "r")
	page = f.read()
	f.close()
	return BeautifulSoup(page)


def parseIndex():
	s = soup("index.html")
	table = s.find("table", {"border": 8})
	trs = table.findAll("tr")	
	
	talmud = []
	links = {}
	
	
	f = open("names.json")
	names = json.load(f)
	f.close()
	
	talmudMap = {}
	
	for i in range(len(names)):
		talmudMap[names[i]["titleHe"]] = names[i]["title"]
		
	for i in range(2, len(trs)):
		tds = trs[i].findAll("td")
		for k in range(len(tds)):
			a = tds[k].findAll("a")
			if a:
				t = {}
				t["titleHe"] = a[0].string
				t["title"] = talmudMap[t["titleHe"]]
				talmud.append(t)
				links[t["title"]] = "http://he.wikisource.org%s" % (a[0]["href"])
										
	return links
	
def getIndexPages():
	links = parseIndex()
	
	for book in links:
		wikiGet(links[book], book.replace(" ", "_"))

def getDafLinks(name):
	s = soup("./pages/%s" % (name))
	td = s.find("td", {"align": "right"})	
	az = td.findAll("a")
	
	links = {}
	
	for i in range(len(az)):
		daf = (i + 4) / 2
		amud = "b" if (i%2) else "a"
		daf = str(daf) + amud
		links["%s.%s" % (name, daf)] = "http://he.wikisource.org%s" % (az[i]["href"])
			
	return links
			

def getDafs():
	ls = os.listdir("./pages")
	for filename in ls:
		if not "." in filename:
			links = getDafLinks(filename)
			for daf in links:
				wikiGet(links[daf], daf)
		

def parseDaf(filename):
	s = soup(filename)
	mishna = 0
	text = []
	g = s.find("div", "gmara_text")
	if not g:
		print "Parsing failed for %s (couldn't find gmara_text)" % (filename)	
		return
	p = g.findAll("p")
	if not p:
		print "Parsing failed for %s (couldn't find paragraphs in gmara_text)" % (filename)	
		return
	
	for i in range(len(p)):
		text.append(deepText(p[i]).encode("utf-8").strip())		

	parsed = {
		"language": "he",
		"versionTitle": "Wikisource Talmud Bavli",
		"versionUrl": "http://he.wikisource.org/wiki/%D7%AA%D7%9C%D7%9E%D7%95%D7%93_%D7%91%D7%91%D7%9C%D7%99",
	}
	
	parsed["text"] = text
	
	return parsed
	
def parseAll():
	ls = os.listdir("./pages")
	for filename in ls:
		if not "." in filename or filename == ".DS_Store": continue
		print filename
		parsed = parseDaf("pages/%s" % (filename))
		
		if parsed:
			f = open("parsed/%s" % (filename), "w")
			json.dump(parsed, f, ensure_ascii=False, indent=4)
			f.close()
			print "ok: found %d sections" % len(parsed["text"])
			
			
def deepText(element):

	if element.string:
		text = element.string.replace("\n", " ")
		return text
		
	text = ""
	
	for i in element:
		text += deepText(i)
	
	if "nextSibling" in element:	
		text += deepText(element.next)
		
	return text


def wikiGet(url, name):
	"""
	Takes a url and saves it to ./page/name
	"""

	ls = os.listdir("./pages")
	if name in ls:
		print "Already have %s" % (name)
		return
	print "Getting %s" % (name)
	opener = urllib2.build_opener()
	opener.addheaders = [('User-agent', 'Mozilla/5.0')]
	page = opener.open(url)

	print "Ok"
	f = open("./pages/%s" %(name), "w")
	f.write(page.read())
	f.close()



def getOrders():
	s = soup("index")
	table = s.find("table", {"align": "center"})
	trs = table.findAll("tr")
	
	seders = []
	for seder in trs[1].findAll("td"):
		seders.append(seder.find("a").string)		
	
	mishnas = {}
	
	for i in range(2, len(trs)):
		tds = trs[i].findAll("td")
		for k in range(len(tds)):
			a = tds[k].findAll("a")
			if a:
				mishnas["Mishna %s" % (a[0].string)] = {"seder": seders[k], "order": i-1}
	
	return mishnas

def sederSort(a,b):

	seders = ("Seder Zeraim", "Seder Moed", "Seder Nashim", "Seder Nezikin", "Seder Kodashim", "Seder Tahorot")

	sa = seders.index(a["categories"][1])
	sb = seders.index(b["categories"][1])

	if sa < sb: return -1
	if sb < sa: return 1
	
	if a["order"] < b["order"]: return -1
	if b["order"] < a["order"]: return 1
	
	return 0


def renameUp(name, start, end):
	for i in range(end, start, -1):
		os.rename("pages/%s.%da" % (name, i), "pages/%s.%da" % (name, i + 1))
		os.rename("pages/%s.%db" % (name, i), "pages/%s.%db" % (name, i + 1))

def checkDafs():
	f = open("talmud.json")
	talmud = json.load(f)
	f.close()
	
	files = os.listdir("pages")
	
	for t in talmud:
		correctNames(t["title"], t["length"])

def correctNames(name, length):
	for k in range(length, 1, -1):
		if name == "Tamid" and k == 25: return
		for am in ("a", "b"):
			try:
				s = soup("pages/%s.%d%s" % (name.replace(" ", "_"), k, am))
			except IOError:
				print "*** File missing %s.%d%s" % (name, k, am)
				continue	
			selflink = s.find("strong", "selflink")
			if not selflink:
				print "*** No self link found %s.%d%s" % (name, k, am)
				continue
			selflink = selflink.string 
			try: 
				amud = "a" if selflink[-1] == a2h(1) else "b"
				daf = h2a(selflink[:-2])
				if k != daf or am != amud:
					print "Renaming %s %d.%s to %d.%s" % (name, k, am, daf, amud)
					os.rename("pages/%s.%d%s" % (name.replace(" ", "_"), k, am), "pages/%s.%d%s" % (name.replace(" ", "_"), daf, amud))
			except KeyError:
				print "*** Numeral conversion failed for %s.%d%s" % (name, k, am)
						
def findMismatch(name, length):
	for k in range(2, length):
		for am in ("a", "b"):
			try:
				s = soup("pages/%s.%d%s" % (name.replace(" ", "_"), k, am))
			except IOError:
				print "*** File missing %s.%d%s" % (name, k, am)
				continue
			selflink = s.find("strong", "selflink")
			if not selflink:
				print "*** No self link found %s.%d%s" % (name, k, am)
				continue
			selflink = selflink.string 
			hebnum = "%s %s" % (a2h(k), a2h(1) if am == "a" else a2h(2))
			if not hebnum == selflink:
				print "*** Mismatch at %s.%d%s" % (name, k, am)
				return			

def checkTexts():
	files = os.listdir("./parsed")
	
	for f in files:
		if "." in f:
			sys.stdout.write(".")
			url = 'http://www.sefaria.org/texts/%s' % (f)
			response = urllib2.urlopen(url)
			data = json.load(response)
			
			try:
				if data["he"] == []:
					print ""
					postText(f)
			except KeyError:
				print "Key Error for %s" % f	
		

def postText(filename):
	f = open("./parsed/%s" % (filename), "r")
	textJSON = f.read()
	f.close()
	
	url = 'http://www.sefaria.org/texts/%s' % (filename)
	values = {'json': textJSON}
	data = urllib.urlencode(values)
	req = urllib2.Request(url, data)
	response = urllib2.urlopen(req)
	print "Posted %s" % (filename)
		

def postAll(prefix=None):
	files = os.listdir("./parsed")
	
	for f in files:
		if "." in f:
			if not prefix or f.startswith(prefix):
				parsed = postText(f)


