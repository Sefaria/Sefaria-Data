from sources.functions import *
from linking_utilities.dibur_hamatchil_matcher import *

t = Term()
t.name = "Chidushei HaMeiri"
t.add_primary_titles(t.name, u"חידושי המאירי")
# t.save()
add_category("Chidushei HaMeiri", ["Talmud", "Bavli", "Commentary", "Chidushei HaMeiri"], server="https://www.sefaria.org")
i = get_index_api("Chidushei HaMeiri on Eruvin")

def dher(text):
    dh = " ".join(text.split(".")) if " ".join(text.split(".")).count(" ") < 10 else " ".join(text.split(" ")[:7])
    return dh

root = SchemaNode()
root.add_primary_titles("Chidushei HaMeiri on Eruvin", u"חידושי המאירי על ערובין")
intro = JaggedArrayNode()
intro.add_shared_term("Introduction")
intro.add_structure(["Paragraph"])
intro.key = "Introduction"
root.append(intro)
default = JaggedArrayNode()
default.default = True
default.key = "default"
default.add_structure(["Daf", "Comment"], address_types=["Talmud", "Integer"])
root.append(default)
root.validate()
# post_index({"title": "Chidushei HaMeiri on Eruvin",
#             "categories": ["Talmud", "Bavli", "Commentary", "Chidushei HaMeiri"],
#             "schema": root.serialize(),
#             "dependence": "Commentary", "collective_title": "Chidushei HaMeiri",
#             "base_text_titles": ["Eruvin"]})

with open("eruvin.tsv") as f:
    comments = {}
    prev_daf = ""
    for line in f:
        daf, text = line.split("\t")
        if not daf:
            daf = prev_daf
        elif daf != "Introduction":
            daf = AddressTalmud(1).toNumber("en", daf)
        if daf not in comments:
            comments[daf] = []
        comments[daf].append(text)
        prev_daf = daf
    links = []
    intro = comments.pop("Introduction")
    send_text = {"language": "he",
                 "text": intro,
                 "versionTitle": "Chidushei HaMeiri on Eruvin, Warsaw 1914",
                 "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH001776964/NLI"}
    #post_text("Chidushei HaMeiri on Eruvin, Introduction", send_text)
    send_text = {"language": "he",
                 "text": convertDictToArray(comments),
                 "versionTitle": "Chidushei HaMeiri on Eruvin, Warsaw 1914",
                 "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH001776964/NLI"}
    #post_text("Chidushei HaMeiri on Eruvin", send_text)
    for daf in comments:
        print(daf)
        actual_daf = AddressTalmud.toStr('en', daf)
        links += match_ref_interface("Eruvin {}".format(actual_daf), "Chidushei HaMeiri on Eruvin {}".format(actual_daf), comments[daf], lambda x: x.split(), dher)
    post_link(links)

