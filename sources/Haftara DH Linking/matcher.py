#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from data_utilities.dibur_hamatchil_matcher import *
from sefaria.system.database import db
from sources.functions import *
parasha_to_haftara = {}

def base_tokenizer(str):
    return str.split()

def dh(str):
    str = str.replace("<b>", "").replace("</b>", "")
    if "." in str.split()[0] or ("(" in str.split()[0] and ")" in str.split()[0]):
        str = u" ".join(str.split()[1:])


    if u"וכו'" in str:
        result = str.split(u"וכו'")[0]
    elif u"וגו'" in str:
        result = str.split(u"וגו'")[0]
    elif "." in u" ".join(str.split()[0:10]):
        result = str.split(".")[0]
    else:
        result = u" ".join(str.split()[0:8])
    return result.strip()

for p in db.parshiot.find():
    parasha_name = p["parasha"]
    haftara_ref = p["haftara"]["ashkenazi"]
    parasha_to_haftara[parasha_name] = haftara_ref


titles = ["Nachal Sorek", "Tzaverei Shalal"]
links = []
for title in titles:
    for ref in library.get_index(title).all_section_refs():
        haftarah_name = ref.normal().replace("Haftarah of ", "").replace("Haftarah for the ", "")
        haftarah_name = haftarah_name.replace("{}, ".format(title), "")
        haftarah_name = re.sub(" \d+$", "", haftarah_name)
        try:
            haftarah_ref = Ref(parasha_to_haftara[haftarah_name][0])
        except KeyError as e:
            print e.message
            continue
        results = match_ref(haftarah_ref.text('he'), ref.text('he').text, base_tokenizer=base_tokenizer, dh_extract_method=dh)
        for n, result in enumerate(results["matches"]):
            if result:
                comm_ref = ref.normal() + ":" + str(n+1) if ref.normal()[-1].isdigit() else ref.normal() + " " + str(n+1)
                links.append({"refs": [result.normal(), comm_ref], "generated_by": "haftara_matcher", "auto": True,
                              "type": "Commentary"})

post_link(links, server="http://ste.sandbox.sefaria.org")
for l in links:
    print l["refs"]