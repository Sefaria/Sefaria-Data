# -*- coding: utf8 -*-

import pdb
import re
import sys
import os
from fuzzywuzzy import fuzz
class Match:
	def __init__(self, in_order=False, acronyms_file="", min_ratio=70, guess=False):
		self.min_ratio = min_ratio
		self.acronyms_file = acronyms_file
		self.in_order = in_order
		self.acronyms = {}
		self.step = 5
		self.found_dict = {}
		self.confirmed_dict = {}
		self.guess = guess
		if acronyms_file != "":
			f = open(acronyms_file, 'r')
			count = 0
			RT = ""
			for line in f:
				count+=1
				line = line.replace("\n", "")
				if count == 1:
					if not line in self.acronyms.keys():
						self.acronyms[line] = []
					RT = line
				elif count == 2:
					self.acronyms[RT].append(line)
				elif count == 3:
					count=0
			f.close()
		self.non_match_file = open('non_matches', 'w')

	def removeHTMLtags(self, line):
		html_start_tag = re.compile('<.*?>')
		html_end_tag = re.compile('</.*?>')
		match = re.search(html_start_tag, line)
		while match:
			line = line.replace(match.group(0), "")
			match = re.search(html_start_tag, line)
		match = re.search(html_end_tag, line)
		while match:
			line = line.replace(match.group(0), "")
			match = re.search(html_end_tag, line)
		return line

	def replaceAcronyms(self, dh):
		if self.acronyms_file == "":
			return []
		dh_list = []
		duplicates = False
		for acronym in self.acronyms:
			if acronym in dh:
				for expansion in self.acronyms[acronym]:
					new_dh = dh.replace(acronym, expansion)
					if new_dh.find('"')>=0 or new_dh.find("'")>=0:
						temp_dh_list = self.replaceAcronyms(new_dh)
						for i in range(len(temp_dh_list)):
							dh_list.append(temp_dh_list[i])
						return dh_list
					else:
						dh_list.append(new_dh)
		return dh_list
							
	def removeEtcFromDH(self, dh):
		etc = " כו'"
		etc_plus_and = " וכו'"
		dh_arr = dh.split(" ")
		last_word = dh_arr[len(dh_arr)-1]
		if dh.find(etc_plus_and) >= 0:
			dh = dh.replace(etc_plus_and, "")
		elif dh.find(etc) >= 0:
			dh = dh.replace(etc, "")
		return dh

	def splitPara(self, para, len_phrase):
		len_phrase *= 2
		phrases = []
		words = para.split(" ")
		len_para = len(words)
		for i in range(len_para):
			phrase = ""
			if i+len_phrase >= len_para:
				j = i
				while j < len_para:
					phrase += words[j] + " "
					j+=1
				phrases.append(phrase)
				break
			else:
				for j in range(len_phrase):
					phrase += words[i+j] + " "
				phrases.append(phrase)
		return phrases
	
	def forceUTF(self, list_dh):
		new_list = []
		for orig_dh in list_dh:
			#pdb.set_trace()
			#if orig_dh != orig_dh.encode('utf-8'):
			#	orig_dh = orig_dh.encode('utf-8')
			new_list.append(orig_dh)
		return new_list	

	def match_list(self, dh_orig_list, page, page_num=-1):
		self.found_dict = {}
		self.page_num = page_num
		self.dh_orig_list = self.forceUTF(dh_orig_list)
		dh_pos = 0
		for dh in self.dh_orig_list:
			self.match(dh, page, dh_pos)
			dh_pos+=1
		self.non_match_file.close()
		return self.multipleMatches()
			
	def match(self, orig_dh, page, dh_position, ratio=85):
		partial_ratios = []	
		self.found_dict[dh_position] = {}
		self.found_dict[dh_position][orig_dh] = []
		dh = self.removeEtcFromDH(orig_dh)
		found = 0
		dh_acronym_list = []
		if dh.find('"') >= 0 or dh.find("'")>=0:
			dh_acronym_list = self.replaceAcronyms(dh)
		for line_n, para in enumerate(page):
			  found_this_line = False
			  para = self.removeHTMLtags(para)
			  para = para.encode('utf-8')
			  if dh in para:
				found += 1
				self.found_dict[dh_position][orig_dh].append((line_n, 100))
				continue
			  para_pr = fuzz.partial_ratio(dh, para)
			  if para_pr < 40: #not worth checking
				continue
			  elif para_pr >= ratio:
				found += 1
				self.found_dict[dh_position][orig_dh].append((line_n, para_pr))
				continue	  	
			  phrases = self.splitPara(para, len(dh)) 
			  for phrase in phrases:
				phrase_pr = fuzz.partial_ratio(dh, phrase)
				if found_this_line == True:
					break
				if dh in phrase: 
					found += 1
					self.found_dict[dh_position][orig_dh].append((line_n, 100))
					break
				elif phrase_pr >= ratio:
					found += 1
					self.found_dict[dh_position][orig_dh].append((line_n, phrase_pr))
					break
				for expanded_acronym in dh_acronym_list:  #only happens if there is an acronym, found_dh refers to expanded acronym
					acronym_pr = fuzz.partial_ratio(expanded_acronym, phrase)
					if expanded_acronym in phrase: 
						found += 1
						self.found_dict[dh_position][orig_dh].append((line_n, 100))
						found_this_line = True
						break
					elif acronym_pr >=ratio:
						found += 1
						self.found_dict[dh_position][orig_dh].append((line_n, acronym_pr))
						found_this_line = True
						break
		if found == 0:
			if ratio > self.min_ratio:
				self.match(orig_dh, page, dh_position, ratio-self.step)
			else:
				self.non_match_file.write(orig_dh)
				self.non_match_file.write("\n")

	def getMinMax(self, dh_pos):
		temp = dh_pos-1
		min = 0
		while temp >= 0:
			if len(self.found_dict[temp][self.dh_orig_list[temp]]) >= 1 and self.confirmed_dict[temp+1][0] > 0:
				try:
				  min = self.confirmed_dict[temp+1][0]-1
				  break
				except:
				  pdb.set_trace()
			temp -= 1
		temp = dh_pos+1
		max = len(self.dh_orig_list)-1
		while temp <= max:
			temp_list = self.found_dict[temp][self.dh_orig_list[temp]]
			if len(temp_list) == 1:
				max = temp_list[0][0]
				break
			temp+=1
		return (min, max)

	def bestGuessFirst(self, list_lines):
		max = 0
		best_line = 0
		for line_n, pr in list_lines:
			if pr > max:
				best_line = line_n
				max = pr
		if self.guess == True:
			return [best_line+1]
		else:
			new_list_lines = [best_line+1]
			for line_n, pr in list_lines:
				if pr == max and line_n != best_line:
					new_list_lines.append(line_n+1)
			return new_list_lines
	
	def multipleMatches(self):
		self.confirmed_dict = {}
		for dh_pos in self.found_dict:
			dh = self.dh_orig_list[dh_pos]
			dh_found_list = self.found_dict[dh_pos][dh] 
			self.confirmed_dict[dh_pos+1] = []
			if len(dh_found_list) == 0:
				self.confirmed_dict[dh_pos+1] = [0]
			elif len(dh_found_list) == 1:
				self.confirmed_dict[dh_pos+1] = [dh_found_list[0][0]+1]
			elif len(dh_found_list) > 1:
				if self.in_order == False:
					self.confirmed_dict[dh_pos+1] = self.bestGuessFirst(dh_found_list)
				else:
					self.multipleInOrder(dh_pos, dh_found_list, dh)
		return self.confirmed_dict

	def multipleInOrder(self, dh_pos, dh_found_list, dh):
		min, max = self.getMinMax(dh_pos)
		list_actual_lines = []
		for line_n, pr in dh_found_list:
			if line_n >= min and line_n <= max:
				list_actual_lines.append((line_n, pr))
		if len(list_actual_lines) == 0:
			 self.confirmed_dict[dh_pos+1] = [0]
		elif len(list_actual_lines) == 1:
			self.confirmed_dict[dh_pos+1] = [list_actual_lines[0][0]+1]
		elif len(list_actual_lines) > 1: 
			self.confirmed_dict[dh_pos+1] = self.bestGuessFirst(list_actual_lines)