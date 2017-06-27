# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'
import codecs
from data_utilities.dibur_hamatchil_matcher import *
from sources.functions import *


sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud

class Rashba:

    def __init__(self, error_file, tractate, server):
        self.error_file = codecs.open(error_file, "w", 'utf-8')
        self.text = ""
        self.dhs = ""
        self.dh_dict = {}
        self.tractate = tractate
        self.server = server


    def noContent(self, line):
        line = line.replace(" ", "")
        return line == "@60" or line == "@10" or line.find("@99") >= 0 or line == "@40" or line == u""


    def makeOneFile(self):
        title = "RS-"
        text = []
        new_file = codecs.open("RS.txt", 'w', 'utf-8')
        for i in range(14):
            fname = title+str(i+1) if i > 8 else title+"0"+str(i+1)
            temp = ""
            for line in open("{}.txt".format(fname)):
                line = line.decode('utf-8')
                line = line.replace("\n","")
                pos = len(line) - 3
                if self.noContent(line):
                    continue
                if line[0:3] == "@60":
                    line = u"@40{}".format(line[3:])
                line = line.replace("@30", "@70")
                line = line.replace("@60", "@10")
                #at this point we can't have @60...@60 or @60...@10, but only @40...@60
                #and also can have @70...@40...@60
                if line[pos:] == '@10':
                    if len(temp) > 0 and temp[-1] != ' ':
                        temp += " "
                    temp += line
                    text.append(temp)
                    temp = ""
                elif line.find("@10") >= 0:
                    line_1, line_2 = line.split("@10")
                    temp += line_1 + "@10"
                    text.append(temp)
                    if self.noContent(line_2):
                        temp = ""
                    else:
                        temp = line_2
                else:
                    if len(temp) > 0 and temp[-1] != ' ':
                        temp += " "
                    temp += line
                prev_line = line

            if len(temp) > 0:
                text.append(temp)
                temp = ""
            for index, para in enumerate(text):
                new_file.write(para+"\n")
            text = []
        new_file.close()


    def create_schema(self):
        root = JaggedArrayNode()
        root.add_structure(["Daf", "Paragraph"], ["Talmud", "Integer"])
        he_title = library.get_index(self.tractate).get_title('he')
        root.add_primary_titles("Rashba on {}".format(self.tractate), u"""רשב"א על {}""".format(he_title))
        root.validate()
        index = {
            "dependence": "Commentary",
            "base_text_titles": [self.tractate],
            "collective_title": "Rashba",
            "schema": root.serialize(),
            "title": "Rashba on {}".format(self.tractate),
            "categories": ["Talmud", "Bavli", "Commentary", "Rashba", library.get_index(self.tractate).categories[-1]]
        }
        post_index(index, server=self.server)



    def postText(self):
        self.text = convertDictToArray(self.text)
        send_text = {
            "text": self.text,
            "language": "he",
            "versionTitle": "Gerlitz edition, published by Oraita",
            "versionSource": "http://www.sefaria.org/"
        }
        post_text("Rashba on {}".format(self.tractate), send_text, server=self.server)




    def getTextAndReportProblems(self, fname):
        patterns = [re.compile(u"(.*?)(@70.*?@40.*?@10$)"), re.compile(u"^@20.*?@\d\d.*?@10$")]
        #bad_patterns = [re.compile(u".*?@70.*?@40.*?@70.*?@10$")]
        current_daf_index = 3
        text = {}
        dhs = {}
        for line in open(fname):
            line = line.decode('utf-8')
            daf_line = patterns[1].match(line)
            dh_line = patterns[0].match(line)
            if daf_line:
                daf_p = re.compile(u"(^@20.*?)@\d+").match(line)
                assert daf_p
                daf_p = daf_p.group(1)
                line = line.replace(daf_p, "")
                daf, amud = daf_p.split(",")
                daf = getGematria(daf)
                amud = getGematria(amud)
                daf_index = (daf * 2) - amud if amud == 1 else (daf * 2)
                assert daf_index >= current_daf_index
                current_daf_index = daf_index
                text[current_daf_index] = []
            if current_daf_index not in dhs:
                dhs[current_daf_index] = []
            if dh_line:
                dh_p = re.compile(u"(^.*?)(@70.*?@40)")
                dh_match = dh_p.match(line)
                assert dh_match
                dh = dh_match.group(2).replace("@70", "").replace("@40", "")
                dhs[current_daf_index].append(dh)
                line = line.replace("@70", "<b>").replace("@40", "</b>")
                line = removeAllTags(line)
                assert current_daf_index in text
                text[current_daf_index].append(line)
            else:
                assert current_daf_index in text
                line = removeAllTags(line)
                text[current_daf_index].append(line)
                dhs[current_daf_index].append("")
        self.error_file.close()
        self.text = text
        self.dhs = dhs


    def makeDicts(self, daf):
        self.dh_dict[daf] = {}
        for count, str in enumerate(self.dhs[daf]):
            if len(str) > 0:
                self.dh_dict[daf][str] = count


    def postLinks(self):
        def base_tokenizer(str):
            str = re.sub(ur"\([^\(\)]+\)", u"", str)
            word_list = re.split(ur"\s+", str)
            word_list = [w for w in word_list if w]  # remove empty strings
            return word_list
        def dh_extract_method(str):
            str = str.replace(u'בד"ה', u'').replace(u'וכו', u'')
            return str
        '''
        1. strip out "" from dhs with list comprehension
        2. make dictionary where each dh str is key and the value is its index in the array
        '''
        links = []
        for daf in self.text:
            dhs_arr = [dh for dh in self.dhs[daf] if len(dh) > 0]
            gemara_text = Ref("{} {}".format(self.tractate, AddressTalmud.toStr("en", daf))).text('he')
            results = match_ref(gemara_text, dhs_arr, base_tokenizer, dh_extract_method=dh_extract_method, verbose=False)['matches']
            self.makeDicts(daf)
            rashba_refs = []
            for dh in dhs_arr:
                rashba_refs.append("Rashba on {} {}.{}".format(self.tractate, AddressTalmud.toStr("en", daf), self.dh_dict[daf][dh]+1))
            link_pairs = zip(rashba_refs, results)
            for link_pair in link_pairs:
                if link_pair[1]:
                    links.append(
                    {
                    "refs": [
                                 link_pair[0],
                                link_pair[1].normal()
                            ],
                    "type": "commentary",
                    "auto": True,
                    "generated_by": "rashba{}".format(self.tractate)
                    }
                    )
        post_link(links, server=self.server)



    def postTerm(self):
        post_term({
            "name": "Rashba",
            "scheme": "commentary_works",
            "titles": [
                {
                    "lang": "en",
                    "text": "Rashba",
                    "primary": True
                },
                {
                    "lang": "he",
                    "text": u'רשב"א',
                    "primary": True
                }
            ]
        })

if __name__ == "__main__":

    rashba = Rashba("no_matches.txt", "Bava Kamma", "https://www.sefaria.org")
    #rashba.postTerm()
    #rashba.create_schema()
    #rashba.makeOneFile()
    #rashba.reportProblems("RS.txt")
    rashba.getTextAndReportProblems("RS.txt")
    #rashba.postLinks()
    rashba.postText()