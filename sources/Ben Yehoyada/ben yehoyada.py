#encoding=utf-8
import django
django.setup()
import csv
from sefaria.model import *
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
    super_root.add_structure(["Daf", "Paragraph"], address_types=["Talmud", "Integer"])
    super_root.validate()
    post_index({
        "schema": super_root.serialize(),
        "title": "Ben Yehoyada on {}".format(title),
        "categories": ["Talmud", "Bavli", "Commentary", "Ben Yehoyada"]
    }, server=SEFARIA_SERVER)

if __name__ == "__main__":
    dappim = Counter()
    new_csv = ""
    for title in ["Eruvin", "Shabbat", "Pesachim"]:
        text_dict = {}

        #create_index(title)
        with open(title+".csv") as file:
            # reader = csv.reader(f)
            for row in file:
                ref, text = row.split(",", 1)
                if '\0' in row:
                    print ref
                    print text
                text = text.replace('\0', "")
                text = text.decode('utf-8')
                # if "Introduction" not in row and "Yehoyada" in ref:
                    # text = text.replace("</strong></big>", "!? ")
                    # text = re.sub(u"<.*?>", u"", text)
                    # text = re.sub(u"</.*?>", u"", text)
                    #
                    # daf = ref.split(":")[0].split()[-1]
                    # if daf not in text_dict:
                    #     text_dict[daf] = []
                    # text_dict[daf].append(text)

                    #BELOW CONVERTS FORMAT SHMUEL GAVE ME
                if ref is not "":
                    daf = getGematria(ref)*2
                    if "." in ref:
                        daf -= 1
                    dappim[daf] += 1
                    if daf not in text_dict:
                        text_dict[daf] = []
                text = text.replace('""', '"')
                text_dict[daf].append(text)

                ref = "Ben Yehoyada on {} {}:{}".format(title, daf, dappim[daf])

        links = []
        send_text = {
            "text": convertDictToArray(text_dict),
            "versionTitle": "Senlake edition 2019 based on Ben Yehoyada, Jerusalem, 1897",
            "versionSource": "http://beta.nli.org.il/he/books/NNL_ALEPH001933802/NLIl",
            "language": "he"
        }
        #post_text("Ben Yehoyada on {}".format(title), send_text)
        for daf, text in text_dict.items():
            daf = AddressTalmud.toStr("en", daf)
            base = TextChunk(Ref("{} {}".format(title, daf)), lang='he')
            results = match_ref(base, text, lambda x: x.split(), dh_extract_method=dher)
            for i, ref in enumerate(results["matches"]):
                if ref:
                    berakhot = "Ben Yehoyada on {} {}:{}".format(title, daf, i+1)
                    links.append({"refs": [ref.normal(), berakhot], "type": "Commentary", "auto": True, "generated_by": "ben_yeh"})

        post_link(links, server=SEFARIA_SERVER)
        with codecs.open("{}_Sefaria_structure.csv".format(title), 'w', encoding='utf-8') as f:
            f.write(new_csv)


