# -*- coding: utf8 -*-
'''
To use the matching library, first instantiate a Match object.  
As an example:
match_obj = Match(in_order=True, min_ratio=70, guess=False)
--or--
match_obj = Match()
The Match constructor has four optional parameters it can be passed, all of which have default values.
1. in_order (default is False) - if true, the dibbur hamatchils must be matched in order to the text such that
when a dibbur hamatchil matches multiple lines of text, the lines matching the dibbur hamatchil before and after 
the current one are checked, and matches that are not in order are thrown out.
2. acronyms_file (default is no file) - if set, this file's list of acronyms can be used to match acronyms to 
the words or phrases that they are an acronym of.
the acronyms_file is in the following format:
א'
אחת

בה"מ
בית המקדש

יר"מ
יהי רצון מלפניך

In other words, one line is the acronym, the next is the actual word or phrase, and then a blank line.

3. min_ratio (default is 70) -  The Match class uses the python library fuzzywuzzy to calculate 
the similarity between two strings, returning a number between 0 and 100 indicating how similar two strings are.  
The Match class' match function starts out looking
for matches of at least 85 (see below in the match function where you can change the number 85 to whatever you want),
and then, when there is no match it recursively lowers the ratio it is looking for by self.step, which is set
in the constructor to 5.  (Also, since it is often the case that the line to match to the dibbur hamatchil is much longer than
the dibbur hamatchil, and in this case, partial_ratios are much lower than they should be,
the match function divides up the line into smaller units so that those units can match better).

4. guess (default is False) - If False, returns a list of all possible guesses for the specific 
dibbur hamatchil (except those that have been thrown out as out-of-order if 'in_order' is set to True.  
The match with the highest partial_ratio is the first item in the list.  If guess is True,
returns only the guess with the highest partial_ratio.  In a tie, the first one is chosen.

5. range (default is False) - This parameter determines what the output will look like.  I'll explain this more below.

After instantiating a Match object as match_obj, then all that needs to be done is to call 
the match_list function as below:

result = match_obj.match_list(dh_list[j], perek[j])

In this example, the first argument is the list of the dibbur hamatchils, the second argument is a list of the text
that is to be matched.
The match_list function then goes through the list of dibbur hamatchils and calls the match function on each one and
the list of text.   Then, it calls the mutlipleMatches function to deal with dibbur hamatchils that have multiple 
matches.  The behvaior of multipleMatches, as can be seen below, depends on whether 
the in_order parameter was set to True or left as the default as False.  If True, then the function getInOrder is called
and removes out-of-order matches.

After running match_list above, a dictionary will be returned.
It will look completely different depending on whether 'range' is set to True or left as the default of False.
(The cases are so different because I designed them months apart.  Sorry about that.)
If range is False, here is an example of how the result might look:
    {1: [2], 2: [2], 3: [3], 4: [3], 5: [4], 6: [5], 7: [6,7], 8: [0], 9: [8], 10: [9]}
    Each key corresponds exactly to the order of the dibbur hamatchils.
    In other words, the first dibbur hamatchil is matched to line 2 of the text 'perek[j]'.
    Notice that the 7th dibbur hamatchil is matched to both lines 6 and 7.  This means that it was matched
    to multiple lines and neither of them could be removed as impossible.  In this case, 'guess' must have been set to False,
    so that the entire list is returned, because if 'guess' was set to True, only line 6 would have been returned since it is
    the first one.
    Finally, notice that dibbur hamatchil 8 is matched to line 0.  There is no line 0, and therefore, '0' indicates
    that no match could be found.
If range is True, the same result might look like:
    {1: '2', 2: '2', 3: '3', 4: '3', 5: '4', 6: '5', 7: '6-7', 8: '5-8', 9: '8', 10: '9'}

'''
import pdb
import re
import sys
import os
from fuzzywuzzy import fuzz

class Match:
    def __init__(self, in_order=False, acronyms_file="", min_ratio=70, guess=False, range=False):
        self.range = range
        self.ranged_dict = {}
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

    def match_list(self, dh_orig_list, page):
        self.maxLine = len(page)-1
        self.found_dict = {}
        self.dh_orig_list = self.forceUTF(dh_orig_list)
        dh_pos = 0
        for dh in self.dh_orig_list:
            self.match(dh, page, dh_pos)
            dh_pos+=1
        self.non_match_file.close()
        self.multipleMatches()
        if self.range==True:
            self.getRanges()
        return self.confirmed_dict

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
        min = 0
        if dh_pos > 0:
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
        else:
            min = 100000
            for line_n, pr in self.found_dict[0][self.dh_orig_list[0]]:
                if line_n < min:
                    min = line_n
        temp = dh_pos+1
        highest = len(self.dh_orig_list)-1
        max = -1
        while temp <= highest:
            temp_list = self.found_dict[temp][self.dh_orig_list[temp]]
            if len(temp_list) == 1:
                max = temp_list[0][0]
                break
            temp+=1
        if max==-1 and dh_pos != highest:
            next_list = self.found_dict[dh_pos+1][self.dh_orig_list[dh_pos+1]]
            for line_n, pr in next_list:
                if line_n > max:
                    max = line_n
        elif max==-1:
            my_list = self.found_dict[dh_pos][self.dh_orig_list[dh_pos]]
            for line_n, pr in my_list:
                if line_n > max:
                    max = line_n
        if max==-1:
            max=self.maxLine
        if min > max:
            min = 0
            max = self.maxLine
        return (min, max)

    def getRanges(self):
        for dh_pos in self.found_dict:
            dh = self.dh_orig_list[dh_pos]
            if self.confirmed_dict[dh_pos+1][0] == 0:
                min, max = self.getMinMax(dh_pos)
                self.ranged_dict[dh_pos+1] = "0:"+str(min+1)+"-"+str(max+1)
            elif len(self.confirmed_dict[dh_pos+1]) > 1:
                looking_for_values = True
                while looking_for_values==True:
                    min = 100000
                    max = -1
                    for line_n in self.confirmed_dict[dh_pos+1]:
                        if line_n < min:
                            min = line_n
                        if line_n > max:
                            max = line_n
                    looking_for_values = False
                    min+=1
                    max+=1
                self.ranged_dict[dh_pos+1] = str(min)+"-"+str(max)
        for dh_pos in self.confirmed_dict:
            self.confirmed_dict[dh_pos] = str(self.confirmed_dict[dh_pos][0])
            if dh_pos in self.ranged_dict:
                self.confirmed_dict[dh_pos] = self.ranged_dict[dh_pos]

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
                if line_n != best_line:
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
                    self.getInOrder(dh_pos, dh_found_list, dh)
        return self.confirmed_dict

    def getInOrder(self, dh_pos, dh_found_list, dh):
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
            if self.range == True:
                for line_n, pr in list_actual_lines:
                    self.confirmed_dict[dh_pos+1].append(line_n+1)
            else:
                self.confirmed_dict[dh_pos+1] = self.bestGuessFirst(list_actual_lines)