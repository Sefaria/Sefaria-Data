import django
from pymongo import MongoClient

django.setup()

from sefaria.model import *
import csv


# TODO: Fix rewriter function to handle errors
# TODO: Also need to handle 'sources' in DB
# TODO: conditional debug on uuid, why the rewriter function is failing, and rewrite to fix

def ingest_map():
    with open("full_mapping.csv", "r") as f:
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


def rewriter_function(prod_ref, mapper, uuid=None, id=None):
    set_list = []
    if "old" not in prod_ref:  # i.e. prod ref hasn't been affected by name change
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

    ## TODO - maybe take this out so we can catch segment levels (trying to catch upper section, but only one instance)
    elif prod_ref in ["Mekhilta d'Rabbi Yishmael Old 22",
                      "Mekhilta d'Rabbi Yishmael Old 19",
                      "Mekhilta d'Rabbi Yishmael Old 20",
                      "Mekhilta d'Rabbi Yishmael Old 17",
                      "Mekhilta d'Rabbi Yishmael Old 1",
                      "Mekhilta d'Rabbi Yishmael Old 3",
                      "Mekhilta d'Rabbi Yishmael Old 2"]:
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

    # For each source sheet quoting mekhilta
    # capture the UUID, the old_ref and the new_ref
    # Generate a CSV that can be used on prod with a script to replace.

    local_uri = "mongodb://localhost:27017"

    # Connect to MongoDB
    client = MongoClient(local_uri)
    db = client['sefaria']
    collection = db['sheets']

    # Define the search term
    search_term = 'Mekhilta d\'Rabbi Yishmael'

    # Query the collection
    query = {"includedRefs": {"$regex": search_term}}
    result = collection.find(query)

    # Results map
    results = []

    # Print or process the result
    for document in result:
        uuid = document["owner"]
        sheet_id = document["id"]
        mapper_dict = {"uuid": uuid, "sheet_id": sheet_id, "includedRefsMap": [], "expandedRefsMap": []}

        for ref in document["includedRefs"]:
            if "Mekhilta d'Rabbi Yishmael" in ref:
                mapper_dict["includedRefsMap"].append(
                    {"old_ref": ref, "new_ref": rewriter_function(ref, mapping, uuid, sheet_id)})

        for ref in document["expandedRefs"]:
            if "Mekhilta d'Rabbi Yishmael" in ref:
                mapped_ref = rewriter_function(ref, mapping, uuid, sheet_id)
                if mapped_ref:
                    ref_list = Ref(mapped_ref).all_segment_refs()
                    tref_list = []
                    for r in ref_list:
                        tref_list.append(r.normal())

                mapper_dict["expandedRefsMap"].append({"old_ref": ref, "new_refs": ref_list})

        results.append(mapper_dict)

    # Close the MongoDB connection
    client.close()
    print("FINISHED")
    # print(results)
