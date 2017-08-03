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
sys.path.insert(0,p+"/sources")
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
sys.path.append(p+"/data_utilities")
from data_utilities.dibur_hamatchil_matcher import *
from sources.functions import *


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
        self.missing_ones = []
        self.heb_numbers = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "ששי", "שביעי", "שמיני", "תשיעי", "עשירי", "אחד עשר", "שנים עשר", "שלשה עשר", "ארבעה עשר", "חמשה", "ששה"]
        self.comm_dict = {}
        self.dh1_dict = {}
        self.gemara1_dict = {}
        self.tosafot1_dict = {}
        self.rashi1_dict = {}
        self.mishnah1_dict = {}
        self.rashi ='רש"י'
        self.tosafot = "תוס"
        self.dibbur_hamatchil = ['בד"ה', 'ד"ה', 'בא"ד', """ד'"ה"""]
        self.gemara = "גמ"
        self.shom = "שם"
        self.amud_bet = 'ע"ב'
        self.mishnah = ['במשנה', 'מתני']
        self.current_daf = 3
        self.current_perek = 1
        self.categories = ['rashi', 'tosafot', 'gemara', 'mishnah', 'paragraph']
        self.links_to_post = []
        self.category = ""



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

    def addDHComment(self, dh1, comment, category, heb_category):
        if len(dh1)>0:
            self.dh1_dict[self.current_daf].append((category, dh1))
            first_word = dh1.split(" ")[0]
            dh1 = " ".join(dh1.split(" ")[1:])
            append_str = first_word + " <b>" + dh1 + "</b> " + comment + ": "
            self.comm_dict[self.current_daf].append(append_str)
        else:
            last_comment = len(self.comm_dict[self.current_daf])-1
            if last_comment == -1:
                self.comm_dict[self.current_daf].append(comment)
                self.dh1_dict[self.current_daf].append((category, ""))
            else:
                self.comm_dict[self.current_daf].append(comment)
        if category == 'gemara':
            self.gemara1_dict[self.current_daf].append(dh1)
        elif category == 'rashi':
            self.rashi1_dict[self.current_daf].append(dh1)
        elif category == 'tosafot':
            self.tosafot1_dict[self.current_daf].append(dh1)
        elif category == 'mishnah':
            self.mishnah1_dict[current_perek].append(dh1)

    def dh_extract_method(self, str):
        str = str.replace(u'בד"ה', u'').replace(u'וכו', u'')
        return str


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
            self.gemara1_dict[self.current_daf] = []
            self.tosafot1_dict[self.current_daf] = []
            self.rashi1_dict[self.current_daf] = []
            self.mishnah1_dict[self.current_perek] = []
        self.actual_text = actual_text
        return self.current_daf




    def determineCategory(self, count, comment):
        comment = comment + ':'
        if count == 0 and len(comment) == 0:
            return ""
        first_line = " ".join(comment.split(" ")[0:10])
        word = comment.split(" ")[0] if comment.split(" ")[0] != " " else comment.split(" ")[1]
        if word.find(self.rashi)>=0:
            self.category = 'rashi'
            self.heb_category = word
        elif word.find(self.tosafot)>=0:
            self.category = 'tosafot'
            self.heb_category = word
        elif word.find(self.gemara)>=0:
            self.category = 'gemara'
            self.heb_category = word
        elif word in self.mishnah:
            self.category = 'mishnah'
            self.heb_category = word


    def parseDH(self, comment, category):
        first_10 = " ".join(comment.split(" ")[0:10])
        if first_10.find(".") > 0:
            dh, comment = comment.split(".", 1)
            comment = comment[1:] if comment[0] == ' ' else comment
            dh += ". "
        elif first_10.find("כו'") > 0:
            dh, comment = comment.split("כו'", 1)
            comment = comment[1:] if comment[0] == ' ' else comment
            dh += "כו' "
        else:
            dh = first_10 + " "
            comment = " ".join(comment.split(" ")[10:])
        self.addDHComment(dh, comment, category, self.heb_category)


    def parseText(self, file):
        this_line = False
        for line in file:
            line = line.replace("\n", "").replace("@33", "").replace("@55", "").replace("@44","").replace("@77","").replace("@99","")
            if len(line)==0:
                continue

            if line.find("@00")>=0 and line.find("פרק")>=0:
                self.current_perek += 1
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
                    if len(comment) < 5:
                        continue
                    if comment[0] == ' ':
                        comment = comment[1:]
                    self.determineCategory(count, comment)
                    self.parseDH(comment, self.category)
            else:
                print line
            prev_line = line


    def convertToOldFormat(self, arr):
        arr = arr['matches']
        for index, item in enumerate(arr):
            if item is None:
                arr[index] = '0'
            else:
                arr[index] = arr[index].normal()
        return arr



    def RashiOrTosafot(self, daf, category, rashi_in_order, tosafot_in_order):
        if category == 'rashi':
            self.maharam_line+=1
            self.rashi_line+=1
            title = 'Rashi on '+masechet
            in_order = rashi_in_order[self.rashi_line]
        elif category == 'tosafot':
            self.maharam_line+=1
            self.tosafot_line+=1
            title = 'Tosafot on '+masechet
            in_order = tosafot_in_order[self.tosafot_line]
        if in_order == '0':
            self.missing_ones.append("Maharam on "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(self.maharam_line))
        else:
            self.links_to_post.append({
                "refs": [
                             in_order,
                            "Maharam on "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(self.maharam_line)
                        ],
                "type": "commentary",
                "auto": True,
                "generated_by": "Maharam on "+masechet+" linker"
            })
            sections = Ref(in_order).sections
            toSections = Ref(in_order).toSections
            if sections == toSections:
                in_order = Ref(in_order

            in_order = in_order.replace("Tosafot on ", "").replace("Rashi on ", "")
            ref = Ref(in_order)
            assert len(ref.sections) in [2, 3]
            if len(ref.sections) == 3:
                last_colon = ref.normal().rfind(":")
                gemara_ref = ref.normal()[0:last_colon]
            else:
                gemara_ref = ref.normal()
            print gemara_ref
            self.links_to_post.append({
                "refs": [
                    "Maharam on "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(self.maharam_line),
                    gemara_ref
                ],
                "type": "commentary",
                "auto": True,
                "generated_by": "Maharam on "+masechet+" linker"
            })


    def Gemara(self, daf, gemara_in_order):
        self.maharam_line+=1
        self.gemara_line+=1
        if gemara_in_order[self.gemara_line] == '0':
            self.missing_ones.append("Maharam on "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(self.maharam_line))
        else:
            self.links_to_post.append({
            "refs": [
                     gemara_in_order[self.gemara_line],
                    "Maharam on "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(self.maharam_line)
                ],
            "type": "commentary",
            "auto": True,
            "generated_by": "Maharam on "+masechet+" linker",
         })


    def postLinks(self):
        def base_tokenizer(str):
            str = re.sub(ur"\([^\(\)]+\)", u"", str)
            word_list = re.split(ur"\s+", str)
            word_list = [w for w in word_list if w]  # remove empty strings
            return word_list

        mishnah_in_order = {}
        mishnah_out_order = {}
        links_to_post = []
        for daf in sorted(self.dh1_dict.keys()):
            print daf
            self.maharam_line = 0
            self.rashi_line = -1
            self.tosafot_line = -1
            self.gemara_line = -1
            mishnah_line = 0
            tosafot1_arr = self.tosafot1_dict[daf]
            rashi1_arr = self.rashi1_dict[daf]
            gemara1_arr = self.gemara1_dict[daf]
            print "matching tosafot"+str(len(tosafot1_arr))
            tosafot_text = Ref("Tosafot on "+masechet+"."+AddressTalmud.toStr("en", daf)).text('he')
            tosafot1_arr = [text.decode('utf-8') for text in tosafot1_arr]
            tosafot_in_order = match_ref(tosafot_text, tosafot1_arr, base_tokenizer, dh_extract_method=self.dh_extract_method, verbose=True)
            tosafot_in_order = self.convertToOldFormat(tosafot_in_order)
            print "matching rashi"+str(len(rashi1_arr))
            rashi_text = Ref("Rashi on "+masechet+"."+AddressTalmud.toStr("en", daf)).text('he')
            rashi1_arr = [text.decode('utf-8') for text in rashi1_arr]
            rashi_in_order = match_ref(rashi_text, rashi1_arr, base_tokenizer, dh_extract_method=self.dh_extract_method, verbose=True)
            rashi_in_order = self.convertToOldFormat(rashi_in_order)
            print "matching gemara"+str(len(gemara1_arr))
            gemara_text = Ref(masechet+" "+AddressTalmud.toStr("en", daf)).text('he')
            gemara1_arr = [text.decode('utf-8') for text in gemara1_arr]
            gemara_in_order = match_ref(gemara_text, gemara1_arr, base_tokenizer, dh_extract_method=self.dh_extract_method, verbose=True)
            gemara_in_order = self.convertToOldFormat(gemara_in_order)
            dh1_arr = self.dh1_dict[daf]
            print "done matching"
            for category, dh in self.dh1_dict[daf]:
                print category
                if category == 'rashi' or category == 'tosafot':
                    self.RashiOrTosafot(daf, category, rashi_in_order, tosafot_in_order)
                elif category == 'gemara':
                    self.Gemara(daf, gemara_in_order)
                #elif category == "mishnah":
                #    self.Mishnah(daf, mishnah_in_order)
                elif category == 'paragraph' and self.maharam_line == 0:
                    self.maharam_line+=1
        post_link(self.links_to_post, server=SERVER)


def create_index(tractate):
    root=JaggedArrayNode()
    heb_masechet = library.get_index(tractate).get_title('he')
    root.add_title(u"Maharam on "+tractate.replace("_"," "), "en", primary=True)
    root.add_title(u'מהר"ם '+heb_masechet, "he", primary=True)
    root.key = 'maharam'
    root.sectionNames = ["Daf", "Comment"]
    root.depth = 2
    root.addressTypes = ["Talmud","Integer"]

    root.validate()

    index = {
        "dependence": "Commentary",
        "collective_title": "Maharam",
        "base_text_titles": [tractate]
        "title": "Maharam on "+tractate.replace("_"," "),
        "categories": ["Talmud", "Bavli", "Commentary", "Maharam", library.get_index(tractate).categories[-1]],
        "schema": root.serialize()
    }
    post_index(index, server=SERVER)
    return tractate


if __name__ == "__main__":
    SERVER = "http://proto.sefaria.org"
    titles = ["Avodah Zarah"]
    '''
        ["Bava Batra", "Bava Kamma","Bava Metzia"]
    , "Chullin", "Eruvin", "Gittin", "Ketubot",
    "Kiddushin", "Makkot",
              "Niddah", "Sanhedrin", "Shabbat", "Sukkah", "Yevamot"
              ]
        '''
    done = []
    for masechet in titles:
        if masechet in done:
            continue

        print masechet

        create_index(masechet)
        file = open(masechet+"2.txt", 'r')

        maharam = Maharam()
        maharam.parseText(file)

        text_to_post = convertDictToArray(maharam.comm_dict)
        send_text = {
                        "versionTitle": "Vilna Edition",
                        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002023637",
                        "language": "he",
                        "text": text_to_post,
                    }
        post_text("Maharam on "+masechet, send_text, "on", server=SERVER)
        print 'posted'

        maharam.postLinks()

        missing = open("missing_ones_"+masechet+".txt", "w")
        for each_ref in maharam.missing_ones:
            missing.write(each_ref+"\n")

