import django

django.setup()

from sefaria.model import *
import csv

from source_sheet_map_utilities import write_to_json, get_sheets_quoting_mekhilta, retrieve_sheets_collection


# TODO: Have JSON file go to immediate subdir vs parent dir

def ingest_map():
    with open("/Users/sefaria/Sefaria-Data/sources/Content_Quality/beeri_mekhilta/full_mapping.csv", "r") as f:
        reader = csv.DictReader(f)
        map = {}
        for row in reader:
            if row["prod_ref"] in map:
                map[row["prod_ref"]].append(row["beeri_ref"])
            else:
                map[row["prod_ref"]] = [row["beeri_ref"]]
    return map


def make_prod_ref_old(prod_ref):
    idx = prod_ref.find("Yishmael")
    idx = idx + len("Yishmael")
    new_prod_ref = prod_ref[:idx] + " Old" + prod_ref[idx:]
    return new_prod_ref


def rewriter_function(prod_ref, mapper, uuid=None, sheet_id=None):
    if "Old" not in prod_ref:  # i.e. prod ref hasn't been affected by name change
        prod_ref = make_prod_ref_old(prod_ref)
    # If a segment-level ref
    if prod_ref and prod_ref in mapper:
        cur_beeri_ref_list = mapper[prod_ref]

        # If the segment-level ref maps to multiple Beeri refs
        if len(cur_beeri_ref_list) > 1:
            first_ref = Ref(cur_beeri_ref_list[0])
            last_ref = Ref(cur_beeri_ref_list[len(cur_beeri_ref_list) - 1])
            ranged_ref = first_ref.to(last_ref)
            return ranged_ref.normal()

        # If the segment-level ref maps to a single Beeri ref
        else:
            return cur_beeri_ref_list[0]

    elif prod_ref in ["Mekhilta DeRabbi Yishmael Old 22",
                      "Mekhilta DeRabbi Yishmael Old 19",
                      "Mekhilta DeRabbi Yishmael Old 20",
                      "Mekhilta DeRabbi Yishmael Old 17",
                      "Mekhilta DeRabbi Yishmael Old 1",
                      "Mekhilta DeRabbi Yishmael Old 3",
                      "Mekhilta DeRabbi Yishmael Old 2"]:
        print(f"Sheet ID: {sheet_id} -- {prod_ref} needs to be handled manually for (user: {uuid})")
        return ""

    # If a section or book level ref, determine the mapping based on the segment refs within
    elif prod_ref and (not Ref(prod_ref).is_segment_level() or Ref(prod_ref).is_range()):
        segment_ranged_ref = Ref(prod_ref).as_ranged_segment_ref()
        start_tref = segment_ranged_ref.starting_ref().normal()
        end_tref = segment_ranged_ref.ending_ref().normal()
        if start_tref in mapper and end_tref in mapper:
            first_oref = Ref(mapper[start_tref][0])
            last_oref = Ref(mapper[end_tref][0])
            ranged_ref = first_oref.to(last_oref)
            return ranged_ref.normal()
        print(f"Sheet ID: {sheet_id} -- {prod_ref} not a valid ref (user: {uuid})")
        return ""

    print(f"Sheet ID: {sheet_id} -- {prod_ref} not a valid ref (user: {uuid})")
    return ""


if __name__ == '__main__':


    mapping = ingest_map()
    collection = retrieve_sheets_collection()
    result = get_sheets_quoting_mekhilta(collection)

    # Results map
    results = []

    for document in result:
        uuid = document["owner"]
        sheet_id = document["id"]
        sources = document["sources"]
        mapper_dict = {"uuid": uuid, "sheet_id": sheet_id, "newIncludedRefs": [], "newExpandedRefs": [],
                       "newSources": []}

        for ref in document["includedRefs"]:
            if "Mekhilta DeRabbi Yishmael Old" in ref:
                print(ref)
                mapper_dict["newIncludedRefs"].append(rewriter_function(ref, mapping, uuid, sheet_id))
            else:
                mapper_dict["newIncludedRefs"].append(ref)

        for ref in document["expandedRefs"]:
            if "Mekhilta DeRabbi Yishmael Old" in ref:
                mapped_ref = rewriter_function(ref, mapping, uuid, sheet_id)
                if mapped_ref:
                    ref_list = Ref(mapped_ref).all_segment_refs()
                    for r in ref_list:
                        mapper_dict["newExpandedRefs"].append(r.normal())
            else:
                mapper_dict["newExpandedRefs"].append(ref)

        for source_dict in sources:

            if "ref" in source_dict:
                ref = source_dict["ref"]

                if "Mekhilta DeRabbi Yishmael Old" in ref:
                    new_ref_dict = source_dict
                    en_ref = rewriter_function(ref, mapping, uuid, sheet_id)
                    oref = Ref(en_ref)

                    if oref.index:  # exclude weird refs like Mekhilta 22 (ask, since it's a Nechama sheet?)
                        new_ref_dict["ref"] = oref.normal(lang="en")
                        new_ref_dict["heRef"] = oref.normal(lang="he")
                        mapper_dict["newSources"].append(new_ref_dict)
                    else:
                        mapper_dict["newSources"].append(new_ref_dict)
                else:
                    mapper_dict["newSources"].append(source_dict)

        print(f"Rewriting Mekhilta refs for Sheet ID: {sheet_id}")
        results.append(mapper_dict)

    write_to_json(mapper_dictionary=results)
    print(f"{len(results)} sheets written to JSON")
