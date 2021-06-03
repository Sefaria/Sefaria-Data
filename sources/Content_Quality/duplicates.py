from sources.functions import *
# def find_duplicates():
#     indices = library.get_indexes_in_category("Tanakh")
#     indices += library.get_indexes_in_category("Talmud")
#     for i in indices:
#         i = library.get_index(i)
#         vs = i.versionSet()
#         segment_refs = i.all_segment_refs()
#         for v in vs:
#             tc = ""
#             for ref in segment_refs:
#                 new_tc = TextChunk(ref, lang=v.language, vtitle=v.versionTitle).text
#                 if tc == new_tc and len(tc) > 4:
#                     print("{},{},{}".format(ref, v.language, v.versionTitle))
#                 tc = new_tc


def find_duplicates_across_daf():
    indices = library.get_indexes_in_category("Tanakh", include_dependant=True)
    indices += library.get_indexes_in_category("Talmud", include_dependant=True)
    for i in indices:
        if not "Rashi" in i and not "Tosafot" in i:
            continue
        i = library.get_index(i)
        vs = i.versionSet()
        section_refs = i.all_section_refs()
        for v in vs:
            for sec_ref in section_refs:
                prev = ""
                new_sec_tc_text = []
                change = False
                sec_tc = TextChunk(sec_ref, lang=v.language, vtitle=v.versionTitle)
                for line in sec_tc.text:
                    if len(prev.strip()) > 0 and line == prev:
                        change = True
                    else:
                        new_sec_tc_text.append(line)
                    prev = line
                if change:
                    print("***")
                    print(sec_ref)
                    sec_tc.text = new_sec_tc_text
                    sec_tc.save(force_save=True)

find_duplicates_across_daf()