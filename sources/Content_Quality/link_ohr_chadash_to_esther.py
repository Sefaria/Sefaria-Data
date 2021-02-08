from sources.functions import *
links = []
existing_esther = []
ls = LinkSet({"$and": [{"refs": {"$regex": "^Esther \d+:\d+$"}}, {"refs": {"$regex": "^Ohr Chadash \d+"}}]})
for l in ls:
    esther_ref = l.refs[0] if l.refs[0].startswith("Esther") else l.refs[1]
    existing_esther.append(esther_ref)
    print(esther_ref)
for segment in library.get_index("Ohr Chadash").all_segment_refs():
    if "," not in segment.normal():
        esther_ref = segment.section_ref().normal().replace("Ohr Chadash", "Esther")
        if esther_ref in existing_esther:
            links.append({"refs": [esther_ref, segment.normal()], "generated_by": "esther_to_ohr_chadash", "type": "Commentary",
                      "auto": True})
post_link_in_steps(links, sleep_amt=30, server="https://www.sefaria.org")