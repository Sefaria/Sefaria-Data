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
def extract_comments(ref, base):
    comms = [x for x in TextChunk(ref, lang='he').text]
    comm_dict = {f"Tosafot on {base}": [], f"Rashi on {base}": [], base: []}
    prev_type = ""
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
    return comm_dict



#def match_ref_interface(base_ref, comm_ref, comments, base_tokenizer, dh_extract_method, vtitle="", generated_by="", padding=False):
results = []
for t in ["Arukh LaNer on Sanhedrin", "Arukh LaNer on Rosh Hashanah"]:
    for ref in library.get_index(t).all_section_refs():
        orig_base_ref = ref.normal().replace("Arukh LaNer on ", "")
        comms = extract_comments(ref, orig_base_ref)
        for base_ref in comms:
            try:
                results += match_ref_interface(base_ref, ref.normal(), comms[base_ref], baser, dher)
            except:
                print(base_ref)

LinkSet({"generated_by": "Arukh_LaNer_linker"}).delete()
for link in results:
    link['generated_by'] = "Arukh_LaNer_linker"
    Link(link).save()
print(LinkSet({"generated_by": "Arukh_LaNer_linker"}).count())