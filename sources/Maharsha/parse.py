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
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from data_utilities.dibur_hamatchil_matcher import *
from sources.functions import *


sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud




class Maharsha:
    def __init__(self, masechet, title, heTitle, server):
        '''
        dictionary for each category allows matching to work
        then after we have match dictionaries for in order and out of order for each category
        we go through the actual self.dh1_dict and self.dh2_dict, checking its category
        whatever the category is we increment the maharam line and post the link between maharam and the appropriate
        book based on the category. remember to deal with paragraph case and gemara case.
        '''
        self.dont_post = False #if an error occurs in parsing
        self.list_of_dafs = []
        self.server = server
        self.title = title
        self.heTitle = heTitle
        self.comm_wout_base = open("comm_wout_base.txt", 'w')
        self.masechet = masechet
        self.missing_ones = []
        self.heb_numbers = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "ששי", "שביעי", "שמיני", "תשיעי", "עשירי", "אחד עשר", "שנים עשר", "שלשה עשר", "ארבעה עשר", "חמשה", "ששה"]
        self.comm_dict = {}
        self.dh1_dict = {}
        self.rashi ='רש"י'
        self.rashbam = 'פרשב"ם'
        self.ran = 'ר"ן'
        self.rosh = 'רא"ש'
        self.tosafot = "תוס"
        self.dibbur_hamatchil = ['בד"ה', 'ד"ה', 'בא"ד', """ד'"ה"""]
        self.gemara = "גמ"
        self.shom = "שם"
        self.amud_bet = 'ע"ב'
        self.mishnah = ['במשנה', 'מתני']
        self.current_daf = 2
        self.current_perek = 0
        self.categories = ['rashi', 'tosafot', 'gemara', 'ran', 'rosh', 'rashbam']
        self.dh_by_cat = {}
        self.dh_by_cat = {cat: {} for cat in self.categories}
        self.links_to_post = []
        self.category = "gemara"
        self.prev_dh = ""
        self.comm_by_perek = {}
        self.dh_by_perek = {}
        self.rosh_line = 0
        self.looking_for_perakim = False




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

    def addDHComment(self, dh, comment, category, same_dh):
        dh = removeAllTags(dh)
        comment = removeAllTags(comment)
        dh = dh.decode('utf-8')
        comment = comment.decode('utf-8')
        self.dh1_dict[self.current_daf].append((category, dh))
        if same_dh:
            post_comment = comment
        else:
            post_comment = dh + comment

        post_comment = post_comment.strip()
        first_word = post_comment.split(" ")[0]
        post_comment = u"<b>{}</b> {}".format(first_word, " ".join(post_comment.split(" ")[1:]))
        self.comm_dict[self.current_daf].append(post_comment)
        self.dh_by_cat[category][self.current_daf].append(dh)
        if self.looking_for_perakim:
            self.dh_by_perek[self.current_perek].append((category, dh, self.current_daf))
            self.comm_by_perek[self.current_perek].append(post_comment)

    def dh_extract_method(self, str):
        str = str.encode('utf-8')
        str = str.replace('בד"ה', '').replace('וכו', '').replace('שם','')
        for each in [self.rashi, self.tosafot, self.gemara, self.ran, self.rashbam, self.rosh, 'בא"ד']:
            if each in str[0]:
                str = " ".join(str.split(" ")[1:])
                break
        return str.decode('utf-8')


    def getPerek(self, line):
        which_perek = -1
        for count, word in enumerate(self.heb_numbers):
            if line.find(word)>=0:
                which_perek = count+1
                break
        if which_perek == -1:
            pdb.set_trace()
        return which_perek


    def getDaf(self, line, current_daf, len_masechet, prev_line):
        prev_num = self.current_daf
        orig_line = line
        line = line.replace("@11 ", "@11")
        if line.split(" ")[0].find('דף')>=0:
            daf_value = getGematria(line.split(" ")[1].replace('"', '').replace("'", ''))
            if line.split(" ")[2].find(self.amud_bet)>=0:
                self.current_daf = 2*daf_value
            else:
                self.current_daf = 2*daf_value - 1
            actual_text = ""
            start_at = 3
            if line.split(" ")[2] not in ['ע"ב', 'ע"א']:
                start_at = 2
            for count, word in enumerate(line.split(" ")):
                if count >= start_at:
                    actual_text += word + " "
        else:
            self.current_daf += 1
            actual_text = line[3:]

        if self.current_daf <= prev_num:
            he_current = AddressTalmud.toStr("he", self.current_daf)
            he_prev = AddressTalmud.toStr("he", prev_num)
            #prev_line = " ".join(prev_line.split(" ")[0:5])
            #orig_line = " ".join(orig_line.split(" ")[0:5])
            print u"{} before {}\n".format(he_prev, he_current)
            self.dont_post = True
            #print u"The line starting: {} is {}\n".format(prev_line, he_prev)
            #print u"It came before the line starting {}, which is {}\n\n".format(orig_line, he_current)


        if not self.current_daf in self.dh1_dict:
            self.dh1_dict[self.current_daf] = []
            for each_cat in self.categories:
                self.dh_by_cat[each_cat][self.current_daf] = []
        self.actual_text = actual_text
        if self.current_daf > len_masechet:
            print "DAF EXTRA {} > {} in {} {}".format(self.current_daf, len_masechet, self.title, self.masechet)
            pass
        self.list_of_dafs.append(self.current_daf)

        return self.current_daf




    def determineCategory(self, count, comment):
        comment = comment + ':'
        if count == 0 and len(comment) == 0:
            return ""
        word = comment.split(" ")[0] if comment.split(" ")[0] != " " else comment.split(" ")[1]
        if self.rashi in word:
            self.category = 'rashi'
        elif self.tosafot in word:
            self.category = 'tosafot'
        elif self.gemara in word or word in self.mishnah:
            self.category = 'gemara'
        elif self.ran in word:
            self.category = 'ran'
        elif self.rosh in word:
            self.category = 'rosh'
        elif self.rashbam in word:
            self.category = "rashbam"
        elif word == 'בא"ד' or word == 'עוד בדבור זה':
            return "same_dh"
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
            self.addDHComment(dh, comment, category, same_dh)
        else:
            self.addDHComment(self.prev_dh, comment, category, same_dh)


    def pre_parse(self, file):
        arr_text = []
        for line in file:
            temp_list = check_for_other_daf(line)
            for comment in temp_list:
                arr_text.append(comment)
        return arr_text

    def parseText(self, file, len_masechet):
        this_line = False
        prev_line_require_text = False
        prev_line = ""
        lines = self.pre_parse(file)
        for line in lines:
            orig_line = line
            line = line.encode('utf-8')

            if line.find("@00") >= 0 or line.find("0") == 0:
                #if len(line.split("@")) > 2:
                    #print "Previous daf: {}".format(AddressTalmud.toStr("en", self.current_daf))
                    #print line
                self.current_perek += 1
                if not self.current_perek in self.dh_by_perek:
                    self.dh_by_perek[self.current_perek] = []
                    self.comm_by_perek[self.current_perek] = []
                line = line.replace("@00", "<br/>")

            if line.find('ח"א ') == 3:
                line = line.replace('ח"א ', '')

            line = line.replace("\n", "")
            if len(line) == 0:
                continue

            if line[0] == " ":    #not part of the logic, just solving something caused by the text file
                start = line.find("@11")
                line = line[start:]
            try:
                if len(re.split(ur'@\d{2}\u05D3\u05E3|@\d{2}\u05D7"\u05D0', line.decode('utf-8'))) > 2:
                    print "BAD FORMATTING of @11"
                    check_for_other_daf(line)
            except UnicodeDecodeError:
                if len(re.split(ur'@\d{2}\u05D3\u05E3|@\d{2}\u05D7"\u05D0', line)) > 2:
                    print "BAD FORMATTING of @11"
                    check_for_other_daf(line)

            if line.find("@11")>=0:
                category = ""
                self.current_daf = self.getDaf(line, self.current_daf, len_masechet, prev_line)

                if not self.current_daf in self.comm_dict:
                    self.comm_dict[self.current_daf] = []

                comments = self.actual_text.split(": ")
                for count, comment in enumerate(comments):
                    if len(comment.replace(" ", "")) < 3:
                        continue
                    if comment[0] == ' ':
                        comment = comment[1:]
                    comment += ':'
                    same_dh = self.determineCategory(count, comment)
                    self.parseDH(comment, self.category, same_dh)

            prev_line = line


    def convertToOldFormat(self, arr):
        arr = arr['matches']
        for index, item in enumerate(arr):
            if item is None:
                arr[index] = '0'
            else:
                arr[index] = arr[index].normal()
        return arr


    def Commentary(self, daf, category, results):
        self.maharam_line += 1
        self.which_line[category] += 1
        title = category.title() + " on " + self.masechet
        base_ref = results[category][self.which_line[category]]
        comm_ref = self.title+" on "+self.masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(self.maharam_line)
        if base_ref == '0':
            self.missing_ones.append(comm_ref)
        else:
            self.links_to_post.append({
                "refs": [
                             base_ref,
                            comm_ref
                        ],
                "type": "commentary",
                "auto": True,
                "generated_by": self.title+self.masechet+" linker"
            })
            gemara_ref = self.getGemaraRef(base_ref)
            self.links_to_post.append({
                "refs": [
                    comm_ref,
                    gemara_ref
                ],
                "type": "commentary",
                "auto": True,
                "generated_by": self.title+self.masechet+" linker"
            })

    def getGemaraRef(self, ref):
        ref = Ref(ref)
        assert len(ref.sections) == 3 ^ (not ref.is_segment_level())
        d = ref._core_dict()
        if len(d['sections']) == 3:
            d['sections'] = d['sections'][0:-1]
            d['toSections'] = d['toSections'][0:-1]
            gemara_ref = Ref(_obj=d)
        return gemara_ref.normal().replace("Tosafot on ", "").replace("Rashi on ", "").replace("Rosh on ", "").replace("Ran on ", "")


    def Gemara(self, daf, results):
        self.maharam_line+=1
        self.which_line['gemara']+=1
        if results['gemara'][self.which_line['gemara']] == '0':
            self.missing_ones.append(self.title+" on "+self.masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(self.maharam_line))
        else:
            self.links_to_post.append({
            "refs": [
                     results['gemara'][self.which_line['gemara']],
                    self.title+" on "+self.masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(self.maharam_line)
                ],
            "type": "commentary",
            "auto": True,
            "generated_by": self.title+self.masechet+" linker",
         })


    def getTC(self, category, daf, masechet):
        if category in ["tosafot", "ran", "rosh"]:
            title = "{} on {}".format(category.title(), masechet)
            return Ref(title+"."+AddressTalmud.toStr("en", daf)).text('he')
        elif category == "gemara":
            return Ref(masechet+" "+AddressTalmud.toStr("en", daf)).text('he')
        elif category == "rashi":
            rashi = Ref("Rashi on "+self.masechet+"."+AddressTalmud.toStr("en", daf)).text('he')
            if len(rashi.text) == 0:
                print "rashbam by default {} {}".format(masechet, AddressTalmud.toStr("en", daf))
                return Ref("Rashbam on "+self.masechet+"."+AddressTalmud.toStr("en", daf)).text('he')
            else:
                return rashi
        elif category == "rashbam":
            print "rashbam {} {}".format(masechet, AddressTalmud.toStr("en", daf))
            return Ref("Rashbam on "+self.masechet+"."+AddressTalmud.toStr("en", daf)).text('he')

    def postLinks(self, masechet):
        def base_tokenizer(str):
            str = re.sub(ur"\([^\(\)]+\)", u"", str)
            word_list = re.split(ur"\s+", str)
            word_list = [w for w in word_list if w]  # remove empty strings
            return word_list

        rosh_results = []
        perek_key = {}
        for perek in sorted(self.dh_by_perek.keys()):
            tuples = filter(lambda x: x[0] is 'rosh', self.dh_by_perek[perek])
            if len(tuples) > 0:
                cats, dhs, dappim = zip(*tuples)
                #for each daf and dh pair, that's the key to get the perek
                for daf, dh in zip(list(dappim), list(dhs)):
                    perek_key[(daf, dh)] = perek
                base = Ref("Rosh on {} {}".format(masechet, perek)).text('he')
                assert len(base.text) > 0
                these_results = match_ref(base, list(dhs), base_tokenizer, dh_extract_method=self.dh_extract_method, verbose=False, with_num_abbrevs=False)['matches']
                assert len(tuples) is len(these_results)
                rosh_results.append(these_results)

        results = {}
        comments = {}

        for daf in sorted(self.dh1_dict.keys()):
            comments[daf] = {}
            results[daf] = {}
            for each_cat in self.categories:
                if each_cat == 'rosh':
                    continue
                comments[daf][each_cat] = self.dh_by_cat[each_cat][daf]
            for each_type in comments[daf]:
                if each_type == 'rosh':
                    continue
                results[daf][each_type] = []
                if len(comments[daf][each_type]) > 0:
                    base = self.getTC(each_type, daf, masechet)
                    if len(base.text) == 0:
                        self.comm_wout_base.write("{} {}: {}\n".format(masechet, daf, each_type))
                        base = self.getTC(each_type, daf-1, masechet)
                        combined_comments = comments[daf-1][each_type]+comments[daf][each_type]
                        if len(base.text) == 0:
                            print "Problem in {}".format(AddressTalmud.toStr("en", daf))
                        else:
                            results[daf-1][each_type] = match_ref(base, combined_comments, base_tokenizer, dh_extract_method=self.dh_extract_method, verbose=False, with_num_abbrevs=False)
                            results[daf-1][each_type] = self.convertToOldFormat(results[daf-1][each_type])
                        self.dh1_dict[daf] = [x for x in self.dh1_dict[daf] if x[0] != each_type]
                    else:
                        results[daf][each_type] = match_ref(base, comments[daf][each_type], base_tokenizer, dh_extract_method=self.dh_extract_method, verbose=False, with_num_abbrevs=False)
                        results[daf][each_type] = self.convertToOldFormat(results[daf][each_type])

        prev_perek = 0
        for daf in sorted(self.dh1_dict.keys()):
            self.maharam_line = 0
            self.which_line = {"rashi": -1, "tosafot": -1, "rosh": -1, "ran": -1, "gemara": -1, "rashbam": -1}
            for category, dh in self.dh1_dict[daf]:
                if category == 'gemara':
                    self.Gemara(daf, results[daf])
                elif category == 'rosh':
                    perek = perek_key[(daf, dh)]
                    if perek > prev_perek:
                        self.rosh_line = -1
                    prev_perek = perek
                    self.Rosh(perek, daf, dh, rosh_results)
                else:
                    self.Commentary(daf, category, results[daf])

        post_link(self.links_to_post, server=self.server)
        self.comm_wout_base.close()


    def Rosh(self, perek, daf, dh, results):
        self.maharam_line += 1
        self.rosh_line += 1
        if results[perek-1][self.rosh_line]:
            self.links_to_post.append({
                "refs": [
                         results[perek-1][self.rosh_line].normal(),
                        self.title+" on "+self.masechet+"."+AddressTalmud.toStr("en", daf)+"."+str(self.maharam_line)
                    ],
                "type": "commentary",
                "auto": True,
                "generated_by": self.title+self.masechet+" linker",
             })



    def create_index(self, tractate):
        categories = library.get_index(tractate).categories
        root=JaggedArrayNode()
        heb_masechet = library.get_index(tractate).get_title('he')
        root.add_title(self.title+" on "+tractate.replace("_"," "), "en", primary=True)
        root.add_title(self.heTitle+u" על "+heb_masechet, "he", primary=True)
        root.key = self.title+tractate
        root.sectionNames = ["Daf", "Comment"]
        root.depth = 2
        root.addressTypes = ["Talmud", "Integer"]

        root.validate()

        index = {
            "title": self.title+" on "+tractate.replace("_"," "),
            "categories": ["Talmud", "Bavli", "Commentary", self.title, categories[-1]],
            "schema": root.serialize(),
            "base_text_titles": [tractate],
            "collective_title": self.title,
            "dependence": "Commentary",

        }
        post_index(index, server=self.server)
        return tractate


def split_files_agadot_halachot(only_these=None):
    if not only_these:
        only_these = os.listdir(".")
    files = [file.decode('utf-8') for file in only_these if file.endswith(".txt") and not "2" in file and not file.startswith("chid")
             and not "comm_wout_base" in file]
    files = [file for file in files]
    prev_line_agadic = False
    for file in files:
        print file
        if "Arakhin" in file:
            ch_ha = open(u"chidushei_agadot_Arakhin.txt", 'w')
        elif "Rosh" in file:
            ch_ag = open(u"chidushei_agadot_{}".format(file), 'w')
            ch_ha = open(u"chidushei_halachot_{}".format(file), 'w')
        else:
            ch_ha = open(u"chidushei_halachot_{}".format(file), 'w')

        for line in open("./"+file):
            if line.replace("\r", "").replace(" ", "") == "\n":
                continue
            if not (line.find("@00") == 0 or line.find("@11") == 0):
                line = "@11" + line
            if "@00" in line:
                if "Rosh" in file:
                    ch_ag.write(line)
                ch_ha.write(line)
                continue
            if line.startswith('@11ח"א'):
                if "Rosh" in file:
                    ch_ag.write(line)
                prev_line_agadic = True
            elif line.startswith('@11דף'):
                ch_ha.write(line)
                prev_line_agadic = False
            elif prev_line_agadic:
                if "Rosh" in file or "Arakhin" in file:
                    ch_ag.write(line)
                prev_line_agadic = False
            else:
                ch_ha.write(line)


    #ch_ag.close()
    ch_ha.close()


def get_titles(file):
    try:
        he_title = file.split(" ")[-1]
        title = library.get_index(he_title).title
    except:
        he_title = " ".join(file.split(" ")[-2:])
        title = library.get_index(he_title).title
    return he_title, title


def split_lines_into_amudim(only_these=None):
    if not only_these:
        only_these = os.listdir("./hebrew")

    files = [file.replace(".txt", "").decode('utf-8') for file in only_these if not file.endswith("2.txt") and file.endswith(".txt")]
    for file in files:
        print file
        f = open("./hebrew/"+file+".txt", 'r')
        he_title, title = get_titles(file)

        arr_text = []
        prev_special = False
        prev_chid_agadot = False
        for count, line in enumerate(f):
            line = line.replace("\n", "").replace("\r", "")
            if len(line.replace(" ", "")) == 0:
                continue

            if re.compile(u'^(@\d{2}\u05D3\u05E3|@\d{2}\u05D7"\u05D0)').match(line.decode('utf-8')) is None:
                if line[0] == "0" or line.startswith("@00") or line.startswith("@99"):
                    continue
                else:
                    last_pos = len(arr_text) - 1
                    if arr_text == []:
                        print file + " has intro.\n"
                        continue
                    arr_text[last_pos] += "<br/>"+line
                    prev_special = True
                    continue
            else:
                if prev_special:
                    arr_text[len(arr_text) - 1] += "\n"
                    prev_special = False

            no_match = True
            line = line.replace("@66", "@11", 1).replace("@33", "").replace("\n", "").replace("\r", "")

            lines, prev_chid_agadot = stamp_amudim_with_11s(line, prev_chid_agadot)
            if len(lines[0]) == 0:
                continue
            arr_text += lines

        f.close()
        f = open("./"+title+".txt", 'w')
        for line in arr_text:
            if len(line) == 0:
                continue
            what_to_write = check_for_other_daf(line)
            for each_line in what_to_write:
                try:
                    f.write(each_line.encode('utf-8'))
                except:
                    f.write(each_line)

        f.close()


def stamp_amudim_with_11s(line, prev_chid_agadot):
    chid_agadot = 'ח"א' in " ".join(line.split(" ")[0:2])
    lines = re.split('@\d+ע"ב', line)
    if len(lines[0]) == 0:
        return lines

    for sub_count, sub_line in enumerate(lines):
        if lines[sub_count].startswith("@99") or lines[sub_count].startswith("@22"):
            lines[sub_count] = ""
            continue
        while lines[sub_count][0] == ' ':
            lines[sub_count] = lines[sub_count][1:]

        if lines[sub_count].find("@11") != 0 and lines[sub_count].find("@00") == -1:
            if prev_chid_agadot:
                lines[sub_count] = "@11" + 'ח"א ' + lines[sub_count]
            else:
                lines[sub_count] = "@11" + lines[sub_count]
        prev_chid_agadot = chid_agadot
        chid_agadot = False
    return lines, prev_chid_agadot


def force_encoding(comment):
    import chardet
    encoding = chardet.detect(comment)
    if type(comment) is str:
        return comment.decode('utf-8')

def check_for_other_daf(comment):
    comment = force_encoding(comment)
    lines = re.split(ur'(@\d{2}\u05D3\u05E3|@\d{2}\u05D7"\u05D0)', comment)
    text_list = []
    if len(lines) is 1:
        text_list = [comment + "\n"]
    else:
        if lines[0] == "":
            lines = lines[1:]
        if len(lines) % 2 == 1:
            text_list.append(lines[0]+"\n")
            lines = lines[1:]

        for i in range(len(lines)):
            text_list.append(lines[i]+lines[i+1]+"\n")
            if i == len(lines) - 2:
                break
    return text_list







if __name__ == "__main__":
    done = []
    #split_lines_into_amudim(["מהרשא יבמות.txt"])
    #split_files_agadot_halachot(["Yevamot.txt"])
    '''
    done_arr = ["Bekhorot",
        "Chagigah",
        "Kiddushin",
        "Sanhedrin",
        "Eruvin",
        "Taanit", "Bava Batra", "Rosh Hashanah", "Sotah", "Avodah Zarah", "Bava Metzia", "Shabbat", "Beitzah", "Chullin", "Gittin", "Pesachim", "Sukkah", "Yoma"]
    '''
    files = [file for file in os.listdir(".") if file.startswith("chidushei_") and file.endswith(".txt")]
    dont_start = True


    add_category("Seder Nezikin", ["Talmud", "Bavli", "Commentary", "Chidushei Halachot", "Seder Nezikin"], server="http://ste.sefaria.org")


    for file in files:
        if "Pesachim" not in file:
            continue
        masechet = file.split(".txt")[0].replace("chidushei_agadot_", "").replace("chidushei_halachot_","").title()
        print file
        len_masechet = len(Ref(masechet).text('he').text)
        if file.startswith("chidushei_ag"):
            title = "Chidushei Agadot"
            heTitle = u"חידושי אגדות"
            obj = Maharsha(masechet, title, heTitle, server="http://ste.sefaria.org")
        elif file.startswith("chidushei_ha"):
            title = "Chidushei Halachot"
            heTitle = u"חדושי הלכות"
            obj = Maharsha(masechet, title, heTitle, server="http://ste.sefaria.org")
        obj.parseText(open("./"+file), len_masechet)

        if len(obj.comm_dict) > 0 and obj.dont_post is False:
            obj.create_index(masechet)
            text_to_post = convertDictToArray(obj.comm_dict)
            send_text = {
                                "versionTitle": "Vilna Edition",
                                "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
                                "language": "he",
                                "text": text_to_post,
                        }
            post_text("{} on {}".format(title, masechet), send_text, "on", server="http://ste.sefaria.org")
            obj.postLinks(masechet)


