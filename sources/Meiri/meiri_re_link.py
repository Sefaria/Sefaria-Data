from sources.functions import *

def dher(str):
    dh = " ".join(bleach.clean(str, tags=[], strip=True).split()[:8])
    return dh

links = []
text = {}
mishnah = "המשנה"
probs = []
with open("meiri.csv", 'r') as f:
    for row in csv.reader(f):
        if row[0].startswith("Meiri on Berakhot "):
            daf = row[0].split()[-1].split(":")[0]
            if daf not in text:
                text[daf] = []
            if mishnah in row[1].split()[0]:
                lines = Ref("Berakhot "+daf).text('he').text
                found = -1
                for i, line in enumerate(lines):
                    if "מַתְנִי׳" in line.split()[0]:
                        found = i
                if found == -1:
                    probs.append(row[0])
                links.append({"generated_by": "mishnah_to_meiri", "auto": True, "type": "Commentary", "refs": [row[0], "Berakhot {}:{}".format(daf, found+1)]})
            text[daf].append(row[1])

print(len(links))
print(len(probs))
for daf in text:
    comments = text[daf]
    links += match_ref_interface("Berakhot "+daf, "Meiri on Berakhot "+daf, comments, lambda x: x.split(), dh_extract_method=dher)


print(len(links))
post_link(links)