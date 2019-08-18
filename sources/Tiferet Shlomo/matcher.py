#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from sources.functions import UnicodeReader, convertDictToArray, post_link
from data_utilities.dibur_hamatchil_matcher import *
def dh_extract(str):
    if u"כו'" in str:
        str = str.split(u"כו'")[0]
    if "<b>" in str:
        str = str.split("</b>")[0].replace("<b>", "")
    elif "." in str:
        str = str.split(".")[0]
    else:
        str = u" ".join(str.split()[0:8])
    return u" ".join(str.split()[0:-1])

links = []
reader = UnicodeReader(open("Tiferet Shlomo - he - Tiferet Shlomo, Warsaw, 1867.csv"))
text_dict = {}
for row in reader:
    if not row[0].startswith("Tiferet Shlomo, on Torah, "):
        continue
    ref, text = row
    segment = ref.replace("Tiferet Shlomo, on Torah, ", "").split()[-1]
    parsha = u" ".join(ref.replace("Tiferet Shlomo, on Torah, ", "").split()[0:-1])
    segment = int(segment)
    curr_parsha_dict = text_dict.get(parsha, {})
    curr_parsha_dict[segment] = text
    text_dict[parsha] = curr_parsha_dict

for parsha in text_dict.keys():
    print parsha
    text_dict[parsha] = convertDictToArray(text_dict[parsha])
    term = Term().load({"name": parsha})
    if not term or not getattr(term, "ref", None):
        print "Didn't find term {}".format(parsha)
    else:
        base_text = TextChunk(Ref(term.ref), lang='he', vtitle='Tanach with Text Only')
        # if isinstance(base_text[0], list):
        #     for i, lines in enumerate(base_text):
        #         base_text[i] = u" ".join(lines)
        results = match_ref(base_text, text_dict[parsha], char_threshold=0.27, word_threshold=0.33, dh_extract_method=dh_extract, base_tokenizer=lambda x: x.split())
        for i, tanakh_ref in enumerate(results["matches"]):
            if not tanakh_ref:
                continue
            tiferet_ref = "Tiferet Shlomo, on Torah, {} {}".format(parsha, i+1)
            links.append({"refs": [tiferet_ref, tanakh_ref.normal()],
                    "type": "Commentary", "auto": True, "generated_by": "tiferet_matcher"})
post_link(links, server="http://shmuel.sandbox.sefaria.org")
