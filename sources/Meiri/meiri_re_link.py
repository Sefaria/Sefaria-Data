from sources.functions import *

def dher(str):
    dh = " ".join(bleach.clean(str, tags=[], strip=True).split()[:8])
    return dh

links = []
text = {}

with open("meiri.csv", 'r') as f:
    for row in csv.reader(f):
        if row[0].startswith("Meiri on Berakhot "):
            daf = row[0].split()[-1].split(":")[0]
            if daf not in text:
                text[daf] = []
            text[daf].append(row[1])


for daf in text:
    comments = text[daf]
    links += match_ref_interface("Berakhot "+daf, "Meiri on Berakhot "+daf, comments, lambda x: x.split(), dh_extract_method=dher)


print(len(links))
post_link(links)