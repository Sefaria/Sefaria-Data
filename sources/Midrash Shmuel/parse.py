# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sources.functions import *
from data_utilities.dibur_hamatchil_matcher import *
links = []

def parse_intro(file):
    found_perek_one = False
    lines = []
    with open(file) as f:
        for line in f:
            found_perek_one = "@00פרק"  in line
            if found_perek_one:
                break
            if "@11" in line:
                line = line.replace("@11", "<b>").replace("@33", "</b>").replace("@44", "<br/><b>").replace("@55", "</b>")
                lines.append(line)
    return lines


def parse_main(file):
    found_perek_one = False
    text = {}
    perek = 0
    dhs = {}
    with open(file) as f:
        for count, line in enumerate(f):
            orig_line = line
            if not found_perek_one and "@00פרק" not in line:
                continue
            found_perek_one = True
            if "@00פרק" in line:
                perek += 1
                assert perek not in text.keys()
                text[perek] = {}
                dhs[perek] = []
                mishnah = 0
            elif "@22" in line:
                mishnah = getGematria(line)
                text[perek][mishnah] = []
            elif "@11" in line:
                if "@33" not in line:
                    split_lines = re_split_line(line, "@44")
                    for line in split_lines:
                        line = line.replace("@11", "")
                        markers = re.findall("@\d+", line)
                        line = line.replace("@44", "").replace("@55", "")
                        text[perek][mishnah].append(line)
                else:
                    markers = re.findall("@\d+", line)
                    split_lines = re_split_line(line, "@\d+.*?@\d+")
                    for i, line in enumerate(split_lines):
                        if i == 0:
                            line = line.replace(markers[0], "<b>").replace(markers[1], "</b>")
                        else:
                            assert line.find(": "+markers[i]) > 0 or line.find(". "+markers[i])
                            line = removeAllTags(line)
                        text[perek][mishnah].append(line)

    return text


def create_links(text_dict):
    start_of_range = None
    for perek_num, perek_text in text_dict.items():
        for mishnah_num, mishnah_text in perek_text.items():
            for segment_num, segment_text in enumerate(mishnah_text):
                dh = dh_extract_method(segment_text)

                if segment_num == 0 or dh:
                    if start_of_range:
                        create_link(prev_ref, start_of_range)
                    start_of_range = (perek_num, mishnah_num, segment_num+1)

                prev_ref = (perek_num, mishnah_num, segment_num + 1)





def create_link(prev_ref_tuple, prev_ref_with_dh):
    start_ref = Ref("Midrash Shmuel on Avot {}:{}:{}".format(prev_ref_with_dh[0], prev_ref_with_dh[1], prev_ref_with_dh[2]))
    end_ref = Ref("Midrash Shmuel on Avot {}:{}:{}".format(prev_ref_tuple[0], prev_ref_tuple[1], prev_ref_tuple[2]))
    assert prev_ref_tuple[0] == prev_ref_with_dh[0] and prev_ref_tuple[1] == prev_ref_with_dh[1]
    midrash_shmuel_ref = start_ref.to(end_ref)
    avot_ref = Ref("Avot {}:{}".format(prev_ref_with_dh[0], prev_ref_with_dh[1]))
    link = {"generated_by": "midrash shmuel linker", "auto": True, "type": "Commentary"}
    link["refs"] = [midrash_shmuel_ref.normal(), avot_ref.normal()]
    links.append(link)


def create_schema():
    root = SchemaNode()
    root.add_primary_titles("Midrash Shmuel on Avot", u"מדרש שמואל על אבות")
    intro = JaggedArrayNode()
    intro.add_shared_term("Introduction")
    intro.add_structure(["Paragraph"])
    intro.key = "intro"
    root.append(intro)
    content = JaggedArrayNode()
    content.add_structure(["Chapter", "Mishnah", "Paragraph"])
    content.default = True
    content.key = "default"
    root.append(content)
    root.validate()
    index = {
        "schema": root.serialize(),
        "title": "Midrash Shmuel on Avot",
        "base_text_titles": ["Pirkei Avot"],
        "dependence": "Commentary",
        "categories": ["Mishnah", "Commentary"]
    }
    post_index(index, server=SERVER)


'''
def midrash_shmuel_links(text):
    links = []
    ref_pairs = make_commentary_links("Midrash Shmuel", "Pirkei Avot")
    generic_link = {"generated_by": "midrash shmuel linker", "auto": True, "type": "Commentary"}
    for each_ref_pair in ref_pairs:
        link = dict(generic_link)
        link["refs"] = each_ref_pair
        links.append(link)
    post_link(links, server=SERVER)
'''

def dh_extract_method(line):
    start = line.find("<b>")
    end = line.find("</b>")
    if start == -1:
        return ""
    else:
        assert end != -1
        dh = line[start + 3:end]
        return dh


def base_tokenizer(str):
    str_list = str.split(" ")
    return [str for str in str_list if str]


def convert_ms_to_vilna(ms_text_dict):
    ms_to_vilna = {}
    with open("ms to vilna.csv") as csvfile:
        for row in csv.reader(csvfile):
            ms_to_vilna[row[0]] = row[1]

    vilna_text_dict = {}

    for perek_num, perek_text in ms_text_dict.items():
        vilna_text_dict[perek_num] = {}
        for mishnah_num, mishnah_text in perek_text.items():
            ms_ref = "{}:{}".format(perek_num, mishnah_num)
            vilna_perek, vilna_mishnah = ms_to_vilna[ms_ref].split(":")
            vilna_mishnah = int(vilna_mishnah)
            vilna_perek = int(vilna_perek)
            if vilna_mishnah not in vilna_text_dict[vilna_perek]:
                vilna_text_dict[vilna_perek][vilna_mishnah] = []
            for line in mishnah_text:
                vilna_text_dict[vilna_perek][vilna_mishnah].append(line)

    return vilna_text_dict

if __name__ == "__main__":
    for book in books:
        print """./run scripts/move_draft_text.py '{}' --noindex -d 'https://www.sefaria.org' -v "en:{}" -k 'kAEw7OKw5IjZIG4lFbrYxpSdu78Jsza67HgR0gRBOdg'""".format(book, vtitle)
    servers = ["http://draft.sefaria.org"]
    for SERVER in servers:
        VersionState("Midrash Shmuel on Avot").refresh()
        #create_schema()

        intro = parse_intro("midrash shmuel.txt")
        #create_payload_and_post_text("Midrash Shmuel on Avot, Introduction", intro, 'he', "Midrash Shmuel, Warsaw, 1876",
        #                            "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001125478", SERVER)

        main_text = parse_main("midrash shmuel.txt")
        main_text = convert_ms_to_vilna(main_text)
        create_links(main_text)
        post_link(links, server=SERVER)
        for key in main_text.keys():
            main_text[key] = convertDictToArray(main_text[key])
        main_text = convertDictToArray(main_text)
        for i in range(len(main_text)):
            print len(main_text[i])
            create_payload_and_post_text("Midrash Shmuel on Avot {}".format(i+1), main_text[i], 'he', "Midrash Shmuel, Warsaw, 1876",
                                "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001125478", SERVER)


