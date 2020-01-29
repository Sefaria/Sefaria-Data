# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sources.functions import *
from sefaria.model import *
from sefaria.helper.schema import *
import bleach
import os
import re
curr_perek = 0
curr_halacha = 0
curr_hilchot = ""
text = {}
for f in os.listdir("."):
    if f.endswith(".txt"):
        print(f)
        lines = list(open(f))
        for line_n, line in enumerate(lines):
            hilchot = re.search("\$(.*?)\$", line)
            halacha = re.search("@EE(.*?)@FF", line)
            perek = re.search("\#(.*?)\#", line)
            if hilchot:
                curr_hilchot = hilchot.group(1)
                curr_halacha = 0
                curr_perek = 0
                text[curr_hilchot] = {}
            elif halacha:
                halacha = halacha.group(1)
                curr_halacha = getGematria(halacha.split()[-1])
                assert curr_perek > 0
                assert curr_halacha > 0
                text[curr_hilchot][curr_perek][curr_halacha] = []
            elif perek:
                perek = perek.group(1)
                curr_perek = getGematria(perek.split()[-1])
                text[curr_hilchot][curr_perek] = {}
                curr_halacha = 0
            else:
                if curr_halacha > 0 and curr_perek > 0:
                    if re.search("^@[A-Z]{2}.*?@[A-Z]{2}", line):
                        text[curr_hilchot][curr_perek][curr_halacha].append("")
                    orig_line = line
                    line = re.sub("^[@JG]{3}", "<b>", line)
                    if "<b>" in line:
                        line = re.sub("[@LKH]{3}", "</b>", line)
                    else:
                        line = re.sub("[@LKH]{3}", "", line)

                    line = re.sub("\{\}\@\d+", "", line)
                    if ("<b>" in line and "</b>" not in line) or ("<b>" not in line and "</b>" in line):
                        line = line.replace("<b>", "").replace("</b>", "")
                    curr_comm = len(text[curr_hilchot][curr_perek][curr_halacha]) - 1
                    text[curr_hilchot][curr_perek][curr_halacha][curr_comm] += line
                else:
                    print("Perek {} Halacha {} found at line {}".format(curr_perek, curr_halacha, line))
