# encoding=utf-8

import re
import unicodecsv
import bisect
import bleach
import django
django.setup()
from sefaria.model import *
from data_utilities.util import WeightedLevenshtein, LevenshteinError

from sefaria.system.database import db
from sefaria.system.exceptions import InputError
from sefaria.utils.hebrew import strip_cantillation

wl = WeightedLevenshtein()


def tokenizer(s):
    s = strip_cantillation(s, strip_vowels=True)
    s = s.replace(u"...", u" ")
    s = re.sub(ur"[.,'\"־״׳]", u" ", s)
    s = re.sub(ur"\((?:\d{1,3}|[\u05d0-\u05ea]{1,3})\)", u" ", s)  # sefaria automatically adds pasuk markers. remove them
    s = bleach.clean(s, strip=True, tags=()).strip()
    return s.split()


def get_token_info_for_ref(r, lang):
    tc = TextChunk(r, lang)
    ref_index_list, ref_list, total_len = tc.text_index_map(tokenizer)
    word_list = [w for seg in tc.ja().flatten_to_array() for w in tokenizer(seg)]
    word_index_list = reduce(lambda a, b: a + [len(b) + a[-1] + 1], word_list, [0])  # last element is extraneous but who cares
    actual_text = u" ".join(word_list)
    return ref_index_list, ref_list, word_index_list, actual_text


def mutation(ref, en, he):
    dominant_lang = "en" if len(he) == 0 or ((1.0*len(en)) / len(he) > 7.0) else "he"  # only choose english if its way longer
    sheet_text = en if len(he) == 0 or ((1.0*len(en)) / len(he) > 7.0) else he
    ref_index_list, ref_list, word_index_list, actual_text = get_token_info_for_ref(ref, dominant_lang)
    if len(word_index_list) == 0 or len(ref_list) == 0:
        return None
    if abs(len(sheet_text) - len(actual_text)) < 20:
        return None
    if len(sheet_text) > 100:
        start_sheet_text = sheet_text[:sheet_text.find(u" ", min(len(sheet_text)/2, 100))]
        end_sheet_text = sheet_text[sheet_text.find(u" ", max(len(sheet_text)/2, len(sheet_text)-100))+1:]
        start_ref, start_score, end_pos = find_subref(start_sheet_text, actual_text, word_index_list, ref_list, ref_index_list)
        end_ref, end_score, end_pos = find_subref(end_sheet_text, actual_text, word_index_list, ref_list, ref_index_list)
        new_ref = start_ref.to(end_ref)
        score = min(start_score, end_score)
    else:
        new_ref, score, end_pos = find_subref(sheet_text, actual_text, word_index_list, ref_list, ref_index_list)

    if (score < 75) and ref.is_segment_level():
        #print "Trying section ref"
        return mutation(ref.section_ref(), en, he)
    #print u"Original:", ref
    #print u"New:", new_ref
    return new_ref


def find_subref(sheet_text, actual_text, word_index_list, ref_list, ref_index_list):

        max_score = 0
        max_start = 0
        max_end = 0
        max_start_word = 0
        max_end_word = 0
        final_end_word = bisect.bisect_right(word_index_list, word_index_list[-1]-len(sheet_text)) - 1
        for start_word, start in enumerate(word_index_list[:final_end_word]):
            end_word = bisect.bisect_right(word_index_list, start+len(sheet_text) + 1) - 1
            end = word_index_list[end_word if end_word < len(word_index_list) else -1]
            actual_slice = actual_text[start:end-1]
            try:
                score = wl.calculate(sheet_text, actual_slice)
            except LevenshteinError as e:
                continue
            if score > max_score:
                max_score = score
                max_start = start
                max_end = end
                max_start_word = start_word
                max_end_word = end_word
        start_ref = ref_list[bisect.bisect_right(ref_index_list, max_start_word) - 1]
        end_ref = ref_list[bisect.bisect_right(ref_index_list, max_end_word - 1) - 1]

        # print "Original", ref
        # print "New     ", ranged_ref.normal()
        #print "Score   ", max_score
        #print sheet_text
        #print actual_text[max_start:max_end-1]
        return start_ref.to(end_ref), max_score, max_end


def mutate_sheet(sheet, action):
    #print sheet["title"]
    #print sheet["id"]
    for s in sheet["sources"]:
        mutate_subsources(sheet["id"], s, action)


def mutate_subsources(id, source, action):
    ref = source.get("ref", "")
    he = source.get("text", {}).get("he", "")
    he = u" ".join(tokenizer(he))
    en = source.get("text", {}).get("en", "")
    en = u" ".join(tokenizer(en))
    if not ref:
        return
    try:
        new_ref = action(Ref(ref), en, he)
    except InputError as e:
        return
    if new_ref:
        new_ref = new_ref.normal()
        if new_ref != ref:
            global out_rows
            out_rows += [{"Old Ref": ref, "New Ref": new_ref, "Id": id, "Url": "https://www.sefaria.org/sheets/{}".format(id)}]
    if "subsources" in source:
        print "subsources"
        for s in source["subsources"]:
            mutate_subsources(id, s, action)

out_rows = []
ids = db.sheets.find({"status": "public"}).distinct("id")
for i, id in enumerate(ids[::200]):
    print u"{}/{}".format(i, len(ids))
    sheet = db.sheets.find_one({"id": id})
    if not sheet: continue
    mutate_sheet(sheet, mutation)

with open("Fixed Source Sheets.csv", "wb") as fout:
    csv = unicodecsv.DictWriter(fout, ["Id", "Url", "Old Ref", "New Ref"])
    csv.writeheader()
    csv.writerows(out_rows)