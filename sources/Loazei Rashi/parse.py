import django
django.setup()
from sefaria.model import *
from data_utilities.dibur_hamatchil_matcher import *
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
from fuzzywuzzy import fuzz
import bleach

class Laaz:
    def __init__(self, serial, ref, hebrew_word, french_he, french_en, definition, comment=""):
        self.base_ref = ref
        self.serial = serial
        self.hebrew_word = hebrew_word
        self.french_he = french_he
        self.french_en = french_en
        self.definition = definition
        self.comment = comment

    def format(self):
        first_line = "{} {} <b>{}</b><br>".format(self.serial, self.base_ref, self.hebrew_word)
        second_line = "{} {} <b>{}</b><br>".format(self.french_he, self.french_en, self.definition)
        third_line = "<small>{}</small>".format(self.comment) if self.comment else ""
        return first_line+second_line+third_line


def get_best_pair(ref, en, he, recurse=True):
    curr_max = {"en": 85, "he": 85}
    curr_best = {"he": set(), "en": set()}
    ref = Ref(ref)
    versionSet = ref.index.versionSet()
    for segment_ref in ref.all_subrefs():
        for version in versionSet:
            lang = version.language
            if lang not in ["he", "en"]:
                continue
            vtitle = version.versionTitle
            tc = TextChunk(segment_ref, vtitle=vtitle, lang=lang)
            text = bleach.clean(tc.text, tags=[], strip=True)
            curr_dh = en if lang == "en" else he
            score = 100 if " {} ".format(curr_dh) in text else fuzz.partial_ratio(curr_dh, text)
            if 'בלע"ז' in text or "French" in text:
                score += 13
            if score > curr_max[lang]:
                curr_max[lang] = score
                curr_best[lang].add(segment_ref)
    if curr_best["en"] != curr_best["he"]:
        retval = curr_best["he"] or curr_best["en"]
        return retval
    # elif recurse:
    #     neighbors = [ref.prev_segment_ref().normal(), ref.next_segment_ref().normal()]
    #     return curr_best["en"] or get_best_pair(neighbors[0], en, he, recurse=False) \
    #            or get_best_pair(neighbors[1], en, he, recurse=False)
    else:
        return curr_best["en"]


laazim = {}
dhs = {}
with open("Laaz-Rashi-Bible.txt", 'r') as f:
    for line in f:
        if "@" in line:
            row = line.split("@")
            serial = row[0]
            ref = row[1]
            hebrew = row[2]
            french_he = row[3]
            french_en = row[4]
            comm_2 = row[5]
            comm_3 = row[6]
            laaz = Laaz(serial, ref, hebrew, french_he, french_en, comm_2, comm_3)
            ref = "Rashi on {}".format(Ref(ref).normal())
            if ref not in dhs:
                dhs[ref] = []
                laazim[ref] = []
            dhs[ref].append((french_en, french_he))
            laazim[ref].append(laaz)

dhs_by_segment = {}
for ref in dhs.keys():
    book = Ref(ref).index.title
    for i, dh in enumerate(dhs[ref]):
        en, he = dh
        m = get_best_pair(ref, en, he)
        if book not in dhs_by_segment:
            dhs_by_segment[book] = []
        dhs_by_segment[book].append(m)


count = 0
total_found = 0
total = 0
for ref, matches in dhs_by_segment.items():
    found = len([m for m in matches if m])
    total += len(matches)
    total_found += found
    percent = int(100.0*float(found)/len(matches))
    print("{}: {}%".format(ref, percent))
    # laazim_in_ref = laazim[ref]
    # for laaz, match in zip(laazim_in_ref, matches):
    #     print(laaz.french_en)
    #     if not match:
    #         print(match + " " + ref)
    #     else:
    #         print(match)
    #     print()
print(total)
print(total_found)