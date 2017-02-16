# -*- coding: utf-8 -*-
import tools

'''
This method that works by grabbing list of files from a file which was obtained by parsing the index.html file
index = open("nnn", "r")
for line in index:
	line = line.rstrip()
	title = urllib.unquote(line).decode('utf8')
	wikiGet("https://he.wikisource.org/w/index.php?title=%s&printable=yes" %(line), title)
index.close()
'''

#this method just iterates through the files based on name
#it's less "correct" but it works where there's no English name to get

for siman in range(1, 697): #696 simanim in O.C.
	if siman == 5 or siman == 6: continue # 5 & 6 are simanim with no text but a page
	title = "Biur_Halacha." + str(siman)
	name = "ביאור_הלכה_על_אורח_חיים_" + tools.numToHeb(siman)
	tools.wikiGet("https://he.wikisource.org/w/index.php?title=%s&printable=yes" %(name), title)
