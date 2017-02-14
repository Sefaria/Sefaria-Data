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
	title = "Biur_Halacha." + str(siman)
	name = "ביאור_הלכה_על_אורח_חיים_" + tools.numToHeb(siman)
	tools.wikiGet("https://he.wikisource.org/w/index.php?title=%s&printable=yes" %(name), title)


title = "Biur_Halacha_index"
tools.wikiGet("https://he.wikisource.org/w/index.php?title=%D7%91%D7%99%D7%90%D7%95%D7%A8_%D7%94%D7%9C%D7%9B%D7%94&printable=yes", title)
