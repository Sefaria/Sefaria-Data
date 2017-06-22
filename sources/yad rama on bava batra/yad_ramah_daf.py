# -*- coding: utf-8 -*-
from sources.functions import *
__author__ = 'stevenkaplan'
import pdb
from data_utilities.dibur_hamatchil_matcher import match_ref

class Yad_Ramah:

    def __init__(self, server):
        self.server = server
        self.daf_re = re.compile(u"^.*?(\[[\u05D0-\u05EA]{1,3},[\u05D0-\u05EA]{1}\])")
        self.siman_re = re.compile(u"^([\u05D0-\u05EA]+)\. ")


    def getText(self, file):
        text = []
        temp = ""
        for line in file:
            line = line.decode('utf-8')
            line = line.replace("\n", "")
            line = self.removeBadText(line)
            if line.replace(" ", "") == "":
                continue
            if line.find(u"פרק ") >= 0 and len(line.split(" ")) < 4:
                text.append(line.replace("#", ""))
                continue
            if ":#" in line or ".#" in line:
                temp += line.replace("#", "")
                if len(temp) > 0:
                    text.append(temp)
                temp = ""
            else:
                temp += line.replace("#", "")

        file.close()
        if len(temp) > 0:
            text.append(temp)
        return text


    def removeBadText(self, para):
        arr = [u"דח.", u".זע", u".כע"]
        arr = re.findall(u">.*?<", para)
        arr += re.findall(u"<.*?>", para)
        for each in arr:
            if len(each) < 12:
                para = para.replace(each, u"")
        return para


    def structureText(self, text):
        perek_alt_struct = {}
        text_by_daf = {}
        dh_by_daf = {}
        perek_just_happened = False
        page = 1
        for index, para in enumerate(text):
            if para.find(u"פרק") == 0:
                perek_just_happened = True
                continue

            daf_match = self.daf_re.match(para)
            if daf_match:
                data = daf_match.group(1)
                para = para.replace(data+" ", "")
                para = para.replace(data, "")
                daf = getGematria(data.split(",")[0])
                amud = getGematria(data.split(",")[1])
                if amud == 2:
                    page = daf * 2
                else:
                    page = daf * 2 - 1
                assert page+1 not in text_by_daf
                text_by_daf[page] = []
                dh_by_daf[page] = []



            text_for_dh = " ".join(para.split(" ")[0:6])
            dh_by_daf[page].append(text_for_dh)

            siman_match = self.siman_re.match(para)
            if siman_match:
                siman = siman_match.group(0)

                para = para.replace(siman, u"<b>{}</b>".format(siman))


            assert page in text_by_daf
            text_by_daf[page].append(para)
        return text_by_daf, dh_by_daf


    def create_schema(self):
        '''
        siman_alt_struct = convertDictToArray(siman_alt_struct)
        nodes = []
        en =  "Simanim"
        he = u"סימנים"
        node = ArrayMapNode()
        node.add_primary_titles(en, he)
        node.depth = 1
        node.addressTypes = ["Integer"]
        node.sectionNames = ["Siman"]
        node.refs = siman_alt_struct

        node.wholeRef = "Yad Ramah on Bava Batra"
        nodes.append(node.serialize())
        '''

        root = JaggedArrayNode()
        root.add_primary_titles("Yad Ramah on Bava Batra", u"יד רמה על בבא בתרא")
        root.add_structure(["Daf", "Paragraph"], address_types=["Talmud", "Integer"])
        root.validate()
        index = {
            "title": "Yad Ramah on Bava Batra",
            "schema": root.serialize(),
            "collective_title": "Yad Ramah",
            "base_text_titles": ["Bava Batra"],
            "dependence": "Commentary",
            "categories": ["Talmud", "Bavli", "Commentary", "Seder Nezikin"],
            #'alt_structs': {"Subject": {"nodes": nodes}}
        }
        post_index(index, server=self.server)


    def siman_filter(self, text_segment):
        matched = re.compile(u"^<b>([\u05D0-\u05EA]+)\. </b>").match(text_segment)
        return matched


    def dh_func(self, string):
        if self.siman_re.match(string):
            string = string.replace(self.siman_re.match(string), "")

        return " ".join(string.split(" ")[0:6])


if __name__ == "__main__":
    yad_ramah = Yad_Ramah("http://localhost:8000")
    text = yad_ramah.getText(open("YR.txt"))
    text, dh_dict = yad_ramah.structureText(text)
    links = []
    text = convertDictToArray(text)
    results = get_matches_for_dict_and_link(dh_dict, "Bava Batra", "Yad Ramah", server="http://proto.sefaria.org", rashi_filter=yad_ramah.siman_filter, dh_extract_method=yad_ramah.dh_func)


    #yad_ramah.create_schema()
    send_text = {
        "text": text,
        "language": "he",
        "versionTitle": "Yad Ramah on Bava Batra",
        "versionSource": "http://www.sefaria.org/"
    }
    print "about to post"
    #post_text("Yad Ramah on Bava Batra", send_text, server=yad_ramah.server)