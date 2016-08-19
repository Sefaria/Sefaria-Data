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
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.insert(0, '../Match/')
from match import Match
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *


sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud




class Maharam:
    def __init__(self):
        '''
        dictionary for each category allows matching to work
        then after we have match dictionaries for in order and out of order for each category
        we go through the actual self.dh1_dict and self.dh2_dict, checking its category
        whatever the category is we increment the maharam line and post the link between maharam and the appropriate
        book based on the category. remember to deal with paragraph case and gemara case.
        '''
        self.heb_numbers = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "ששי", "שביעי", "שמיני", "תשיעי", "עשירי", "אחד עשר", "שנים עשר", "שלשה עשר", "ארבעה עשר"]
        self.comm_dict = {}
        self.dh1_dict = {}
        self.dh2_dict = {}
        self.gemara1_dict = {}
        self.gemara2_dict = {}
        self.tosafot1_dict = {}
        self.tosafot2_dict = {}
        self.rashi1_dict = {}
        self.rashi2_dict = {}
        self.mishnah1_dict = {}
        self.mishnah2_dict = {}
        self.rashi ='רש"י'
        self.tosafot = "תוס"
        self.dibbur_hamatchil = ['בד"ה', 'ד"ה', 'בא"ד', """ד'"ה"""]
        self.gemara = "גמ"
        self.amud_bet = 'ע"ב'
        self.mishnah = ['במשנה', 'מתני']
        self.current_daf = 3
        self.current_perek = 1
        self.categories = ['rashi', 'tosafot', 'gemara', 'mishnah', 'paragraph']
        self.links_to_post = []



    def convertRefCommentaryTalmud(self, ref, replace_text):
        ref = ref.replace('.', ':')
        if ref.find('-')==-1:
            first_case = True
        else:
            which_range = ref.split('-')[1].find(':')
            if which_range == -1:
                first_case = True
                ref = ref.split('-')[0]
            else:
                refs = []
                beg, end = ref.split('-')
                refs.append(beg)
                refs.append(end)
                first_colon = beg.find(':')
                second_colon = beg.rfind(':')
                if second_colon <= first_colon:
                    pdb.set_trace()
                beg = beg[0:second_colon]
                only_colon = end.find(':')
                if only_colon == -1:
                    pdb.set_trace()
                end = end[0:only_colon]
                return beg.replace(replace_text,"")+'-'+end
        if first_case:
            first_colon = ref.find(':')
            second_colon = ref.rfind(':')
            if second_colon <= first_colon:
                pdb.set_trace()
            ref = ref[0:second_colon]
        return ref.replace(replace_text, "")

    def addDHComment(self, dh1, dh2, comment, category, heb_category):
        if hasTags(dh1) or hasTags(dh2) or hasTags(comment):
            print "tags!"
            pdb.set_trace()
        if len(dh1)>0 and len(dh2)>0:
            self.dh1_dict[self.current_daf].append((category, dh1))
            self.dh2_dict[self.current_daf].append((category, dh2))
            self.comm_dict[self.current_daf].append(self.heb_category+" <b>"+dh1+" "+dh2+" </b>"+comment)
        elif len(dh1)>0:
            self.dh1_dict[self.current_daf].append((category, dh1))
            self.dh2_dict[self.current_daf].append((category, ""))
            self.comm_dict[self.current_daf].append(self.heb_category+" <b>"+dh1+" </b>"+comment)
        else:
            last_comment = len(self.comm_dict[self.current_daf])-1
            if last_comment == -1:
                self.comm_dict[self.current_daf].append(comment)
                self.dh1_dict[self.current_daf].append((category, ""))
                self.dh2_dict[self.current_daf].append((category, ""))
            else:
                self.comm_dict[self.current_daf][last_comment] += "<br>"+comment
        if category == 'gemara':
            self.gemara1_dict[self.current_daf].append(dh1)
            self.gemara2_dict[self.current_daf].append(dh2)
        elif category == 'rashi':
            self.rashi1_dict[self.current_daf].append(dh1)
            self.rashi2_dict[self.current_daf].append(dh2)
        elif category == 'tosafot':
            self.tosafot1_dict[self.current_daf].append(dh1)
            self.tosafot2_dict[self.current_daf].append(dh2)
        elif category == 'mishnah':
            self.mishnah1_dict[current_perek].append(dh1)
            self.mishnah2_dict[current_perek].append(dh2)

    def removeBDH(self, array):
        try:
            new_array = []
            for elem in array:
                elem = elem.replace('בד"ה', '')
                new_array.append(elem)
        except:
            pdb.set_trace()
        return new_array


    def getPerek(self, line):
        which_perek = -1
        for count, word in enumerate(self.heb_numbers):
            if line.find(word)>=0:
                which_perek = count+1
                break
        if which_perek == -1:
            pdb.set_trace()
        return which_perek


    def getDaf(self, line, current_daf):
        line = line.replace("@11 ", "@11")
        if line.split(" ")[0].find('דף')>=0:
            daf_value = getGematria(line.split(" ")[1].replace('"', '').replace("'", ''))
            if line.split(" ")[2].find(self.amud_bet)>=0:
                self.current_daf = 2*daf_value
            else:
                self.current_daf = 2*daf_value - 1
            actual_text = ""
            for count, word in enumerate(line.split(" ")):
                if count >= 3:
                    actual_text += word + " "
        else:
            self.current_daf += 1
            actual_text = line[3:]
        if not self.current_daf in self.dh1_dict:
            self.dh1_dict[self.current_daf] = []
            self.dh2_dict[self.current_daf] = []
            self.gemara1_dict[self.current_daf] = []
            self.gemara2_dict[self.current_daf] = []
            self.tosafot1_dict[self.current_daf] = []
            self.tosafot2_dict[self.current_daf] = []
            self.rashi1_dict[self.current_daf] = []
            self.rashi2_dict[self.current_daf] = []
            self.mishnah1_dict[self.current_perek] = []
            self.mishnah2_dict[self.current_perek] = []
        self.actual_text = actual_text
        return self.current_daf

    def getCategory(self, count, comment):
        comment = comment + ':'
        if count == 0 and len(comment) == 0:
            return ""
        self.heb_category = comment.split(" ")[0]
        if self.heb_category.find(self.rashi)>=0:
            category = 'rashi'
        elif self.heb_category.find(self.tosafot)>=0:
            category = 'tosafot'
        elif self.heb_category.find(self.gemara)>=0:
            category = 'gemara'
        elif self.heb_category in self.mishnah:
            category = 'mishnah'
        elif self.heb_category in self.dibbur_hamatchil:
            if count == 0:
                category = 'gemara'
        else:
            if count == 0:
                category = 'gemara'
            else:
                if comment.split(".",1)[0].find('וכו') > 0:
                    category = 'gemara'
                category = 'paragraph'
        return category


    def parseDH(self, comment, category):
        end_of_first_word = comment.find(' ')
        comment = comment[end_of_first_word+1:]
        marker_max = max(comment.rfind('.'), comment.rfind(':'))
        marker_min = min(comment.find('.'), comment.find(':'))
        if marker_min == -1:
            marker_min = max(comment.find('.'), comment.find(':'))
        if marker_min == marker_max or (onlyOne(comment, '.') and onlyOne(comment, ':') and comment.find('.')>comment.find(':')):
            if onlyOne(comment, "כו'"):
                dh1, comment = comment.split("כו'", 1)
                if len(comment)<5:
                    dh1 += "כו'"
                else:
                    dh1 += "כו'. "
                dh2 = ""
            elif comment.find("כו'")>=0: #multiple cases
                dh1, dh2, comment = comment.split("כו'", 2)
                dh1 += "כו' "
                if len(comment)<5:
                    dh2 += "כו'"
                else:
                    dh2 += "כו'. "
            else: #no periods or etc so nothing to work with, should this be a comment or DH?
                    #depends on whether it's paragraph comment??
                dh1 = comment
                dh2 = ""
                comment = ""
        elif comment.find(".")>=0:
            dh, comment = comment.split(".", 1)
            dh += ". "
            if dh.find("כו'")>=0:
                dh1, dh2 = dh.split("כו'", 1)
                dh1 += "כו' "
            else:
                dh1 = dh
                dh2 = ""
        self.addDHComment(dh1, dh2, comment, category, self.heb_category)


    def parseText(self, file):
        this_line = False
        for line in file:
            line = line.replace("\n", "").replace("@33", "").replace("@55", "").replace("@44","").replace("@77","").replace("@99","")
            if len(line)==0:
                continue

            if line.find("@00")>=0 and line.find("פרק")>=0:
                self.current_perek = self.getPerek(line)
                continue

            if line[0] == " ":    #not part of the logic, just solving something caused by the text file
                start = line.find("@11")
                line = line[start:]

            if line.find("@11")>=0:
                category = ""
                self.current_daf = self.getDaf(line, self.current_daf)

                if not self.current_daf in self.comm_dict:
                    self.comm_dict[self.current_daf] = []

                comments = self.actual_text.split(":")
                for count, comment in enumerate(comments):
                    if len(comment) < 2:
                        continue
                    category = self.getCategory(count, comment)
                    if category == "":
                        continue
                    if hasTags(comment):
                        pdb.set_trace()
                    if category == 'paragraph':
                        self.addDHComment("","", comment, 'paragraph', "")
                    else:
                        self.parseDH(comment, category)
            else:
                print line
            prev_line = line

    def RashiOrTosafot(self, daf, category, rashi_in_order, tosafot_in_order):
        if category == 'rashi':
            self.maharam_line+=1
            self.rashi_line+=1
            title = 'Rashi on '+masechet
            if rashi_in_order[self.rashi_line].find('-')>=0:
                in_order, out_order = rashi_in_order[self.rashi_line].split('-')
            else:
                in_order = rashi_in_order[self.rashi_line]
                out_order = in_order
            replace_text = "Rashi on "
        elif category == 'tosafot':
            self.maharam_line+=1
            self.tosafot_line+=1
            title = 'Tosafot on '+masechet
            if tosafot_in_order[self.tosafot_line].find('-')>=0:
                print tosafot_in_order[self.tosafot_line]
                in_order, out_order = tosafot_in_order[self.tosafot_line].split('-')
            else:
                in_order = tosafot_in_order[self.tosafot_line]
                out_order = in_order
            replace_text = "Tosafot on "
        if category == 'rashi' or category == 'tosafot':
            in_order = in_order.replace('0:','')
            out_order = out_order.replace('0:','')
            in_order = int(in_order)
            out_order = int(out_order)
            if out_order != 0: #out_order only equals 0 if there really is no Tosafot or Rashi on the given daf
                masechet_daf_line_start = lookForLineInCommentary(title, daf, in_order)
                masechet_daf_line_end = lookForLineInCommentary(title, daf, out_order)
                try:
                    masechet_daf_line = Ref(masechet_daf_line_start).to(Ref(masechet_daf_line_end)).normal()
                except:
                    masechet_daf_line = masechet_daf_line_start
                if len(masechet_daf_line)>0:
                    self.links_to_post.append({
                    "refs": [
                                 masechet_daf_line,
                                "Maharam on "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(self.maharam_line)
                            ],
                    "type": "commentary",
                    "auto": True,
                    "generated_by": "Maharam on "+masechet+" linker"})
                if len(masechet_daf_line)>0:
                    talmud_ref = self.convertRefCommentaryTalmud(masechet_daf_line, replace_text)
                    self.links_to_post.append({
                        "refs": [
                                 talmud_ref,
                                "Maharam on "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(self.maharam_line)
                            ],
                        "type": "commentary",
                        "auto": True,
                        "generated_by": "Maharam "+masechet+" linker"})

    def Gemara(self, daf, gemara_in_order):
        self.maharam_line+=1
        self.gemara_line+=1
        gemara_in_order[self.gemara_line] = gemara_in_order[self.gemara_line].replace('0:','')
        if gemara_in_order[self.gemara_line].find('-')>=0:
            in_order, out_order = gemara_in_order[self.gemara_line].split('-')
        else:
            in_order = gemara_in_order[self.gemara_line]
            out_order = in_order
        masechet_daf_line_start = masechet+" "+AddressTalmud.toStr("en", daf)+":"+in_order
        masechet_daf_line_end = masechet+" "+AddressTalmud.toStr("en", daf)+":"+out_order
        try:
            masechet_daf_line = Ref(masechet_daf_line_start).to(Ref(masechet_daf_line_end)).normal()
        except:
            masechet_daf_line = masechet_daf_line_start
        self.links_to_post.append({
            "refs": [
                     masechet_daf_line,
                    "Maharam on "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(self.maharam_line)
                ],
            "type": "commentary",
            "auto": True,
            "generated_by": "Maharam on "+masechet+" linker",
         })


    def Mishnah(self, daf, mishnah_in_order):
        self.maharam_line+=1
        mishnah_line+=1
        pos = 0
        for perek in self.mishnah1_dict:
            for key in mishnah_in_order[perek]:
                pos+=1
                if pos==mishnah_line:
                    mishnah_in_order[perek][key] = mishnah_in_order[perek][key].replace('0:','')
                    if mishnah_in_order[perek][key].find('-')>=0:
                        in_order, out_order = mishnah_in_order[perek][key].split('-')
                    else:
                        in_order = mishnah_in_order[perek][key]
                        out_order = in_order
                    in_order = int(in_order)
                    out_order = int(out_order)
                    masechet_daf_line_start = "Mishnah "+masechet+"."+str(perek)+"."+str(mishnah_in_order[perek][key][0])
                    masechet_daf_line_end = "Mishnah "+masechet+"."+str(perek)+"."+str(mishnah_out_order[perek][key][0])
                    try:
                        masechet_daf_line = Ref(masechet_daf_line_start).to(Ref(masechet_daf_line_end)).normal()
                    except:
                        masechet_daf_line = masechet_daf_line_start
                    self.links_to_post.append({
                        "refs": [
                                 masechet_daf_line,
                                "Maharam "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(self.maharam_line)
                            ],
                        "type": "commentary",
                        "auto": True,
                        "generated_by": "Maharam on "+masechet+" linker",
                    })

    def postLinks(self):
        mishnah_in_order = {}
        mishnah_out_order = {}
        for perek in self.mishnah1_dict:
            print "matching mishnah"
            mishnah_text = get_text_plus("Mishnah "+masechet+"."+str(perek))['he']
            mishnah_in_order[perek] = match_in_order.match_list(self.removeBDH(self.mishnah1_dict[perek]), mishnah_text, "Mishnah "+masechet+"."+str(perek))
            #mishnah_out_order[perek] = match_out_of_order.match_list(removeBDH(self.mishnah2_dict[perek]), mishnah_text, "Mishnah "+masechet+"."+str(perek))

        links_to_post = []
        for daf in self.dh1_dict:
            print daf
            self.maharam_line = 0
            self.rashi_line=0
            self.tosafot_line = 0
            self.gemara_line = 0
            mishnah_line = 0
            tosafot1_arr = self.tosafot1_dict[daf]
            tosafot2_arr = self.tosafot2_dict[daf]
            rashi1_arr = self.rashi1_dict[daf]
            rashi2_arr = self.rashi2_dict[daf]
            gemara1_arr = self.gemara1_dict[daf]
            gemara2_arr = self.gemara2_dict[daf]
            print "matching tosafot"+str(len(tosafot1_arr))
            tosafot_text = compileCommentaryIntoPage("Tosafot on "+masechet, daf)
            tosafot_in_order = match_in_order.match_list(self.removeBDH(tosafot1_arr), tosafot_text, "Tosafot on "+masechet+" "+AddressTalmud.toStr("en", daf))
            #tosafot_out_order = match_out_of_order.match_list(removeBDH(tosafot2_arr), tosafot_text, "Tosafot on "+masechet+" "+AddressTalmud.toStr("en", daf))
            if not (masechet == "Bava Batra" and daf > 57):
                print "matching rashi"+str(len(rashi1_arr))
                rashi_text = compileCommentaryIntoPage("Rashi on "+masechet, daf)
                rashi_in_order = match_in_order.match_list(self.removeBDH(rashi1_arr), rashi_text, "Rashi on "+masechet+" "+AddressTalmud.toStr("en", daf))
                #rashi_out_order = match_out_of_order.match_list(removeBDH(rashi2_arr), rashi_text, "Rashi on "+masechet+" "+AddressTalmud.toStr("en", daf))
            print "matching gemara"+str(len(gemara1_arr))
            gemara_text = get_text(masechet+" "+AddressTalmud.toStr("en", daf))
            gemara_in_order = match_in_order.match_list(self.removeBDH(gemara1_arr), gemara_text, masechet+" "+AddressTalmud.toStr("en", daf))
            #gemara_out_order = match_out_of_order.match_list(removeBDH(gemara2_arr), gemara_text, masechet+" "+AddressTalmud.toStr("en", daf))
            dh1_arr = self.dh1_dict[daf]
            print "done matching"
            for category, dh in self.dh1_dict[daf]:
                print category
                if category == 'rashi' or category == 'tosafot':
                    self.RashiOrTosafot(daf, category, rashi_in_order, tosafot_in_order)
                elif category == 'gemara':
                    self.Gemara(daf, gemara_in_order)
                elif category == "mishnah":
                    self.Mishnah(daf, mishnah_in_order)
                elif category == 'paragraph' and self.maharam_line == 0:
                    self.maharam_line+=1
        post_link(links_to_post)

def create_index(tractate):
    root=JaggedArrayNode()
    heb_masechet = get_text_plus(tractate)['heBook']
    root.add_title(u"Maharam on "+tractate.replace("_"," "), "en", primary=True)
    root.add_title(u'חידושי רמב"ן על '+heb_masechet, "he", primary=True)
    root.key = 'ramban'
    root.sectionNames = ["Daf", "Comment"]
    root.depth = 2
    root.addressTypes = ["Talmud","Integer"]

    root.validate()

    index = {
        "title": "Chiddushei Ramban on "+tractate.replace("_"," "),
        "categories": ["Commentary2", "Talmud", "Ramban"],
        "schema": root.serialize()
    }
    post_index(index)
    return tractate


if __name__ == "__main__":
    if len(sys.argv) == 3:
        masechet = sys.argv[1]+" "+sys.argv[2]
    else:
        masechet = sys.argv[1]

    create_index(masechet)
    file = open(masechet+"2.txt", 'r')

    maharam = Maharam()
    maharam.parseText(file)

    match_in_order=Match(in_order=True, min_ratio=80, guess=False, range=True, can_expand=False)
    match_out_of_order = Match(in_order=False, min_ratio=85, guess=False, range=True, can_expand=False)
    text_to_post = convertDictToArray(maharam.comm_dict)
    send_text = {
                    "versionTitle": "Vilna Edition",
                    "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002023637",
                    "language": "he",
                    "text": text_to_post,
                }
    post_text("Maharam on "+masechet, send_text, "on")

    maharam.postLinks()

