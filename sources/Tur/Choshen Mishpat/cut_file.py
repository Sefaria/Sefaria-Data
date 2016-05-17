# -*- coding: utf-8 -*-

import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Title of input file to be divided in half.")
    parser.add_argument("--first_half", help="Title of file to put the first half of the original file.")
    parser.add_argument("--second_half", help="Title of file to put the second half of the original file.")
    parser.add_argument("--where", help="String that identifies where the original file should be split.")
    args = parser.parse_args()
    where = args.where
    if where:
    	file = open(args.file, 'r')
    	where_pos = -1
    	for count, line in enumerate(file):
    		if line.find(where)>=0:
    			where_pos = count
    			break
    	print where_pos
    	first_half = open(args.first_half, 'w')
    	second_half = open(args.second_half, 'w')
    	file.close()
    	file = open(args.file, 'r')
    	for count, line in enumerate(file):
    		if count < where_pos:
    			first_half.write(line)
    		else:
    			second_half.write(line)
    	first_half.close()
    	second_half.close()
    	file.close()