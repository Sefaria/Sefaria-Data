from sources.functions import *
from linking_utilities.parallel_matcher import ParallelMatcher
from linking_utilities.citation_disambiguator.main import CitationDisambiguator
import os
from functools import reduce
from sefaria.utils.hebrew import strip_cantillation
from linking_utilities.dibur_hamatchil_matcher import get_maximum_dh, ComputeLevenshteinDistanceByWord, match_text
from linking_utilities.weighted_levenshtein import WeightedLevenshtein
levenshtein = WeightedLevenshtein()
mode = "0"
import json
import math
from linking_utilities.dibur_hamatchil_matcher import get_maximum_dh, ComputeLevenshteinDistanceByWord


class ScoreManager:
    def __init__(self, word_counts_file):
        with open(word_counts_file, "r") as fin:
            self.word_counts = json.load(fin)
        self.max_count = 0
        for word, count in self.word_counts.items():
            if count > self.max_count:
                self.max_count = count

    def word_count_score(self, w):
        max_score = 1
        wc = self.word_counts.get(w, None)
        score = 1 if wc is None else -math.log10(20 * (wc + (self.max_count / 10 ** max_score))) + math.log10(
            20 * self.max_count)
        return 3 * score

    def is_stopword(self, w):
        if len(w) > 0 and w[0] == 'ו' and self.word_counts.get(w[1:], 0) > 1.8e5:
            # try to strip off leading vav
            return True
        return self.word_counts.get(w, 0) > 10000

    def get_score(self, words_a, words_b):
        # negative because for score higher is better but for leven lower is better
        num_stopwords_a = reduce(lambda a, b: a + (1 if self.is_stopword(b) else 0), words_a, 0)
        num_stopwords_b = reduce(lambda a, b: a + (1 if self.is_stopword(b) else 0), words_b, 0)
        if len(words_a) - num_stopwords_a < 2 or len(words_b) - num_stopwords_b < 2:
            print("stopwords!")
            # print num_stopwords_a, len(words_a)
            # print num_stopwords_b, len(words_b)
            return -40
        lazy_tfidf = sum([self.word_count_score(w) for w in words_b])
        best_match = get_maximum_dh(words_a, words_b, min_dh_len=len(words_b) - 1, max_dh_len=len(words_b))
        if best_match:
            return -best_match.score + lazy_tfidf
        else:
            return -ComputeLevenshteinDistanceByWord(" ".join(words_a), " ".join(words_b)) + lazy_tfidf

def get_ref(pos, text, ref):
    count = 0
    start = -1
    end = -1
    words = []
    for i, line in enumerate(text):
        orig_count = count
        count += line.count(" ") + 1
        if orig_count <= pos[0] <= count:
            start = i+1
        if orig_count <= pos[1] <= count:
            end = i+1
            break

    ref = "{}:{}-{}".format(ref, start, end) if end != start else "{}:{}".format(ref, start)
    return ref, " ".join(" ".join(text).split()[pos[0]:pos[1]])


def PM_regular(lines, comm_title, base_ref, writer, score_manager):
    links = []
    matcher = ParallelMatcher(CitationDisambiguator.tokenize_words, max_words_between=4, min_words_in_match=9,
                              ngram_size=5,
                              parallelize=False, all_to_all=False,
                              verbose=False, calculate_score=score_manager.get_score)
    words = " ".join(lines)
    base = TextChunk(Ref(base_ref), lang='he')
    ber_word_list = [w for seg in base.ja().flatten_to_array() for w in CitationDisambiguator.tokenize_words(seg)]
    match_list = matcher.match(
        tref_list=[(words, comm_title), (" ".join(ber_word_list), base_ref)],
        return_obj=True)
    all_matches = [[mm.a.ref.normal(), mm.b.mesechta, mm.a.location, mm.b.location, mm.score] for mm in match_list
                   if not mm is None]
    meiri_found = {}
    for m in all_matches:
        print(m[4])
        if m[4] > 10:
            ref, ref_words = get_ref(m[3], base.ja().flatten_to_array(), base_ref)
            meiri_range, meiri_words = get_ref(m[2], lines, comm_title)

            # if meiri in meiri_found and meiri_found[meiri]:
            #     new_ref = meiri_found[meiri]["refs"][1].split("-")[0] + "-" + ref.split(":")[-1]
            #     meiri_found[meiri]["refs"][1] = new_ref
            #     ref = new_ref
            # else:

            for meiri in Ref(meiri_range).range_list():
                writer.writerow([ref, ref_words, meiri.normal(), meiri_words])
                if meiri not in meiri_found:
                    links += [{"refs": [meiri.normal(),
                                    ref],
                           "generated_by": "meiri_to_daf", "auto": True, "type": "Commentary"}]

                    meiri_found[meiri] = links[-1]
    # for l in links:
    #     for r, ref in enumerate(l["refs"]):
    #         l["refs"][r] = re.sub("(\d+)-\d+-(\d+)", "\g<1>-\g<2>", ref)
    return links

def tokenize_words(base_str):
    base_str = base_str.strip()
    base_str = strip_cantillation(base_str, strip_vowels=True)
    base_str = re.sub(r"<[^>]+>", "", base_str)
    for match in re.finditer(r'\(.*?\)', base_str):
        if len(match.group().split()) <= 5:
            base_str = base_str.replace(match.group(), "")
            # base_str = re.sub(ur"(?:\(.*?\)|<.*?>)", u"", base_str)
    base_str = re.sub(r'־', ' ', base_str)
    base_str = re.sub(r'\[[^\[\]]{1,7}\]', '',
                      base_str)  # remove kri but dont remove too much to avoid messing with brackets in talmud
    base_str = re.sub(r'[A-Za-z.,"?!״:׃]', '', base_str)
    # replace common hashem replacements with the tetragrammaton
    base_str = re.sub(r"(^|\s)([\u05de\u05e9\u05d5\u05db\u05dc\u05d1]?)(?:\u05d4['\u05f3]|\u05d9\u05d9)($|\s)",
                      "\1\2\u05d9\u05d4\u05d5\u05d4\3", base_str)
    # replace common elokim replacement with elokim
    base_str = re.sub(r"(^|\s)([\u05de\u05e9\u05d5\u05db\u05dc\u05d1]?)(?:\u05d0\u05dc\u05e7\u05d9\u05dd)($|\s)",
                      "\1\2\u05d0\u05dc\u05d4\u05d9\u05dd\3", base_str)

    word_list = re.split(r"\s+", base_str)
    word_list = [w for w in word_list if len(w.strip()) > 0 and w not in CitationDisambiguator.stop_words]
    return word_list

def dher(text):
    dh = " ".join(text.split()[:5])
    #dh = " ".join(text.split(".")) if " ".join(text.split(".")).count(" ") < 10 else " ".join(text.split(" ")[:7])
    return dh

def calc(words_a, words_b):

    str_a = u" ".join(words_a)
    str_b = u" ".join(words_b)
    dist = levenshtein.calculate(str_a, str_b, normalize=True)

    return dist


lines = {}
curr = ""
curr_section = ""
word_count_meiri = {}
for f in os.listdir("."):
    if f.endswith(".txt"):
        with open(f, 'r') as open_f:
            curr = f.replace(".txt", "")
            curr = (library.get_index(curr).get_title('en'), curr)
            lines[curr] = {}
            for line in open_f:
                line = line.strip()
                if line == "":
                    continue
                if "@פתיחה" in line:
                    curr_section = "Introduction"
                    lines[curr][curr_section] = []
                elif line.startswith("@דף"):
                    marker, daf, amud = line.split()
                    daf = getGematria(daf) * 2
                    daf -= 1 if getGematria(amud) == 1 else 0
                    curr_section = daf
                    lines[curr][curr_section] = []
                else:
                    words = CitationDisambiguator.tokenize_words(line)
                    for word in words:
                        if word not in word_count_meiri:
                            word_count_meiri[word] = 1
                        else:
                            word_count_meiri[word] += 1
                    if line.startswith("זהו ביאור") and line.count(" ") < 20:
                        line = "<b>" + line + "</b>"
                    else:
                        line = "<b>" + line.split()[0] + "</b> " + " ".join(line.split()[1:])
                    lines[curr][curr_section].append(line)


def just_mishnah(str):
    value = " ".join(str.split()[1:5]) if mishnah in str.split()[0] else ""
    return value

if __name__ == "__main__":
    t = Term()
    t.add_primary_titles("Meiri", "מאירי")
    t.name = "Meiri"
    #t.save()
    c = Category()
    c.path = ["Talmud", "Bavli", "Commentary", "Meiri"]
    c.add_shared_term("Meiri")
    #c.save()
    #add_category("Meiri", c.path)

    links = []
    start = "Yoma"
    starting = False
    # for en_title, he_title in lines.keys():
    #     print(en_title)
    #     for ref in library.get_index(en_title).all_segment_refs():
    #         tc = TextChunk(ref, vtitle="William Davidson Edition - Aramaic", lang="he").text
    #         words = CitationDisambiguator.tokenize_words(tc)
    #         for word in words:
    #             if word not in word_count_meiri:
    #                 word_count_meiri[word] = 0
    #             word_count_meiri[word] += 1
    # with open("word_count.json", 'w') as f:
    #     json.dump(word_count_meiri, f)
    score_manager = ScoreManager("word_count.json")
    for en_title, he_title in lines.keys():
        if start in en_title:
            starting = True
        if not starting:
            continue

        f = open("{}.csv".format(en_title), 'w')
        writer = csv.writer(f)
        categories = ["Talmud", "Bavli", "Commentary", "Meiri", library.get_index(en_title).categories[-1]]
        print(categories)
        c = Category()
        c.path = categories
        c.add_shared_term(categories[-1])
        try:
            c.save()
        except Exception as e:
            print(e)

        #add_category(categories[-1], categories)
        full_title = "Meiri on {}".format(en_title)
        he_full_title = "מאירי על {}".format(he_title)
        if "Introduction" in lines[(en_title, he_title)]:
            root = SchemaNode()
            root.add_primary_titles(full_title, he_full_title)
            intro = JaggedArrayNode()
            intro.add_shared_term("Introduction")
            intro.add_structure(["Paragraph"])
            intro.key = "Introduction"
            default = JaggedArrayNode()
            default.default = True
            default.key = "default"
            default.add_structure(["Daf", "Line"], address_types=["Talmud", "Integer"])
            root.append(intro)
            root.append(default)
        else:
            root = JaggedArrayNode()
            root.add_primary_titles(full_title, he_full_title)
            root.add_structure(["Daf", "Line"], address_types=["Talmud", "Integer"])
        root.validate()
        print(categories)
        # post_index({"title": full_title, "schema": root.serialize(), "dependence": "Commentary",
        #           "categories": categories, "base_text_titles": [en_title], "collective_title": "Meiri"}, dump_json=True)
        lines_in_title = lines[(en_title, he_title)]
        intro = lines_in_title.pop("Introduction")
        send_text = {
            "language": "he",
            "versionTitle": "Meiri on Shas",
            "versionSource": "http://www.sefaria.org",
            "text": intro
        }
        post_text(full_title + ", Introduction", send_text, index_count="on", server="https://www.sefaria.org")
        send_text = {
            "language": "he",
            "versionTitle": "Meiri on Shas",
            "versionSource": "http://www.sefaria.org",
            "text": convertDictToArray(lines_in_title)
        }
        mishnah = "משנה"
        post_text(full_title, send_text, index_count="on", server="https://www.sefaria.org")
        found_refs = []

        new_links = []
        # for daf in lines_in_title:
        #     actual_daf = AddressTalmud.toStr('en', daf)
        #     comm_title = "{} {}".format(full_title, actual_daf)
        #     base_ref = "{} {}".format(en_title, actual_daf)
        #     found = -1
        #     leave = False
        #     #get positions of base and comm that are Mishnah
        #     positions_comm = [l for l, line in enumerate(lines_in_title[daf]) if mishnah in line.split()[0]]
        #     base = Ref("{} {}".format(en_title, actual_daf)).text('he')
        #     positions_base = [l for l, line in enumerate(base.text) if "מַתְנִי׳" in line.split()[0] or "מתני׳" in line.split()[0]]
        #     for base, comm in zip(positions_base, positions_comm):
        #         found_refs.append("Meiri on {} {}:{}".format(en_title, actual_daf, comm + 1))
        #         links.append({"generated_by": "mishnah_to_meiri", "auto": True, "type": "Commentary",
        #                       "refs": ["Meiri on {} {}:{}".format(en_title, actual_daf, comm + 1),
        #                                "{} {}:{}".format(en_title, actual_daf, base + 1)]})
        #     if len(positions_base) != len(positions_comm) > 0:
        #         print("Meiri on {} {}".format(en_title, actual_daf))
        #
        #
        #     if mode == "1":
        #         new_links = PM_regular(lines_in_title[daf], comm_title, base_ref, writer, score_manager)
        #     elif mode == "2":
        #         new_links = match_ref_interface(base_ref, comm_title, lines_in_title[daf], lambda x: x.split(), dher, generated_by="meiri_to_daf")
        #     elif mode == "3":
        #         if daf-1 in lines_in_title:
        #             new_links = PM_regular(lines_in_title[daf-1], comm_title, base_ref)
        #         new_links = PM_regular(lines_in_title[daf], comm_title, base_ref)
        #         if daf+1 in lines_in_title:
        #             new_links = PM_regular(lines_in_title[daf+1], comm_title, base_ref)
        #     for l in new_links:
        #         meiri_ref = l["refs"][0] if l["refs"][0].startswith("Meiri") else l["refs"][1]
        #         if meiri_ref not in found_refs:
        #             links.append(l)
        # f.close()
        #

    with open("{}.json".format(mode), 'w') as f:
        json.dump(links, f)
post_link(links, server="https://pele.cauldron.sefaria.org")