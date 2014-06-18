# -*- coding: utf-8 -*-

import sys
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
import xml.etree.ElementTree as ET
import pprint

apikey = 'any-string-for-your-key' #Add your API key
server = 'localhost:8000'


def getKnownTexts():
	url = 'http://www.sefaria.org/api/index'
	try:
		response = urllib2.urlopen(url)
		resp = response.read()
		return json.loads(resp)
	except HTTPError, e:
		print 'Error code: ', e.code


#returns a dict of hebrew titles to english titles from the sefaria library
def build_title_map(top_category, key_str, value_str):
	texts = getKnownTexts()
	books_map = {}
	retval = None
	# find the first level corpus we are parsing (e.g. the Mishna)
	for elem in texts:
		if elem['category'] == top_category:
			retval = elem
			break
	flatten_by_keyvalue(books_map, retval, 'contents', True, key_str, value_str)
	return books_map

#flattens sefaria JSON to a dict with only a key value pair
def flatten_by_keyvalue(target_dict, origin_dict, child_name, iterate_over_child, key_str, value_str):
	if key_str in origin_dict:
		#some of the sefaria titles are prefixed with the word "Mishnah" in hebrew, get rid of it
		#this should probably be moved to a more generic place in the code.
		trim_key = origin_dict[key_str].replace(u'משנה', '').strip()
		#print "type of raw: ", type(origin_dict[key_str]), type(trim_key)
		#print "type of encoded ", type(trim_key.encode('utf-8'))
		target_dict[trim_key] = origin_dict[value_str]
	#if the child struct is in an array
	elif iterate_over_child:
		for sub_dict in origin_dict[child_name]:
			flatten_by_keyvalue(target_dict, sub_dict, child_name, iterate_over_child, key_str, value_str)
	#not really used yet
	else:
		flatten_by_keyvalue(target_dict, origin_dict[child_name], child_name, iterate_over_child, key_str, value_str)



def createBookRecord(book_obj, oldTitle=''):
	update_record = False
	#first see if this book exists already, if so we will need to update it.
	"""url = 'http://www.sefaria.org/api/index/'+book_obj["title"].replace(" ", "_")
	try:
		response = urllib2.urlopen(url)
		resp = json.loads(response.read())
		if 'error' not in resp:
			update_record = True
	except HTTPError, e:
		print 'Error code: ', e.code"""

	if(oldTitle):
		book_obj['oldTitle'] = oldTitle

	url = 'http://' + server + '/api/index/' + book_obj["title"].replace(" ", "_")
	indexJSON = json.dumps(book_obj)
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



def postText(ref, text):
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

#api/links/
def postLink(link_obj, link_id = None):
	url = 'http://' + server + '/api/links/?'
	indexJSON = json.dumps(link_obj)
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