# -*- coding: utf-8 -*-
import json
import os

all_letters = {}

mmfiles = os.listdir("./mm")
for fname in mmfiles:
	if fname in (".DS_Store"):
		continue
	f = open('./mm/%s' % fname, 'r')
	text = f.read().encode('utf-8')
	f.close()
	text = json.loads(text)

	letters = []
	for c in text["chapter"]:
		# grab the first letter of the first verse of each chapter
		letter = c[0][0]
		# letter = "'" if letter == "’" else letter
		letters.append(letter)
	all_letters[fname[:-5].title()] = letters


files = os.listdir("./json")
wrong = 0
right = 0
for fname in files:
	if fname in (".DS_Store", "EZRA.txt", "NEHEMIAH.txt"):
		continue
	f = open("./json/%s" % fname, 'r')
	text = f.read().encode('utf-8')
	f.close()
	name = fname[:-4].title()
	text = json.loads(text)
	
	for i, c in enumerate(text["text"]):
		if all_letters[name][i] != c[0][0].encode('utf-8'):
			wrong += 1
			print "%s %d: %s / %s" % (name, i+1, all_letters[name][i], c[0][0])
		else:
			right += 1

print "***\nTOTAL: %d wrong, %d right" % (wrong, right)