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
import csv

class WordObj:
    def __init__(self, word, info=[], before=False):
        self.word = word
        self.before = before
        self.info = info

    def toStr(self):
        html = ""
        for i_tag in self.info:
            html += "<i "
            html += u'{}="{}"'.format("data-commentator", i_tag["data-commentator"])
            if "data-label" in i_tag:
                html += u' {}="{}"'.format("data-label", i_tag["data-label"])
            html += u' {}="{}"'.format("data-order", i_tag["data-order"])
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
    line = line.replace("<br>", "<br> ")
    i_tags = re.findall(u"<i data.*?></i>", line)
    i_tag_dicts = {}
    word_objs = []
    word_dict = {}
    for n, i_tag in enumerate(i_tags):
        i_tag_dict = BeautifulSoup(i_tag).find("i").attrs
        i_tag_start_pos = line.find(i_tag)
        # get i_tag positions
        # then take line from 0 until there, remove all i tags, and count words
        line_until_tag = re.sub("<i data.*?></i>", u"", line[0:i_tag_start_pos])
        word_pos = len(line_until_tag.split())
        after_word = re.search(u"[\u05d0-\u05EA]+$", line_until_tag)
        if word_pos == len(re.sub("<i data.*?></i>", u"", line).split()) or after_word:
            word_pos -= 1
        if word_pos not in word_dict:
            word_dict[word_pos] = []
        word_dict[word_pos] += [i_tag_dict]

    # now go through all words45
    for n, word in enumerate(re.sub("<i data.*?></i>", u"", line).split()):
        if n not in word_dict.keys():
            word_objs.append(WordObj(word))
        else:
            word_objs.append(WordObj(word, word_dict[n], True))

    new_i_tags = list(itertools.chain(*[word.info for word in word_objs]))
    assert len(i_tags) == len(new_i_tags)
    return word_objs

def get_kereti_dhs_in_mechaber(files, siman_marker="@22", seif_marker="@11", pos_siman=0):
    def clean_up(line):
        line = re.sub(u"\[\S{1,3}\]", u"", line)
        line = re.sub(u"[!*]+\S+", u"", line)
        line = re.sub(u"@\d+\S{1,5}", u"", line)
        line = re.sub(u"\(#\)", u"", line)
        line = re.sub(u" \*", u"", line)
        line = line.replace("  ", " ").strip()
        return line
    siman = 0
    prev_seif = 0
    all_dhs = {}
    for file in files:
        with open(file) as f:
            for n, line in enumerate(f):
                if line.startswith(siman_marker):
                    siman = getGematria(line.split()[pos_siman])
                    all_dhs[siman] = {}
                    all_dhs[siman][1] = []
                    seif = 1
                elif line.startswith(seif_marker) and siman > 0:
                    seif = getGematria(line.split()[0])
                    all_dhs[siman][seif] = []

                if line.count("&") > 0:
                    dhs = [clean_up(u" ".join(dh.split()[0:3])) for dh in re.split("\s?&\s?", line)]
                    dhs = dhs[1:]
                    all_dhs[siman][seif] += dhs
    return all_dhs


def create_new_pieces(title, results, section, data_order_running_count):
    data_order = 0
    word_dict = {}
    words = re.sub("<i data.*?></i>", u"", section.text('he').text.replace("<br>", "<br> "))
    words = words.split()
    probs = 0
    for m in results:
        data_order += 1
        if m[0] != -1:
            tag = {}
            tag["data-commentator"] = title
            tag["data-order"] = data_order + data_order_running_count
            pos = m[0]
            if pos in word_dict:
                print("Found duplicate in {}".format(section))
                orig = word_dict[pos][1]
                if m[1] > orig:
                    word_dict[pos] = (tag, m[1])
            else:
                word_dict[pos] = (tag, m[1])
        else:
            print("Didnt find match in {}".format(section))
            probs += 1


    word_objs = []
    for n, word in enumerate(words):
        if n in word_dict.keys():
            word_obj = WordObj(word, [word_dict[n][0]], before=True)
        else:
            word_obj = WordObj(word, before=True)
        word_objs.append(word_obj)
    return word_objs

def get_kereti_tags(title, all_dhs):
    sections = Ref("Shulchan Arukh, Orach Chayim").all_subrefs()
    i_tags_kereti = {}
    for sec in sections:
        data_order = 0
        for seg in sec.all_segment_refs():
            if seg.sections[0] not in all_dhs or seg.sections[1] not in all_dhs[seg.sections[0]]:
                continue
            if all_dhs[seg.sections[0]][seg.sections[1]]:
                if sec.sections[0] - 1 not in i_tags_kereti:
                    i_tags_kereti[sec.sections[0] - 1] = {}
                base_text = TextChunk(seg, lang='he').text
                base_words = re.sub(u"<.*?>", u" ", base_text)
                while u"  " in base_words:
                    base_words = base_words.replace(u"  ", u" ")
                results = match_text(base_words.split(), all_dhs[seg.sections[0]][seg.sections[1]])
                if (-1, -1) in results["matches"]:
                    results = match_text(base_words.split(), all_dhs[seg.sections[0]][seg.sections[1]], prev_matched_results=results["matches"], char_threshold=0.3, word_threshold=0.3)
                    if (-1, -1) in results["matches"]:
                        results = match_text(base_words.split(), all_dhs[seg.sections[0]][seg.sections[1]], prev_matched_results=results["matches"], char_threshold=0.4, word_threshold=0.4)

                i_tags_kereti[sec.sections[0]-1][seg.sections[1]-1] = create_new_pieces(title, results["matches"], seg, data_order)
                data_order += len(results["matches"])
    return i_tags_kereti


def create_new_tags(new_vtitle, old_vtitle, kereti_word_objs, change_nothing=False):
    SA_word_objs = {}
    tc = TextChunk(Ref("Shulchan Arukh, Orach Chayim"), lang='he',
                   vtitle=old_vtitle)
    for i, section in enumerate(tc.text):
        SA_word_objs[i] = {}
        for j, line in enumerate(section):
            SA_word_objs[i][j] = remove_i_tags(line)

    # now take out all tags in file and then create data structure of all & and two words after
    # dh_matcher can take all these two word strings and TextChunk(Ref("Shulchan Arukh, Yoreh Deah")
    tc = TextChunk(Ref("Shulchan Arukh, Orach Chayim"), lang='he')
    base_text = tc.text
    if not change_nothing:
        for i in range(len(SA_word_objs)):
            if i not in kereti_word_objs:
                continue
            for j in range(len(SA_word_objs[i])):
                new_base_text = []
                if j not in kereti_word_objs[i]:
                    continue
                for n, word_obj in enumerate(SA_word_objs[i][j]):
                    SA_before = word_obj.beforeStr()
                    kereti_before = kereti_word_objs[i][j][n].beforeStr()
                    SA_after = word_obj.afterStr()
                    kereti_after = kereti_word_objs[i][j][n].afterStr()
                    full_word = SA_before + kereti_before + word_obj.word + SA_after + kereti_after
                    new_base_text.append(full_word)

                base_text[i][j] = u" ".join(new_base_text)

    # text_version = {
    #     "text": base_text,
    #     "versionTitle": new_vtitle,
    #     "language": "he",
    #     "versionSource": "http://www.sefaria.org",
    # }
    # post_text("Shulchan Arukh, Yoreh De'ah", text_version)



if __name__ == "__main__":
    title = "Kereti"
    starter = "Dec 22 Peleti"
    default = "Ashlei Ravrevei: Shulchan Aruch Yoreh Deah, Lemberg, 1888"
    all_dhs = get_kereti_dhs_in_mechaber()
    all_dhs = get_kereti_tags(title, all_dhs)
    create_new_tags("Kereti and Peleti", starter, all_dhs, change_nothing=True)
    create_new_tags("Kereti and Peleti", starter, all_dhs, change_nothing=False)


