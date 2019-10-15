#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from data_utilities.dibur_hamatchil_matcher import *
from sefaria.system.database import db
from sources.functions import *
import json
import csv
import re
from sefaria.export import import_versions_from_stream
import_versions_from_stream(open("nachal.csv"), [1], 1)
import_versions_from_stream(open("tzaverei.csv"), [1], 1)


parsha_to_haftarot = {}
with open("parashot-haftarot.csv") as f:
    for row in csv.reader(f):
        parsha, ref = row[0], row[1]
        parsha_to_haftarot[row[0]] = row[1]


parsha_to_haftarot["Haftarah of Kedoshim"] = Ref("Kedoshim").normal()
def base_tokenizer(str):
    return str.split()

def dh(str):
    if u"וכו'" in str:
        str = str.split(u"וכו'")[0]
    elif u"וגו'" in str:
        str = str.split(u"וגו'")[0]
    str = str[str.find("<b>")+3:str.find("</b>")]
    return str

def convertHolidays(str):
    str = str.replace("Rosh Hashanah", "Rosh Hashana")
    if "Day of" in str:
        str = str.replace("Day of ", "")
        str = str.replace("First", "I").replace("Second", "II").replace("Seventh", "VII").replace("Eighth", "VIII")
        str = str.replace("Haftarah for the ", "")
        str = u" ".join(str.split()[1:] + str.split()[0:1])
    elif "Haftarah for Shabbat Chol HaMoed" in str:
        str = str.replace("Haftarah for ", "")
    return str


titles = ["Nachal Sorek", "Tzaverei Shalal"]
links = {"Nachal Sorek": [], "Tzaverei Shalal": []}
for title in titles:
    print title
    all_refs = library.get_index(title).all_section_refs() if title == "Nachal Sorek" else library.get_index(title).all_segment_refs()
    for ref in all_refs:
        if ref.is_segment_level() and len(ref.sections) > 1 and ref.sections[1] > 1:
            continue
        haftarah_name = ref.normal()
        haftarah_name = haftarah_name.replace("{}, ".format(title), "")
        haftarah_name = re.sub(" [\:\d]+$", "", haftarah_name)
        #haftarah_name = convertHolidays(haftarah_name)
        # haftarah_name = haftarah_name.replace("Matot Masei", "Matot-Masei")
        # haftarah_name = haftarah_name.replace("Lech Lecha", "Lech-Lecha").replace("Achrei Mot Kedoshim", u'Achrei Mot-Kedoshim')
        try:
            haftarah_ref = parsha_to_haftarot[haftarah_name]
        except KeyError as e:
            print e.message
            continue
        haftarah_ref = Ref(haftarah_ref)
        haftarah_tc = TextChunk(haftarah_ref, lang='he', vtitle="Tanach with Text Only")
        comments = ref.text('he').text if title == "Nachal Sorek" else [ref.text('he').text]
        results = match_ref(haftarah_tc, comments, base_tokenizer=base_tokenizer, dh_extract_method=dh)
        for n, result in enumerate(results["matches"]):
            if result:
                if title != "Nachal Sorek":
                    comm_ref = Ref(ref.normal().rsplit(":", 1)[0])
                    comm_ref = comm_ref.as_ranged_segment_ref().normal()
                else:
                    comm_ref = "{} {}".format(ref, n+1)

                links[title].append({"refs": [result.normal(), comm_ref], "generated_by": "haftara_matcher", "auto": True,
                              "type": "Commentary"})


post_link(links["Nachal Sorek"], server="http://ste.sandbox.sefaria.org")
post_link(links["Tzaverei Shalal"], server="http://ste.sandbox.sefaria.org")

#for l in links:
#    print l["refs"]
print links.keys()
print len(links[links.keys()[0]])
print len(links[links.keys()[1]])