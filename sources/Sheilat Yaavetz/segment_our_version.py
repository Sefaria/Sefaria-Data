from sources.functions import *
from linking_utilities.dibur_hamatchil_matcher import *
import os
from sefaria.export import *
import bleach
from collections import *




def extract_text(dir, files):
    text = {}
    for f in files:
        num = getGematria(f.replace(".md", ""))
        text[num] = []
        with open(dir+"/"+f) as open_f:
            for line in open_f:
                if line != "\n":
                    text[num].append(line)
    return text

def dher(str):
    dh_num = 10
    str = str.replace("<b>", "").replace("</b>", "")
    str = str.split(".")[-1]
    if str.count(" ") > dh_num:
        return " ".join(str.split()[-1*dh_num:])
    else:
        return str


offset = 0
prev_matched = []
#
# import_versions_from_file("Altona.csv", [1])
# import_versions_from_file("Lemberg.csv", [1])
resegmented_lemberg = {}
probs_dict = Counter()
with open("new lemberg.csv", 'w', encoding='utf-8') as new_lemberg_csv:
    writer = csv.writer(new_lemberg_csv)
    for ref in library.get_index("Sheilat Yaavetz").all_section_refs():
        # for ending in [" I 1", " I 75", " I 33", " I 41", " I 5", " I 168"]:
        #     if ref.normal().endswith(ending):
        print(ref)
        altona = TextChunk(ref, lang='he', vtitle='Sheilat Yaavetz, Altona, 1738-1759')
        lemberg = TextChunk(ref, lang='he', vtitle='Sheilat Yaavetz, Lemberg 1884')
        if len(altona.text) == 0 or len(lemberg.text) == 0:
            print("Altona has {} and Lemberg has {}".format(len(altona.text), len(lemberg.text)))
            continue

        resegmented_lemberg[ref] = resegment_X_based_on_Y(ref, lemberg, altona)




        send_text = {
            "language": "he",
            "versionTitle": "NEW LEMBERG",
            "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH001277626/NLI",
            "text": resegmented_lemberg[ref]
        }
        post_text(ref.normal(), send_text, server="http://ezra.sandbox.sefaria.org")


print(probs_dict.most_common(50))

# for i, match_text_tuple in enumerate(results["match_word_indices"]):
#     if i < len(results["match_word_indices"]) - 1:
#         next_one = results["match_word_indices"][i+1][0]
#         if next_one == -1:
#             #need to consider when there are many (-1, -1)s in a row
#             while i+1 < len(results["match_word_indices"]) - 1
#             if i+1 == len(results["match_word_indices"]) - 1:
#                 next_tuple = (match_text_tuple[1]+1, len(lemberg_words))
#             else:
#                 next_tuple = (match_text_tuple[1]+1, results["match_word_indices"][i+2]
#             results["match_word_indices"][i+1] = (match_text_tuple[1]+1:)
#             next_one = match_text_tuple[1]
#         resegmented_lemberg[ref][i] += " ".join(lemberg_words[match_text_tuple[0]:next_one])
#     else:
#         resegmented_lemberg[ref][i] += " ".join(lemberg_words[match_text_tuple[0]:])