# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from os import listdir
from os.path import isfile
from sources.functions import *
from data_utilities.util import wordToNumber, getGematria, convert_dict_to_array
import re
from sefaria.model import *


def getMishnah(line):
    if line.find("@22") == 0:
        line = line.split(" ")[0].replace("@22", "")
        return getGematria(line)
    else:
        first_word = line.replace("@11", "").split(" ")[0]
        if len(first_word) == 1:
            return getGematria(first_word)
    return None


def getLine(line):
    if len(line) > 13:
        while line[0] == " ":
            line = line[1:]
        return line
    return None


def parse(file):
    text = {}
    file = open(file)
    perek = 1
    text[1] = {}
    mishnah = 0
    for line in file:
        line = line.decode('utf-8')
        if line.find("@00") == 0:
            continue
        poss_mishnah = getMishnah(line)
        if poss_mishnah:
            poss_mishnah = ChetAndHey(poss_mishnah, mishnah)
            if poss_mishnah not in text[perek]:
                text[perek][poss_mishnah] = []
                mishnah = poss_mishnah
            else:
                assert poss_mishnah == 1
                mishnah = 1
                perek += 1
                text[perek] = {}
                text[perek][1] = []

        line = getLine(line)
        if line:
            if line.find("@22") == 0:
                line = " ".join(line.split(" ")[1:])
            if line.find("@58") >= 0 or line.find("@78") >= 0:
                matches = re.findall("@58\S+|@78\S+", line)
                for match in matches:
                    line = line.replace(match, "")
            line = line.replace("@11", "<b>").replace("@33", "</b>")
            line = line.replace("@66", "<small>(").replace("@77", ")</small>")
            line = removeAllTags(line)
            lines = line.split("<b>")[1:]
            for each_line in lines:
                text[perek][mishnah].append("<b>"+each_line)
        prev_line = line

    for perek in text:
        text[perek] = convert_dict_to_array(text[perek])
    text = convert_dict_to_array(text)
    return text

def post(text):
    send_text = {
        "lang": "he",
        "text": text,
        "versionTitle": "Talmud Bavli, Vilna, 1880.",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957"
    }


def create_schema(title, mishnah_title):
    index = Index().load({"title": mishnah_title})
    he_title = index.get_title("he")
    root = JaggedArrayNode()
    root.add_primary_titles(title, u'ר"ש משאנץ על {}'.format(he_title))
    root.add_structure(["Perek", "Mishnah", "Paragraph"])
    root.toc_zoom = 2
    index_to_post = {
        "schema": root.serialize(),
        "title": title,
        "categories": ["Mishnah", "Commentary", "Rash MiShantz"],
        "base_text_mapping": "many_to_one",
        "dependence": "Commentary",
        "base_text_titles": [index.get_title("en")]
    }
    post_index(index_to_post)
    if mishnah_title == "Mishnah Middot":
        index = Index().load({"title": mishnah_title})
        he_title = index.get_title("he")
        root = JaggedArrayNode()
        root.add_primary_titles(title, u"רבינו שמעיה על משנה מדות")
        root.add_structure(["Perek", "Mishnah", "Paragraph"])
        root.toc_zoom = 2
        index_to_post = {
            "schema": root.serialize(),
            "title": title,
            "categories": ["Mishnah", "Commentary", "R' Shemaiah"],
            "base_text_mapping": "many_to_one",
            "dependence": "Commentary",
            "base_text_titles": [index.get_title("en")]
        }
        post_index(index_to_post)





def post_terms():
    term_obj = {
        "name": "Rash MiShantz",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Rash MiShantz",
                "primary": True
            },
            {
                "lang": "he",
                "text": u'ר"ש משאנץ',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
    term_obj = {
        "name": "R' Shemaiah",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "R' Shemaiah",
                "primary": True
            },
            {
                "lang": "he",
                "text": u'רבינו שמעיה',
                "primary": True
            }
        ]
    }
    post_term(term_obj)

if __name__ == "__main__":
    #post_terms()
    files = [f for f in listdir("./") if isfile(f) and f.endswith(".txt")]
    files = ["middot.txt"]
    for file in files:
        print file
        text = parse(file)
        if file == "middot.txt":
            title = "R' Shemaiah on Mishnah Middot"
        else:
            title = "Rash MiShantz on Mishnah "+file.replace('.txt', '').title()
        create_schema(title, "Mishnah "+file.replace('.txt', '').title())
        text = {
            "text": text,
            "language": "he",
            "versionTitle": "Talmud Bavli, Vilna, 1880.",
            "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957"
        }
        if file == "middot.txt":
            post_text(title, text)


    # if library.get_index
    # go through each book
    # check length
