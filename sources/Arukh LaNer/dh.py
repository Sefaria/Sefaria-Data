from sources.functions import *
def baser(xyz):
    return xyz.split(" ")

def dher(x):
    return x

def get_dh(comm, word):
    if word is not None:
        comm = comm.replace(word+".", "").replace(word+":", "").replace(word, "").strip()
    dh_pos = comm.find("""ד"ה""")
    if dh_pos >= 0:
        comm = comm[dh_pos+3:].strip()
    dh = comm.split(".")[0].split(":")[0].strip()
    return dh
def extract_comments(ref, base, prev_type):
    # comms = [x for x in TextChunk(ref, lang='he').text]
    comms = [TextChunk(ref, lang='he').text]
    comm_dict = {f"Tosafot on {base}": [], f"Rashi on {base}": [], base: []}
    for comm in comms:
        if comm.startswith("<b>"):
            comm = re.search("<b>(.*?)</b>", comm).group(1)
        if comm.startswith("""בתוס'"""):
            dh = get_dh(comm, """בתוס'""")
            comm_dict[f"Tosafot on {base}"].append(dh)
            prev_type = f"Tosafot on {base}"
        elif comm.startswith("""בתוספת"""):
            dh = get_dh(comm, """בתוספת""")
            comm_dict[f"Tosafot on {base}"].append(dh)
            prev_type = f"Tosafot on {base}"
        elif comm.startswith('בתוספות'):
            dh = get_dh(comm, 'בתוספות')
            comm_dict[f"Tosafot on {base}"].append(dh)
            prev_type = f"Tosafot on {base}"
        elif comm.startswith('תוספות'):
            dh = get_dh(comm, 'תוספות')
            comm_dict[f"Tosafot on {base}"].append(dh)
            prev_type = f"Tosafot on {base}"
        elif comm.startswith("""ברש"י"""):
            dh = get_dh(comm, """ברש"י""")
            comm_dict[f"Rashi on {base}"].append(dh)
            prev_type = f"Rashi on {base}"
        elif comm.startswith("""רש"י"""):
            dh = get_dh(comm, """רש"י""")
            comm_dict[f"Rashi on {base}"].append(dh)
            prev_type = f"Rashi on {base}"
        elif comm.startswith("""בא"ד"""):
            dh = get_dh(comm, """בא"ד""")
            comm_dict[prev_type].append(dh)
        else:
            comm = comm.replace("בגמרא", "").replace("""בד"ה""", "").replace("""ד"ה""", "")
            dh = get_dh(comm, None)
            comm_dict[base].append(dh)
            prev_type = base
    for k in list(comm_dict.keys()):
        if len(comm_dict[k]) == 0:
            comm_dict.pop(k)
    return (comm_dict, prev_type)



#def match_ref_interface(base_ref, comm_ref, comments, base_tokenizer, dh_extract_method, vtitle="", generated_by="", padding=False):
all_results = []
LinkSet({"generated_by": "Arukh_LaNer_linker"}).delete()
for t in ["Arukh LaNer on Sanhedrin", "Arukh LaNer on Rosh Hashanah"]:
    prev_type = ""
    for ref in library.get_index(t).all_segment_refs():
        orig_base_ref = ref.section_ref().normal().replace("Arukh LaNer on ", "")
        comms, prev_type = extract_comments(ref, orig_base_ref, prev_type)
        for base_ref in comms:
            try:
                results = match_ref(TextChunk(Ref(base_ref), lang='he'), comms[base_ref], lambda x: x.split())
                Link({"refs": [results['matches'][0].normal(), ref.normal()], "auto": True, "type": "Commentary",
                                "generated_by": "Arukh_LaNer_linker"}).save()
            except Exception as e:
                pass


print(LinkSet({"generated_by": "Arukh_LaNer_linker"}).count())