import django
django.setup()
from sefaria.model import *
from linking_utilities.dibur_hamatchil_matcher import *
from linking_utilities.parallel_matcher import ParallelMatcher
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


def get_best_pair(ref, en, he):
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

with open("loazei.csv", 'w') as f:
    writer = csv.writer(f)
    writer.writerow(["French Word (en)", "French Word (he)", "Tanakh Ref", "Rashi Matches"])
    for ref in dhs.keys():
        book = Ref(ref).index.title
        for i, dh in enumerate(dhs[ref]):
            en, he = dh
            m = get_best_pair(ref, en, he)
            m = [el.normal() for el in list(m)]
            writer.writerow([en, he, ref.split(" on ")[-1], m])
