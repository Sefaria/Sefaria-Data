#encoding=utf-8
import django
import codecs
from sefaria.model import *
import re
from bs4 import BeautifulSoup
comm_ref_probs = []
links = []
tc = TextChunk(Ref("Shulchan Arukh, Yoreh De'ah"), vtitle="Kereti and Peleti", lang="he")
#LinkSet(Ref("Kereti on Shulchan Arukh, Yoreh De'ah")).delete()
#LinkSet(Ref("Peleti on Shulchan Arukh, Yoreh De'ah")).delete()

for siman_n, siman in enumerate(tc.text):
    for seif_n, seif in enumerate(siman):
        for i_tag in re.findall("(<i .*?>)</i>", seif):
            i_tag_dict = BeautifulSoup(i_tag).find("i").attrs
            data_commentator = i_tag_dict["data-commentator"]
            data_order = i_tag_dict["data-order"]
            SA_ref = "Shulchan Arukh, Yoreh De'ah {}:{}".format(siman_n+1, seif_n+1)
            if data_commentator in ["Kereti", "Peleti"]:
                comm_ref = Ref("{} on Shulchan Arukh, Yoreh De'ah {}:{}".format(data_commentator, siman_n+1, data_order))
                if not comm_ref.text('he').text and comm_ref.normal() not in comm_ref_probs:
                    comm_ref_probs.append("{} vs {}".format(SA_ref, comm_ref))
                elif comm_ref.text('he').text:
                    links.append({"refs": [comm_ref.normal(), SA_ref], "generated_by": "relinker_kereti_peleti",
                                  "auto": True, "type": "Commentary", "inline_reference": {"data-order": data_order, "data-commentator": data_commentator}})
                    #Link(links[-1]).save()


for comm_ref in comm_ref_probs:
    print(comm_ref)