# for every commentator, counts tags and links and compare counts
#encoding=utf-8
import django
django.setup()
import codecs
from sefaria.model import *
import re
from bs4 import BeautifulSoup
import pdb
vtitle_kereti_peleti = ""
links_per_siman = {"Peleti": {}, "Kereti": {}}
i_tags_per_siman = {"Peleti": {}, "Kereti": {}}
tc = TextChunk(Ref("Shulchan Arukh, Yoreh De'ah"), vtitle="Kereti and Peleti", lang="he")
for siman_n, siman in enumerate(tc.text):
    if siman_n > 112:
        break
    links_per_siman[siman_n+1] = {}
    i_tags_per_siman[siman_n+1] = {}
    kereti_links = list(LinkSet({"refs": {"$regex": "^Kereti on Shulchan Arukh, Yoreh De'ah {}:".format(siman_n+1)}}))
    peleti_links = list(LinkSet({"refs": {"$regex": "^Peleti on Shulchan Arukh, Yoreh De'ah {}:".format(siman_n+1)}}))
    for l in kereti_links + peleti_links:
        if "inline_reference" in l.contents():
            shulchan_ref = l.refs[0] if l.refs[0].startswith("Shulchan Arukh") else l.refs[1]
            seif = Ref(shulchan_ref).sections[1]
            if seif not in links_per_siman[siman_n+1]:
                links_per_siman[siman_n+1][seif] = {}
                i_tags_per_siman[siman_n+1][seif] = {}
            inline_ref = l.contents()["inline_reference"]
            data_comm = inline_ref["data-commentator"]
            data_order = int(inline_ref["data-order"])
            if data_comm not in links_per_siman[siman_n+1][seif]:
                links_per_siman[siman_n+1][seif][data_comm] = set()
                i_tags_per_siman[siman_n+1][seif][data_comm] = set()
            links_per_siman[siman_n+1][seif][data_comm].add(data_order)
    for seif_n, seif in enumerate(siman):
        try:
            for i_tag in re.findall("(<i .*?>)</i>", seif):
                i_tag_dict = BeautifulSoup(i_tag).find("i").attrs
                data_comm = i_tag_dict["data-commentator"]
                data_order = int(i_tag_dict["data-order"])
                if data_comm in ["Kereti", "Peleti"]:
                    i_tags_per_siman[siman_n+1][seif_n+1][data_comm].add(data_order)
        except KeyError as e:
            pass
        try:
            for data_comm in ["Kereti", "Peleti"]:
                i_tags = i_tags_per_siman[siman_n+1][seif_n+1].get(data_comm, [])
                links = links_per_siman[siman_n+1][seif_n+1].get(data_comm, [])
                i_tag_num = len(i_tags)
                links_num = len(links)
                if i_tag_num != links_num:
                    print "{} {} {}: {} {}".format(data_comm, siman_n+1, seif_n+1, i_tag_num, links_num)
        except KeyError as e:
            pass



