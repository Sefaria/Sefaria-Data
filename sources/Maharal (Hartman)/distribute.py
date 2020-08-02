import django
django.setup()
from sefaria.model import *
from sources.functions import *
import csv
import re
with open("footnotes.csv", 'r') as f:
    ftnotes = {}
    for row in csv.reader(f):
        if re.search("^Footnotes and Annotations on Derech Chaim \d", row[0]):
            ref, comment = row
            chapter = ref.split()[-1].split(":")[0]
            chapter = int(chapter)
            if not chapter in ftnotes:
                ftnotes[chapter] = []
            ftnotes[chapter].append(comment)

with open("distribution.csv", 'r') as f:
    text = {}
    prev_col_c = ""
    prev_comment = ""
    for row in csv.reader(f):
        if re.search("^Derech Chaim \d", row[0]):
            orig_seg_ref, comment, col_c = row
            if not col_c:
                col_c = prev_col_c
            orig_sec_ref = orig_seg_ref.rsplit(":")[0]
            chapter, mishnah = col_c.split()[-1].split(":")
            chapter = int(chapter)
            mishnah = int(mishnah)
            if not chapter in text:
                text[chapter] = {}
            if not mishnah in text[chapter]:
                text[chapter][mishnah] = []
            text[chapter][mishnah].append(comment)
            prev_col_c = col_c
            prev_comment = comment

# organize footnotes
organized_ftnotes = {}
for c, ch in text.items():
    organized_ftnotes[c] = {}
    for m, mishnah in ch.items():
        first_i_tag = []
        counter = 0
        while len(first_i_tag) is 0:
            first_i_tag = re.findall("<i data-commentator=\"Footnotes and Annotations\" data-label=\"(\d+)\"></i>", mishnah[counter])
            counter += 1
        last_i_tag = []
        counter = -1
        while len(last_i_tag) is 0:
            last_i_tag = re.findall("<i data-commentator=\"Footnotes and Annotations\" data-label=\"(\d+)\"></i>", mishnah[counter])
            counter -= 1
        first_i_tag = int(first_i_tag[0])
        last_i_tag = int(last_i_tag[-1])
        organized_ftnotes[c][m] = ftnotes[c][first_i_tag-1:last_i_tag]
    text[c] = convertDictToArray(text[c])
    organized_ftnotes[c] = convertDictToArray(organized_ftnotes[c])
text = convertDictToArray(text)
organized_ftnotes = convertDictToArray(organized_ftnotes)

vtitle = "Derech Chaim, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2005-2010"
vsource = "https://www.nli.org.il/he/books/NNL_ALEPH005271216/NLI"
send_text = {"versionSource": vsource, "versionTitle": vtitle, "language": "he", "text": None}
for c, ch in enumerate(text):
    send_text["text"] = ch
    #post_text("Derech Chaim {}".format(c+1), send_text)
    send_text["text"] = organized_ftnotes[c]
    post_text("Footnotes and Annotations on Derech Chaim {}".format(c+1), send_text, server="https://www.sefaria.org")


