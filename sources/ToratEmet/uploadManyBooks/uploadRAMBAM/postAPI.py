import urllib.request
from urllib.parse import urlencode
from urllib.error import HTTPError,URLError
import json
import urllib

from local_settings import apikey

def post_index(index, useRealSite = False, actuallyPost = False, postBookIndex = True):
	if not postBookIndex:
		return;

	if useRealSite:
		siteType = "www.";
	else:
		siteType = "dev.";
	url = 'http://' + siteType + 'sefaria.org/api/index/' + index["title"].replace(" ", "_")
	
	indexJSON = json.dumps(index)
	values = {
			'json': indexJSON,
			'apikey': apikey,
			
	}
	
	data = urlencode(values)
	data = data.encode('utf-8')
	
	print(url);
	if not actuallyPost:
		return;
		

	try:
		response = urllib.request.urlopen(url, data)
	except HTTPError as e:
		print('Error code: ', e.code)

		
def postTorah(ref, text, textIndex, useRealSite = False, setCountTo0 = True, actuallyPost = False):
	
	if useRealSite:
		siteType = "www.";
	else:
		siteType = "dev.";
		
	ref = ref.replace(" ", "_")
	if setCountTo0:
		additionalURL = '?count_after=0&index_after=0';
		countTrueStr = ""
	else:
		additionalURL = '' #'?index_after=0';
		countTrueStr = 'COUNT-TRUE'

		
	url = 'http://' + siteType + ('sefaria.org/api/texts/%s'  % ref) + additionalURL;
	
	
	if not actuallyPost:
		print(ref, countTrueStr)
		return
	else:
		print(siteType, ref, countTrueStr)
	textIndex['text'] = text;
	indexJSON = json.dumps(textIndex)
	values = {
			'json': indexJSON,
			'apikey': apikey,
			
	}

	data = urlencode(values)
	data = data.encode('utf-8')
	
	try:
			response = urllib.request.urlopen(url, data)
	except HTTPError as e:
			print('Error code: ', e.code)
			
	if not setCountTo0:
		print(response);
		

def postLink(link_obj, useRealSite = False, serializeText = True):
	if useRealSite:
		url = 'http://' + "www.sefaria.org" + '/api/links/'
	else:
		url = 'http://' + "dev.sefaria.org" + '/api/links/'
	if serializeText:
		textJSON = json.dumps(link_obj)
	else:
		textJSON = link_obj
	values = {
		'json': textJSON,
		'apikey': apikey
		}
	data = urlencode(values)
	data = data.encode('utf-8')

	req = urllib.request.urlopen(url, data)
		

def createSingleLink(source1, source2):
    return {
		"refs": [
			source1,
			source2 ],
		"type": "Commentary",
		"auto": True,
		"generated_by": "Torat_Emet_uploader",
		}
			
"""
Sample use:
if __name__ == '__main__':
	links = []
	source1 = "Sefer_haArouch.1.1"
	source2 = "The_Jastrow_Dictionary.1.1"
	links.append(createSingleLink(source1, source2))
	postLink(links)
"""
