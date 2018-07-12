# -*- coding: utf-8 -*-
import sys
import os
import re

def parse(file):
	# print file
	file = file.upper()
	f = open("split/%s.txt" % file, "r")
	text = f.read()
	f.close()

	# Remove space from heading, add \h tag
	text = re.sub(r'([^\r\n]*)[\n\r ]+', r'\1\n', text, count=1)
	text = "\h " + text

	# mark page breaks
	# leave a new line if it seems to be a chapter break
	pageRe = re.compile(r'\. \r\n\r\n\x0c\r\n([A-Z])')
	text = re.sub(pageRe, r'.\\f + Page  \\f*\n\1', text)
	# leave a new line if it seems to be a chapter break
	pageRe = re.compile(r'\r\n\r\n\x0c\r\n(\d)')
	text = re.sub(pageRe, r'.\\f + Page  \\f*\n\1', text)
	# otherwise leave the rest inline
	pageRe = re.compile(r'\r\n\r\n\x0c\r\n')
	text = re.sub(pageRe, r'\\f + Page  \\f*', text)

	# Remove excess space after first verse in some books
	# Aren't these paragraphs?
	# text = re.sub(r'[\n\r ]{3,}2', '\r\n\r\n2', text, count=1)

	# Remove chapter marks which are inconsistently placed
	chapterRe = re.compile(r'((\r\n)?\d+ \r\n)+\r\n')
	text = re.sub(chapterRe, '', text)

	# Remove uninformative line breaks
	linesRe = re.compile(r'([^\n\r])\r\n([^\r\n])')
	text = re.sub(linesRe, r'\1\2', text)

	# insert verses labels
	text = re.sub(r' (\d+)(?![.,;\d])', r'\n\\v \1 ', text)
	text = re.sub(r'\n(\d+)', r'\n\\v \1 ', text)
	save_step(text, file, 1)

	text = re.sub(r'(?<![ \d])(\d+) ?([a-zA-Z])', r'\n\\v \1 \2', text)

	# mark footnotes
	footnoteRe = re.compile(r'\r\n\r\n([abdcef] [^\r\n]*)')
	text = re.sub(footnoteRe, r'\\f + \1 \\f*', text)

	# insert first verse numbers (which are not in the text), and chapter marks
	# handle common case is psalms where \p occurrs in middle of first verse
	#psalmsStyle = re.compile(r'(\r\n[\n\r ]+\r\n)(.+)(\r\n[\n\r ]+\r\n)((([^\\\n\r].*)[\r\n]+)*)\\v 2 ')
	#text = re.sub(psalmsStyle, r'\n\\p\n\\c\n\\v 1 \2\n\\p\n\4\n\\v 2 ', text)
	#text = re.sub(r'(\\c\n\\v 1 .*\n\\p)(.*)[\r\n]*(.*)(\\v 2 )', r'\1\2\n\\q1\3\4', text)

	# handle cases of paragraph immediately after first verse	
	pAfterFirst = re.compile(r'\n([^\\\n\r][^\n\r]*)(\r\n[\n\r ]+\r\n)\\v 2 ')
	#text = re.sub(pAfterFirst, r'\n\\c\n\\v 1 \1\n\\p\n\\v 2 ', text)


	# remove all carriage returns which make things confusing
	text = re.sub(r'\r', '', text)

	# remove hebrew characters that appear as . or ..
	text = re.sub(r'\n\.+\n', r'\n', text)
	text = re.sub(r'\n\. ', r'\n', text)

	# catch poetic verses
	poeticRe = re.compile(r'([^\n][^\n])\n\n([^\\\n][^\n]+\n)(?!\\v 2 )')
	text = re.sub(poeticRe, r'\1\n\\q1 \2', text)
	text = re.sub(poeticRe, r'\1\n\\q1 \2', text) # apply twice to catch overlapping 
	text = re.sub(r'(\n[^\n]+\n\\p\n)(?!\\v 2 )', r'\\q1 \1', text)
	save_step(text, file, 2)


	# make q1 if hangin directly off another q1
	text = re.sub(r'(\\q1 [^\n]+\n)([^\\\n][^\n]+\n)', r'\1\q1 \2', text)


	# undo q1 if there's nothing left before \v 2
	q1Fix = r'(\\v \d+ [^\n]+\n)\\q1 ([^\n]+\n)(|\\q1 [^\n]+\n|[ \n]+)*(\n\\v 2 )'
	text = re.sub(q1Fix, r'\1\2\3\\p\n\\v 2 ', text)
	save_step(text, file, 3)

	# treat remaining new lines as paragrpahs 
	text = re.sub(r'(\n[\n ]*\n)', '\n\\p\n', text)
	save_step(text, file, 4)

	# marked missed q1's that come after p's
	# mark \p line \p unmarked 
	text = re.sub(r'(\\p\n[^\\][^\n]+\n\\p\n)(?!\\)', r'\1\\q1 ', text)
	# mark \h line \p unmarked 
	text = re.sub(r'(\\h [^\n]+\n[^\\][^\n]+\n\\p\n)(?!\\)', r'\1\\q1 ', text)
	# mark \p unmarked \p marked-not-v2 
	text = re.sub(r'(\\p\n)([^\\]+\n)(\\p\n\\v )(?!2 )', r'\1\\q1 \2\3', text)
	save_step(text, file, 5)

	# any unmarked line whose next \v is not \v 2 is a q1
	aboveV = r'\n([^\\\n][^\n]+\n(|\\p\n|\\q1 [^\n]+\n)*\\v )(?!2 )'
	text = re.sub(aboveV, r'\n\\q1 \1', text)

	# If v 1 is already maked and something hangs above, call it q1
	text = re.sub(r'\\p\n([^\\\n][^\n]+\n\\v 1 )', r'\\p\n\q1 \1', text)

	# handle first verse marks for the rest 
	# firstVerseRe = re.compile(r'\n(([^\\\n\r][^\n\r]*\r\n[\n\r ]+\r\n)?(([^\\\n\r][^\n\r]*)[\r\n]+)+)\\v 2 ')
	firstVerseRe = re.compile(r'\n([^\n\\])')
	text = re.sub(firstVerseRe, r'\n\\c\n\\v 1 \1', text)
	save_step(text, file, 6)

	# insert chapters of for cases where first verse was already labled
	text = re.sub(r'(?<!\\c\n)\\v 1 ', r'\\c\n\\v 1 ', text)
	save_step(text, file, 7)

	# fix bad chapters 
	badChap = r'\\c\n\\v 1([^\n]+\n)(|(\\p [^\n]+|\\q1 [^\n]+)\n)+(\\v )(?!2 )'
	text = re.sub(badChap, r'\\q1 \1\2\4', text)
	save_step(text, file, 8)


	# don't place a paragraph immediately before a chapter (correct?)
	text = re.sub(r'\\p\n\\c', r'\\c', text)

	# fix common mistakes
	text = re.sub(r'\\v 1\n\\q1', r'\\v 1', text)


	# insert chapter numbers
	count = 1
	while re.search(r'\n\\c\n', text):
		text = re.sub(r'\n\\c\n', '\n\c %d\n' % (count), text, count=1)
		count += 1

	# remove trailing lines
	text = text.strip()

	w = open("usfm-raw/%s.txt" % file, "w")
	w.write(text)
	w.close()


def save_step(text, file, step):
	w = open("steps/%s/%s.txt" % (step, file), "w")
	w.write(text)
	w.close()


if __name__ == "__main__":
	files = os.listdir("./split")
	for f in files:
		parse(f[:-4])