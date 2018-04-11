# -*- coding: utf-8 -*-

import codecs
import cal_util
import json
import re
from collections import defaultdict

# with codecs.open("caldbfull.txt", "rb", "utf8") as f, \
#      codecs.open("caldbfull.out", "wb", "utf8") as o:
#     for line in f:
#         lo = cal_util.parseCalLine(line, False)
#         o.write(cal_util.writeCalLine(lo) + u"\n")


def checkFullDict():
    with codecs.open("../data/Cal-Data-Files/dictfull.json", "rb", encoding="utf-8") as fin:
        fulldict = json.load(fin)
        for hw, posdict in fulldict.items():
            for p, defs in posdict.items():
                def_nums = set()
                for d in defs:
                    if d["def_num"] in def_nums:
                        print u"{}, {}, {}".format(hw, p, d["def_num"])
                    def_nums.add(d["def_num"])


def parseBCal():
    out_obj = defaultdict(lambda: defaultdict(list))
    with codecs.open("../data/Cal-Data-Files/bcal.txt", "rb", encoding="utf-8") as fin, \
         codecs.open("../data/Cal-Data-Files/bcal.json", "wb", encoding="utf-8") as fout:
        for i, line in enumerate(fin):
            try:
                lo = cal_util.parseBCalLine(line, True)
                out_obj[lo["cal_word"]][lo["cal_pos"]] += [{"dict_word": lo["dict_word"], "dict_pos": lo["dict_pos"]}]
            except ValueError:
                print u"{}, {}".format(i + 1, line)
        json.dump(out_obj, fout, encoding="utf8", indent=4, ensure_ascii=False)


def parseFullDict():
    out_obj = defaultdict(lambda: defaultdict(list))
    with codecs.open("../data/Cal-Data-Files/dictfull.txt" , "rb", encoding="utf-8") as fin, \
         codecs.open("../data/Cal-Data-Files/dictfull.json", "wb", encoding="utf-8") as fout:
        for i, line in enumerate(fin):
            try:
                lo = cal_util.parseDictLine(line, True)
            except cal_util.CalParsingException as e:
                print u"{}, {}".format(i+1, e)
                continue

            hw = lo[u"head_word"]
            pos = lo[u"POS"]
            del lo[u"head_word"]
            del lo[u"POS"]
            out_obj[hw][pos] += [lo]
        json.dump(out_obj, fout, indent=4, ensure_ascii=False, encoding="utf-8")


def generate_dialects_schema():
    dialect_schema = defaultdict(dict)
    with open("../data/Cal-Data-Files/dialects.txt", "rb") as fin, \
         open("../data/Cal-Data-Files/dialects.json", "wb") as fout:
        for line in fin:
            line = line.rstrip()
            code, desc = line.split(" = ")
            desc, tag = re.split(ur" (?=\([^)]+\)$)", desc)
            dialect_schema[code[0]][code[1]] = {
                "tag": tag[1:-1],
                "desc": desc
            }
        json.dump(dialect_schema, fout, indent=4)

# parseFullDict()
# checkFullDict()
parseBCal()
