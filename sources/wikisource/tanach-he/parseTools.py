import urllib
import urllib2
import json
import os
from BeautifulSoup import BeautifulSoup


def parseChapter(name):
	f = open("./pages/%s" % (name), "r")
	page = f.read()
	f.close()
	
	soup = BeautifulSoup(page)
	
	pz = soup.findAll(style="font-size:60%;")
	
	f = open("./parsed/%s" % (name), "w")
	
	parsed = {
		"language": "he",
		"versionTitle": "Wikisource Tanach",
		"versionUrl": "http://he.wikisource.org/wiki/%D7%9E%D7%A7%D7%A8%D7%90",
		"text": []
	}
	
	for i in range(len(pz)): 
		line = pz[i].nextSibling.encode("utf-8").strip()
		parsed["text"].append(line)
	
	json.dump(parsed, f, ensure_ascii=False)
	f.close()
	
	return parsed

def parseLinks(seedfile):
	print "Getting links from %s" % (seedfile)
	f = open("./pages/%s" % (seedfile), "r")
	page = f.read()
	f.close()
	
	soup = BeautifulSoup(page)
	
	start = soup.findAll("strong", "selflink")
	if  len(start) < 2:
		print "No links found in %s" % (seedfile)
		return
	else:
		start = start[1]
	
	p = start.parent
	
	a = p.findAll("a")
	
	links = ["", ""]
	for link in a:
		links.append("http://he.wikisource.org" + link["href"])
		
	return links

def wikiGet(url, name):

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
	

def getAll():
	for seed in seeds:
		links = parseLinks("%s.1" % (seed))
		for i in range(2, len(links)):
			wikiGet(links[i], "%s.%d" % (seed, i))
		
def parseAll():
	files = os.listdir("./pages")
	
	for f in files:
		parsed = parseChapter(f)

def postAll(prefix=None):
	files = os.listdir("./parsed")
	
	for f in files:
		if not prefix or f.startswith(prefix):
			parsed = postText(f)


seeds = {
	"Amos": "http://he.wikisource.org/wiki/%D7%A2%D7%9E%D7%95%D7%A1_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Chronicles-1": "http://he.wikisource.org/wiki/%D7%93%D7%91%D7%A8%D7%99_%D7%94%D7%99%D7%9E%D7%99%D7%9D_%D7%90_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Chronicles-2": "http://he.wikisource.org/wiki/%D7%93%D7%91%D7%A8%D7%99_%D7%94%D7%99%D7%9E%D7%99%D7%9D_%D7%91_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Daniel": "http://he.wikisource.org/wiki/%D7%93%D7%A0%D7%99%D7%90%D7%9C_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Deuteronomy": "http://he.wikisource.org/wiki/%D7%93%D7%91%D7%A8%D7%99%D7%9D_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Ecclesiastes": "http://he.wikisource.org/wiki/%D7%A7%D7%94%D7%9C%D7%AA_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Esther": "http://he.wikisource.org/wiki/%D7%90%D7%A1%D7%AA%D7%A8_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Exodus": "http://he.wikisource.org/wiki/%D7%A9%D7%9E%D7%95%D7%AA_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Ezekiel": "http://he.wikisource.org/wiki/%D7%99%D7%97%D7%96%D7%A7%D7%90%D7%9C_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Ezra": "http://he.wikisource.org/wiki/%D7%A2%D7%96%D7%A8%D7%90_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Genesis": "http://he.wikisource.org/wiki/%D7%91%D7%A8%D7%90%D7%A9%D7%99%D7%AA_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Habakkuk": "http://he.wikisource.org/wiki/%D7%97%D7%91%D7%A7%D7%95%D7%A7_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Haggai": "http://he.wikisource.org/wiki/%D7%97%D7%92%D7%99_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Hosea": "http://he.wikisource.org/wiki/%D7%94%D7%95%D7%A9%D7%A2_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Isaiah": "http://he.wikisource.org/wiki/%D7%99%D7%A9%D7%A2%D7%99%D7%94%D7%95_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Jeremiah": "http://he.wikisource.org/wiki/%D7%99%D7%A8%D7%9E%D7%99%D7%94%D7%95_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Job": "http://he.wikisource.org/wiki/%D7%90%D7%99%D7%95%D7%91_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Joel": "http://he.wikisource.org/wiki/%D7%99%D7%95%D7%90%D7%9C_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Jonah": "http://he.wikisource.org/wiki/%D7%99%D7%95%D7%A0%D7%94_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Joshua": "http://he.wikisource.org/wiki/%D7%99%D7%94%D7%95%D7%A9%D7%A2_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Judges": "http://he.wikisource.org/wiki/%D7%A9%D7%95%D7%A4%D7%98%D7%99%D7%9D_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Kings-1": "http://he.wikisource.org/wiki/%D7%9E%D7%9C%D7%9B%D7%99%D7%9D_%D7%90_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Kings-2": "http://he.wikisource.org/wiki/%D7%9E%D7%9C%D7%9B%D7%99%D7%9D_%D7%91_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Lamentations": "http://he.wikisource.org/wiki/%D7%90%D7%99%D7%9B%D7%94_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Leviticus": "http://he.wikisource.org/wiki/%D7%95%D7%99%D7%A7%D7%A8%D7%90_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Malachi": "http://he.wikisource.org/wiki/%D7%9E%D7%9C%D7%90%D7%9B%D7%99_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Micah": "http://he.wikisource.org/wiki/%D7%9E%D7%99%D7%9B%D7%94_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Nahum": "http://he.wikisource.org/wiki/%D7%A0%D7%97%D7%95%D7%9D_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Nehemiah": "http://he.wikisource.org/wiki/%D7%A0%D7%97%D7%9E%D7%99%D7%94_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Numbers": "http://he.wikisource.org/wiki/%D7%91%D7%9E%D7%93%D7%91%D7%A8_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Obadiah": "http://he.wikisource.org/wiki/%D7%A2%D7%95%D7%91%D7%93%D7%99%D7%94_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Proverbs": "http://he.wikisource.org/wiki/%D7%9E%D7%A9%D7%9C%D7%99_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Psalms": "http://he.wikisource.org/wiki/%D7%AA%D7%94%D7%9C%D7%99%D7%9D_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Ruth": "http://he.wikisource.org/wiki/%D7%A8%D7%95%D7%AA_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Samuel-1": "http://he.wikisource.org/wiki/%D7%A9%D7%9E%D7%95%D7%90%D7%9C_%D7%90_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Samuel-2": "http://he.wikisource.org/wiki/%D7%A9%D7%9E%D7%95%D7%90%D7%9C_%D7%91_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Song-of-Songs": "http://he.wikisource.org/wiki/%D7%A9%D7%99%D7%A8_%D7%94%D7%A9%D7%99%D7%A8%D7%99%D7%9D_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Zechariah": "http://he.wikisource.org/wiki/%D7%96%D7%9B%D7%A8%D7%99%D7%94_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93",
	"Zephaniah": "http://he.wikisource.org/wiki/%D7%A6%D7%A4%D7%A0%D7%99%D7%94_%D7%90/%D7%A0%D7%99%D7%A7%D7%95%D7%93"

}
