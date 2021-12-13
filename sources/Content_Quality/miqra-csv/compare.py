import django
django.setup()
import csv
import sys
from sources.functions import *
new_file = ""
import difflib


import os
import csv
issues = []
files = [open(f, 'r') for f in os.listdir(".") if f.endswith("csv")]
count = 0
for new_file in files:
    if "MAM" in new_file.name:
        continue
    # if "Moed" not in new_file or "Rosh" not in new_file:
    #     continue
    diff = defaultdict(set)
    reader = list(csv.reader(new_file))
    title = reader[0][1]
    orig_vtitle = reader[1][1]
    new_vtitle = orig_vtitle+"_new"
    lang = reader[2][1]
    vsource = reader[3][1]
    text = {}
    for row in reader[5:]:
        ref, comm = row
        tc = TextChunk(Ref(ref), lang=lang, vtitle=orig_vtitle)
        chars = ["&nbsp;", "thinsp;", "\xa0", "\u2009"]
        for char in chars:
            comm = comm.replace(char, " ")
            tc.text = tc.text.replace(char, " ")
        if tc.text.replace("&nbsp;", "\xa0").replace("thinsp;", '\u2009') != comm:
            count += 1
            diff[Ref(ref).index.title].update(set(tc.text).difference(set(comm)))
            diff[Ref(ref).index.title].update(set(comm).difference(set(tc.text)))
            minus_diff = ""
            plus_diff = ""
            prev = None
            for i, s in enumerate(difflib.ndiff(comm, tc.text)):
                if s[0] == ' ':
                    continue
                elif s[0] == '-':
                    if prev and prev[0] == "-":
                        minus_diff += s[-1]
                    elif prev:
                        if len(minus_diff) > 0:
                            print("New text -> {}".format(minus_diff))
                            issues.append((minus_diff, ref, "New Text", comm, tc.text))

                        minus_diff = ""
                elif s[0] == '+':
                    if prev and prev[0] == "+":
                        plus_diff += s[-1]
                    elif prev:
                        if len(plus_diff) > 0:
                            print("Our text -> {}".format(plus_diff))
                            issues.append((plus_diff, ref, "Our Text", comm, tc.text))
                        plus_diff = ""
                prev = s
            if len(plus_diff) > 0:
                print("New text -> {}".format(plus_diff))
                issues.append((plus_diff, ref, "Our Text", comm, tc.text))
            if len(minus_diff) > 0:
                issues.append((minus_diff, ref, "New Text", comm, tc.text))
                print("Our text -> {}".format(minus_diff))

with open("MAM_&.csv", 'w') as f:
    writer = csv.writer(f)
    writer.writerow(["Text with Addition", "Ref", "New Text", "Our Text", "Difference"])
    for x in list(issues):
        chars, ref, ours_or_new, new, ours = x
        if "&" in chars:
            writer.writerow([ours_or_new, ref, new, ours, chars])
with open("MAM_hebrew.csv", 'w') as f:
    writer = csv.writer(f)
    writer.writerow(["Text with Addition", "Ref", "New Text", "Our Text", "Difference"])
    for x in list(issues):
        chars, ref, ours_or_new, new, ours = x
        if "&" not in chars and "class=" not in chars:
            writer.writerow([ours_or_new, ref, new, ours, chars])
print(count)