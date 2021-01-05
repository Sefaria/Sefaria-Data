from sources.functions import *
from fuzzywuzzy import fuzz
import time

def is_ref(ref, title):
    return ref.startswith("{}, Letter".format(title))

def compare(word1, word2):
    for c, char in enumerate(word1):
        #if there is nothing left in word2, count it as equal
        if c >= len(word2):
            break
        else:
            word2_char = word2[c]
            if char > word2_char:
                return 1
    return 0

prev_masechet = ""
refs = {}
title = "Hafla'ah ShebaArakhin on Sefer HeArukh"
with open("{} - he - Sefer HeArukh, Lublin 1883.csv".format(title), 'r') as f:
    words = []
    last_word = "אא"
    for row in csv.reader(f):
        ref, comm = row
        if is_ref(ref, title):
            #match = re.match(".*?<big>(.*?)\s", comm)
            match = re.match("<b>(.*?)</b>\s", comm)
            if match:
                dappim = re.findall("\(([\S]+) ([\S]+)\) ([\S]+ [\S]+ [\S]+ [\S]+)", comm)
                for daf in dappim:
                    citation = None
                    masechet, amud, dh = daf
                    if masechet == 'שם':
                        masechet = prev_masechet
                    try:
                        citation = Ref(masechet+" "+amud)
                    except Exception as e:
                        try:
                            if masechet.startswith("וב"):
                                masechet = masechet.replace("וב", "")
                            if masechet.startswith("ב"):
                                masechet = masechet[1:]
                            citation = Ref(masechet + " " + amud)
                        except Exception as e:
                            pass
                    if citation:
                        if ref not in refs:
                            refs[ref] = []
                        try:
                            library.get_index(masechet)
                            refs[ref].append((citation.normal(), dh))
                        except Exception as e:
                            pass

                    prev_masechet = masechet

# converted_citations = {}
# for key in refs:
#     for ref_dh in refs[key]:
#         ref, dh = ref_dh
#         if ref not in converted_citations:
#             converted_citations[ref] = {}
#         if Ref(ref).index.categories[0] == "Talmud":
#             segs = Ref(ref).all_subrefs()
#             next = Ref(ref).next_section_ref()
#             if next:
#                 segs += next.all_subrefs()
#         else:
#             segs = Ref(ref).all_subrefs()
#         best = None
#         poss = 0
#         max_find = 75
#         for seg in segs:
#             seg_text = TextChunk(seg, vtitle="William Davidson Edition - Aramaic", lang='he').text
#             poss = fuzz.partial_ratio(dh, seg_text)
#             if poss > max_find:
#                 max_find = poss
#                 best = seg
#         if best:
#             converted_citations[ref][dh] = best.normal()
#
# with open("info.json", 'w') as f:
#     json.dump(converted_citations, f)

for ref in refs:
    if refs[ref]:
        print(ref)
        for citation in refs[ref]:
            print(citation)
        print()

with open('info.json', 'r') as f:
    converted_citations = json.load(f)

good = 0
links = []
bad = 0

with open("new_arukh.csv", 'w') as new_f:
    writer = csv.writer(new_f)
    with open("{} - he - Sefer HeArukh, Lublin 1883.csv".format(title), 'r') as f:
        words = []
        last_word = "אא"
        for row in csv.reader(f):
            ref, comm = row
            changed = False
            if is_ref(ref, title):
                #match = re.match(".*?<big>(.*?)\s", comm)
                match = re.match("<b>(.*?)</b>\s", comm)
                if match:
                    dappim = re.findall("\(([\S]+) ([\S]+)\) ([\S]+ [\S]+ [\S]+ [\S]+)", comm)
                    for daf in dappim:
                        citation = None
                        masechet, amud, dh = daf
                        if masechet == 'שם':
                            masechet = prev_masechet
                        try:
                            citation = Ref(masechet + " " + amud)
                        except Exception as e:
                            try:
                                if masechet.startswith("וב"):
                                    masechet = masechet.replace("וב", "")
                                if masechet.startswith("ב"):
                                    masechet = masechet[1:]
                                citation = Ref(masechet + " " + amud)
                            except Exception as e:
                                pass
                        if citation:
                            if ref not in refs:
                                refs[ref] = []
                            try:
                                library.get_index(masechet)
                                converted = converted_citations[citation.normal()][dh]
                                orig_comm = comm
                                changed = True
                                links.append({"refs": [Ref(converted).normal(), ref], "generated_by": "sefer_he_arukh_disambiguation",
                                              "auto": True, "type": ""})
                                comm = comm.replace("{} {}".format(masechet, amud), Ref(converted).he_normal().replace('״', ''))

                                good += 1
                            except Exception as e:
                                bad += 1

                        prev_masechet = masechet

            send_text = {
                "text": comm,
                "versionTitle": "Sefer HeArukh, Lublin 1883",
                "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH002021120/NLI",
                "language": "he"
            }
            # if changed:
            #post_text(ref, send_text)
            writer.writerow([ref, comm])
print(len(links))
step = 500
start = 0
with open("attempted_post.json", 'r') as f:
    links = json.load(f)
for i in range(start, len(links), step):
    post_link(links[i:i+step], server="https://ste.cauldron.sefaria.org")
    time.sleep(30)
# #
# print(good)
# print(bad)