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


servers = ["https://ste.cauldron.sefaria.org", "https://ezradev.cauldron.sefaria.org", "http://sterling.sandbox.sefaria.org"]
files = ["1.json", "2.json"]
servers = [servers[1]]
links = []
import json
with open("1.json", 'r') as f:
    one_links = filter_tractates(json.load(f))
with open("2.json", 'r') as f:
    two_links = filter_tractates(json.load(f))

links = one_and_two(one_links, two_links)

print(len(links))
step = int(len(links)/2)
#post_link(links, skip_lang_check=1)
init = 0
for i in range(init, len(links), step):
    init += step
    post_link(links[0:step+init], skip_lang_check=1)
    time.sleep(20)
    # post_link(links, server=server)