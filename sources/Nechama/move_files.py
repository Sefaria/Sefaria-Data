import shutil
parshat_bereshit = ["1", "2", "30", "62", "84", "148","212","274","302","378","451","488","527","563","570","581","750","787","820","844","894","929","1021","1034","1125","1183","1229","1291","1351","1420"]
for file in parshat_bereshit:
	file = "html_sheets/{}.html".format(file)
	f = open(file)
	shutil.copy(file, "html_sheets/Bereshit")
	f.close()

