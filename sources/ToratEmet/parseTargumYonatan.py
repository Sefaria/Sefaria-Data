# -*- coding: utf-8 -*-

import tools

apikey = '' #Add your API key
server = 'www.sefaria.org'

books = [['Genesis','f_01588'],['Exodus','f_01589'],['Leviticus','f_01590'],['Numbers','f_01591'],['Deuteronomy','f_01592']]

for book in books:
	filekey = book[1]
	ref = "Targum Jonathan on " + book[0]
	tools.createBookRecord(server, apikey, ref, "Targum Yonatan on " + book[0], "Targum")
	tools.preprocess(filekey)
	text_whole = tools.parseText(filekey,ref)
	tools.postText(server, apikey, ref ,text_whole)
	
