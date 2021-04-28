from sources.functions import *
indices = library.get_indexes_in_category("Tanakh")
indices += library.get_indexes_in_category("Talmud")
for i in indices:
    # if "Rashi" not in i and "Tosafot" not in i:
    #     continue
    i = library.get_index(i)
    vs = i.versionSet()
    segment_refs = i.all_segment_refs()
    for v in vs:
        tc = ""
        for ref in segment_refs:
            new_tc = TextChunk(ref, lang=v.language, vtitle=v.versionTitle).text
            if tc == new_tc and len(tc) > 4:
                print("{},{},{}".format(ref, v.language, v.versionTitle))
            tc = new_tc
