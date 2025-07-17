import django

django.setup()

from sefaria.model import *
from sefaria.helper.schema import cascade
import csv


def rename_books():
    # Todo - cascade name change? Index should cascade...
    index_query = {"title": "Mekhilta DeRabbi Yishmael"}
    index = Index().load(index_query)
    print(f"Retrieved {index.title}")
    index.set_title("Old Mekhilta d'Rabbi Yishmael")
    index.save()
    print(f"Saved and renamed {index.title}")

    index_query = {"title": "Mekhilta DeRabbi Yishmael Beeri"}
    index = Index().load(index_query)
    print(f"Retrieved {index.title}")
    index.set_title("Mekhilta d'Rabbi Yishmael")
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


def rewriter_function(prod_ref):
    mapper = ingest_map()
    print(prod_ref)

    # If a segment-level ref
    if prod_ref in mapper:
        cur_beeri_ref_list = mapper[prod_ref]

        # If the segment-level ref maps to multiple Beeri refs
        if len(cur_beeri_ref_list) > 1:
            first_ref = cur_beeri_ref_list[0]
            last_ref = cur_beeri_ref_list[len(cur_beeri_ref_list) - 1]
            ranged_ref = Ref(first_ref).to(last_ref)
            return ranged_ref.normal()

        # If the segment-level ref maps to a single Beeri ref
        else:
            return cur_beeri_ref_list[0]

    # If a section or book level ref, determine the mapping based on the segment refs within
    elif not Ref(prod_ref).is_segment_level():
        segment_ranged_ref = Ref(prod_ref).as_ranged_segment_ref()
        if segment_ranged_ref.starting_ref() in mapper and segment_ranged_ref.ending_ref() in mapper:
            first_ref = mapper[segment_ranged_ref.starting_ref()]
            last_ref = mapper[segment_ranged_ref.ending_ref()]
            ranged_ref = Ref(first_ref).to(last_ref)
            return ranged_ref.normal()
        else:
            # Catches weird/wrong refs, like Mekhilta 1, which does not exist - but according to the code will become Mekhilta 1:1:1
            print(f"ERROR: {prod_ref} was not handled by rewriter")
            return ""
    else:
        print(f"ERROR: {prod_ref} was not handled by rewriter")
        return ""


if __name__ == '__main__':
    # Run the following function once on DB refresh, make sure Mekhilta copied from Piaczena DB (index & text)
    rename_books()

    # cascade("Mekhilta d'Rabbi Yishmael Old", rewriter=rewriter_function, skip_history=False)
