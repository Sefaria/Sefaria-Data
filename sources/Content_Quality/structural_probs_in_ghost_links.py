from sources.functions import *
links_from_text_get_refs_from_string = []
links_from_text_no_ref_in_string = []
commentary_links_base_prob = []
commentary_links_fine = []
other_links = []
with open("broken_links copy", 'r') as f:
    for line in f:
        _type = line.split("\t")[1]

        refs = eval(line.split("]")[0]+"]")
        if "add_commentary_links" in _type and "auto" in _type:
            comm_ref, base_ref = (refs[0], refs[1]) if " on " in refs[0] else (refs[1], refs[0])
            if len(Ref(base_ref).text('he').text) == 0:
                commentary_links_base_prob.append(refs)
            else:
                commentary_links_fine.append(refs)
        elif "auto" in _type and "add_links_from_text" in _type:
            empty_ref, other_ref = (refs[0], refs[1]) if len(Ref(refs[0]).text('he').text) == 0 else (refs[1], refs[0])
            i = Ref(other_ref).index
            found_refs = []
            for v in i.versionSet():
                tc = TextChunk(Ref(other_ref), vtitle=v.versionTitle, lang=v.language.lower()).text
                if isinstance(tc, list):
                    tc = " ".join(tc)
                poss_found_refs = [r.normal() for r in library.get_refs_in_string(tc, v.language.lower())]
                if len(poss_found_refs) > 0:
                    found_refs += poss_found_refs
            if len(found_refs) > 0 and empty_ref in found_refs:
                links_from_text_get_refs_from_string.append(refs)
            else:
                links_from_text_no_ref_in_string.append(refs)
        else:
            other_links.append(refs)
        # empty_ref = ""
        # if len(Ref(refs[0]).text('he').text) == 0:
        #     empty_ref = refs[0]
        # elif len(Ref(refs[1]).text('he').text) == 0:
        #     empty_ref = refs[1]
        # assert len(empty_ref) > 0
        # i = Ref(empty_ref).index
        # if " on " in i.title:
        #     if i.categories[0] == "Tanakh" and getattr(i, "base_text_titles", None) and len(i.base_text_titles) == 1:
        #         base_text_title = i.base_text_titles[0]
        #         base_ref = empty_ref.replace(i.title, base_text_title)
        #         if base_ref.find(":") != base_ref.rfind(":"):
        #             base_ref = ":".join(base_ref.split(":")[:-1])
        #         if len(Ref(base_ref).text('he').text) == 0:
        #             print(refs)


with open("manual.csv", 'w') as f:
    writer = csv.writer(f)
    for l in other_links:
        writer.writerow(l)
with open("add_commentary_links_base_problem.csv", 'w') as f:
    writer = csv.writer(f)
    for l in commentary_links_base_prob:
        writer.writerow(l)
with open("add_commentary_links_fine.csv", 'w') as f:
    writer = csv.writer(f)
    for l in commentary_links_fine:
        writer.writerow(l)
with open("add_links_from_text_get_refs.csv", 'w') as f:
    writer = csv.writer(f)
    for l in links_from_text_get_refs_from_string:
        writer.writerow(l)
with open("add_links_from_text_no_refs.csv", 'w') as f:
    writer = csv.writer(f)
    for l in links_from_text_no_ref_in_string:
        writer.writerow(l)

