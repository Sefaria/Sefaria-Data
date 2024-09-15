from sources.functions import *
def baser(xyz):
    return xyz.split(" ")

def dher(x):
    return x

def get_dh(comm, word):
    if word is not None:
        comm = re.split(rf"{word}[.:]{0,1}", comm)[-1].strip()
    dh_pos = comm.find("""ד"ה""")
    if dh_pos >= 0:
        comm = comm[dh_pos+3:].strip()
    dh = comm.split(".")[0].split(":")[0].split("וכו'")[0].strip()
    if dh.count(" ") > 5:
        return " ".join(dh.split()[:5])
    return dh
def extract_comments(ref, base, prev_type, prev_match):
    # comms = [x for x in TextChunk(ref, lang='he').text]
    comms = [TextChunk(ref, lang='he').text]
    comm_dict = {f"Tosafot on {base}": [], f"Rashi on {base}": [], base: []}
    if prev_type not in comm_dict and len(prev_type) > 0:
        keys = list(comm_dict.keys())
        if "Tosafot" in prev_type:
            prev_type = [k for k in keys if "Tosafot" in k][0]
        elif "Rashi" in prev_type:
            prev_type = [k for k in keys if "Rashi" in k][0]
        else:
            prev_type = [k for k in keys if "Tosafot" not in k and "Rashi" not in k][0]
    for comm in comms:
        first_5_words = " ".join(comm.split()[:5])
        if comm.startswith("<b>"):
            comm = re.search("<b>(.*?)</b>", comm).group(1)
        if "תוס'" in first_5_words:
            dh = get_dh(comm, "תוס'")
            comm_dict[f"Tosafot on {base}"].append(dh)
            prev_type = f"Tosafot on {base}"
        elif """בתוס'""" in first_5_words:
            dh = get_dh(comm, """בתוס'""")
            comm_dict[f"Tosafot on {base}"].append(dh)
            prev_type = f"Tosafot on {base}"
        elif """בתוספת""" in first_5_words:
            dh = get_dh(comm, """בתוספת""")
            comm_dict[f"Tosafot on {base}"].append(dh)
            prev_type = f"Tosafot on {base}"
        elif 'בתוספות' in first_5_words:
            dh = get_dh(comm, 'בתוספות')
            comm_dict[f"Tosafot on {base}"].append(dh)
            prev_type = f"Tosafot on {base}"
        elif 'תוספות' in first_5_words:
            dh = get_dh(comm, 'תוספות')
            comm_dict[f"Tosafot on {base}"].append(dh)
            prev_type = f"Tosafot on {base}"
        elif """ברש"י""" in first_5_words:
            dh = get_dh(comm, """ברש"י""")
            comm_dict[f"Rashi on {base}"].append(dh)
            prev_type = f"Rashi on {base}"
        elif """רש"י""" in first_5_words:
            dh = get_dh(comm, """רש"י""")
            comm_dict[f"Rashi on {base}"].append(dh)
            prev_type = f"Rashi on {base}"
        elif """בא"ד""" in first_5_words:
            return ({}, prev_type)
        elif """בד"ה""" in first_5_words:
            dh = get_dh(comm, """בד"ה""")
            comm_dict[prev_type].append(dh)
        elif 'ד"ה' in first_5_words:
            dh = get_dh(comm, 'ד"ה')
            comm_dict[prev_type].append(dh)
        elif """במתניתן""" in first_5_words or """בגמרא""" in first_5_words:
            dh = comm.replace("""במתניתן""", "").replace("""בגמרא""", "").replace(":", "").replace(".", "").strip()
            comm_dict[base].append(dh)
            prev_type = base
        # if comm.startswith("תוס'"):
        #     dh = get_dh(comm, "תוס'")
        #     comm_dict[f"Tosafot on {base}"].append(dh)
        #     prev_type = f"Tosafot on {base}"
        # elif comm.startswith("""בתוס'"""):
        #     dh = get_dh(comm, """בתוס'""")
        #     comm_dict[f"Tosafot on {base}"].append(dh)
        #     prev_type = f"Tosafot on {base}"
        # elif comm.startswith("""בתוספת"""):
        #     dh = get_dh(comm, """בתוספת""")
        #     comm_dict[f"Tosafot on {base}"].append(dh)
        #     prev_type = f"Tosafot on {base}"
        # elif comm.startswith('בתוספות'):
        #     dh = get_dh(comm, 'בתוספות')
        #     comm_dict[f"Tosafot on {base}"].append(dh)
        #     prev_type = f"Tosafot on {base}"
        # elif comm.startswith('תוספות'):
        #     dh = get_dh(comm, 'תוספות')
        #     comm_dict[f"Tosafot on {base}"].append(dh)
        #     prev_type = f"Tosafot on {base}"
        # elif comm.startswith("""ברש"י"""):
        #     dh = get_dh(comm, """ברש"י""")
        #     comm_dict[f"Rashi on {base}"].append(dh)
        #     prev_type = f"Rashi on {base}"
        # elif comm.startswith("""רש"י"""):
        #     dh = get_dh(comm, """רש"י""")
        #     comm_dict[f"Rashi on {base}"].append(dh)
        #     prev_type = f"Rashi on {base}"
        # elif comm.startswith("""בא"ד"""):
        #     return ({}, prev_type)
        # elif comm.startswith("""בד"ה"""):
        #     dh = get_dh(comm, """בד"ה""")
        #     comm_dict[prev_type].append(dh)
        # elif comm.startswith('ד"ה'):
        #     dh = get_dh(comm, 'ד"ה')
        #     comm_dict[prev_type].append(dh)
        # elif comm.startswith("""במתניתן""") or comm.startswith("""בגמרא"""):
        #     dh = comm.replace("""במתניתן""", "").replace("""בגמרא""", "").replace(":", "").replace(".", "").strip()
        #     comm_dict[base].append(dh)
        #     prev_type = base
        else:
            comm = comm.replace("בגמרא", "").replace("""בד"ה""", "").replace("""ד"ה""", "").strip()
            dh = get_dh(comm, None)
            comm_dict[base].append(dh)
            prev_type = base
    for k in list(comm_dict.keys()):
        if len(comm_dict[k]) == 0:
            comm_dict.pop(k)
    return (comm_dict, prev_type)



#def match_ref_interface(base_ref, comm_ref, comments, base_tokenizer, dh_extract_method, vtitle="", generated_by="", padding=False):
all_results = []
# generated_by = "Arukh_LaNer_linker"
# titles = ["Arukh LaNer on Sanhedrin", "Arukh LaNer on Rosh Hashanah"]
title_part = "Tziyyun LeNefesh Chayyah"
collective = 'Tzelach'
titles = library.get_indices_by_collective_title(collective)
generated_by = "Tziyun_LaNefesh_linker"
LinkSet({"generated_by": generated_by}).delete()
possible_matches = 0
for t in titles:
    prev_type = ""
    prev_match = None
    for ref in library.get_index(t).all_segment_refs():
        if "Introduction" in ref.normal() or "Foreword" in ref.normal():
            continue
        possible_matches += 1
        orig_base_ref = ref.section_ref().normal().replace(title_part+ " on ", "")
        comms, prev_type = extract_comments(ref, orig_base_ref, prev_type, prev_match)
        if len(comms) == 0:
            assert prev_match is not None
            Link({"refs": [prev_match, ref.normal()], "auto": True, "type": "Commentary",
                  "generated_by": generated_by}).save()
            if " on " in prev_match:
                real_base_ref = Ref(prev_match).section_ref().normal().replace("Rashi on ", "").replace(
                    "Tosafot on ", "")
                Link({"refs": [real_base_ref, ref.normal()], "auto": True, "type": "Commentary",
                      "generated_by": generated_by}).save()
        for base_ref in comms:
            try:
                results = match_ref(TextChunk(Ref(base_ref), lang='he', vtitle='William Davidson Edition - Aramaic'), comms[base_ref], lambda x: x.split())
                if results['matches'][0] is not None:
                    prev_match = results['matches'][0].normal()
                    if " on " in results['matches'][0].normal():
                        real_base_ref = results['matches'][0].section_ref().normal().replace("Rashi on ", "").replace("Tosafot on ", "")
                        Link({"refs": [real_base_ref, ref.normal()], "auto": True, "type": "Commentary",
                             "generated_by": generated_by}).save()
                    Link({"refs": [results['matches'][0].normal(), ref.normal()], "auto": True, "type": "Commentary",
                                "generated_by": generated_by}).save()
                else:
                    print(dher(comms[base_ref]))
            except Exception as e:
                print(e)


print(LinkSet({"generated_by": generated_by}).count())
print(possible_matches)