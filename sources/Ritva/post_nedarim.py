from sources.functions import *
links = []
with open("Ritva_on_Nedarim_-_to_parse (1).csv", 'r') as f:
    text = {}
    for row in list(csv.reader(f))[1:]:
        daf, comm, link = row
        orig_daf = daf
        daf = AddressTalmud(0).toNumber("en", daf)
        if daf not in text:
            text[daf] = []
            seg = 0
        seg += 1
        text[daf].append(comm)
        ref = "Ritva on Nedarim {}:{}".format(orig_daf, seg)
        if len(link) > 0:
            links.append({"refs": [ref, link], "generated_by": "Ritva_Nedarim", "auto": True, "type": "Commentary"})

root = JaggedArrayNode()
root.add_primary_titles("Ritva on Nedarim", """ריטב"א על נדרים""")
root.add_structure(["Daf", "Paragraph"], address_types=["Talmud", "Integer"])
root.key = "Ritva on Nedarim"
indx = {
    "authors": ["Ritva"],
    "enDesc": "Concise commentary on the Talmud, written by Rabbi Yom Tov ben Avraham Isbilli (Ritva). The author was a Spanish, medieval rabbi and halakhic authority. His commentaries to many tractates of the Talmud are a mainstay of yeshiva study to this day.",
    "pubDate": "1833",
    "compDate": "1300",
    "compPlace": "Middle-Age Spain",
    "pubPlace": "Livorno, Italy",
    "era": "RI",
    "title": root.key,
    "categories": ["Talmud", "Bavli", "Rishonim on Talmud", "Ritva", "Seder Nashim"],
    "schema": root.serialize(),
    "collective_title": "Ritva",
    "dependence": "Commentary",
    "base_text_titles": ["Nedarim"]
}
send_text = {
    "language": "he",
    "versionTitle": "Vilna, 1884",
    "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH003807843/NLI",
    "text": convertDictToArray(text)
}
post_index(indx, server="https://arukhtanakh.cauldron.sefaria.org")
#post_text("Ritva on Nedarim", send_text, server="https://arukhtanakh.cauldron.sefaria.org")
#post_link(links, server="https://arukhtanakh.cauldron.sefaria.org")