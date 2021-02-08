from sources.functions import *
import json
def sorter(x):
    return int(x.split()[-1])

with open("old_links.json", 'r') as f:
    links = json.load(f)
with open("report.csv", 'w') as f:
    writer = csv.writer(f)
    neg = {}
    pos = {}
    for l in links:
        zohar_ref, azharot_ref = (l["ref"], l["anchorRef"]) if l["ref"].startswith("Zohar") else (l["anchorRef"], l["ref"])
        if "Index" in zohar_ref and "Neg" in zohar_ref:
            if azharot_ref not in neg:
                neg[azharot_ref] = []
            neg[azharot_ref].append(zohar_ref)
        if "Index" in zohar_ref and "Pos" in zohar_ref:
            if azharot_ref not in pos:
                pos[azharot_ref] = []
            pos[azharot_ref].append(zohar_ref)
    for ref in sorted(pos.keys(), key=sorter):
        writer.writerow([ref, pos[ref]])
    for ref in sorted(neg.keys(), key=sorter):
        writer.writerow([ref, neg[ref]])



for tuple in ["Positive", "Negative"]:
    base = "Azharot of Solomon ibn Gabirol, {} Commandments".format(tuple)
    for i, azharot_ref in enumerate(Ref(base).all_segment_refs()):
        zohar_ref = Ref("Zohar HaRakia, {} Commandments {}".format(tuple, i+1)).as_ranged_segment_ref()
        print(zohar_ref)
        Link({"generated_by": "Azharot_to_Zohar_Commandments", "type": "Commentary",
                      "auto": True, "refs": [zohar_ref, azharot_ref]}).save()
