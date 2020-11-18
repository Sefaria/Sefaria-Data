from sources.functions import *

indices = library.get_indexes_in_category("Rashash", include_dependant=True)[63:]
rashash_to_daf = {}
rashash_to_rashi = {}
rashash_to_tosafot = {}
total_rashash = {}
for i in indices:
    i = library.get_index(i)
    rashash_to_daf[i.title] = 0
    rashash_to_rashi[i.title] = 0
    rashash_to_tosafot[i.title] = 0
    library.refresh_index_record_in_cache(i)
    vs = VersionState(index=i)
    vs.refresh()
    library.update_index_in_toc(i)
    refs = i.all_segment_refs()
    total_rashash[i.title] = len(refs)
    base = i.title.replace("Rashash on ", "")
    for ref in refs:
        for l in LinkSet(ref):
            refs = l.refs
            rashash_ref_index = 0 if refs[0].startswith("Rashash") else 1
            other_ref_index = 1 - rashash_ref_index
            other_ref = refs[other_ref_index]
            rashash_ref = refs[rashash_ref_index]
            if other_ref.startswith("Tosafot"):
                rashash_to_tosafot[i.title] += 1
            elif other_ref.startswith("Rashi"):
                rashash_to_rashi[i.title] += 1
            elif other_ref.startswith(base):
                rashash_to_daf[i.title] += 1

print("Tractate, % Matched to Daf, % Matched to Rashi, % Matched to Tosafot, Total Segments in Tractate")
for k in rashash_to_rashi:
    print("{},{},{},{},{}".format(k, round(100.0*float(rashash_to_daf[k]/total_rashash[k])),
                                               round(100.0*float(rashash_to_rashi[k]/total_rashash[k])),
                                               round(100.0*float(rashash_to_tosafot[k]/total_rashash[k])), total_rashash[k]))



