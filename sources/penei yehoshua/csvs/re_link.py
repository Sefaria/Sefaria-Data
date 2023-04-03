#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from linking_utilities.dibur_hamatchil_matcher import match_ref
from sources.functions import UnicodeReader, post_index, post_link
import os


def dh_extract_method(str):
    if not str:
        return str
    first_word = str.split()[0]
    str = " ".join(str.split()[1:])  # remove the first word since it just indicates category
    chulay = u"כו'"
    str = str.split(u"כו'")[0]
    for el in ['בד"ה', 'ד"ה', 'בא"ד', """ד'"ה"""]:
        str = str.replace(el.decode('utf-8'), u"")
    str = " ".join(str.replace(u"<b>", u"").replace(u"</b>", u"").split()[0:8])
    return str

if __name__ == "__main__":
    files = [file for file in os.listdir(".") if file.endswith(".csv")]
    for file in files:
        links = []
        title = file.split(" - ")[0] # get "Penei Yehoshua on Beitzah" out of filename "Penei Yehoshua on Beitzah - he - Penei Yehoshua, Warsaw 1861.csv"
        base_title = title.replace("Penei Yehoshua on ", "")
        base_he_title = library.get_index(base_title).get_title('he')
        root = JaggedArrayNode()
        root.add_primary_titles(title, u"פני יהושע על {}".format(base_he_title))
        root.key = "penei"+base_title
        root.add_structure(["Daf", "Comment"], ["Talmud", "Integer"])
        index = {
            "schema": root.serialize(),
            "title": title,
            "categories": ["Talmud", "Bavli", "Commentary", "Penei Yehoshua"]
        }
        #post_index(index, server="http://localhost:8000")
        section_refs = library.get_index(title).all_section_refs()
        for sec_ref in section_refs:
            print sec_ref
            base_ref = sec_ref.normal().replace("Penei Yehoshua on ", "")
            base_tc = TextChunk(Ref(base_ref), lang='he')
            comm_tc = TextChunk(sec_ref, lang='he')
            results = match_ref(base_tc, comm_tc, lambda x: [el for el in x.split(" ") if el], dh_extract_method=dh_extract_method)["matches"]
            for i, result in enumerate(results):
                if not result:
                    continue
                comm_ref = "{}:{}".format(sec_ref.normal(), i+1)
                link = {"refs": [result.normal(), comm_ref], "auto": True, "type": "Commentary", "generated_by": "penei_yehoshua_try_2"}
                links.append(link)
        post_link(links, server="http://proto.sefaria.org")
        #
        #
        # with open(file) as f:
        #     reader = UnicodeReader(f)
        #     for row in reader:
        #         if title not in row[0]: #top of file has metadata, but if title is in row[0], now we have actual data
        #             continue
        #         ref, text = row
        #         base_ref = ref.replace("Penei Yehoshua on ", "")
        #         daf, line_n = base_ref.split().split(":")


