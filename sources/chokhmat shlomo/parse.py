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




class Maharshal:
    def __init__(self):
        '''
        dictionary for each category allows matching to work
        then after we have match dictionaries for in order and out of order for each category
        we go through the actual self.dh1_dict and self.dh2_dict, checking its category
        whatever the category is we increment the maharam line and post the link between maharam and the appropriate
        book based on the category. remember to deal with paragraph case and gemara case.
        '''
        self.comm_wout_base = open("comm_wout_base.txt", 'w')
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
        self.prev_dh = ""



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

    def addDHComment(self, dh, comment, category):
        dh = dh.decode('utf-8')
        comment = comment.decode('utf-8')
        self.dh1_dict[self.current_daf].append((category, dh))
        self.comm_dict[self.current_daf].append(dh + comment)
        if category == 'gemara':
            self.gemara1_dict[self.current_daf].append(dh)
        elif category == 'rashi':
            self.rashi1_dict[self.current_daf].append(dh)
        elif category == 'tosafot':
            self.tosafot1_dict[self.current_daf].append(dh)

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
        if word.find(self.rashi) == 0:
            self.category = 'rashi'
            self.heb_category = word
        elif word.find(self.tosafot) == 0:
            self.category = 'tosafot'
            self.heb_category = word
        elif word.find(self.gemara) == 0:
            self.category = 'gemara'
            self.heb_category = word
        elif word.find('בא"ד') == 0:
            return "b'oto dibur"
        return None




    def parseDH(self, comment, category, same_dh):
        if same_dh is None:
            chulay = comment.find("כו'")
            if chulay > 0:
                dh, comment = comment[0:chulay+5], comment[chulay+5:]
            else:
                dh = comment
                comment = ""
            self.prev_dh = dh
            self.addDHComment(dh, comment, category)
        else:
            self.addDHComment(self.prev_dh, comment, category)


    def parseText(self, file):
        this_line = False
        for line in file:
            orig_line = line
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
                    if len(comment.replace(" ", "")) < 3:
                        continue
                    if comment[0] == ' ':
                        comment = comment[1:]
                    same_dh = self.determineCategory(count, comment)
                    self.parseDH(comment, self.category, same_dh)
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



    def RashiOrTosafot(self, daf, category, results):
        self.maharam_line += 1
        if category == 'rashi':
            self.rashi_line+=1
            title = 'Rashi on '+masechet
            ref = results[category][self.rashi_line]
        elif category == 'tosafot':
            self.tosafot_line+=1
            title = 'Tosafot on '+masechet
            ref = results[category][self.tosafot_line]
        if ref == '0':
            self.missing_ones.append("Maharshal on "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(self.maharam_line))
        else:
            self.links_to_post.append({
                "refs": [
                             ref,
                            "Maharshal on "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(self.maharam_line)
                        ],
                "type": "commentary",
                "auto": True,
                "generated_by": "Maharshal on "+masechet+" linker"
            })
            gemara_ref = self.getGemaraRef(ref)
            self.links_to_post.append({
                "refs": [
                    "Maharshal on "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(self.maharam_line),
                    gemara_ref
                ],
                "type": "commentary",
                "auto": True,
                "generated_by": "Maharshal on "+masechet+" linker"
            })

    def getGemaraRef(self, ref):
        ref = Ref(ref)
        assert len(ref.sections) == 3 ^ (not ref.is_segment_level())
        d = ref._core_dict()
        if len(d['sections']) == 3:
            d['sections'] = d['sections'][0:-1]
            d['toSections'] = d['toSections'][0:-1]
            gemara_ref = Ref(_obj=d)
        return gemara_ref.normal().replace("Tosafot on ", "").replace("Rashi on ", "")

    def Gemara(self, daf, results):
        self.maharam_line+=1
        self.gemara_line+=1
        if results['gemara'][self.gemara_line] == '0':
            self.missing_ones.append("Maharshal on "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(self.maharam_line))
        else:
            self.links_to_post.append({
            "refs": [
                     results['gemara'][self.gemara_line],
                    "Maharshal on "+masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(self.maharam_line)
                ],
            "type": "commentary",
            "auto": True,
            "generated_by": "Maharshal on "+masechet+" linker",
         })


    def getTC(self, category, daf, masechet):
        if category == "tosafot":
            return Ref("Tosafot on "+masechet+"."+AddressTalmud.toStr("en", daf)).text('he')
        elif category == "gemara":
            return Ref(masechet+" "+AddressTalmud.toStr("en", daf)).text('he')
        elif category == "rashi":
            rashi = Ref("Rashi on "+masechet+"."+AddressTalmud.toStr("en", daf)).text('he')
            if len(rashi.text) == 0:
                return Ref("Rashbam on "+masechet+"."+AddressTalmud.toStr("en", daf)).text('he')
            else:
                return rashi

    def postLinks(self, masechet):
        def base_tokenizer(str):
            str = re.sub(ur"\([^\(\)]+\)", u"", str)
            word_list = re.split(ur"\s+", str)
            word_list = [w for w in word_list if w]  # remove empty strings
            return word_list

        results = {}
        comments = {}

        for daf in sorted(self.dh1_dict.keys()):
            print "DAF {}".format(daf)
            comments[daf] = {}
            results[daf] = {}
            comments[daf]["tosafot"] = self.tosafot1_dict[daf]
            comments[daf]["rashi"] = self.rashi1_dict[daf]
            comments[daf]["gemara"] = self.gemara1_dict[daf]
            for each_type in comments[daf]:
                results[daf][each_type] = []
                if len(comments[daf][each_type]) > 0:
                    base = self.getTC(each_type, daf, masechet)
                    if len(base.text) == 0:
                        self.comm_wout_base.write("{} {}: {}\n".format(masechet, daf, each_type))
                        base = self.getTC(each_type, daf-1, masechet)
                        combined_comments = comments[daf-1][each_type]+comments[daf][each_type]
                        results[daf-1][each_type] = match_ref(base, combined_comments, base_tokenizer, dh_extract_method=self.dh_extract_method, verbose=True, with_num_abbrevs=False)
                        results[daf-1][each_type] = self.convertToOldFormat(results[daf-1][each_type])
                        self.dh1_dict[daf] = [x for x in self.dh1_dict[daf] if x[0] != each_type]
                    else:
                        results[daf][each_type] = match_ref(base, comments[daf][each_type], base_tokenizer, dh_extract_method=self.dh_extract_method, verbose=True, with_num_abbrevs=False)
                        results[daf][each_type] = self.convertToOldFormat(results[daf][each_type])

        for daf in sorted(self.dh1_dict.keys()):
            self.maharam_line = 0
            self.rashi_line = -1
            self.tosafot_line = -1
            self.gemara_line = -1
            for category, dh in self.dh1_dict[daf]:
                if category == 'rashi' or category == 'tosafot':
                    self.RashiOrTosafot(daf, category, results[daf])
                elif category == 'gemara':
                    self.Gemara(daf, results[daf])
                elif category == 'paragraph' and self.maharam_line == 0:
                    self.maharam_line += 1
        post_link(self.links_to_post)
        self.comm_wout_base.close()


def create_index(tractate):
    root=JaggedArrayNode()
    heb_masechet = library.get_index(tractate).get_title('he')
    root.add_title(u"Maharshal on "+tractate.replace("_"," "), "en", primary=True)
    root.add_title(u'מהרש"ל '+heb_masechet, "he", primary=True)
    root.key = 'maharshal'+tractate
    root.sectionNames = ["Daf", "Comment"]
    root.depth = 2
    root.addressTypes = ["Talmud","Integer"]

    root.validate()

    index = {
        "title": "Maharshal on "+tractate.replace("_"," "),
        "categories": ["Talmud", "Commentary", "Maharshal"],
        "schema": root.serialize()
    }
    post_index(index)
    return tractate


if __name__ == "__main__":
    done = []
    term_obj = {
        "name": "Maharshal",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Maharshal",
                "primary": True
            },
            {
                "lang": "he",
                "text": u'מהרש"ל',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
    not_those = ["bava batra.txt2.txt", "bava kamma.txt2.txt", "bava metzia.txt2.txt"]
    files = [file for file in os.listdir(".") if file.endswith("txt2.txt") and file not in not_those]
    files = ["eruvin.txt2.txt", "niddah.txt2.txt", "gittin.txt2.txt"]
    start_file = "sotah.txt2.txt"
    for count, file in enumerate(files):
        print "MASECHET"
        print file
        masechet = file.replace(".txt2.txt", "").title()
        #create_index(masechet)

        obj = Maharshal()
        obj.parseText(open(file))

        text_to_post = convertDictToArray(obj.comm_dict)
        send_text = {
                        "versionTitle": "Vilna Edition",
                        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
                        "language": "he",
                        "text": text_to_post,
                    }
        #post_text("Maharshal on "+masechet, send_text, "on")
        print 'posted'

        obj.postLinks(masechet)

        missing = open("missing_ones_"+masechet+".txt", "w")
        for each_ref in obj.missing_ones:
            missing.write(each_ref+"\n")

