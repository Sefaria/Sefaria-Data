# -*- coding: utf-8 -*-
import sys
import helperFunctions as Helper
import json

try:
	import xml.etree.cElementTree as ET
except ImportError:
	import xml.etree.ElementTree as ET
import pprint
import itertools

xml_index_file = 'source/tnc.xml'
xml_main_node_name = u'משנה'


def create_book_record():
	index = {
		"title": 'Bartenura',
		"titleVariants": ['Bartenura', 'Obadiah ben Abraham of Bertinoro', 'Obadiah of Bertinoro', 'Ovadia of Bartenura',
						  'עובדיה מברטנורא', "ר' עובדיה מברטנורא"],
		"heTitle": 'ברטנורא',
		"sectionNames": ["", ""],
		"categories": ['Commentary'],
	}
	Helper.createBookRecord(index)


def run_parser():
	create_book_record()
	"""first, get a mapping of hebrew book names to english ones so we can correctly
	store the OnYourWay xml data that is listed by hebrew title """
	book_titles = Helper.build_title_map('Mishnah', 'heTitle', 'title')
	#pprint.pprint(book_titles)
	#now get the OnYourWay table of contents in order to list the books we want
	file_ids_tree = ET.parse(xml_index_file)
	root = file_ids_tree.getroot()
	#find the Mishnah
	for child in root:
		if child.get('name') == u'משנה':
			root = child
			break
	#iterate over all the masechtot. nested loop to account for them being listed inside their Sedarim
	for child in root:
		for gchild in child:
			print gchild.get('name').encode('utf-8'), ' in file: ', gchild.get('nid')
			create_commentary_entry(book_titles, gchild.get('nid'), gchild.get('name'))


def create_commentary_entry(book_titles, file_id, book_name):
	book_ref = book_titles[book_name]
	print "Book Ref: ", book_ref
	commentary_text = parse_masechet_commentary(file_id)
	print "==============================================================================================="
	text_whole = {
		"title": "Bartenura on " + book_ref,
		"versionTitle": "On Your Way",
		"versionSource": "http://mobile.tora.ws/",
		"language": "he",
		"text": commentary_text,
	}
	Helper.postText("Bartenura on " + book_ref, text_whole)


def parse_masechet_commentary(file_id):
	file_name = 'source/' + file_id + '.xml'
	book_tree = ET.parse(file_name)
	root = book_tree.getroot()
	#this will hold all the mishna's commentary in a 3 level deep array
	text = []
	#xml has chapters under the root with the mishna text, and two commentaries under it.
	for chapter in root.findall('chap'):
		print chapter.get('n').encode('utf-8')
		chapter_text = []
		text.append(chapter_text)
		for mishnah in chapter.findall('p'):
			print mishnah.get('n').encode('utf-8')
			mishnah_text = []
			chapter_text.append(mishnah_text)
			bartenura_commentary = mishnah.find("t[@i='14']")
			if bartenura_commentary is None:
				continue
			#if there is no commentary, this string should appear (somewhere inside the mishnah element)
			elif bartenura_commentary.text is not None and bartenura_commentary.text.find(u"אין פירוש למשנה זו") != -1:
				continue
			#have seen some cases in the xml where the commentary is outside the normal flow of <b> tags
			elif bartenura_commentary.text is not None:
				#print "commentary in irregular place"
				#print bartenura_commentary.text.encode('utf-8')
				mishnah_text.append(bartenura_commentary.text)
			for child in bartenura_commentary:
				"""the "Dibur HaMatchil" is (normally) in the <b> tags (that we need to re-insert since they get dropped
				in the parsing. The rest of the comment is at the tail of that element with a superfluous period
				"""
				if (child.text is not None and child.text.find(u"אין פירוש למשנה זו") != -1) or (child.tail is not None and child.tail.find(u"אין פירוש למשנה זו") != -1):
					break
				elif child.text is None:
					continue
				comment_verse = '<b>' + child.text + '</b>' + child.tail.replace(".", "", 1)
				#print comment_verse.encode('utf-8')
				mishnah_text.append(comment_verse)
			#print child.tail.replace(".", "", 1).encode('utf-8')
	return text


if __name__ == '__main__':
	"""Map command line arguments to function arguments."""
	run_parser(*sys.argv[1:])