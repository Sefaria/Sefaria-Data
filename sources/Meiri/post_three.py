from sources.functions import *
def filter_tractates(links, tracates):
    new_links = {}
    for l in links:
        for t in tracates:
            if t in str(l):
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
    one_links = filter_tractates(json.load(f), ["Gittin", "Kiddushin", "Sanhedrin"])
with open("2.json", 'r') as f:
    two_links = filter_tractates(json.load(f), ["Gittin", "Kiddushin", "Sanhedrin"])

links = one_and_two(one_links, two_links)

print(len(links))
step = int(len(links)/10)
init = 0
for i in range(init, len(links), step):
    init += step
    post_link(links[0:step+init])
    # post_link(links, server=server)