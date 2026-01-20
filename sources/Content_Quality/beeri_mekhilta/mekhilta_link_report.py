import django

django.setup()

from sefaria.model import *
import csv
from beeri_utilities import write_to_csv


def rename_books():
    # Todo - cascade name change? Index should cascade...
    # index_query = {"title": "Mekhilta DeRabbi Yishmael"}
    # index = Index().load(index_query)
    # print(f"Retrieved {index.title}")
    # index.set_title("Mekhilta d'Rabbi Yishmael Old")
    # index.save()
    # print(f"Saved and renamed {index.title}")

    index_query = {"title": "Mekhilta DeRabbi Yishmael Beeri"}
    index = Index().load(index_query)
    print(f"Retrieved {index.title}")
    index.set_title("Mekhilta DeRabbi Yishmael")
    index.save()
    print(f"Saved and renamed {index.title}")


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


def rewriter_function(prod_ref, mapper):
    # If a segment-level ref
    if prod_ref in mapper:
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

    # If a section or book level ref, determine the mapping based on the segment refs within
    elif not Ref(prod_ref).is_segment_level() or Ref(prod_ref).is_range():
        segment_ranged_ref = Ref(prod_ref).as_ranged_segment_ref()
        start_tref = segment_ranged_ref.starting_ref().normal()
        end_tref = segment_ranged_ref.ending_ref().normal()
        if start_tref in mapper and end_tref in mapper:
            first_oref = Ref(mapper[start_tref][0])
            last_oref = Ref(mapper[end_tref][0])
            if first_oref.book == last_oref.book:
                ranged_ref = first_oref.to(last_oref)
                return ranged_ref.normal()
        return f"ERROR: {prod_ref}"

    return f"ERROR: {prod_ref}"


if __name__ == '__main__':
    # Run the following function once on DB refresh, make sure Mekhilta copied from Piaczena DB (index & text)
    # Can't both be d', one needs to be De, because of the way the regex search works
    # rename_books()

    print("old_mekhilta_ref,beeri_mekhilta_ref,other_text_ref,type,generated_by,all,status")

    errors = []
    results = []
    mapper = ingest_map()

    with open("mekhilta_all_links.csv", "r") as f:
        reader = csv.DictReader(f)
        map = {}
        for row in reader:
            mlink = row["mlink"]
            new_link = rewriter_function(mlink, mapper)
            olink = rewriter_function(row["other_link"], mapper) if "Mekhilta DeRabbi Yishmael" in row[
                "other_link"] else row["other_link"]
            link_type = row["type"]
            generated_by = row["generated_by"]

            if "ERROR" in new_link:
                errors.append(row)
            else:
                results.append({"old_ref": mlink,
                                "beeri_ref": new_link,
                                "other_ref": olink,
                                "type": link_type,
                                "generated_by": generated_by})

    print(f"Error count: {len(errors)}")

    print("old_mekhilta_ref,other_text_ref,type,generated_by,all,status")
    # for e in errors:
    #     print(f"{e['mlink']},{e['other_link']},{e['type']},{e['generated_by']}")

    write_to_csv("mekhilta_link_report_qa_manual.csv", errors)
    write_to_csv("mekhilta_link_report_qa.csv", results)
