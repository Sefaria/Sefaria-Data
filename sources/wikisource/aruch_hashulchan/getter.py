# -*- coding: utf-8 -*-
import tools

'''
This method that works by grabbing list of files from a file which was obtained by parsing the index.html file
index = open("nnn", "r")
for line in index:
	line = line.rstrip()
	title = urllib.unquote(line).decode('utf8')
	wikiGet("http://he.wikisource.org/w/api.php?format=json&action=query&prop=revisions&rvprop=content&titles=%s" %(line), title)
index.close()
'''

#this method just iterates through the files based on name	
#it's less "correct" but it works where there's no English name to get

for siman in range(1, 698): #697 simanim in O.C.
	title = "Aruch_HaShulchan.1." + str(siman)
	name = "ערוך_השולחן_אורח_חיים_" + tools.numToHeb(siman)
	tools.wikiGet("http://he.wikisource.org/w/api.php?action=query&prop=extracts&format=xml&exlimit=1&exsectionformat=plain&titles=%s" %(name), title)




