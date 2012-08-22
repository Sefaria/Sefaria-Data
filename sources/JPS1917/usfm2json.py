import json
import re
import os

files = os.listdir("./usfm")
for fname in files:
	if fname.startswith("."):
		continue
	text = []
	chapter = -1
	f = open("./usfm/%s" % fname, 'r')
	#print "Book " + fname
	while True:
	 	line = f.readline().decode("windows-1252")
	 	if not line:
	 		break
	 	tag = line.split(" ")[0]

	 	# remove pagebreaks first (they can be inside of footnotes)
	 	line = re.sub(r'\\f \+ Page  \\f\*', '', line)
	 	# remove footnotes
	 	line = re.sub(r'\\f .+ \\f\*', '', line)
	 	# standardize unicode open single quote
	 	line = line.replace(u'\u00e2\u20ac\u02dc', u'\u2018')
	 	# close single quote
	 	line = line.replace(u'\u00e2\u20ac\u2122', u'\u2019')
	 	# mdash
	 	line = line.replace(u'\u00e2\u20ac\u201d', u'\u2014')

	 	if tag == '\\c':
	 		#print("%s: Chapter: %d" % (fname, (chapter+1)))
	 		text.append([])
	 		chapter += 1
	 		verse = -1

	 	elif tag == '\\v':
	 		#print("%s: Chapter: %d: Verse: %d" % (fname, (chapter+1), len(text[chapter])+1))
	 		line = line[3:].strip()
	 		line = re.sub(r'^\d+ ', '', line)
	 		text[chapter].append(line)
	 		verse += 1

	 	elif tag == '\\q1':
	 		line = line[4:].strip()
	 		text[chapter][verse] = text[chapter][verse] + " " + line

	f.close()
	doc = {
		'text': text,
		'versionTitle': 'The Holy Scriptures: A New Translation (JPS 1917)',
		'versionSource': 'http://opensiddur.org/2010/08/%D7%AA%D7%A0%D7%B4%D7%9A-the-holy-scriptures-a-new-translation-jps-1917/',
		'language': 'en'
	}

	f = open("./json/%s" % fname, 'w')
	out = json.dumps(doc, indent=4)
	f.write(out)
	f.close()

