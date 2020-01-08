#encoding=utf-8
import django
django.setup()
import codecs
from sefaria.model import *
from sources.functions import *
import json

def create_dict(marker="&", title="Kereti"):
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
                    mechaber_kereti_dict[siman][1] = line.count(marker)
                    seif = 0
                elif "@11" in line:
                    seif = getGematria(line.split()[0])
                    if seif == 1:
                        mechaber_kereti_dict[siman][seif] += line.count(marker)
                    else:
                        mechaber_kereti_dict[siman][seif] = line.count(marker)
                    for n in range(mechaber_kereti_dict[siman][seif]):
                        kereti_ref = "{} on Shulchan Arukh, Yoreh De'ah {}:{}".format(title, siman, n+1+running_total_per_siman)
                        base_ref = "Shulchan Arukh, Yoreh De'ah {}:{}".format(siman, seif)
                        inline_info = {
                                "data-order": n+1+running_total_per_siman,
                                "data-commentator": title
                            }
                        links.append({"inline_reference": inline_info, "refs": [base_ref, kereti_ref], "type": "Commentary", "auto": True, "generated_by": "mechaber_kereti"})

                    running_total_per_siman += mechaber_kereti_dict[siman][seif]
                prev_siman = siman

    return links, mechaber_kereti_dict

def get_comm_text(title, post=False):
    files = ["{} 1.txt".format(title), "{} 2.txt".format(title)]

    text = {}
    siman = 0
    for file in files:
        seif = 0
        with open(file) as f:
            for line in f:
                if line.startswith("@00"):
                    siman = getGematria(line.split()[-1])
                    seif = 0
                    text[siman] = {}
                elif line.startswith("@22"):
                    seif = getGematria(line)
                    if seif in text[siman]:
                        print "Duplicate Seif {} in Siman {}".format(seif, siman)
                    text[siman][seif] = ""
                elif len(line.strip()) > 0:
                    text[siman][seif] += removeAllTags(line) + "\n"


    for siman in text.keys():
        text[siman] = convertDictToArray(text[siman], empty="")
    text = convertDictToArray(text)
    version = {
        "text": text,
        "language": "he",
        "versionTitle": "Ashlei Ravrevei: Shulchan Aruch Yoreh Deah, Lemberg, 1888",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002097765"
    }
    if post:
        post_text("{} on Shulchan Arukh, Yoreh De'ah".format(title), version, index_count="on")
    return text


if __name__ == "__main__":
    get_comm_text("Kereti", True)
    links, other = create_dict()
    post_link(links)