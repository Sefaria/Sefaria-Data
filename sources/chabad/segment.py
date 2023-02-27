import csv
from collections import defaultdict
from sources.functions import post_text
import numpy
from bs4 import BeautifulSoup, Tag
from sefaria.search import *

def add_to_new_rows(text, henay, new_rows, just_found_paren):
    text = text.replace("  ", " ")
    text = cut_line(text, 0, asdf=henay, dont_recurse=True)
    new_rows_to_add = []
    if text[0].count(" ") > _max:
        new_rows_to_add += cut_line(text[0], 150)
    else:
        new_rows_to_add += [text[0]]
    check(new_rows_to_add, ". והנה")
    others = []
    for line in text[1:]:
        if line != text[-1] and not line.endswith("."):
            line += "."
        if line.count(" ") > _max:
            others += cut_line(line, 150)
        else:
            others.append(line)
    check(others, ". והנה")
    if len(new_rows) == 0 or not just_found_paren: #or new_rows[-1].count(" ") > _max:
        new_rows += new_rows_to_add + others
    else:
        new_rows[-1] += new_rows_to_add[0]
        new_rows += new_rows_to_add[1:] + others

def check(lines, henay):
    for line in lines:
        if line.count(" ") > 175 and henay in line:
            pass

probs = []
min = 30
total = 0
_max = 90
data_overlay = ".</i> ו"
def cut_line(line, num, asdf = ". ו", dont_recurse=True):
    lines = [line]
    global total
    global min
    global _max
    prob = False
    while len(lines) < len(line):
        x = []
        split = False
        for i in lines:
            if i.count(" ") > _max:
                split_text = i.split(asdf)
                if len(split_text) == 1:
                    if i.count(" ") > _max:
                        prob = True
                    x.append(i)
                else:
                    index = 0
                    running_text = split_text[0]
                    while running_text.count(" ") < min and index < len(split_text) - 1:
                        index += 1
                        running_text += asdf+split_text[index]
                    new_i = i.replace(running_text, "", 1)
                    if asdf[0] == ".":
                        vav = 'ו'
                        start = new_i.find(vav)
                        new_i = new_i[start:]
                        running_text += "."
                    elif asdf == data_overlay:
                        running_text += data_overlay
                        new_i = new_i[4:]
                    if running_text.count(" ") < min or new_i.count(" ") < min:
                        if i.count(" ") > _max:
                            prob = True
                        x.append(i)
                    else:
                        x.append(running_text)
                        x.append(new_i)
                        split = True
            else:
                x.append(i)
        lines = x
        if not split:
            break

    if data_overlay in line and asdf != data_overlay and not dont_recurse:
        actual_lines = []
        for l in lines:
            if l.count(" ") > _max:
                actual_lines += cut_line(l, 0, asdf=data_overlay, dont_recurse=dont_recurse)
            else:
                actual_lines += [l]
        return actual_lines
    else:
        return lines



def segment(file, new_name):
    global min
    global _max
    how_many = 0
    r = list(csv.reader(file))
    header = r[:5]
    r = r[5:]
    nums = []
    all_rows = []
    new_rows_dict = defaultdict(list)
    just_found_paren = False
    for row in r:
        ref, text = row
        orig = text
        if ":" in ref:
            sec_ref = ref.split(":")[0]
        else:
            sec_ref = " ".join(ref.split()[:-1])
        henay = ". והנה"
        new_rows = new_rows_dict[sec_ref]
        if len(new_rows) == 0:
            just_found_paren = False
        if text.count(" ") < _max:
            new_rows += [text]
        else:
            soup = BeautifulSoup("<html>"+text.replace("(", "<p>").replace(")", "</p>")+"</html>")
            running_text = ""

            for tag in soup.find("body").contents:
                if tag.name == "p":
                    if running_text:
                        add_to_new_rows(running_text, henay, new_rows, just_found_paren)
                    running_text = ""
                    if len(new_rows) == 0:
                        new_rows.append("("+tag.text+")")
                    else:
                        new_rows[-1] += "("+tag.text+")"
                    just_found_paren = True
                else:
                    running_text += str(tag) if isinstance(tag, Tag) else tag
            if running_text:
                add_to_new_rows(running_text, henay, new_rows, just_found_paren)
                just_found_paren = False

    with open(new_name, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(header)
        for sec_ref in new_rows_dict:
            #new_rows_dict[sec_ref] = [x.replace("..", ".").replace(":.", ":") for x in new_rows_dict[sec_ref]]
            for x in new_rows_dict[sec_ref]:
                # if x.count(" ") < min:
                #     how_many += 1
                if x.count(" ") > 175 and ". והנה" in x:
                    how_many += 1
            writer.writerows(new_rows_dict[sec_ref])
    for sec_ref in new_rows_dict:
        send_text = {"text": new_rows_dict[sec_ref], "language": "he", "versionTitle": "segmented", "versionSource": "https://www.sefaria.org"}
        for l, line in enumerate(new_rows_dict[sec_ref]):
            # if line.count(" ") < min and henay[2:] in line:
            #     print(line)
            if line.count(" ") > 500:
                print(f"{sec_ref} {l+1}")
                print(str(line.count(" ")) + " words")
                print("*****\n")
            nums.append(line.count(" "))
        post_text(sec_ref, send_text, server="http://localhost:8000")
    return nums


if __name__ == "__main__":
    nums = [] #/Exodus.1.10?ven=Tanakh:_The_Holy_Scriptures,_published_by_JPS&lang=bi&aliyot=0
    with open("Likkutei Torah - he - Kehot Publication Society.csv", 'r') as lt:
        nums += segment(lt, "Likkutei Torah (segmented) - he - Kehot Publication Society.csv")
    with open("Torah Ohr - he - Kehot Publication Society.csv", 'r') as to:
        nums += segment(to, "Torah Ohr (segmented) - he - Kehot Publication Society.csv")

    print(sum(nums)/float(len(nums)))
    np = numpy.histogram(nums)
