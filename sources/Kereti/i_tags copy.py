#encoding=utf-8
import django
django.setup()
import codecs
from sefaria.model import *
from sources.functions import *
import re
from bs4 import BeautifulSoup
from difflib import context_diff
from linking_utilities.dibur_hamatchil_matcher import *
import bleach


def get_two_words(line, pos, dir=1):
    orig_pos = pos
    curr = pos
    words = [None, None]
    i = 0
    while i < 1 and len(line) > curr >= 0:
        if dir == 1 and line[curr:].startswith("<i data"):
            curr_i_tag = re.findall("<i data.*?></i>", line[curr:])[0]
            curr += len(curr_i_tag)
        elif dir == -1 and line[curr] == ">":

        elif line[curr] == " ":
            word_to_add = line[curr+1:pos] if dir == -1 else line[pos:curr]
            if word_to_add:
                words[i] = word_to_add.strip()
                i += 1
                pos = curr
            curr += dir
        else:
            curr += dir
    words_str = words[0] #" ".join(reversed(words)) if dir == -1 else " ".join(words)
    if words_str not in line:
        print words_str
    return words_str


def extract_i_tags(line):
    i_tags = []
    len_i_tags = 0
    for n, m in enumerate(re.finditer("""<i data.*?></i>""", line)):
        pos = m.regs[0]
        i_tag = line[pos[0]:pos[1]]
        # two_words_before = get_two_words(line, pos[0], dir=-1)
        # two_words_after = get_two_words(line, pos[1])
        tag_dict = BeautifulSoup(i_tag).find("i").attrs
        i_tags.append((pos[0], tag_dict))
        len_i_tags += len(i_tag)
    return i_tags


def remove_i_tags(line):
    return re.sub(u"<i data.*?></i>", u"", line)

def insert_i_tags(line, i_tags):
    for i_tag in reversed(i_tags):
        html = "<i "
        before_word, after_word, i_tag_dict = i_tag
        html += u'{}="{}"'.format("data-commentator", i_tag_dict["data-commentator"])
        if "data-label" in i_tag_dict:
            html += u' {}="{}"'.format("data-label", i_tag_dict["data-label"])
        html += u' {}="{}"'.format("data-order", i_tag_dict["data-order"])
        #assert i_tag_dict.keys() in ["data-commentator", "data-order", "data-label"]
        html += "></i>"
        start_pos = line.find(before_word + " " + after_word)
        re.findall(u"{}")
        assert start_pos != -1
        start_pos += len(before_word)
        line = line[0:start_pos] + html + line[start_pos:]
    return line


i_tags = {}
tc = TextChunk(Ref("Shulchan Arukh, Yoreh Deah"), lang='he', vtitle="Ashlei Ravrevei: Shulchan Aruch Yoreh Deah, Lemberg, 1888")
for i, section in enumerate(tc.text):
    i_tags[i] = {}
    for j, line in enumerate(section):
        i_tags[i][j] = extract_i_tags(line)
        altered_line = remove_i_tags(line)
        altered_line = insert_i_tags(altered_line, i_tags[i][j])
        for line in context_diff(altered_line.split(), line.split()):
            print line


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
            line = re.sub(u"[!*]+\S+", u"", line)
            line = re.sub(u"@\d+\S{1,5}", u"", line)
            line = re.sub(u"\(#\)", u"", line)
            line = re.sub(u" \*", u"", line)

            line = line.replace("  ", " ").strip()
            dhs = [u" ".join(dh.split()[0:3]) for dh in re.split("\s?&\s?", line)]
            dhs = dhs[1:]
            curr = all_dhs.get(siman, [])
            all_dhs[siman] = curr + dhs


i_tags = {}
sections = Ref("Shulchan Arukh, Yoreh Deah").all_subrefs()
total = missed = 0
print "Reference,Sefaria's Text,Mechaber Text"
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
    match_index = 0
    for n, line in enumerate(tc.text):
        for m in results["match_text"][match_index:]:
            if m[0] and m[0] in line:
                match_index += 1
                line = line.replace(m[0], new_i_tag+m[0])

    for m in results["match_text"]:
        if m[0] == "":
            print sec
            print m[1]
            print
        else:
            if m[0] != m[1]:
                pass
                #print u"{},{},{}".format(sec.normal().replace("Shulchan Arukh, ", ""), m[0], m[1])
print 100.0*float(missed)/total
# for i, section in enumerate(tc.text):
#     i_tags[i] = {}
#     for j, line in enumerate(section):
#         i_tags[i][j] = extract_i_tags(line)
#         altered_line = remove_i_tags(line)
#         altered_line
#         altered_line = insert_i_tags(altered_line, i_tags[i][j])
