# -*- coding: utf-8 -*-

masechet = 'נדרים'
directory = 'Ran'

def read():
	commFile = open('RanAP','r')
	commText = commFile.readlines()
        commFile.close()
	for line in commText:
		line = line.replace("<B><U><span style='color:RGB(34,80,136);'><u>","")
		line = line.replace("</u></span><BR></U></B></span><br>", "X")
		lines = line.split("X", 1)
		filename = masechet+lines[0].replace(' ', '_')+'.txt'
		filename = filename.replace('דף', '').replace('_-', '')
		#print filename
		f = open(directory+'/'+filename,'w')
		comments = lines[1].split("<B>")
		for c in comments:
			if "." in c:
				c = c.replace("</B>", "").lstrip()
				f.write(c.split(".",1)[0]+"\n")
				f.write(c.replace(".", " -")+"\n")
			else:
				if len(c) > 0:
					f.write(c.split("</B>",1)[0]+"\n")
					f.write(c.replace("</B>", " -")+"\n")
					#print filename
					#print "We have a problem - no period to mark DHM"
					#print "comment is: "+c+"\n"


read()
