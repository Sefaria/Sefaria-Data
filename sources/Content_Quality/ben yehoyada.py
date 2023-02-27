#encoding=utf-8
import django
django.setup()
import csv
from sefaria.model import *
from sefaria.model.schema import AddressTalmud
from sources.functions import *
import codecs
from collections import Counter
from linking_utilities.dibur_hamatchil_matcher import *
def dher(str):
    if "!? " in str:
        return str.split("!? ")[0]
    else:
        return ""

if __name__ == "__main__":
    super_root = SchemaNode()
    super_root.add_primary_titles("Ben Yehoyada on Berakhot", u"בן יהוידע על ברכות")
    intro = create_intro()
    root = JaggedArrayNode()
    root.default = True
    root.key = "default"
    root.add_structure(["Daf", "Paragraph"], address_types=["Talmud", "Integer"])
    root.validate()
    super_root.append(intro)
    super_root.append(root)
    # #post_index({
    #     "schema": super_root.serialize(),
    #     "title": "Ben Yehoyada on Berakhot",
    #     "categories": ["Talmud", "Bavli", "Commentary"]
    # }, server=SEFARIA_SERVER)
    dappim = Counter()
    new_csv = ""
    text_dict = {}
    with open("Ben Yehoyada on Berakhot - he - Senlake edition 2019 based on Ben Yehoyada, Jerusalem, 1897.csv") as f:
        # reader = csv.reader(f)
        for row in f:
            ref, text = row.split(",", 1)
            if '\0' in row:
                print ref
                print text
            text = text.replace('\0', "")
            text = text.decode('utf-8')
            if "Introduction" not in row and "Yehoyada" in ref:
                text = text.replace("</strong></big>", "!? ")
                text = re.sub(u"<.*?>", u"", text)
                text = re.sub(u"</.*?>", u"", text)

                daf = ref.split(":")[0].split()[-1]
                if daf not in text_dict:
                    text_dict[daf] = []
                text_dict[daf].append(text)

                #BELOW CONVERTS FORMAT SHMUEL GAVE ME
                # daf = getGematria(ref)*2
                # if "." in ref:
                #     daf -= 1
                # daf = AddressTalmud.toStr("en", daf)
                # dappim[daf] += 1
                # if daf not in text_dict:
                #     text_dict[daf] = []
                #
                #
                # ref = "Ben Yehoyada on Berakhot {}:{}".format(daf, dappim[daf])

            new_csv += ref+","+text
    links = []
    for daf, text in text_dict.items():
        base = TextChunk(Ref("Berakhot {}".format(daf)), lang='he')
        results = match_ref(base, text, lambda x: x.split(), dh_extract_method=dher)
        for i, ref in enumerate(results["matches"]):
            if ref:
                berakhot = "Ben Yehoyada on Berakhot {}:{}".format(daf, i+1)
                links.append({"refs": [ref.normal(), berakhot], "type": "Commentary", "auto": True, "generated_by": "ben_yeh"})

    post_link(links, server=SEFARIA_SERVER)
    with codecs.open("Ben_Yeh2.csv ", 'w', encoding='utf-8') as f:
        f.write(new_csv)


