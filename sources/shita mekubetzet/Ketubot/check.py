# -*- coding: utf-8 -*-
title = "P0"
start = 33
end = 55
daf_file = open('daf_file', 'w')
for count in range(55-33):
	f=open(title+str(count+start)+".txt", 'r')
	for line in f:
		if line.find('@08דף')>=0:
			daf_file.write('page: '+str(count+start)+'\n')
			daf_file.write(line)
			daf_file.write('\n')