#encoding=utf-8
import django
django.setup()
import csv
from sefaria.model import *
from sefaria.system.exceptions import InputError
from sefaria.model.schema import AddressTalmud
from sources.functions import *
import codecs
from collections import Counter
from data_utilities.dibur_hamatchil_matcher import *
def dher(str):
    str = str.replace(".</b>", "</b>.")
    if "</b>." in str:
        assert "</b>" in str
        str = str.split("</b>")[0]
    else:
        str = str.split("</b>.")[0]
    str = str.replace("<b>", "")
    return str

def create_index(title):
    super_root = JaggedArrayNode()
    he_title = library.get_index(title).get_title('he')
    super_root.add_primary_titles("Ben Yehoyada on {}".format(title), u"בן יהוידע על {}".format(he_title))
    super_root.key = "Ben Yehoyada on {}".format(title)
    if title != "Eduyot":
        super_root.add_structure(["Daf", "Paragraph"], address_types=["Talmud", "Integer"])
    else:
        super_root.add_structure(["Chapter", "Mishnah"], address_types=["Integer", "Integer"])
    super_root.validate()
    post_index({
        "schema": super_root.serialize(),
        "title": "Ben Yehoyada on {}".format(title),
        "dependence": "Commentary",
        "collective_title": "Ben Yehoyada",
        "categories": ["Talmud", "Bavli", "Commentary", "Ben Yehoyada"],
        "base_text_titles": [title]

    }, server=SEFARIA_SERVER)

if __name__ == "__main__":
    dappim = Counter()
    new_csv = ""

    for title in os.listdir("new masechtot"):
        text_dict = {}

        create_index(title[:-4])
        with open("new masechtot/{}".format(title)) as file:
            reader = csv.reader(file)
            title = title[:-4]
            rows = list(reader)[2:]
            prev_ref = ""
            for row in rows:
                ref, text = row
                text = text.replace('""', '%')
                text = text.replace('"', '').replace('%', '"')
                if '\0' in row:
                    print(ref)
                    print(text)
                text = text.replace('\0', "")

                    #BELOW CONVERTS FORMAT SHMUEL GAVE ME
                if ref == "":
                    ref = prev_ref
                prev_ref = ref
                if title != "Eduyot":
                    daf = getGematria(ref)*2
                    if "." in ref:
                        daf -= 1
                    dappim[daf] += 1
                    if daf not in text_dict:
                        text_dict[daf] = []
                    text_dict[daf].append(text)
                    ref = "Ben Yehoyada on {} {}:{}".format(title, daf, dappim[daf])
                else:
                    perek, mishnah = ref.split(",")
                    perek = getGematria(perek)
                    mishnah = getGematria(mishnah)
                    if perek not in text_dict:
                        text_dict[perek] = {}
                    if mishnah not in text_dict[perek]:
                        text_dict[perek][mishnah] = ""
                    text_dict[perek][mishnah] += text+"\n"
                    ref = "Ben Yehoyada on {} {}:{}".format(title, perek, mishnah)


        if title == "Eduyot":
            for perek in text_dict.keys():
                text_dict[perek] = convertDictToArray(text_dict[perek], empty="")
        links = []
        send_text = {
            "text": convertDictToArray(text_dict),
            "versionTitle": "Senlake edition 2019 based on Ben Yehoyada, Jerusalem, 1897",
            "versionSource": "http://beta.nli.org.il/he/books/NNL_ALEPH001933802/NLIl",
            "language": "he"
        }
        post_text("Ben Yehoyada on {}".format(title), send_text, index_count="on")
        for daf, text in text_dict.items():
            daf = AddressTalmud.toStr("en", daf) if title != "Eduyot" else daf
            try:
                base = TextChunk(Ref("{} {}".format(title, daf)), lang='he')
            except InputError as e:
                print(e)
                continue
            try:
                results = match_ref(base, text, lambda x: x.split(), dh_extract_method=dher)
                for i, ref in enumerate(results["matches"]):
                    if ref:
                        berakhot = "Ben Yehoyada on {} {}:{}".format(title, daf, i+1)
                        links.append({"refs": [ref.normal(), berakhot], "type": "Commentary", "auto": True, "generated_by": "ben_yeh"})
            except:
                print(base)
        print(len(links))
        post_link(links, server=SEFARIA_SERVER)
        with codecs.open("{}_Sefaria_structure.csv".format(title), 'w', encoding='utf-8') as f:
            f.write(new_csv)


