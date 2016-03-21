# -*- coding: utf-8 -*-

title = "CN-"
start_title = 1
num_files = 72
masechet = "Bava Metziah"
daf_file = open('daf.txt', 'w')
for count_file in range(num_files):
	if count_file < 9:
		f = open(masechet+"/"+title+"0"+str(start_title+count_file)+".txt")
	else:
		f = open(masechet+"/"+title+str(start_title+count_file)+".txt")
	for line in f:
		if line.find("עמוד")>=0:
			daf_file.write(line)
			daf_file.write('\n')
daf_file.close()