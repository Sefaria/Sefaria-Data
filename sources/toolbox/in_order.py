# -*- coding: utf-8 -*-
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json 
import pdb
import os
import sys
from bs4 import BeautifulSoup
import re
p = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *
import argparse
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud

#user inputs a tag that always marks a new segment,
#			the starting number (default is 0),
#(eventually)whether or not more than one segment can be mentioned on one line (default is False),
# and the output are all places where this doesn't fit

curr_num = 0

multiple_segments = False

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Title of input file to be checked.")
    parser.add_argument("-t", "--tag", help="The tag that always indicates, and only ever indicates, what section the following text belongs to.  As an example,"+
    			"suppose the first section of the text is marked '@22 א' and the second section is marked '@22 ב', in this case, '-t @22'.", default="")
    parser.add_argument("-n", "--start_number", help="The start_number is one below the number of the first section of the text.  "+
    				"If the first section is marked '@22 א', then the first section is section one, and the start_number should be 0.", default=0)
	parser.add_argument("-m", "--multiple_segments", help="Multiple segments can be True or False and if true, this indicates that there can a section header "+
					" such as '@22 א ב ג' which means that the following text is linked to all three sections.", default=False) 				    					
	parser.add_argument("-o", "--order", help="Name of output file.", default="in_order.csv")
    args = parser.parse_args()
	tag = args.tag
	file = args.file
	output_file = open('in_order.csv', 'w')
	open_file = open(file, 'r')
	multiple_segments = args.multiple_segments
	perfect = True
	for line in open_file:
		actual_line = line
		if line.find(tag)>=0:
			line = removeAllStrings(["@", "1", "2", "3", "4", "5", "6", "7", "8", "9"], line)
			if line[0] == ' ':
				line = line[1:]
			if line[len(line)-1] == ' ':
				line = line[:-1]
			if multiple_segments == True and len(line.split(" "))>1:			
				all = line.split(" ")
				num_list = []
				for i in range(len(all)):
					num_list.append(getGematria(all[i]))
				num_list = sorted(num_list)
				for poss_num in num_list:
					if poss_num < curr_num:
						perfect = False
						output_file.write("Previous_section:_"+str(curr_num)+",_Current_section:_"+str(poss_num)+",_Current_line:_"+actual_line+"\n")
					else:
						curr_num = poss_num
			else:
				poss_num = getGematria(line)
				print poss_num
				if poss_num < curr_num:
					perfect = False
					output_file.write("Previous_section:_"+str(curr_num)+",_Current_section:_"+str(poss_num)+",_Current_line:_"+actual_line+"\n")
				curr_num = poss_num
			
	if perfect == True:
		print "100% in order!"
	else:
		print "Not in order.  See file: in_order"+str(file)+".csv"