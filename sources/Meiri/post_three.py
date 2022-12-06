from sources.functions import *
import time
def filter_tractates(links):
    new_links = {}
    for l in links:
        meiri = l["refs"][0] if l["refs"][0].startswith("Meiri on") else l["refs"][1]
        if meiri not in new_links:
            new_links[meiri] = []
        new_links[meiri].append(l)
    return new_links


def one_and_two(one, two):
    for meiri in two:
        if meiri not in one:
            one[meiri] = two[meiri]
    return [seg for el in list(one.values()) for seg in el]


links = []
import json
#
# with open("all_links.json", 'r') as f:
#     links = json.load(f)
# post_link_in_steps(links, step=200, sleep_amt=10)

links = [x for x in json.load(open("1.json", 'r'))+json.load(open("2.json", 'r'))+json.load(open("3.json", 'r')) if " on Yoma" in str(x["refs"])]
post_link(links, server="https://www.sefaria.org")