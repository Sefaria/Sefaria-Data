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

class WordObj:
    def __init__(self, word, info={}, before=False):
        self.word = word
        self.before = before
        self.info = info

    def toStr(self):
        html = ""
        if self.info:
            html += "<i "
            html += u'{}="{}"'.format("data-commentator", self.info["data-commentator"])
            if "data-label" in self.info:
                html += u' {}="{}"'.format("data-label", self.info["data-label"])
            html += u' {}="{}"'.format("data-order", self.info["data-order"])
            html += "></i>"
        return html

    def beforeStr(self):
        if self.before:
            return self.toStr()
        else:
            return ""

    def afterStr(self):
        if not self.before:
            return self.toStr()
        else:
            return ""

def remove_i_tags(line):
    assert not "$" in line
    assert not "^" in line
    i_tags = re.findall(u"<i data.*?></i>", line)
    i_tag_dicts = {}
    for n, i_tag in enumerate(i_tags):
        i_tag_dict = BeautifulSoup(i_tag).find("i").attrs
        marker = "${}".format(n+1)
        line = line.replace(i_tag, marker, 1)
        line = line.replace(" {} ".format(marker), "{} ".format(marker))
        start_pos = line.split("${}".format(n+1))[0].count(" ")
        before = False
        if line.split(" ")[start_pos].startswith(marker):
            before = True
        i_tag_dicts[start_pos] = (i_tag_dict, before)

    words = []
    line = re.sub("\$\d+", "", line)
    for n, word in enumerate(line.split()):
        if n in i_tag_dicts.keys():
            word_obj = WordObj(word, i_tag_dicts[n][0], i_tag_dicts[n][1])
        else:
            word_obj = WordObj(word)

        words.append(word_obj)
    return words

def get_kereti_dhs_in_mechaber():
    siman = 0
    all_dhs = {}
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
    return all_dhs


def create_new_pieces(results, section):
    data_order = 0
    pieces = []
    prev = 0
    word_dict = {}
    words = section.text('he').text.split()
    for m in results:
        data_order += 1
        if m[0] != -1:
            tag = {}
            tag["data-commentator"] = "Kereti"
            tag["data-order"] = data_order
            pos = m[0]
            word_dict[pos] = tag
        else:
            print "Didnt find match in {}".format(section)

    word_objs = []
    for n, word in enumerate(words):
        if n in word_dict.keys():
            word_obj = WordObj(word, word_dict[n])
        else:
            word_obj = WordObj(word)
        word_objs.append(word_obj)
    return word_objs

def get_kereti_tags():
    sections = Ref("Shulchan Arukh, Yoreh Deah").all_segment_refs()
    i_tags_kereti = {}
    for sec in sections:
        if sec.sections[0] == 112:
            break
        base_text = TextChunk(sec, lang='he').text
        base_words = re.sub(u"<.*?>", u" ", base_text)
        while u"  " in base_words:
            base_words = base_words.replace(u"  ", u" ")
        try:
            results = match_text(base_words.split(), all_dhs[sec.sections[0]][sec.sections[1]])
        except:
            print "Problem with {}".format(sec)
            continue
        if sec.sections[0]-1 not in i_tags_kereti:
            i_tags_kereti[sec.sections[0]-1] = {}
        i_tags_kereti[sec.sections[0]-1][sec.sections[1]-1] = create_new_pieces(results["matches"], sec)
    return i_tags_kereti


SA_word_objs = {}
tc = TextChunk(Ref("Shulchan Arukh, Yoreh Deah"), lang='he', vtitle="Ashlei Ravrevei: Shulchan Aruch Yoreh Deah, Lemberg, 1888")
for i, section in enumerate(tc.text):
    SA_word_objs[i] = {}
    for j, line in enumerate(section):
        #i_tags[i][j] = extract_i_tags(line)
        SA_word_objs[i][j] = remove_i_tags(line)
        # altered_line = insert_i_tags(i_tags[i][j])
        # for txt in context_diff(altered_line.split(), section[j].split()):
        #     print txt

#now take out all tags in file and then create data structure of all & and two words after
#dh_matcher can take all these two word strings and TextChunk(Ref("Shulchan Arukh, Yoreh Deah")
all_dhs = get_kereti_dhs_in_mechaber()
kereti_word_objs = get_kereti_tags()
tc = TextChunk(Ref("Shulchan Arukh, Yoreh Deah"), lang='he')
base_text = tc.text

for i in range(len(SA_word_objs)):
    if i > 110:
        break
    for j in range(len(SA_word_objs[i])):
        new_base_text = []
        try:
            for n, word_obj in enumerate(SA_word_objs[i][j]):
                SA_before = word_obj.beforeStr()
                kereti_before = kereti_word_objs[i][j][n].beforeStr()
                SA_after = word_obj.afterStr()
                kereti_after = kereti_word_objs[i][j][n].afterStr()
                full_word = SA_before + kereti_before + word_obj.word + SA_after + kereti_after
                new_base_text.append(full_word)
            base_text[i][j] = u" ".join(new_base_text)
        except Exception as e:
            print (i, j)

text_version = {
    "text": base_text,
    "versionTitle": "Kereti",
    "language": "he",
    "versionSource": "http://www.sefaria.org",
}
post_text("Shulchan Arukh, Yoreh Deah", text_version)
