import django
django.setup()
import csv
from sources.functions import *
import os
import re
from data_utilities.dibur_hamatchil_matcher import *
def parse_daf(text, daf, prev_daf, amud, line):
    amud = getGematria(amud)
    if amud not in [1, 2, 71, 72]:
        amud = 1 if "'" in daf else 2
    amud = amud % 2
    curr_daf = getGematria(daf) * 2 - (amud)
    curr_daf = fix_daf(daf, curr_daf, prev_daf, amud)
    prev_daf = curr_daf
    text[curr_daf] = []
    return curr_daf, prev_daf

def fix_daf(text, daf, prev, amud):
    if daf > prev + 1 and text.startswith("ד") and len(text) in [3, 4]:
        return (getGematria(text[1:]) * 2) - amud
    elif daf > prev + 1:
        text = text.replace("(", "").replace(")", "")
        return (getGematria(text[0]) * 2) - amud
    elif daf < prev:
        return None
    else:
        return daf

def process_old_files():
    for f in os.listdir("."):
        text = {}
        if f.endswith("txt"):
            title = u" ".join(f.split(".txt")[:-1])
            prev_daf = 3
            text[prev_daf] = []
            with open(f) as file:
                lines = list(file)

                for n, line in enumerate(lines):
                    poss_daf = re.search("[@\d(]{3,4}דף \S{1,} \S{1,} ", line)
                    poss_daf_2 = re.search("@\d+(\(.*?\)) ", line)
                    if poss_daf:
                        print(" ".join(line.split()[:5]))
                        marker, daf, amud = poss_daf.group(0).split()
                        curr_daf, prev_daf = parse_daf(text, daf, prev_daf, amud, line)
                        line = line.replace(poss_daf.group(0), "")
                    elif poss_daf_2:
                        print(" ".join(line.split()[:5]))
                        info = poss_daf_2.group(1).split()
                        if len(info) == 1:
                            daf = prev_daf
                            amud = info[0]
                            if amud == '(ע"ב)':
                                daf = prev_daf if prev_daf % 2 == 0 else prev_daf + 1
                        elif len(info) == 2:
                            daf = info[0]
                            amud = info[1]
                        elif len(info) == 3:
                            daf = info[1]
                            amud = info[2]

                        amud = getGematria(amud)
                        if daf == '(שם':
                            daf = prev_daf if prev_daf % 2 == 0 else prev_daf + 1
                        elif len(info) > 1:
                            poss_daf = getGematria(daf) * 2
                            # if poss_daf > prev_daf + 5:
                            #     poss_daf = getGematria(daf[1]) * 2
                            amud = amud % 2
                            poss_daf = poss_daf - amud
                            daf = fix_daf(daf, poss_daf, prev_daf, amud)
                        prev_daf = daf
                        line = line.replace(poss_daf_2.group(0), "")
                        if prev_daf not in text:
                            text[prev_daf] = []
                    text[prev_daf].append(line)

if __name__ == "__main__":
    for f in os.listdir("."):
        if not f.endswith("tsv"):
            continue
        title = f.split(" - ")[-1]
        try:
            en_title = library.get_index(title).title
        except:
            continue
        text = {}
        dhs = {}
        with open(f) as tsv_file:
            for line in f:
                daf, comment = line.split("\t", 1)
                daf_as_num = getGematria(daf) * 2
                amud = 1 if "." in daf else 0
                daf_as_num -= amud
                dh = comment.split(".")[0]
                if dh.count(" ") > 7:
                    dh = ""
                if daf_as_num not in text:
                    text[daf_as_num] = []
                    dhs[daf_as_num] = []
                text[daf_as_num].append(comment)
                dhs[daf_as_num].append(dh)
            links = []
            for daf, comments in dhs.items():
                daf = AddressTalmud.toStr("en", daf)
                comm_ref = "Chidushei Chatam Sofer on {} {}".format(en_title, daf)
                base_ref = "{} {}".format(en_title, daf)
                links += match_ref_interface(base_ref, comm_ref, comments, lambda x: x.split(), lambda x: x)
            text = convertDictToArray(text)
            send_text = {
                "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH002036613/NLI",
                "versionTitle": "Chidushei Chatam Sofer, 1864-1908",
                "text": text,
                "language": "he"
            }
            root = JaggedArrayNode()
            root.add_structure(["Daf", "Paragraph"], address_types=["Talmud", "Integer"])
            root.add_primary_titles("Chatam Sofer on {}".format(en_title), u"חתם סופר על {}".format(title))
            root.validate()
            indx = {
                "schema": root.serialize(),
                "title": "Chatam Sofer on {}".format(en_title),
                "categories": ["Talmud", "Bavli", "Commentary", "Chatam Sofer"]
            }
            post_index(indx)
            post_text("Chatam Sofer on {}".format(en_title), send_text)

