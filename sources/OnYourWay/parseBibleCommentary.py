# -*- coding: utf-8 -*-

import argparse
import sys
import helperFunctions as Helper
from helperFunctions import run_once
import json
import re
import os, errno
import os.path
import bleach


try:
	import xml.etree.cElementTree as ET
except ImportError:
	import xml.etree.ElementTree as ET
import pprint
import itertools
from bibleCommentators import available_commentators

xml_index_file = 'source/tnc.xml'
xml_main_node_name = u'תנך'
book = None
commentator = None
#this regex will match things like {א} and {טו} for the comment indices
regex = re.compile(ur'\{([\u0590-\u05ea]{1,2})\}',re.UNICODE)
preprocess_path = 'preprocess_json/bibleCommentary/'

ALLOWED_TAGS = ("b")





""" Will create an index record """
@run_once
def create_book_records(commentator_name):
	if not commentator_name:
		for commentator_name in available_commentators:
			print commentator_name
			create_book_record(available_commentators[commentator_name])
	else:
		create_book_record(available_commentators[commentator_name])

def create_book_record(commentator):
	index = commentator['record']
	Helper.createBookRecord(index)

""" Main function, runs the appropriate functions according to params from CLI """
def run_text_tool(handler):
	#first, get a mapping of hebrew book names to english ones so we can correctly store the OnYourWay xml data that is listed by hebrew title
	book_titles = Helper.build_title_map('Tanach', 'heTitle', 'title')
	#now get the OnYourWay table of contents in order to list the books we want
	file_ids_tree = ET.parse(xml_index_file)
	root = file_ids_tree.getroot()
	#find the top node
	for child in root:
		if child.get('name') == xml_main_node_name:
			root = child
			break
	#iterate over all the books. they are nested in the 3 top bible categories (Torah, Prophets and Writings)
	for child in root:
		for gchild in child:

			if (book and book.lower() == book_titles[gchild.get('name')].lower()) or book is None:
				#print gchild.get('name').encode('utf-8'), ' in file: ', gchild.get('nid')
				#either parsing or posting
				handler(book_titles[gchild.get('name')], gchild.get('nid'))

""" This functiona handles posting the parsed data to the database via the API """
def run_post_to_api_calls(book_name, file_id):
	create_book_records(commentator)
	#the specific book
	print book_name
	file_name = 'source/' + file_id + '.xml'
	book = ET.parse(file_name).getroot()

	#this will hold all the book's commentary in a 3 level deep array
	#the top of the OnYourWay xml lists the commentator id's, so let's use that
	existing_commentators = make_commentator_text_dict(book)
	#will return a structure keyed to the commentator with the comments object as value.
	if commentator and commentator in existing_commentators:
		post_parsed_text(commentator, book_name)
	else:
		#we want both texts and the links between them.
		for commentator_name in existing_commentators:
			post_parsed_text(commentator_name, book_name)
		#post_links(book_name)

"""This function runs the various parsing methods to extract the commentary texts for a given book """
def run_parser(book_name, file_id):
	#the specific book
	print book_name
	file_name = 'source/' + file_id + '.xml'
	book = ET.parse(file_name).getroot()

	#this will hold all the book's commentary in a 3 level deep array
	#the top of the OnYourWay xml lists the commentator id's, so let's use that
	existing_commentators = make_commentator_text_dict(book)
	#will return a structure keyed to the commentator with the comments object as value.
	if commentator and commentator in existing_commentators:
		#go over the book, extract this specific commentator
		commentary_text = parse_book_commentator_commentary(book, commentator)
		print "saving %s" % commentator
		save_parsed_text(commentator, book_name, commentary_text)
	elif commentator is None:
		#go over all commentators and extract them
		for commentator_name in existing_commentators:
			commentary_text = parse_book_commentator_commentary(book, commentator_name)
			print "saving %s" % commentator_name
			save_parsed_text(commentator_name, book_name, commentary_text)



"""
Parses a commentator commentary out of the entire book.
"""
def parse_book_commentator_commentary(book, commentator):
	print commentator
	#get the commentator xml id
	xml_id = available_commentators[commentator]['xml_id']
	#get the proper parsing function for the commentary nodes
	parsing_func = get_parsing_func(commentator)
	print "parsing: ", parsing_func.__name__
	#this will hold all the book's commentary in a 3 level deep array
	all_chapters = []
	#xml has chapters under the root with the book text, and commentaries under it.
	#iterate over each verse and handle it according to parameters
	for chap_num, chapter_node in enumerate(book.findall('chap'),1):
		print "chapter ", chap_num, ": ", chapter_node.get('n').encode('utf-8')
		verses = []
		all_chapters.append(verses)
		for v_num,verse_node in enumerate(chapter_node.findall('p'),1):
			print "verse ", v_num, ": ", verse_node.get('n').encode('utf-8')
			commentator_node = verse_node.find("t[@i='" + xml_id + "']")
			comments = parsing_func(commentator_node)
			log_comments(comments)
			verses.append(comments)
	return all_chapters

"""
Makes a dictionary for containing the commentary texts of the commentators.
"""
def make_commentator_text_dict(book):
	result_dict = {}
	for pid in book.findall('pid'):
		c_id = pid.get('n')
		if c_id in commentator_map:
			#init the commentators text array
			result_dict[commentator_map[c_id]] = []
	return result_dict


"""
Returns the correct parsing function for the commentator, looks first in the commentator
json for a function name, then the module
namespace
"""
def get_parsing_func(commentator):
	commentator_nsp = commentator.replace(" ", "_")
	#look for a special function in the commentator's struct. and check if such a function exists in this module.
	if 'parsing_func' in available_commentators[commentator] and hasattr(sys.modules[__name__], available_commentators[commentator]['parsing_func']):
		return getattr(sys.modules[__name__], available_commentators[commentator]['parsing_func'])
	#look for a function name with a standard name.
	elif hasattr(sys.modules[__name__], "parse_%s_text" % commentator_nsp):
		return getattr(sys.modules[__name__], "parse_%s_text" % commentator_nsp)
	else:
		return parse_default_text


""" Saves a text to JSON """
def save_parsed_text(commentator, book_name, text):
	#assemble the title ref
	commentator_title = unicode(available_commentators[commentator]['record']['title'],'utf-8')
	ref = commentator_title + ' on ' + book_name
	#print ref
	#JSON obj matching the API requirements
	text_whole = {
		"title": ref,
		"versionTitle": "On Your Way",
		"versionSource": "http://mobile.tora.ws/",
		"language": "he",
		"text": text,
	}
	#save
	Helper.mkdir_p(preprocess_path + commentator + "/")
	with open(preprocess_path + commentator + "/" + ref + ".json", 'w') as out:
		json.dump(text_whole, out)


""" posts a text to the API """
def post_parsed_text(commentator, book_name):
	#assemble the title ref
	commentator_title = unicode(available_commentators[commentator]['record']['title'],'utf-8')
	ref = commentator_title + ' on ' + book_name
	dir_name = preprocess_path + commentator
	with open(dir_name + "/" + ref + ".json", 'r') as filep:
		file_text = filep.read()
	Helper.postText(ref, file_text, False)


""" Handles parsing of a default text ,separated by <b> tags """
def parse_default_text(commentator_node):
	# #3 Rashi, #4 Ramban has <small>s and <span style="bla">s
	# #6 Sforno and #7 Baal Haturim seem fine
	comments = []
	if commentator_node is None:
		print "no commentary"
		return comments
	#in the bible commentaries, the xml is in CDATA so it all gets interpreted as one big text for each node.
	#print "length: ", len(commentator_node.findall('*')) > 0
	if commentator_node.text is not None:
		#gets rid of all the extra HTML in the xml.
		str_comments = bleach.clean(commentator_node.text, tags=ALLOWED_TAGS, strip=True)
		#ugly hack to make a parsable xml with <b> children
		xml_comments = ET.XML('<t>' + str_comments.encode('utf-8') +'</t>')
	if xml_comments.text is not None:
		comments.append(xml_comments.text)
	for i,child in enumerate(xml_comments,1):
		#the "Dibur HaMatchil" is (normally) in the <b> tags (that we need to re-insert since they get dropped in the parsing. The rest of the comment is at the tail of that element with a superfluous period
		if child.text is None or child.text.strip() == '':
			continue
		comment_verse = '<b>' + child.text + '</b>' + (child.tail.replace(".", "", 1) if child.tail is not None else '')
		comments.append(comment_verse)
	return comments

def parse_ibn_ezra_text(commentator_node):
	# #5 Ibn Ezra might have dibur hmatchil words not in the beginning of a verse, and the first words might get cut off if parsing by <b>
	sh_regex = re.compile(ur':\s',re.UNICODE)
	comments = parse_regex_text(commentator_node, sh_regex)
	return comments


def parse_or_hachaim_text(commentator_node):
	# #8
	#text is complex. half of bold words are not even d"h's, for now we will parse by the letters followed by a parenthesis
	sh_regex = re.compile(ur'<b>[\u0590-\u05ea]{1,2}\)</b>',re.UNICODE)
	comments =  parse_regex_text(commentator_node, sh_regex)
	#look for paragraph breaks and add them,
	for i,comment in enumerate(comments):
		comments[i] = re.sub('\n+<b>', '<br/><b>', comment)
	return comments


def parse_siftei_hachamim_text(commentator_node):
	# #28
	#text is keyed with curly brackets.
	sh_regex = re.compile(ur'\{\{[\u0590-\u05ea]{1,2}\}\}',re.UNICODE)
	return parse_regex_text(commentator_node, sh_regex)


def parse_malbim_text(commentator_node):
	# #30 There are sometimes letters in triple curly braces.
	comments = parse_default_text(commentator_node)
	#clean out letters in curly brackets in the text. replace them with the letter itself, it's a numeric counting.
	del_regex = re.compile(ur'\{+([\u0590-\u05ea]{1,2})\}+',re.UNICODE)
	return [del_regex.sub(r'\1.', x) for x in comments]

def parse_torah_temimah_text(commentator_node):
	# #9
	#text has weird markup. <sp> nodes seem to have the DH, <sidcom1> seem to have references.
	b_regex = re.compile(ur'<ps>(.*)</ps>',re.UNICODE)
	c_regex = re.compile(ur'<sidcom1>(.*)</sidcom1>',re.UNICODE)
	if commentator_node is not None and commentator_node.text is not None:
		#replace the captured text with itself surrounded by the desired tags (or brackets)
		new_text = b_regex.sub(r'<b>\1</b>.', commentator_node.text)
		new_text = c_regex.sub(r'(\1)', new_text)
		commentator_node.text = new_text
	return parse_default_text(commentator_node)


""" Handles parsing of a text needing splitting by a certain regular expression"""
def parse_regex_text(commentator_node, regex_obj):
	comments = []
	if commentator_node is None:
		print "no commentary"
		return comments
	#this is an ugly hack to get the complete contents of the node and then parse it,
	#not as xml, but with a regex on the hebrew letters in curly brackets.
	if commentator_node.text is not None:
		#gets rid of all the extra HTML in the xml.
		str_comments = bleach.clean(commentator_node.text, tags=ALLOWED_TAGS, strip=True)
		#check if the commentary is declared in the xml as not existing.
		comments_list = regex_obj.split(str_comments)
		#now the list will contain both the letter indices and the comment verses.
		#so the even places will be the verses, except probably the first element that will be an empty string.
		comments = [x.strip() for x in comments_list if x.strip() != ""]
	return comments


""" Remove curly brackets from verses """
def strip_notation(text):
	for c,chapter in enumerate(text):
		for m,mishnah in enumerate(chapter):
			for v,comment_verse in enumerate(mishnah):
				text[c][m][v] = regex.sub("", comment_verse)
	return text

""" Flips the structure to be keyed by the xml ids of the xml """
def map_ids_to_commentators(commentators):
	result = {}
	for key, commentator in commentators.items():
		result[commentator['xml_id']] = key
	return result

def log_comments(comments):
	for i,comment_verse in enumerate(comments, 1):
		print i, ") ", comment_verse.encode('utf-8')



""" The main function, runs when called from the CLI"""
if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('book', default='all', nargs='?', help="choose what book to parse or type 'all'")
	parser.add_argument('commentator', default='all', nargs='?', choices= list(available_commentators.copy().keys())+['all'], help="choose what commentator to parse", )
	parser.add_argument("-p", "--preprocess", help="Perform the preprocess and parse the files but do not post them to the db", action="store_true")
	parser.add_argument("-a", "--postapi", help="post data to API",
                    action="store_true")
	args = parser.parse_args()
	book = args.book if args.book != 'all' else None
	commentator = args.commentator if args.commentator != 'all' else None
	print "%s on %s" % (args.commentator, args.book)
	commentator_map = map_ids_to_commentators(available_commentators)
	#Map command line arguments to function arguments.
	if args.preprocess:
		run_text_tool(run_parser)
	if args.postapi:
		print "posting to api"
		run_text_tool(run_post_to_api_calls)