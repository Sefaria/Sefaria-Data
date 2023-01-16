#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from sources.functions import UnicodeReader, convertDictToArray, post_link
from linking_utilities.dibur_hamatchil_matcher import *
def dh_extract(str):
    if u"כו'" in str:
        str = str.split(u"כו'")[0]
    if "<b>" in str:
        str = str.split("</b>")[0].replace("<b>", "")
    elif "." in str:
        str = str.split(".")[0]
    else:
        str = u" ".join(str.split()[0:8])
    return str

links = []
csv_name = "Aderet Eliyahu (Rabbi Yosef Chaim) - he - Aderet Eliyahu, Livorno 1864.csv"
title = csv_name.split(" - ")[0]
reader = UnicodeReader(open(csv_name))
text_dict = {}
for row in reader:
    if not row[0].startswith(title):
        continue
    ref, text = row
    segment = ref.replace("{}, ".format(title), "").split()[-1]
    parsha = u" ".join(ref.replace("{}, ".format(title), "").split()[0:-1])
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
            tiferet_ref = "{}, {} {}".format(title, parsha, i+1)
            links.append({"refs": [tiferet_ref, tanakh_ref.normal()],
                    "type": "Commentary", "auto": True, "generated_by": "{}_matcher".format(title)})
print(links)
print(len(links))
post_link(links, server="http://ste.sandbox.sefaria.org")
