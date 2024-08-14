# -*- coding: utf-8 -*-
from sources.functions import *
from sefaria.utils.hebrew import *
def dher(x):
    return " ".join(x.split()[1:6])
def ref_to_daf(r):
    return r.section_ref().normal().replace("Yad Ramah on ", "")

def bt(x):
    return strip_nikkud(bleach.clean(x, strip=True, tags=[])).split()
base_refs = defaultdict(list)
yad_refs = defaultdict(list)
with open("Yad Ramah on Bava Batra DHs - Sheet1.csv") as f:
    reader = csv.reader(f)
    rows = list(reader)[1:]
    ref = None
    prev = None
    prev_dh = None
    for row in rows:
        ref, dh = row
        dh = dh.strip()
        if prev:
            prev_dh_ref = Ref(prev).to(Ref(ref).prev_segment_ref())
            base_ref = ref_to_daf(prev_dh_ref)
            base_refs[base_ref].append(prev_dh)
            yad_refs[prev_dh].append(prev_dh_ref)
        prev = ref
        prev_dh = dh
prev_dh_ref = Ref(prev)
base_ref = ref_to_daf(prev_dh_ref)
base_refs[base_ref].append(prev_dh)
yad_refs[prev_dh].append(prev_dh_ref)
#
# start = end = None
# dhs = {}
# for sec_ref in library.get_index("Yad Ramah on Bava Batra").all_section_refs():
#     for seg_ref in sec_ref.all_segment_refs():
#         m = re.search("^<b>.{1,2}</b>", seg_ref.text('he').text)
#         if m:
#             if start:
#                 end = seg_ref
#                 dhs[dher(seg_ref.text('he').text)] = start.to(end).normal()
#                 start = None
#             else:
#                 start = seg_ref
#
# base_ref_with_dh = defaultdict(list)
# for dh in dhs:
#     ref = dhs[dh]
#     base_ref = ref_to_daf(ref)
#     base_ref_with_dh[base_ref].append(dh)
#
LinkSet({"generated_by": "add_commentary_links", "refs": {"$regex": "^Yad Ramah on Bava Batra"}}).delete()
LinkSet({"generated_by": "yad_ramah_to_bava_batra_based_on_csv"}).delete()
with open("results.csv", 'w') as f:
    writer = csv.writer(f)
    for base_ref in base_refs:
        results = match_ref(TextChunk(Ref(base_ref), lang='he'), base_refs[base_ref], bt, dh_extract_method=lambda x: x.strip())
        for i, m in enumerate(results["matches"]):
            if m:
                my_dh = results["match_text"][i][1]
                my_ref = [x for x in yad_refs[my_dh] if x.sections[0] == Ref(base_ref).sections[0]][0]
                refs = [my_ref.normal(), m.normal()]
                generated_by = "yad_ramah_to_bava_batra_based_on_csv"
                try:
                    Link({"generated_by": generated_by, "refs": refs, "auto": True, "type": "Commentary"}).save()
                except Exception as e:
                    l = Link().load({"refs": refs}) or Link().load({"refs": refs[::-1]})
                    print(l.generated_by)