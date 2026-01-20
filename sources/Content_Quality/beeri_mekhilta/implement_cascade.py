import django

django.setup()

from sefaria.model import *
from sefaria.helper.schema import cascade
from sources.functions import post_text, post_index, post_link, add_category
import csv
import re


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
    print(prod_ref)
    mapper = ingest_map()
    ranged_ref_list = []
    if prod_ref in mapper:
        cur_beeri_ref_list = mapper[prod_ref]
        if len(cur_beeri_ref_list) > 1:
            cleaned_end_ref = re.sub(r'[a-zA-Z\s\',]', '', cur_beeri_ref_list[len(cur_beeri_ref_list)-1])
            return f"{cur_beeri_ref_list[0]}-{cleaned_end_ref}"
        else:
            return cur_beeri_ref_list[0]
    elif "Mekhilta d'Rabbi Yishmael" in prod_ref:  # Handle ranged refs
        for ref_key in mapper:
            if Ref(ref_key).contains(Ref(prod_ref)):
                if len(mapper[ref_key]) > 1:
                    cleaned_end_ref = re.sub(r'[a-zA-Z\s\',]', '', mapper[ref_key][len(mapper[ref_key])-1])
                    return f"{mapper[ref_key][0]}-{cleaned_end_ref}"
                else:
                    return mapper[ref_key][0]
            elif Ref(prod_ref).contains(Ref(ref_key)):
                ranged_ref_list += mapper[ref_key]
                # print(f"Since {prod_ref} contains {ref_key}, appending {mapper[ref_key]}")
        rr_str = ""
        if ranged_ref_list and len(ranged_ref_list) > 1:
            cleaned_end_ref = re.sub(r'[a-zA-Z\s\',]', '', ranged_ref_list[len(ranged_ref_list)-1])
            rr_str = f"{ranged_ref_list[0]}-{cleaned_end_ref}"
        elif ranged_ref_list:
            rr_str = ranged_ref_list[0]
        return rr_str



def action(segment_str, tref, he_tref, version):
    global prod_refs
    prod_refs.append(tref)


def retrieve_version_text():
    version_query = {"versionTitle": "Mekhilta -- Wikisource",
                     "title": "Mekhilta d'Rabbi Yishmael Old"}
    wiki_version = VersionSet(version_query)
    for v in wiki_version:
        v.walk_thru_contents(action)


def rename_books():
    index_query = {"title": "Mekhilta d'Rabbi Yishmael"}
    index = Index().load(index_query)
    print(f"Retrieved {index.title}")
    index.set_title("Mekhilta d'Rabbi Yishmael Old")
    index.save()
    print(f"Saved and renamed {index.title}")

    index_query = {"title": "Mekhilta DeRabbi Yishmael Beeri"}
    index = Index().load(index_query)
    print(f"Retrieved {index.title}")
    index.set_title("Mekhilta d'Rabbi Yishmael")
    index.save()
    print(f"Saved and renamed {index.title}")


def order_links(refs):
    if "Mekhilta d'Rabbi Yishmael Old" in refs[0]:
        return refs[1], refs[0], True
    return refs[0], refs[1], False


if __name__ == '__main__':

    # TODO - Run this first
    # rename_books()

    # prod_refs = []
    # retrieve_version_text()

    # mapper = ingest_map()
    # for prod_ref in prod_refs:
    #     print(f"Working on {prod_ref}")
    #     cascade(prod_ref, rewriter=lambda beeri_ref: rewriter_function(prod_ref), skip_history=False)

    query = {"refs": {"$regex": "Mekhilta d'Rabbi Yishmael Old"}}
    ls = LinkSet(query)

    generated_by_list_set = []

    print(ls.count())

    # TODO - read in CSV here.
    # old_ref,link_ref,link_type,generated_by,all,status
    # Read in ref, map to new one, ouput all values to create new (but identical minus one column) csv
    print("old_mekhilta_ref, beeri_ref, link_ref, link_type, generated_by, all, status")
    old_ref_list = []
    with open('mekhilta_all_links.csv', newline='') as csvfile:
        all_links = csv.reader(csvfile)
        for row in all_links:
            old_ref = row[0]
            link_ref = row[1]
            link_type = row[2]
            generated_by = row[3]
            all = row[4]
            status = row[5]

            # other_ref, mekhilta_old_ref, from_mekhilta = order_links(link.refs)
            beeri_mekhilta_ref = rewriter_function(old_ref)

            # post_link({'refs': [other_ref, beeri_mekhilta_ref]})
            # generated_by_list_set.append(link.generated_by)
            # exclude automatic
            # if link.generated_by == "add_links_from_text":
            #     print(f"\"{other_ref}\", \"{mekhilta_old_ref}\", \"{beeri_mekhilta_ref}\", True, {from_mekhilta}")
            # elif beeri_mekhilta_ref:
            #     print(f"\"{other_ref}\", \"{mekhilta_old_ref}\", \"{beeri_mekhilta_ref}\", False, {from_mekhilta}")
            if not beeri_mekhilta_ref:
                old_ref_list.append(old_ref)
            else:
                print(f"\"{old_ref}\",\"{beeri_mekhilta_ref}\",\"{link_ref}\",\"{link_type}\",\"{generated_by}\",\"{all}\",\"{status}\"")

        print(f"{len(old_ref_list)} refs need to be dealt with")
        print(old_ref_list)
            # print(set(generated_by_list_set))

