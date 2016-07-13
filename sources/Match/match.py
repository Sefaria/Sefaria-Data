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
# -*- coding: utf-8 -*-
import json 
import pdb
import os
import sys
import re
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud	

from fuzzywuzzy import fuzz

class Match:
    def __init__(self, in_order=False, acronyms_file="", min_ratio=80, guess=False, range=False, can_expand=True):
        self.range = range
        self.ranged_dict = {}
        self.min_ratio = min_ratio
        self.acronyms_file = acronyms_file
        self.in_order = in_order
        self.acronyms = {}
        self.can_expand = can_expand
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
        if isinstance(dh, unicode):
            dh = dh.encode('utf-8')
        etc = " כו'"
        etc_plus_and = " וכו'"
        dh_arr = dh.split(" ")
        last_word = dh_arr[len(dh_arr)-1]

        try:
          if dh.find(etc_plus_and) >= 0:
            dh = dh.replace(etc_plus_and, "")
          elif dh.find(etc) >= 0:
            dh = dh.replace(etc, "")
        except:
          pdb.set_trace()
        return dh


    def match_list(self, dh_orig_list, page, ref_title=None):
        if self.can_expand == True and ref_title == None:
            print 'Error: If can_expand is set to true, you must pass a valid reference so we know where to start expanding from.'
            pdb.set_trace()
        self.maxLine = len(page)-1
        self.ref_title = ref_title
        self.found_dict = {}
        self.ranged_dict = {}
        self.dh_orig_list = dh_orig_list
        dh_pos = 0
        for dh in self.dh_orig_list:
            self.match(dh, page, dh_pos)
            dh_pos+=1
        self.non_match_file.close()
        self.multipleMatches()
        if self.range==True:
            self.getRanges()
        return self.confirmed_dict

    def match(self, orig_dh, page, dh_position, ratio=90):
        partial_ratios = []
        self.found_dict[dh_position] = {}
        self.found_dict[dh_position][orig_dh] = []
        dh = self.removeEtcFromDH(orig_dh)
        found = 0
        for line_n, para in enumerate(page):
          skip_this_line = False
          len_already_here = len(self.found_dict[dh_position][orig_dh])
          if len_already_here > 0:
             for i in range(len_already_here):
                if line_n == self.found_dict[dh_position][orig_dh][i][0]:
                    skip_this_line = True
                    break
          if skip_this_line == True:
            continue
          found_this_line = False
          para = self.removeHTMLtags(para)
          if isinstance(para, unicode):
            para = para.encode('utf-8')
          para_pr = fuzz.partial_ratio(dh, para)
          if para_pr < 40: #not worth checking
              continue
          elif len(para)*4 < len(dh) and self.can_expand == True:
              result_pr = self.matchExpandPara(para, dh, dh_position, orig_dh, line_n+1, ratio)
              if result_pr > 0:
                found+=1
                continue
          elif len(dh)<25 and len(para)<25:
              if para_pr >= 90:
                found+=1
                self.found_dict[dh_position][orig_dh].append((line_n, para_pr))
          elif para_pr >= ratio:
              found+=1
              self.found_dict[dh_position][orig_dh].append((line_n, para_pr))
        if found == 0:
            if ratio > self.min_ratio:
                self.match(orig_dh, page, dh_position, ratio-self.step)

    def matchExpandPara(self, para, dh, dh_position, orig_dh, line_n, ratio):
        start_line = line_n-1
        end_line = start_line
        current_ref = Ref(self.ref_title+" "+str(line_n))
        while len(para)*2 < len(dh):
            end_line+=1
            try:
                next_line_ref = current_ref.next_segment_ref()
            except:
                break
            current_ref = current_ref.to(next_line_ref)
            para = current_ref.text("he").ja().flatten_to_string()
            if isinstance(para, unicode):
                para = para.encode('utf-8')
        if dh == para:
            for i in range(end_line-start_line+1):
                self.found_dict[dh_position][orig_dh].append((i+start_line, 100))
            return 100
        para_pr = fuzz.partial_ratio(dh, para)
        if para_pr >= ratio:
            for i in range(end_line-start_line+1):
                self.found_dict[dh_position][orig_dh].append((i+start_line, para_pr))
            return para_pr
        return self.matchAcronyms(dh, para)

    def matchAcronyms(self, dh, text):
        dh_acronym_list = []
        if dh.find('"') >= 0 or dh.find("'")>=0:
            dh_acronym_list = self.replaceAcronyms(dh)
        for expanded_acronym in dh_acronym_list:  #only happens if there is an acronym, found_dh refers to expanded acronym
            acronym_pr = fuzz.partial_ratio(expanded_acronym, text)
            if expanded_acronym in text:
                self.found_dict[dh_position][orig_dh].append((line_n, 100))
                found_this_line = True
                return 100
            elif acronym_pr >=ratio:
                self.found_dict[dh_position][orig_dh].append((line_n, acronym_pr))
                found_this_line = True
                return acronym_pr
        return 0

    def getMin(self, dh_pos):
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
            if len(self.found_dict[0][self.dh_orig_list[0]])>0:
                min = self.found_dict[0][self.dh_orig_list[0]][0][0]
                for line_n, pr in self.found_dict[0][self.dh_orig_list[0]]:
                    if line_n < min:
                        min = line_n
            else:
                min = 0
        return min

    def getMax(self, dh_pos):
        max = -1
        highest = len(self.dh_orig_list)-1
        if dh_pos == highest:
            return self.maxLine
        else:
            temp = dh_pos+1
        while max == -1 and temp <= highest:
            next_list = self.found_dict[temp][self.dh_orig_list[temp]]
            for line_n, pr in next_list:
                if line_n > max:
                    max = line_n
            temp+=1
        if max == -1:
            return self.maxLine
        return max

    def getRanges(self):
        for dh_pos in self.found_dict:
            dh = self.dh_orig_list[dh_pos]
            if self.confirmed_dict[dh_pos+1][0] == 0:
                min = self.getMin(dh_pos)
                max = self.getMax(dh_pos)
                if min > max:
                    max = self.maxLine
                if max > -1:
                    self.ranged_dict[dh_pos+1] = "0:"+str(min+1)+"-"+str(max+1)
                else:
                    self.ranged_dict[dh_pos+1] = "0:1" #this case only happens where there were no comments to begin with, match lib shouldn't have been used
            elif len(self.confirmed_dict[dh_pos+1]) > 1:
                looking_for_values = True
                min = 100000
                max = -1
                for line_n in self.confirmed_dict[dh_pos+1]:
                    if line_n < min:
                        min = line_n
                    if line_n > max:
                        max = line_n
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
        min = self.getMin(dh_pos)
        max = self.getMax(dh_pos)
        list_actual_lines = []
        if min <= max:
          for line_n, pr in dh_found_list:
            if line_n >= min and line_n <= max:
                list_actual_lines.append((line_n, pr))
        if len(list_actual_lines) == 0:
             self.confirmed_dict[dh_pos+1] = [0]
        elif len(list_actual_lines) == 1:
            self.confirmed_dict[dh_pos+1] = [list_actual_lines[0][0]+1]
        elif len(list_actual_lines) > 1:
            self.confirmed_dict[dh_pos+1] = self.bestGuessFirst(list_actual_lines)