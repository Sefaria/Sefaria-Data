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
        self.alt_struct = [] #list of tuples of name of each section and ref str for where it begins
        self.curr_dh = ""
        self.total = 0

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
            "base_text_mapping": "many_to_one",
            "dependence": "Commentary",
            "categories": ["Talmud", "Bavli", "Commentary"],
            #'alt_structs': {"Subject": {"nodes": nodes}}
        }
        post_index(index, server=self.server)

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
            if line.endswith(".#") or line.endswith(":#"):
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


    #

    def dh_func(self, string):
        siman_re = re.compile(u"^<b>([\u05D0-\u05EA]+)\. </b>")
        if siman_re.match(string):
            string = string.replace(siman_re.match(string).group(0), "")
            self.curr_dh = " ".join(string.split(" ")[0:6])
            self.total += 1
        else:
            return ""
        return self.curr_dh

def ending_in_hebrew(str):
    found_hebrew = False
    while len(str) > 0 and str[-1] not in [".", ":"]:
        found_hebrew = found_hebrew or any_hebrew_in_str(str[-1].encode('utf-8'))
        if found_hebrew:
            return True
        str = str[0:-1]
    return False

def make_fake_index():
    fake = SchemaNode()
    fake.add_primary_titles("Asdf", u"שדגכ")
    genesis = JaggedArrayNode()
    genesis.add_primary_titles("Genesis", u"בראשית")
    genesis.add_structure(["Paragraph"])
    exodus = JaggedArrayNode()
    exodus.add_primary_titles("Exodus", u"שמות")
    exodus.add_structure(["Paragraph"])
    fake.append(genesis)
    fake.append(exodus)
    fake.validate()
    index = {"schema": fake.serialize(), "title": "Asdf", "categories": ["Other"]}
    post_index(index, server="http://localhost:8000")

def is_nonsense(str, nonsense_words):
    found = ""
    for word in nonsense_words:
        if str.startswith(word):
            found = word
            break
    str = str.replace(found, "")
    if len(str.split(" ")) == 1:
        return ""
    if str.strip().startswith(u"בבא בתרא") and len(str.split(" ")) < 7:
        return ""
    return str

if __name__ == "__main__":

    #### code below took text as it existed on proto in early 2017 and re-structured and linked it ####
    import csv, codecs
    dappim = ["Yad Ramah on Bava Batra {}".format(AddressTalmud.toStr("en", daf)) for daf in range(3, 176*2)]
    csvfile = "Yad Ramah on Bava Batra - he - Yad Ramah on Bava Batra.csv"
    newcsvfile = "Yad Ramah on Bava Batra - he - Yad Ramah on Bava Batra2.csv"
    daf_text = {}
    total = bad = 0
    new_daf_text = {}
    temp = u""
    current_ref = ""
    newcsv = UnicodeWriter(open(newcsvfile, 'w'), encoding='utf-8')
    segment_modifier = 0
    prev = ""
    nonsense_set = set()
    nonsense_words = [u'.כע', u'.זע',
    u'.\u05d6\u05e2\u05d9\u05d3\u05e8\u05de\u05d4',
     u'\u05db\u05e2~',
     u'.\u05db\u05e2\u05d9\u05d3\u05e8\u05de\u05d4',
     u'.\u05db\u05e2~',
     u'\u05d3\u05d7',
     u'\u05d6\u05e2\u05d9\u05d3\u05e8\u05de\u05d4',
     u'.\u05d6\u05e2~',
     u'\u05d6\u05e2~',
     u'.\u05d3\u05d7']
    nonsense_dappim = [257, 258, 342, 65, 265, 343, 14, 272, 280, 276, 21, 23, 24, 25, 26, 167, 300, 45, 304, 308, 311, 315, 193, 198, 199, 74, 334, 207, 82, 83, 270, 86, 87, 349, 350, 237, 242, 211, 116, 253, 127]
    dont_attach_list = ["98a", "98b", "99a", "99b", "100a", "100b", "101a", "101b", "102a"]
    with open(csvfile) as f:
        reader = csv.reader(f)
        for row in reader:
            if not row[0].startswith("Yad Ramah"):
                newcsv.writerow(row)
                continue
            total += 1
            ref = row[0]
            current_ref, segment = ref.split(":")
            dont_attach = current_ref.replace("Yad Ramah on Bava Batra ", "") in dont_attach_list
            current_ref = Ref(current_ref.replace("Yad Ramah on ", "")).sections[0]
            segment = int(segment)
            if segment == 1:
                new_daf_text[current_ref] = []
                if len(temp) > 0:
                    temp += ":"
                    new_daf_text[prev].append(temp)
                    temp = u""

            row[1] = row[1].replace("\n", "")
            row[1] = row[1].decode('utf-8')
            row[1] = is_nonsense(row[1], nonsense_words)
            if len(row[1].replace(" ", "")) == 0:
                continue
            temp += row[1]
            if ending_in_hebrew(row[1]) and not dont_attach:
                bad += 1
                temp += " "
            else:
                temp = temp.replace("H", "").replace("P", "").replace("0", "")
                english = set(re.findall("[a-zA-Z0-9]{1}", temp))
                if english:
                    for char in english:
                        if temp[temp.find(char)-1] == "<":
                            print 'tag! not removing...'
                        else:
                            temp = temp.replace(char, "")
                new_daf_text[current_ref].append(temp)
                temp = u""
            prev = current_ref
    print(total)
    print(bad)
    results = []
    dh_dict = {}
    percent_per_daf = {}
    links = []
    matched = 0
    yd = Yad_Ramah("http://draft.sefaria.org")
    #yd.create_schema()
    others = 0
    add_link = False
    for daf, comments in new_daf_text.items():
        base_text = TextChunk(Ref("Bava Batra {}".format(AddressTalmud.toStr("en", daf))), lang='he')
        start_ref = orig_base_ref = prev_base_ref = ""
        orig_comments = comments
        comments = [yd.dh_func(el) for el in comments]
        prev_comm = ""
        for i, comment in enumerate(comments):
            if comment:
                prev_comm = comment
            else:
                comments[i] = prev_comm
        yd.total += len([el for el in comments if el])
        temp_results = match_ref(base_text, comments, base_tokenizer=lambda x: [el for el in x.split(" ") if el], word_threshold=0.45)["matches"]
        assert len(comments) == len(temp_results)
        for this_ref, base_ref in enumerate(temp_results):
            comment = comments[this_ref]
            if base_ref:
                if start_ref and orig_base_ref and (comment != prev_comm or base_ref.normal() != prev_base_ref):
                    #close off previous one
                    if start_ref.split(":")[-1] == str(this_ref):
                        range_ref = start_ref
                    else:
                        range_ref = "{}-{}".format(start_ref, this_ref)
                    links.append(
                        {"refs": [range_ref, prev_base_ref], "auto": True,
                         "generated_by": "yad_ramah_bava_batra_linker",
                         "type": "commentary"})
                    #start new range
                    start_ref = "Yad Ramah on Bava Batra {}:{}".format(AddressTalmud.toStr("en", daf), this_ref + 1)
                elif not start_ref:
                    #no range, start first one
                    orig_base_ref = base_ref.normal()
                    start_ref = "Yad Ramah on Bava Batra {}:{}".format(AddressTalmud.toStr("en", daf), this_ref+1)
                prev_base_ref = base_ref.normal()
            elif start_ref:
                #close off previous range
                if start_ref.split(":")[-1] == str(this_ref):
                    range_ref = start_ref
                else:
                    range_ref = "{}-{}".format(start_ref, this_ref)
                links.append(
                    {"refs": [range_ref, prev_base_ref], "auto": True,
                     "generated_by": "yad_ramah_bava_batra_linker",
                     "type": "commentary"})
                #dont start new range
                start_ref = None
            prev_comm = comment




            # if base_ref:
            #     links.append({"refs": [this_ref, base_ref.normal()], "auto": True, "generated_by": "yad_ramah_bava_batra_linker", "type": "commentary"})
            # else:
            #     others += 1

    post_link(links, server="http://draft.sefaria.org")
    for daf, text in new_daf_text.items():
    send_text = {
            "text": convertDictToArray(new_daf_text),
            "language": "he",
            "versionTitle": "Yad Ramah on Bava Batra",
            "versionSource": "http://www.sefaria.org"
        }
    post_text("Yad Ramah on Bava Batra", send_text, server="http://draft.sefaria.org")

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