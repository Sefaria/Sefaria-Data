# -*- coding: utf-8 -*-

import argparse
import sys
import helperFunctions as Helper
from helperFunctions import run_once
import json
import re
import os, errno
import os.path


try:
	import xml.etree.cElementTree as ET
except ImportError:
	import xml.etree.ElementTree as ET
import pprint
import itertools

xml_index_file = 'source/tnc.xml'
xml_main_node_name = u'משנה'
#this regex will match things like {א} and {טו} for the comment indices
regex = re.compile(ur'\{([\u0590-\u05ea]{1,2})\}',re.UNICODE)

#both of these mishanh commentaries have similar structure in OnYourWay so we can use the same logic
available_commentators = {
	'bartenura' : {'xml_id' : '14', 'record' :{
		"title": 'Bartenura',
		"titleVariants": ['Bartenura', 'Obadiah ben Abraham of Bertinoro', 'Obadiah of Bertinoro', 'Ovadia of Bartenura',
						  'עובדיה מברטנורא', "ר' עובדיה מברטנורא"],
		"heTitle": 'ברטנורא',
		"sectionNames": ["", ""],
		"categories": ['Commentary'],
	}},
	'tosafot' : {'xml_id' : '15', 'record' :{
		"title": 'Tosafot Yom Tov',
		"titleVariants": ['Tosafot Yom Tov', 'התוספות יו"ט', 'התוספות יום-טוב', 'תוספות יום טוב', "ר' יום טוב ליפמן הלוי הלר"],
		"heTitle": 'תוספות יום טוב',
		"sectionNames": ["", ""],
		"categories": ['Commentary'],
	}},
}


""" Will create an index record """
@run_once
def create_book_records(commentator_name):
	if commentator_name == 'mixed':
		for commentator_name in available_commentators:
			print commentator_name
			create_book_record(available_commentators[commentator_name])
	else:
		create_book_record(available_commentators[commentator_name])

def create_book_record(commentator):
	index = commentator['record']
	Helper.createBookRecord(index)

""" Main function, runs the appropriate functions according to params from CLI """
def run_text_tool(commentator, handler):
	print commentator
	#first, get a mapping of hebrew book names to english ones so we can correctly store the OnYourWay xml data that is listed by hebrew title
	book_titles = Helper.build_title_map('Mishnah', 'heTitle', 'title')
	#now get the OnYourWay table of contents in order to list the books we want
	file_ids_tree = ET.parse(xml_index_file)
	root = file_ids_tree.getroot()
	#find the Mishnah
	for child in root:
		if child.get('name') == xml_main_node_name:
			root = child
			break
	#iterate over all the masechtot. nested loop to account for them being listed inside their Sedarim
	for child in root:
		for gchild in child:
			print gchild.get('name').encode('utf-8'), ' in file: ', gchild.get('nid')
			#either parsing or posting
			handler(commentator, book_titles[gchild.get('name')], gchild.get('nid'))

""" This functiona handles posting the parsed data to the database via the API """
def run_post_to_api_calls(commentator, book_name, file_id):
	create_book_records(commentator)
	if commentator != 'mixed':
		post_parsed_text(commentator, book_name)
	else:
		#we want both texts and the links between them.
		for commentator_name in available_commentators:
			post_parsed_text(commentator_name, book_name)
		post_links(book_name)

"""This function runs the various parsing methods toextract the commentary texts """
def run_parser(commentator, book_name, file_id):
	#the specific mishnah
	file_name = 'source/' + file_id + '.xml'
	book_tree = ET.parse(file_name)
	tree_root = book_tree.getroot()
	#this will hold all the mishna's commentary in a 3 level deep array
	if commentator != 'mixed':
		parsing_func = parse_bartenura_text if commentator == 'bartenura' else parse_tosafotyt_text
		comment_text = parse_masechet_commentary(commentator, tree_root, parsing_func)
		print "==============================================================================================="
		save_parsed_text(commentator, book_name, comment_text)
	else:
		#we want both texts and to parse the links between them.
		bartenura_text = parse_masechet_commentary('bartenura', tree_root, parse_bartenura_text)
		tosafot_text = parse_masechet_commentary('tosafot', tree_root, parse_tosafotyt_text)
		links = parse_commentary_links(book_name, tree_root, bartenura_text)
		#get rid of curly brackets, now links are saved
		bartenura_text = strip_notation(bartenura_text)

		save_parsed_text('bartenura', book_name, bartenura_text)
		save_parsed_text('tosafot', book_name, tosafot_text)
		save_links('bartenura', book_name, links)

""" posts a text to the API """
def post_parsed_text(commentator, book_name):
	#assemble the title ref
	commentator_title = unicode(available_commentators[commentator]['record']['title'],'utf-8')
	ref = commentator_title + ' on ' + book_name
	dir_name = 'preprocess_json/mishnahCommentary/' + commentator
	with open(dir_name + "/" + ref + ".json", 'r') as filep:
		file_text = filep.read()
	Helper.postText(ref, file_text, False)

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
	Helper.mkdir_p("preprocess_json/mishnahCommentary/" + commentator + "/")
	with open("preprocess_json/mishnahCommentary/" + commentator + "/" + ref + ".json", 'w') as out:
		json.dump(text_whole, out)

""" posts links in a given book to the API """
def post_links(book_name):
	dir_name = 'preprocess_json/mishnahCommentary/links'
	links=[]
	#we saved an array of links, still need to build them each into the correct obj
	with open(dir_name + "/" + book_name + ".json", 'r') as filep:
		links_arr = json.load(filep)
	for link in links_arr:
		link_obj = {
			"type": "commentary",
			"refs": link,
			"anchorText": "",
		}
		links.append(link_obj)
	Helper.postLink(links)

"""Saves links in commentaries in a given mishnah"""
def save_links(commentator, book_name, links_arr):
	Helper.mkdir_p("preprocess_json/mishnahCommentary/links/")
	with open("preprocess_json/mishnahCommentary/links/" + book_name + ".json", 'w') as out:
		json.dump(links_arr, out)


""" Handles parsing of a text """
def parse_masechet_commentary(commentator, root, parsing_func):
	#this will hold all the mishnah's commentary in a 3 level deep array
	all_chapters = []
	#xml has chapters under the root with the mishnah text, and two commentaries under it.
	#iterate over each mishnah and handle it according to parameters
	for chap_num, chapter_node in enumerate(root.findall('chap'),1):
		print "chapter ", chap_num, ": ", chapter_node.get('n').encode('utf-8')
		mishnayot = []
		all_chapters.append(mishnayot)
		for m_num,mishnah_node in enumerate(chapter_node.findall('p'),1):
			print "mishnah ", m_num, ": ", mishnah_node.get('n').encode('utf-8')
			comments = parsing_func(mishnah_node)
			mishnayot.append(comments)
	return all_chapters

""" Handles parsing of the Bartenura """
def parse_bartenura_text(mishnah_node):
	comments = []
	commentator_key = available_commentators['bartenura']['xml_id']
	mishnah_commentary_node = mishnah_node.find("t[@i='" + commentator_key + "']")

	if mishnah_commentary_node is None:
		#print "no commentary"
		return comments
	#if there is no commentary, this string should appear (somewhere inside the mishnah element)
	elif mishnah_commentary_node.text is not None and mishnah_commentary_node.text.find(u"פירוש למשנה זו") != -1:
		#print "no commentary"
		return comments
	#have seen some cases in the xml where the commentary is outside the normal flow of <b> tags
	elif mishnah_commentary_node.text is not None:
		#print "commentary in irregular place"
		#print mishnah_commentary_node.text.encode('utf-8')
		comments.append(mishnah_commentary_node.text)
	for i,child in enumerate(mishnah_commentary_node,1):
		#print "verse: ", i
		#the "Dibur HaMatchil" is (normally) in the <b> tags (that we need to re-insert since they get dropped in the parsing. The rest of the comment is at the tail of that element with a superfluous period
		if (child.text is not None and child.text.find(u"פירוש למשנה זו") != -1) or (child.tail is not None and child.tail.find(u"פירוש למשנה זו") != -1):
			#print "no commentary"
			break
		elif child.text is None or child.text.strip() == '':
			#print "no text in verse"
			continue
		comment_verse = '<b>' + child.text + '</b>' + child.tail.replace(".", "", 1)
		#print i, ") ", comment_verse.encode('utf-8')
		comments.append(comment_verse)
	return comments

""" Handles parsing of the Tosafot Yom Tov"""
def parse_tosafotyt_text(mishnah_node):
	comments = []
	commentator_key = available_commentators['tosafot']['xml_id']
	mishnah_commentary_node = mishnah_node.find("t[@i='" + commentator_key + "']")
	#if the node doesn't even exist.
	if mishnah_commentary_node is None:
		#print "no commentary"
		return comments
	#this is an ugly hack to get the complete contents of the node and then parse it,
	#not as xml, but with a regex on the hebrew letters in curly brackets.
	str_comment = ET.tostring(mishnah_commentary_node, 'utf-8')
	#print str_comment
	str_comment = re.sub(r'<[^>]*?>', '', str_comment)
	#print str_comment
	str_comment = unicode(str_comment, 'utf-8', 'strict')
	#check if the commentary is declared in the xml as not existing.
	if str_comment.find(u"פירוש למשנה זו") != -1:
		#print "no commentary"
		return comments
	#if not regex.search(str_comment):
		#print "No REGEX"
	comments_list = regex.split(str_comment)
	#now the list will contain both the letter indices and the comment verses.
	#so the even places will be the verses, except probably the first element that will be an empty string.
	comments = [x.strip() for ind, x in enumerate(comments_list) if ind % 2 == 0 and x.strip() != ""]
	indices = comments_list[1::2]
	#print "indices: ", len(indices), "comments: ", len(comments)
	#if len(indices) != len(comments):
		#print "LENGTHS DON'T MATCH!!!"

	#if there is no commentary, this string should appear (somewhere inside the mishnah element)
	return comments

""" Pares links between bartenura and Tosafot YT """
def parse_commentary_links(book_name, root, text_to_search):
	#we will create a one dimensional array, once we have the correct ref for the link, we don't care about order
	links = []
	print book_name
	#iterate over the chapters and mishnayot
	for chap_num, chapter_node in enumerate(root.findall('chap')):
		for m_num,mishnah_node in enumerate(chapter_node.findall('p')):
			#print book_name," chapter ", chap_num, " mishnah ", m_num, ": ", mishnah_node.get('n').encode('utf-8')
			mishnah_commentary_node = mishnah_node.find("t[@i='15']")
			if mishnah_commentary_node is not None:
				str_comment = ET.tostring(mishnah_commentary_node, 'utf-8')
				str_comment = unicode(str_comment, 'utf-8', 'strict')
				#for each letter, search the bartenura verses to find that latter and if so create a link
				#we start enumerating at 1 for easier ref making
				for t_index, m in enumerate(regex.findall(str_comment),1):
					letter = u'{'+ m + u'}'
					bartenura_mishnah = text_to_search[chap_num][m_num]
					for b_index,b_comment in enumerate(bartenura_mishnah,1):
						if letter in b_comment:
							#print m.encode('utf-8'), ")"
							str_t =  u"Tosafot Yom Tov on " + book_name + " " + str(chap_num+1) +":"+str(m_num+1) + ":" + str(t_index)
							str_b = u"Bartenura on " + book_name + " " + str(chap_num+1) +":"+str(m_num+1) + ":" + str(b_index)
							arr = [str_b, str_t]
							links.append(arr)
	return links

""" Remove curly brackets from verses """
def strip_notation(text):
	for c,chapter in enumerate(text):
		for m,mishnah in enumerate(chapter):
			for v,comment_verse in enumerate(mishnah):
				text[c][m][v] = regex.sub("", comment_verse)
	return text







if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('commentator', choices= list(available_commentators.copy().keys()) +['mixed'], help="choose what commentator to parse")
	parser.add_argument("-p", "--preprocess", help="Perform the preprocess and parse the files but do not post them to the db", action="store_true")
	parser.add_argument("-a", "--postapi", help="post data to API",
                    action="store_true")
	args = parser.parse_args()
	#Map command line arguments to function arguments.
	if args.preprocess:
		print "preprocess on", args.commentator
		run_text_tool(args.commentator, run_parser)
	if args.postapi:
		print args.commentator
		print "posting to api"
		run_text_tool(args.commentator, run_post_to_api_calls)
		#