# -*- coding: utf-8 -*-

import tools

apikey = '' #Add your API key
server = 'www.sefaria.org'

books = {'Genesis':'f_01623','Exodus':'f_01624','Leviticus':'f_01625','Numbers':'f_01626','Deuteronomy':'f_01627'}

for bookname, filekey in books.items():
	ref = "Onkelos " + bookname
	if(bookname == "Numbers"):
		tools.createBookRecord(server, apikey, ref, "Targum " + ref, "Targum","Targum Onkelos Numbers")
	else:
		tools.createBookRecord(server, apikey, ref, "Targum " + ref, "Targum")
	tools.preprocess(filekey)
	text_whole = tools.parseText(filekey,ref)
	tools.postText(server, apikey, ref ,text_whole)

