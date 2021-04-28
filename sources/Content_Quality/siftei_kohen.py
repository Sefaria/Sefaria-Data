from sources.functions import *
new_links = []
ls = LinkSet({"$and": [{"refs": {"$regex": "^Shulchan Arukh, Yoreh De'ah"}}, {"refs": {"$regex": "^Siftei Kohen"}}]})
for l in ls:
    shulchan_ref, siftei_ref = (l.refs[0], l.refs[1]) if l.refs[0].startswith("Shulchan") else (l.refs[1], l.refs[0])
    siftei_ref = Ref(siftei_ref).as_ranged_segment_ref().normal()
    if "-" in siftei_ref:
        print(siftei_ref)
    inline_ref = {"data-commentator": "Siftei Kohen", "data-order": 1}
    new_links.append({"refs": [shulchan_ref, siftei_ref], "generated_by": "siftei_to_shulchan", "auto": True,
                      "type": "Commentary"})
    if getattr(l, "inline_reference", None):
        new_links[-1]["inline_reference"] = l.inline_reference
post_link_in_steps(new_links, server="https://www.sefaria.org", sleep_amt=5, step=100)
"""
  "refs" : [
        "Shulchan Arukh, Yoreh De'ah 100:1", 
        "Siftei Kohen on Shulchan Arukh, Yoreh De'ah 100:1"
    ],
    Iterate over set and create a new link between SA ref and the range of the Siftei Kohen segment refs of the section
    ref in the LinkSet. But don't save the link becuase of speed, just create a list of refs.
    Then, delete the LinkSet above and iterate over list and create new links. 
"""