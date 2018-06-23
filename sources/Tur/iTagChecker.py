
from lxml import etree
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
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, p)

os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *

class iTagChecker:

    def __init__(self, bookRef, commentators, refReplace, commentatorIgnored, specialCommentators):
        self.commentatorIgnored = commentatorIgnored # when counting the number of comments of say, Darchei Moshe, on the Tur
                                                    # sometimes, the Darchei Moshe comments on the Beit Yosef.  we want to
                                                    # ignore those comments.  commentatorIgnored = "Beit Yosef" in this example
        self.specialCommentators = specialCommentators #this is an array of which commentators cannot comment on commentatorIgnored
        self.commentators = commentators # ["Beit Yosef", "Bach"]
        self.bookRef = bookRef # Ref("Tur, Orach Chaim")
        self.commentator_refs = {}
        self.number_off_report = {}
        self.out_order_report = {}
        self.refReplace = refReplace  #refReplace is "Tur"; refReplace needs to be replaced in the Ref so we use "Bach on Orach Chaim" instead of "Bach on Tur, Orach Chaim"
        bookRefStr = bookRef.normal()
        for count, commentator in enumerate(commentators):
            self.commentator_refs[commentator] = bookRefStr.replace(self.refReplace, commentator)
            commentators[count] = commentator.replace(" ", "_")
        for count, specComm in enumerate(self.specialCommentators):
            self.specialCommentators[count] = self.specialCommentators[count].replace(" ", "_")



    def run(self):
        for section in self.bookRef.all_subrefs():
            self.number_off_report[section.normal()], self.out_order_report[section.normal()] = self.checkSection(section)


    def output(self):
        '''reportFile = open("out_order_"+self.bookRef.normal()+".txt", 'a')
        for section in sorted(self.out_order_report.keys()):
            if self.out_order_report[section] != "":
                reportFile.write(self.out_order_report[section]+"\n")
        reportFile.close()'''

        wrong = 0
        total = len(self.number_off_report.keys())

        reportFile = open("big_probs_number_off_"+self.bookRef.normal()+".txt", 'w')
        for section in sorted(self.number_off_report.keys()):
            if self.number_off_report[section] != "":
                reportFile.write(section+": "+self.number_off_report[section]+"\n")
                wrong += 1
        reportFile.close()
        print float(wrong)/float(total)
        print "\n"


    def getITagsFromSiman(self, commentator, section):
        iTags = []
        refText = section.text("he").as_string() #need to add the begin and end tags so etree can process it
        possITags = BeautifulSoup(refText)('i')

        for possItag in possITags:
            possItag['data-commentator'] = possItag['data-commentator'].replace(" ","_")
            if possItag['data-commentator'] == commentator:
                iTags.append(possItag)

        return iTags


    def anythingSkipped(self, iTags, how_many_comments):
        '''logic of this: it's OK if they go in order, and if they dont, they have to be equal and .2 > .1
        '''
        flag_msg = ""
        prev_data = 0
        for iTag in iTags:
            this_data = iTag['data-order']
            first_level = int(this_data.split(".")[0])
            second_level = int(this_data.split(".")[1])
            if prev_data == 0:
                prev_data = this_data
            else:
                if int(prev_data.split(".")[0]) + 1 == first_level:
                    prev_data = this_data
                elif int(prev_data.split(".")[0]) == first_level and int(prev_data.split(".")[1]) + 1 == second_level:
                    prev_data = this_data
                else:
                    flag_msg += this_data + " follows " + prev_data + "\n"
                    prev_data = this_data
        return flag_msg


    def getNumberComments(self, ref, looking_for):
        links = LinkSet(ref)
        how_many = 0
        for link in links:
            link_refs = link.contents()['refs']
            if link_refs[0].find(looking_for) >= 0 or link_refs[1].find(looking_for) >= 0:
                how_many += 1
        return how_many

    def countSubRefs(self, ref):
        all_subrefs = ref.all_subrefs()
        count = 0
        for subref in all_subrefs:
            if subref.text("he").text != []:
                count += 1
        return count

    def checkSection(self, section):
        number_off_msgs = {}
        out_order_msgs = {}
        number_off_msgs[section.normal()] = ""
        out_order_msgs[section.normal()] = ""

        for commentator in self.commentators:
            iTags = self.getITagsFromSiman(commentator, section)
            how_many_itags = len(iTags)
            commentator_ref = Ref(section.normal().replace(self.refReplace, commentator))
            if len(commentator_ref.text("he").text) == 0: #ref not valid
                how_many_comments = 0
            elif commentator in self.specialCommentators:
                how_many_comments = self.getNumberComments(commentator_ref, "Tur")
            else:
                how_many_comments = self.countSubRefs(commentator_ref) #len(commentator_ref.all_subrefs()) not working always, Ref("Beit Yosef, Yoreh Deah 112:39") which has text [] is still counted as a subref


            number_off_msg = ""
            if abs(how_many_itags-how_many_comments) > 0:
                number_off_msg +=  "Number of iTags is "+str(how_many_itags)+", and number of comments is "+str(how_many_comments)+"\n"

            out_order_msg = ""
            out_order_msg += self.anythingSkipped(iTags, how_many_comments)

            if len(number_off_msg) > 0:
                number_off_msgs[section.normal()] += "For commentator "+commentator + ": " + number_off_msg

            if len(out_order_msg) > 0:
                out_order_msgs[section.normal()] += "For commentator "+commentator + ": " + out_order_msg

        return number_off_msgs[section.normal()], out_order_msgs[section.normal()]



if __name__ == "__main__":
    commentators = ["Bach", "Beit Yosef", "Prisha", "Drisha", "Darchei Moshe"]
    specialCommentators = ["Drisha", "Prisha", "Darchei Moshe"]
    refs = [Ref("Tur, Even HaEzer"), Ref("Tur, Orach Chaim"), Ref("Tur, Yoreh Deah")]

    for ref in refs:
        print ref.normal()
        checker = iTagChecker(ref, commentators, "Tur", "Beit Yosef", specialCommentators)
        checker.run()
        checker.output()

