
#!/usr/bin/python

import re

books = ["GENESIS", "EXODUS", "LEVITICUS", "NUMBERS", "DEUTERONOMY", "JOSHUA", "JUDGES", "FIRST SAMUEL", "SECOND SAMUEL", "FIRST KINGS", "SECOND KINGS", "ISAIAH", "JEREMIAH", "EZEKIEL", "HOSEA", "JOEL",  "AMOS", "OBADIAH",   "JONAH",  "MICAH", "NAHUM", "HABAKKUK",  "ZEPHANIAH", "HAGGAI", "ZECHARIAH", "MALACHI",  "PSALMS", "PROVERBS", "JOB", "SONG OF SONGS", "RUTH", "LAMENTATIONS", "ECCLESIASTES", "ESTHER", "DANIEL", "EZRA", "NEHEMIAH", "FIRST CHRONICLES", "SECOND CHRONICLES"]

f = open("source/Tanakh1917-trim.txt", "r")

text = f.read()

for i in range(len(books)):
	print books[i]
	start = text.find(books[i])
	print "Start: %d" % (start)
	if i+1 < len(books):
		end = text.find(books[i+1])
		book = text[start:end]
		print "End %d" % (end)
	else:
		book = text[start:]
		print "Last book"

	# Remove "...." lines at end of books
	book = re.sub(r'[\r\n][ .]{3,}[\r\n]', '', book)
	w = open("split/%s.txt" % books[i], "w")
	w.write(book)
	w.close()