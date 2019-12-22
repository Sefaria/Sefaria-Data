#encoding=utf-8
import django
django.setup()
import codecs
from sefaria.model import *
from sources.functions import *
import json
siman = 0
prev_siman = 0
mechaber_kereti_dict = {}
seif = 0
links = []
for f in ["Mechaber 1.txt", "Mechaber 2.txt"]:
    with open(f) as file:
        running_total_per_siman = 0
        for line in file:
            if "@22" in line:
                siman = getGematria(line.split()[0])
                assert siman - prev_siman == 1
                running_total_per_siman = 0
                mechaber_kereti_dict[siman] = {}
                mechaber_kereti_dict[siman][1] = line.count("&")
                seif = 0
            elif "@11" in line:
                seif = getGematria(line.split()[0])
                if seif == 1:
                    mechaber_kereti_dict[siman][seif] += line.count("&")
                else:
                    mechaber_kereti_dict[siman][seif] = line.count("&")
                for n in range(mechaber_kereti_dict[siman][seif]):
                    kereti_ref = "Kereti on Shulchan Arukh, Yoreh De'ah {}:{}".format(siman, n+1+running_total_per_siman)
                    base_ref = "Shulchan Arukh, Yoreh De'ah {}:{}".format(siman, seif)
                    inline_info = {
                            "data-order": n+1+running_total_per_siman,
                            "data-commentator": "Kereti"
                        }
                    links.append({"inline_reference": inline_info, "refs": [base_ref, kereti_ref], "type": "Commentary", "auto": True, "generated_by": "mechaber_kereti"})

                running_total_per_siman += mechaber_kereti_dict[siman][seif]
            prev_siman = siman

post_link(links)
files = ["Kereti 1.txt", "Kereti 2.txt"]
text = {}
siman = 0
for file in files:
    seif = 0
    with open(file) as f:
        for line in f:
            if line.startswith("@00"):
                siman += 1
                seif = 0
                text[siman] = {}
            elif line.startswith("@22"):
                seif = getGematria(line)
                text[siman][seif] = ""
            elif line.startswith("@"):
                text[siman][seif] += removeAllTags(line) + "\n"
            else:
                print line

for siman in text.keys():
    text[siman] = convertDictToArray(text[siman])
text = convertDictToArray(text)
version = {
    "text": text,
    "language": "he",
    "versionTitle": "Ashlei Ravrevei: Shulchan Aruch Yoreh Deah, Lemberg, 1888",
    "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002097765"
}
#post_text("Kereti on Shulchan Arukh, Yoreh De'ah", version, index_count="on")
