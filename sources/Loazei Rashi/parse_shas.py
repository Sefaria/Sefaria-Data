import django
django.setup()
from sefaria.model import *
from linking_utilities.dibur_hamatchil_matcher import *
from linking_utilities.parallel_matcher import ParallelMatcher
from fuzzywuzzy import fuzz
import bleach
from collections import Counter

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


def get_best_pair_talmud(ref, actual_he, french_he, passing_val=80, french_addition=15):
    def convert_set_to_list():
        he_match = list(curr_best["he"])
        fr_match = list(curr_best["fr"])
        if len(he_match) is 0:
            he_match = [""]
        if len(fr_match) is 0:
            fr_match = [""]
        if he_match[0] != "":
            he_match = [ref.normal() for ref in he_match]
        if fr_match[0] != "":
            fr_match = [ref.normal() for ref in fr_match]
        return (he_match, fr_match)

    if ref is None:
        return set()


    curr_max = {"fr": passing_val, "he": passing_val}
    curr_best = {"he": set(), "fr": set()}

    ref = Ref(ref) if isinstance(ref, str) else ref
    if len(ref.all_subrefs()) == 1:
        return {(ref.all_subrefs()[0], ref.all_subrefs()[0].text('he').text)}

    #versionSet = ref.index.versionSet()


    for segment_ref in ref.all_segment_refs():
        score = {"he": 0, "fr": 0}
        # for version in versionSet:
        #     vtitle = version.versionTitle
        #     tc = TextChunk(segment_ref, vtitle=vtitle, lang='he')
        text = bleach.clean(segment_ref.text('he').text, tags=[], strip=True)

        if text == "":
            score["fr"] = score["he"] = 0
        elif score["fr"] == 0 or score["he"] == 0:
            score["fr"] = fuzz.partial_ratio(french_he, text)
            score["he"] = fuzz.partial_ratio(actual_he, text)
            if 'בלע"ז' in text or 'בלשון לעז' in text or 'לעז' in text or 'בלעז' in text or 'בְּלַעַז' in text or "French" in text:
                score["fr"] += french_addition
            elif 'קורין' in text or 'לשון' in text:
                score["fr"] += french_addition
            if score["he"] == 100 and text.split()[0] == actual_he:
                score["fr"] += 25
        for lang in ["he", "fr"]:
            if score[lang] >= curr_max[lang]:
                curr_max[lang] = score[lang]
                curr_best[lang].add(segment_ref)

    return convert_set_to_list()

laazim = {}
dhs = {}
with open("Laaz-Rashi-Shas.txt", 'r') as f:
    for line in f:
        if line[0].isdigit():
            row = line.split("@")
            serial = row[0]
            ref = row[1]
            hebrew = row[2]
            french_he = row[3]
            french_en = row[4]
            comm_2 = row[5]
            comm_3 = row[6]
            laaz = Laaz(serial, ref, hebrew, french_he, french_en, comm_2, comm_3)
            try:
                ref = "Rashi on {}".format(Ref(ref).normal())
            except:
                print(serial)
            if ref not in dhs:
                dhs[ref] = []
                laazim[ref] = []
            dhs[ref].append((french_en, french_he))
            laazim[ref].append(laaz)

not_found_dafs = Counter()
all_words = Counter()
no_match = 0
total = 0
non_overlap_match = 0
with open("loazei_shas.csv", 'w') as f:
    writer = csv.writer(f)
    writer.writerow(["French Word", "Talmud Ref", "French Rashi Matches", "Hebrew Rashi Matches (if different)", "Loazei Rashi Info"])
    for ref in dhs.keys():
        laaz = laazim[ref]
        try:
            book = Ref(ref).index.title
        except:
            print(ref)
            continue

        for i, dh in enumerate(laazim[ref]):
            if book == "Rashi on Bava Batra" and Ref(ref).sections[0] > 75:
                ref = ref.replace("Rashi", "Rashbam")
            matches = get_best_pair_talmud(ref, dh.hebrew_word, dh.french_he)
            he_match = matches[0]
            fr_match = matches[1]
            total += 1
            if fr_match[0] == he_match[0] == "":
                no_match += 1
                writer.writerow(["{}/{}".format(dh.hebrew_word, dh.french_he), ref.split(" on ")[-1], "", "", dh.format()])
            else:
                overlap = set(he_match).intersection(set(fr_match))
                he_refs = ",\n".join(he_match)
                fr_refs = ",\n".join(fr_match)
                if overlap:
                    refs = list(overlap)
                    text = ["({}) {}".format(ref.split()[-1], Ref(ref).text('he').text) for ref in refs]
                    refs = ",\n".join(refs)
                    text = ",\n".join(text)
                    writer.writerow(["{}/{}".format(dh.hebrew_word, dh.french_he), ref.split(" on ")[-1], refs, "", dh.format(), text])
                elif fr_refs or he_refs:
                    relevant_match = fr_match if fr_refs else he_match
                    non_overlap_match += 1
                    text = ["({}) {}".format(ref.split()[-1], Ref(ref).text('he').text) for ref in relevant_match]
                    text = ",\n".join(text)
                    writer.writerow(["{}/{}".format(dh.hebrew_word, dh.french_he), ref.split(" on ")[-1], fr_refs, he_refs, dh.format(), text])



            # elif
            #     # print("Looking for {} in {}".format(he, ref))
            #     # versionSet = Ref(ref).index.versionSet()
            #     # found_subrefs = []
            #     # found_words = []
            #     # for subref in Ref(ref).all_segment_refs():
            #     #     if len(found_words) > 0:
            #     #         break
            #     #     for v in versionSet:
            #     #         if len(found_words) > 0:
            #     #             break
            #     #         tc = TextChunk(subref, lang=v.language, vtitle=v.versionTitle)
            #     #         our_word = he if v.language == "he" else en
            #     #         for word in tc.text.split():
            #     #             results = LexiconLookupAggregator.lexicon_lookup(word)
            #     #             if results is None:
            #     #                 our_word = our_word.replace("ו", "").replace("י", "")
            #     #                 word = word.replace("ו", "").replace("י", "")
            #     #                 if fuzz.ratio(word, our_word) > 75:
            #     #                     found_subrefs.append(subref.normal())
            #     #                     found_words.append((our_word, word))
            #     #                     break
            #     # if len(found_subrefs) > 0:
            #     #     print(ref)
            #     #     print(found_subrefs)
            #     #     print(found_words)
            #     #     print()
            #     #     text = Ref(found_subrefs[0]).text('he').text
            #     #     for word in text.split():
            #     #         all_words[word] += 1
            #     #     writer.writerow(["{}/{}".format(he, en), ref.split(" on ")[-1], found_subrefs[0], text, dh.format()])
            #     # else:
            #     if len(Ref(ref).text('he').text) == 0:
            #         print("PROBLEM WITH {}".format(ref))
            #         not_found_dafs[ref] += 1
            #     writer.writerow(["{}/{}".format(dh.hebrew_word, dh.french_he), ref.split(" on ")[-1], "", "", dh.format()])

print(no_match)
print(non_overlap_match)
print(total)