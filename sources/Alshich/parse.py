# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sources.functions import *
from data_utilities.dibur_hamatchil_matcher import *


SERVER = "https://www.sefaria.org"


def get_DH_comment(line):
    ten_word_pos = line.find(" ".join(line.split(" ")[10:11]))

    if 0 < line.find(".") < ten_word_pos:
        DH, comment = line.split(".", 1)
    elif 0 < line.find(u"וכו'") < ten_word_pos:
        DH, comment = line.split(u"וכו'", 1)
    else:
        DH, comment = line[0:ten_word_pos], line[ten_word_pos:]

    return DH, comment

def parse(file):
    perek_num = 0
    line_num = 0
    last_tag = ""
    last_perek_tag = ""
    pasuk_num = 0
    segment_num = 0
    text = {}
    pasuk_list = []
    DHs = {}
    for count, line in enumerate(open(file)):
        orig_line = line
        line = removeExtraSpaces(line)
        line = line.replace("\n", "").replace("\r", "").decode('utf-8')
        if len(line) == 0 or line.startswith("$") or "@02" in line or "@01" in line or "@03" in line:
            continue

        if line.find("@00") == 0 and len(line.split(" ")) < 3:
            poss_perek_num = getGematria(line)
            perek_num = ChetAndHey(poss_perek_num, perek_num)
            pasuk_num = 0
            assert perek_num not in text
            text[perek_num] = {}
            segment_num = 0
            DHs[perek_num] = {}
            line_num = 0
        elif line.find("@22") == 0:
            pasuk_list.append(line)
            poss_pasuk_num = getGematria(line)
            pasuk_num = ChetAndHey(poss_pasuk_num, pasuk_num)
            text[perek_num][pasuk_num] = []
            DHs[perek_num][pasuk_num] = []
            segment_num = 0
        elif line.find("@11") == 0:
            if DHs[perek_num] == {}:
                print "Perek {} unclear what pasuk.  Assuming pasuk 1...".format(perek_num)
                pasuk_num = 1
                DHs[perek_num][pasuk_num] = []
                text[perek_num][pasuk_num] = []
            if line.find("@33") > 0:
                line = line.replace("@11", "<b>").replace("@33", "</b>")
                text[perek_num][pasuk_num].append(removeAllTags(line))
            else:
                text[perek_num][pasuk_num].append(removeAllTags(line))
            segment_num += 1
        elif len(line.split(" ")) > 4:
            if line.find("@77") > 0 and line.find("@66") >= 0:
                line = line.replace("@66", "<b>").replace("@77", "</b>")
            if line.find("@44") >= 0 and line.find("@55") > 0:
                line = line.replace("@44", "<b>").replace("@55", "</b>")
            if "<b>" not in line:
                line = u"<b>{}</b> {}".format(line.split(" ")[0], " ".join(line.split(" ")[1:]))
            text[perek_num][pasuk_num].append(removeAllTags(line))
            segment_num += 1

        prev_line = orig_line
    return text



def get_DH_comment(line):
    ten_word_pos = line.find(" ".join(line.split(" ")[10:11]))

    if 0 < line.find(".") < ten_word_pos:
        DH, comment = line.split(".", 1)
    elif 0 < line.find(u"וכו'") < ten_word_pos:
        DH, comment = line.split(u"וכו'", 1)
    else:
        DH, comment = line[0:ten_word_pos], line[ten_word_pos:]

    return DH, comment



def create_schema():
    root = SchemaNode()
    root.add_primary_titles("Alshich on Torah", u"אלשיך על התורה")
    root.add_title(u"תורת משה", lang='he')
    root.add_title("Torat Moshe", lang='en')

    books = library.get_indexes_in_category("Torah", full_records=True)
    for book in books:
        en_name = book.get_title("en")
        he_name = book.get_title("he")
        node = JaggedArrayNode()
        node.toc_zoom = 2
        node.add_structure(["Chapter", "Paragraph", "Comment"])
        node.add_primary_titles(en_name, he_name)
        root.append(node)

    index = {
        "schema": root.serialize(),
        "dependence": "Commentary",
        "collective_title": "Alshich",
        "base_text_titles": ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"],
        "categories": ["Tanakh", "Commentary"],
        "title": u"Alshich on Torah",
        }
    post_index(index, server=SERVER)



def make_links(ref, text):
    links = []
    for perek_num, perek in text.items():
        for pasuk_num, pasuk in perek.items():
            bible_ref = "{} {}:{}".format(ref, perek_num, pasuk_num)
            if len(pasuk) > 1:
                alshich_ref = "Alshich on Torah, {}:{}-{}".format(bible_ref, 1, len(pasuk))
            else:
                alshich_ref = "Alshich on Torah, {}:{}".format(bible_ref, 1)
            new_link = {
                    "refs": [
                        bible_ref,
                        alshich_ref
                    ],
                    "generated_by": "Alshich",
                    "type": "Commentary",
                    "auto": True
                }
            links.append(new_link)

    post_link(links, server=SERVER)




if __name__ == "__main__":
    add_term("Alshich", u"אלשיך", "commentary_works", SERVER)
    files = [file for file in os.listdir("./") if not file == "intro.txt" and file.endswith(".txt")]
    create_schema()
    for file in files:
        print file[0:-4]
        parsed = parse(file)
        #make_links(file[0:-4].title(), parsed)
        for perek in parsed.keys():
            parsed[perek] = convertDictToArray(parsed[perek])
        parsed = convertDictToArray(parsed)
        #create_payload_and_post_text("Alshich on Torah, {}".format(file[0:-4].title()), parsed, "he", "Torat Moshe; Warsaw, 1875", "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001268220", server=SERVER)
