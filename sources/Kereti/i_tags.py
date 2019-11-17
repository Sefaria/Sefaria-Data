#encoding=utf-8
import django
django.setup()
import codecs
from sefaria.model import *
from sources.functions import *
import re
from bs4 import BeautifulSoup
from difflib import context_diff
from data_utilities.dibur_hamatchil_matcher import *
import bleach
def extract_i_tags(line):
    i_tags = []
    len_i_tags = 0
    for m in re.finditer("""<i data.*?></i>""", line):
        pos = m.regs[0]
        i_tag = line[pos[0]:pos[1]]
        tag_dict = BeautifulSoup(i_tag).find("i").attrs
        i_tags.append((pos[0]-len_i_tags, tag_dict))
        len_i_tags += len(i_tag)
    return i_tags


def remove_i_tags(line):
    return re.sub(u"<i data.*?></i>", u"", line)

def insert_i_tags(line, i_tags):
    for i_tag in reversed(i_tags):
        html = "<i "
        pos, i_tag_dict = i_tag
        html += u'{}="{}"'.format("data-commentator", i_tag_dict["data-commentator"])
        if "data-label" in i_tag_dict:
            html += u' {}="{}"'.format("data-label", i_tag_dict["data-label"])
        html += u' {}="{}"'.format("data-order", i_tag_dict["data-order"])
        #assert i_tag_dict.keys() in ["data-commentator", "data-order", "data-label"]
        html += "></i>"
        line = line[0:pos] + html + line[pos:]
    return line

#
# i_tags = {}
# tc = TextChunk(Ref("Shulchan Arukh, Yoreh Deah"), lang='he', vtitle="Ashlei Ravrevei: Shulchan Aruch Yoreh Deah, Lemberg, 1888")
# for i, section in enumerate(tc.text):
#     i_tags[i] = {}
#     for j, line in enumerate(section):
#         i_tags[i][j] = extract_i_tags(line)
#         altered_line = remove_i_tags(line)
#         altered_line = insert_i_tags(altered_line, i_tags[i][j])
#         for line in context_diff(altered_line.split(), line.split()):
#             print line


#now take out all tags in file and then create data structure of all & and two words after
#dh_matcher can take all these two word strings and TextChunk(Ref("Shulchan Arukh, Yoreh Deah")
all_dhs = {}
siman = 0
for file in ["Mechaber 1.txt", "Mechaber 2.txt"]:
    with open(file) as f:
        for n, line in enumerate(f):
            line = line.decode('utf-8')
            if line.startswith("@22"):
                siman = getGematria(line.split()[0])
            if line.count("&") == 0:
                continue
            line = re.sub(u"\[\S{1,3}\]", u"", line)
            line = re.sub(u"!\S+", u"", line)
            line = re.sub(u"@\d+\S{1,3}", u"", line)

            line = line.replace("  ", " ").strip()
            dhs = [u" ".join(dh.split()[0:3]) for dh in re.split("\s?&\s?", line)]
            dhs = dhs[1:]
            curr = all_dhs.get(siman, [])
            all_dhs[siman] = curr + dhs


i_tags = {}
sections = Ref("Shulchan Arukh, Yoreh Deah").all_subrefs()
total = missed = 0
for sec in sections:
    if sec.sections[0] == 112:
        break
    tc = TextChunk(sec, lang='he', vtitle="Ashlei Ravrevei: Shulchan Aruch Yoreh Deah, Lemberg, 1888")
    base_text = ""
    for n, line in enumerate(tc.text):
        line = re.sub(u"\<.*?\>", u"", line)
        base_text += line + " "
    results = match_text(base_text.split(), all_dhs[sec.sections[0]])
    total += len(results["matches"])
    missed += results["matches"].count((-1, -1))
    for m in results["match_text"]:
        if m[0] == "":
            print sec
            print m[1]
            print
print 100.0*float(missed)/total
# for i, section in enumerate(tc.text):
#     i_tags[i] = {}
#     for j, line in enumerate(section):
#         i_tags[i][j] = extract_i_tags(line)
#         altered_line = remove_i_tags(line)
#         altered_line
#         altered_line = insert_i_tags(altered_line, i_tags[i][j])
