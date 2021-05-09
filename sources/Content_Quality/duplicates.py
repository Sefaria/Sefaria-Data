from sources.functions import *
def find_duplicates():
    indices = library.get_indexes_in_category("Tanakh")
    indices += library.get_indexes_in_category("Talmud")
    for i in indices:
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


def find_duplicates_across_daf():
    indices = library.get_indexes_in_category("Tanakh", include_dependant=True)
    indices += library.get_indexes_in_category("Talmud", include_dependant=True)
    for i in indices:
        if " on " in i:
            if not "Rashi" in i and not "Tosafot" in i:
                continue
        i = library.get_index(i)
        vs = i.versionSet()
        segment_refs = i.all_segment_refs()
        category = i.categories[0]
        commentary = " on " in i.title
        for v in vs:
            tc = ""
            prev_ref = None
            for ref in segment_refs:
                new_tc = TextChunk(ref, lang=v.language, vtitle=v.versionTitle)
                if tc == new_tc.text and len(tc) > 4:
                    if ref.normal().endswith(":1") and category == "Talmud" and commentary:
                        print("{},{},{}".format(ref, v.language, v.versionTitle))
                    else:
                        new_tc.text = ""
                        try:
                            new_tc.save(force_save=True)
                            print("Deleting... {}".format(ref.normal()))
                        except Exception as e:
                            print("{} -> {}".format(prev_ref, e))
                tc = new_tc.text
                prev_ref = ref
find_duplicates_across_daf()