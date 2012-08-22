import urllib
import urllib2
from urllib2 import URLError, HTTPError
import os	

def post_text(filename):
	f = open("./json/%s" % filename, "r")
	textJSON = f.read()
	f.close()
	ref = filename[:-4].title().replace(" Of ", " of ").replace(" ", "_")
	print "Posting %s" % ref
	url = 'http://www.sefaria.org/api/texts/%s' % ref
	values = {'json': textJSON, 'apikey': 'yourapikey'}
	data = urllib.urlencode(values)
	req = urllib2.Request(url, data)
	try:
		response = urllib2.urlopen(req)
	except HTTPError, e:
		print 'Error code: ', e.code
		print e.read()
	print "Posted %s" % (ref)
		

def post_all(prefix=None):
	files = os.listdir("./json")
	
	for f in files:
		if f.startswith("."):
			continue
		if not prefix or f.startswith(prefix):
			post_text(f)
