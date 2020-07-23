from sources.functions import *

base_ref = "Sefer HaChinukh 1"
comm_ref = "Minchat Chinukh 1"
comments = Ref(comm_ref).text('he').text
base_tokenizer = lambda str: str.split()

def dher(str):
    str = str.replace("<b>", "").replace("</b>", "")
    poss_dh = str.split(".")[0]
    if poss_dh.count(" ") < 6:
        return poss_dh
    else:
        return ""

links = []

def add_to_dict(total_results, key, prev_found, prev_ref):
    if key not in total_results:
        total_results[key] = []
    new_ref = Ref(prev_found).to(Ref(prev_ref))
    total_results[key] += [new_ref]
    links.append({"refs": [key, new_ref.normal()], "generated_by": "sefer_to_minchat",
                  "auto": True, "type": "Commentary"})

total_results = {}
for i in range(1, 614):
    print(i)
    base_ref = Ref("Sefer HaChinukh {}".format(i))
    comm_section_refs = Ref("Minchat Chinukh {}".format(i)).all_subrefs()
    for comm_section_ref in comm_section_refs:
        comments = [ref.text('he').text for ref in comm_section_ref.all_subrefs()]
        results = match_ref_interface(base_ref.normal(), comm_section_ref.normal(), comments, base_tokenizer, dher)
        prev_skipped = False
        prev_found = comm_section_ref.all_subrefs()[0].normal()
        prev_ref = None
        for minchat_ref in comm_section_ref.all_subrefs():
            minchat_ref = minchat_ref.normal()
            if results[minchat_ref]:
                if prev_skipped:
                    add_to_dict(total_results, results[minchat_ref], prev_found, prev_ref)
                prev_found = minchat_ref
            else:
                prev_skipped = True
            prev_ref = minchat_ref
        if prev_found:
            add_to_dict(total_results, results[prev_found], prev_found, prev_ref)

#post_link(links)

if __name__ == "__main__":
    i = library.get_index("Minchat Chinukh")
    i.dependence = "Commentary"
    i.base_text_titles = ["Sefer HaChinukh"]
    i.categories = ["Halakhah", "Commentary"]
    i.save()
    minchat_ls = LinkSet({"$and": [{"refs": {"$regex": "^Minchat Chinukh"}}, {"refs": {"$regex": "^Sefer HaChinukh"}}]})
    for l in minchat_ls:
        minchat_ref = 0 if l.refs[0].startswith("Minch") else 1
        sefer_ref = l.refs[0] if l.refs[0].startswith("Sefer") else l.refs[1]
        is_seg = Ref(sefer_ref).is_segment_level()
        if is_seg:
            minchat_ref = Ref(l.refs[minchat_ref]).as_ranged_segment_ref().normal()
            l.refs = [sefer_ref, minchat_ref]
            l.save()
