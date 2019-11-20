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


class PieceOfText:
    def __init__(self, text):
        self.text = text
        self.tag = None


def get_closest_hebrew_word(line, dir=1):
    words = line.split()
    # dir == 1: start at first word and keep going forward until there's a Hebrew word
    # dir == -1: start at last word and keep going backward until there's a Hebrew word
    curr_word = len(words) - 1 if dir == -1 else 0
    while len(words) > curr_word >= 0:
        m = re.search(u"[<>a-z)(א-ת]+", words[curr_word])
        if m:
            assert " "
            return m.group(0)
        else:
            curr_word += dir

#
#
# def extract_i_tags(line):
#     i_tags = {}
#     altered_line, i_tag_dicts = remove_i_tags(line)
#     for words_before_tag in line.split("$"):

    #altered_line + tag_dicts
    # for n, m in enumerate(re.finditer("""<i data.*?></i>""", line)):
    #     pos = m.regs[0]
    #     i_tag = line[pos[0]:pos[1]]
    #     tag_dict = BeautifulSoup(i_tag).find("i").attrs
    #     word_before = get_closest_hebrew_word(altered_line[0:pos[0]], dir=-1)
    #     word_after = get_closest_hebrew_word(altered_line[pos[0]:], dir=1)
    #     assert "<" not in word_before
    #     assert "<" not in word_after
    #     p = u"{}.*?{}".format(word_before, word_after).replace(")", "\)").replace("(", "\(")
    #     matches = re.finditer(p, line)
    #     for i, m in enumerate(matches):
    #         start = m.regs[0][0]
    #         end = m.regs[0][1]
    #         if pos[0] >= start and end >= pos[1]:
    #             found = i
    #             tag_dict["pos"] = i
    #     curr_tag_dicts = i_tags.get((word_before, word_after), [])
    #     i_tags[(word_before, word_after)] = curr_tag_dicts + [tag_dict]
    # return i_tags


def remove_i_tags(line):
    assert not "$" in line
    i_tags = re.findall(u"<i data.*?></i>", line)
    i_tag_dicts = []
    for i_tag in i_tags:
        i_tag_dict = BeautifulSoup(i_tag).find("i").attrs
        start_pos = line.find(i_tag)
        line = line.replace(i_tag, "$")
        i_tag_dicts.append(i_tag_dict)

    words_before_tag_list = line.split("$")[:-1]
    pieces = []
    prev = 0
    for i, words_before in enumerate(words_before_tag_list):
        tc = PieceOfText((prev, len(words_before.split())))
        tc.tag = i_tag_dicts[i]
        pieces.append(tc)
        prev += len(words_before)

    tc = PieceOfText((prev, -1))
    pieces.append(tc)
    return pieces

def resolve_ambiguity(i_tag_dict):
    words_before_prev = i_tag_dict["words_before_prev"]
    curr_matches = [m.regs[0][0] for m in re.finditer(i_tag_dict["words_before_curr"], line)]
    prev_matches = [m.regs[0][0] + len(words_before_prev) for m in re.finditer(words_before_prev, line)]
    for curr_match in curr_matches:
        for prev_match in prev_matches:
            if curr_match == prev_match:
                return curr_match
    return -1

def insert_i_tags(i_tags):
    for i_tag_dict in i_tags:
        html = ""
        words_before = i_tag_dict["words_before_curr"]
        if line.find(words_before) != line.rfind(words_before): #found many possible locations
            start_pos = resolve_ambiguity(i_tag_dict)
        else:
            start_pos = line.find(words_before)
        i_tag_pos = start_pos + len(words_before)
        html += "<i "
        html += u'{}="{}"'.format("data-commentator", i_tag_dict["data-commentator"])
        if "data-label" in i_tag_dict:
            html += u' {}="{}"'.format("data-label", i_tag_dict["data-label"])
        html += u' {}="{}"'.format("data-order", i_tag_dict["data-order"])
        html += "></i>"
        line = line[0:i_tag_pos] + html + line[i_tag_pos:]

    return line


i_tags = {}
tc = TextChunk(Ref("Shulchan Arukh, Yoreh Deah"), lang='he', vtitle="Ashlei Ravrevei: Shulchan Aruch Yoreh Deah, Lemberg, 1888")
for i, section in enumerate(tc.text):
    i_tags[i] = {}
    for j, line in enumerate(section):
        #i_tags[i][j] = extract_i_tags(line)
        i_tags[i][j] = remove_i_tags(line)
        # altered_line = insert_i_tags(i_tags[i][j])
        # for txt in context_diff(altered_line.split(), section[j].split()):
        #     print txt


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
                all_dhs[siman] = {}
                all_dhs[siman][1] = []
                seif = 1
            elif line.startswith("@11"):
                seif = getGematria(line.split()[0])
                all_dhs[siman][seif] = []

            if line.count("&") > 0:
                line = re.sub(u"\[\S{1,3}\]", u"", line)
                line = re.sub(u"[!*]+\S+", u"", line)
                line = re.sub(u"@\d+\S{1,5}", u"", line)
                line = re.sub(u"\(#\)", u"", line)
                line = re.sub(u" \*", u"", line)

                line = line.replace("  ", " ").strip()
                dhs = [u" ".join(dh.split()[0:3]) for dh in re.split("\s?&\s?", line)]
                dhs = dhs[1:]
                all_dhs[siman][seif] += dhs


sections = Ref("Shulchan Arukh, Yoreh Deah").all_segment_refs()
total = missed = 0
print "Reference,Sefaria's Text,Mechaber Text"
for sec in sections:
    if sec.sections[0] == 112:
        break
    tcs = [tc.text for tc in i_tags[sec.sections[0]-1][sec.sections[1]-1]]
    base_text = u" ".join(tcs)
    while u"  " in base_text:
        base_text = base_text.replace(u"  ", u" ")
    base_words = base_text.split()
    results = match_text(base_words, all_dhs[sec.sections[0]][sec.sections[1]])
    total += len(results["matches"])
    missed += results["matches"].count((-1, -1))
    match_index = 0
    prev = 0
    pieces = []
    data_order = 0
    for n, line in enumerate(tc.text):
        for m in results["matches"]:
            data_order += 1
            if m[0] != -1:
                start_pos = m[0]
                end_pos = m[1]
                tc = PieceOfText((prev, start_pos))
                tag = {}
                tag["data-commentator"] = "Kereti"
                tag["data-order"] = data_order
                tc.tag = tag
                prev = end_pos
                pieces.append(tc)
            else:
                print "didnt find"


# for i, section in enumerate(tc.text):
#     i_tags[i] = {}
#     for j, line in enumerate(section):
#         i_tags[i][j] = extract_i_tags(line)
#         altered_line = remove_i_tags(line)
#         altered_line
#         altered_line = insert_i_tags(altered_line, i_tags[i][j])
