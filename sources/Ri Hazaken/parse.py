#encoding=utf-8

import django
django.setup()
from sefaria.model import *
from data_utilities.dibur_hamatchil_matcher import *
from sources.functions import *

def get_relevant_DHs(ch_name, file_name):
    #returns those DHs of the lines under ch_name in file_name until the ch after ch_name
    dont_start = True
    relevant_DHs = []
    max_length = 6 #how many words in DH
    with open(file_name) as f:
        for line_n, line in enumerate(f):
            if line_n == 0:
                continue
            if line == "@{}\n".format(ch_name):
                if dont_start:
                    dont_start = False
                    continue
                else:
                    break
            if not dont_start:
                dh = line.split(".")[0].decode('utf-8')
                if len(dh.split()) > max_length:
                    dh = " ".join(line.split()[0:max_length]).decode('utf-8')
                relevant_DHs.append(dh)
    return relevant_DHs


def getDaf(new_daf):
    if re.match("\d+[ab]", new_daf):
        return AddressTalmud(0).toNumber("en", new_daf)
    daf, amud = new_daf[0:-1], new_daf[-1]
    daf = getGematria(daf)*2 - 1
    if amud == ":":
        daf += 1
    return daf

class Commentary:
    def __init__(self, file, index, heIndex, versionTitle, versionSource):
        self.file = file
        self.index = index
        self.heIndex = heIndex
        self.versionTitle = versionTitle
        self.versionSource = versionSource
        self.masechet = self.file.split(".csv")[0].title()
        title = "{} on {}".format(self.index, self.masechet)
        self.title = title


    def create_index(self):
        heMasechet = library.get_index(self.masechet).get_title('he')
        heTitle = u"{} על {}".format(self.heIndex, heMasechet)
        seder = library.get_index(self.masechet).categories[-1]

        root = JaggedArrayNode()
        root.add_structure(["Daf", "Comment"], address_types=["Talmud", "Integer"])
        root.add_primary_titles(self.title, heTitle)
        root.key = self.index
        root.validate()

        index = {
            "title": "{} on {}".format(self.index, self.masechet),
            "schema": root.serialize(),
            "categories": ["Talmud", "Bavli", "Commentary", self.index, seder],
            "dependence": "Commentary",
            "collective_title": self.index,
            "base_text_titles": [self.masechet]
        }
        return index


def dh_extract_method(str):
    dh = str.split(".")[0]
    if len(dh.split()) > 7:
        return u" ".join(str.split()[0:7])
    else:
        return dh

def convert_txt_to_csv(f):
    temp = ""
    csv_f = f.replace(".txt", ".csv")
    with open(csv_f, 'w') as csv_file:
        with open(f) as file:
            for line in file:
                line = line.replace("\n", "").replace("\r", "")
                if line[3] == "@":
                    line = line[3:]
                if line.startswith("@"):
                    temp = line
                else:
                    new_line = temp + "," + line
                    csv_file.write(new_line+"\n")
                    temp = ""


if __name__ == "__main__":
    #comms = [Commentary("yevamot.csv", "Tosafot Yeshanim", u"תוספות ישנים", "Vilna Edition", "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957"),
    #         Commentary("nazir.csv", "Commentary of the Rosh", u"""פירוש הרא"ש""", "Vilna Edition", "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957")]
    convert_txt_to_csv("tosafot shantz.txt")
    vtitle = "Vilna Edition"
    vsource = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957"
    comms = [Commentary("sotah.csv", "Tosafot Shantz", u"""תוספות שאנץ""", vtitle, vsource)]
    links = []
    for commentary in comms:
        lines_by_daf = {}
        print commentary.file
        post_index(commentary.create_index(), server=SEFARIA_SERVER)
        with open(commentary.file) as f:
            lines = list(f)
            found_amud_count = 0
            prev_last_word = ""
            curr_daf = 0
            for line_n, line in enumerate(lines):
                if line_n % 50 == 0:
                    print line_n
                line = line.replace("\n", "").replace("\r", "").replace('""', '"')
                new_daf, comment = line.split(",", 1)
                if comment[0] == '"':
                    comment = comment[1:]
                if comment[-1] == '"':
                    comment = comment[:-1]
                new_daf = new_daf.strip()
                if new_daf:
                    poss_daf = getDaf(new_daf)
                    if poss_daf <= curr_daf:
                        print comment
                    curr_daf = poss_daf
                    lines_by_daf[curr_daf] = []
                lines_by_daf[curr_daf].append(comment.decode('utf-8'))
        for daf, comments in lines_by_daf.items():
            base_text = TextChunk(Ref(commentary.file.split(".csv")[0] + " " + AddressTalmud.toStr("en", daf)), lang='he')
            results = match_ref(base_text, comments, lambda x: x.split(), dh_extract_method=dh_extract_method)
            if results:
                for n, match in enumerate(results["matches"]):
                    if not match:
                        continue
                    link = {"refs": ["{} {}:{}".format(commentary.title, AddressTalmud.toStr("en", daf), n+1), match.normal()],
                            "auto": True, "generated_by": "Ri_HaZaken_script", "type": "Commentary"}
                    links.append(link)
        lines_by_daf = convertDictToArray(lines_by_daf)
        send_text = {
            "text": lines_by_daf,
            "language": "he",
            "versionTitle": commentary.versionTitle,
            "versionSource": commentary.versionSource
        }
        post_text(commentary.title, send_text, server=SEFARIA_SERVER)
    post_link(links, server=SEFARIA_SERVER)



#Use alt struct of index to get map of each chapter and its dappim and create range variable from first to last amud
#then using marked up file containing chapter info, gather all DHs for that chapter
#and base text chunk's ref will be based on range variable