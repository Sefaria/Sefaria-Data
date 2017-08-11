# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sources.functions import *

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
    lines = {}
    perek = 0
    with open(file) as f:
        for line in f:
            if not found_perek_one and "@00פרק" not in line:
                continue
            found_perek_one = True
            if "@00פרק" in line:
                perek += 1
                assert perek not in lines.keys()
                lines[perek] = {}
                mishnah = 0
            elif "@22" in line:
                mishnah = getGematria(line)
                lines[perek][mishnah] = []
            elif "@11" in line:
                line = line.replace("@11", "<b>").replace("@33", "</b>").replace("@44", "<br/><b>").replace("@55", "</b>")
                lines[perek][mishnah].append(line)
    for perek in lines.keys():
        lines[perek] = convertDictToArray(lines[perek])
    lines = convertDictToArray(lines)
    return lines

def create_schema():
    root = SchemaNode()
    root.add_primary_titles("Midrash Shmuel", u"מדרש שמואל")
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
        "title": "Midrash Shmuel",
        "base_text_titles": ["Pirkei Avot"],
        "dependence": "Commentary",
        "categories": ["Mishnah", "Commentary"]
    }
    post_index(index, server=SERVER)


def midrash_shmuel_links():
    links = []
    ref_pairs = make_commentary_links("Midrash Shmuel", "Pirkei Avot")
    generic_link = {"generated_by": "midrash shmuel linker", "auto": True, "type": "Commentary"}
    for each_ref_pair in ref_pairs:
        link = dict(generic_link)
        link["refs"] = each_ref_pair
        links.append(link)
    post_link(links, server=SERVER)

if __name__ == "__main__":
    SERVER = "http://draft.sefaria.org"
    create_schema()

    intro = parse_intro("midrash shmuel.txt")
    create_payload_and_post_text("Midrash Shmuel, Introduction", intro, 'he', "Midrash Shmuel, Warsaw, 1876",
                                 "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001125478", SERVER)

    main = parse_main("midrash shmuel.txt")
    create_payload_and_post_text("Midrash Shmuel", main, 'he', "Midrash Shmuel, Warsaw, 1876",
                            "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001125478", SERVER)

    VersionState("Midrash Shmuel").refresh()
    midrash_shmuel_links()