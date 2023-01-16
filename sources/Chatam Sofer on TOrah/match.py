#encoding=utf-8
import django
django.setup()
import codecs
from sefaria.model import *
from sources.functions import *
import csv
from sefaria.system.exceptions import InputError
from linking_utilities.dibur_hamatchil_matcher import *
from sefaria.system.database import db


def dh_func(dh):
    dh = dh.replace("*", "").replace(u"אלקים", u"אלהים").replace(u"ה'", u"יהוה")
    return [dh.strip() for dh in dh.split(u"וגו'") if len(dh.strip()) > 5]


dhs = {}
haftara = ""
prev_ref = ""
with open("Chatam_Sofer_on_Torah.csv") as csvf:
    for row in UnicodeReader(csvf):
        if row[0].startswith("Chatam Sofer"):
            ref, text = row
            para = ref.split()[0:-1]
            ref = u" ".join(ref.split()).replace("Chatam Sofer on Torah, ", "")
            parasha = u" ".join(ref.split()[:-1])
            if ref != prev_ref:
                haftara = ""
            if text == u"<b>בהפטרה</b>":
                try:
                    haftara = list(db.parshiot.find({"parasha": parasha}))[0]["haftara"]["ashkenazi"][0]
                except IndexError as e:
                    print e

                dhs[haftara] = []

            parasha = "Parashat "+parasha if not "Parashat" in parasha else parasha
            if parasha not in dhs:
                dhs[parasha] = []
            poss_dhs = re.findall("<b>(.*?)</b>", text)
            dh_list = dh_func(poss_dhs[0]) if len(poss_dhs) >= 1 else [""]
            if dh_list:
                dhs[parasha] += [(ref.split()[-1], haftara, dh_list)]
            prev_ref = ref

links = []
del dhs[""]
for parasha, tuples in dhs.items():
    for tuple in tuples:
        ref, haftara, dhs = tuple
        if not dhs:
            continue
        base_ref = parasha if not haftara else haftara
        try:
            base_text = TextChunk(Ref(base_ref), lang='he', vtitle="Tanach with Text Only")
        except InputError as e:
            print e
            continue
        boundary_flexibility = 100000       # just need a very high number
        for i, match in enumerate(match_ref(base_text, dhs, lambda x: x.split(), boundaryFlexibility=boundary_flexibility)["matches"]):
            if match:
                parasha = parasha.replace("Parashat ", "")
                chatam_ref = "Chatam Sofer on Torah, {} {}".format(parasha, ref)
                found_base_ref = match.normal()
                link = {"refs": [chatam_ref, found_base_ref], "type": "Commentary", "auto": True, "generated_by": "chatam_sofer_on_torah"}
                links.append(link)
post_link(links, server="http://ste.sandbox.sefaria.org")
print len(links)
