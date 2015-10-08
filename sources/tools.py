import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json

ak = ''

index = {
	"title": "Sefer Ploni",
	"titleVariants": ["Sefer Ploni", "The Book of Someone"],
	"sectionNames": ["Chapter", "Paragraph"],
	"categories": ["Musar"],
}

def post_index(index):
	url = 'http://localhost:8000/api/index/' + index["title"].replace(" ", "_")
	indexJSON = json.dumps(index)
	values = {
		'json': indexJSON, 
		'apikey': ak
	}
	data = urllib.urlencode(values)
	req = urllib2.Request(url, data)
	try:
		response = urllib2.urlopen(req)
		print response.read()
	except HTTPError, e:
		print 'Error code: ', e.code

post_index(index)

text = {
	"versionTitle": "Example Sefer Ploni",
	"versionSource": "http://www.example.com/Sefer_Ploni",
	"language": "en",
	"text": [
		"Paragrpah 1",
		"Paragraph 2",
		"Paragraph 3"
	]
}

def post_text(ref, text):
	textJSON = json.dumps(text)
	ref = ref.replace(" ", "_")
	url = 'http://localhost:8000/api/texts/%s' % ref
	values = {'json': textJSON, 'apikey': ak}
	data = urllib.urlencode(values)
	req = urllib2.Request(url, data)
	try:
		response = urllib2.urlopen(req)
		print response.read()
	except HTTPError, e:
		print 'Error code: ', e.code
		print e.read()

post_text("Sefer Ploni 5", text)
