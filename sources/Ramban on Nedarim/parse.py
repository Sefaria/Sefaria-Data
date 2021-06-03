from sources.functions import *
def dher(str):
    if "." in " ".join(str.split()[:10]):
        return str.split(".")[0].replace('וכו\'', '').strip()
    else:
        return " ".join(str.split()[:5])

root = JaggedArrayNode()
root.add_primary_titles("Hilkhot HaRamban on Nedarim", 'הלכות הרמב"ן על נדרים')
root.add_structure(["Daf", "Paragraph"], address_types=["Talmud", "Integer"])
root.key = "Hilkhot HaRamban on Nedarim"
root.validate()
indx = {
    "title": root.key,
    "categories": ["Talmud", "Bavli", "Commentary", "Ramban", "Seder Nezikin"],
    "schema": root.serialize()
}
post_index(indx)

text = {}

with open("Nedarim.txt", 'r') as f:
    for line in f:
        if line.startswith("~"):
            #daf
            daf = AddressTalmud(0).toNumber('he', line[1:-1])
            assert daf not in text
            text[daf] = []
            continue
        elif line.startswith("@22") and "גמ" in line.split()[0]:
            #mishnah or gemara
            line = " ".join(line.split()[1:])
            text[daf].append(removeAllTags(line))
        elif line.startswith("@22") and "מתנ" in line.split()[0]:
            line = " ".join(line.split()[1:])
            text[daf].append(removeAllTags(line))
        elif "@00" not in line:
            text[daf].append(removeAllTags(line))
links = []
for daf in text:
    print(daf)
    new_links = match_ref_interface("Nedarim {}".format(AddressTalmud(0).toStr("en", daf)), "Hilkhot HaRamban on Nedarim {}".format(AddressTalmud(0).toStr("en", daf)), text[daf], lambda x: x.split(), dher)
    links += new_links
    print("{} vs {}".format(len(text[daf]), len(new_links)))
text = convertDictToArray(text)
send_text = {
    "text": text,
    "language": "he",
    "versionTitle": "Vilna, 1884",
    "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH003807843/NLI"
}
#post_text(root.key, send_text)
post_link_in_steps(links, server="https://arukhtanakh.cauldron.sefaria.org")
print(len(links))