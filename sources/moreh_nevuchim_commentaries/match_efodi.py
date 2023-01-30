import django

django.setup()

django.setup()
superuser_id = 171118
# import statistics
import csv
from sefaria.model import *
from sefaria.helper.schema import insert_last_child, reorder_children
from sefaria.helper.schema import remove_branch
from sefaria.tracker import modify_bulk_text
from sefaria.helper.category import create_category
from sefaria.system.database import db
import json

def insert_links_to_db(list_of_links):
    for l in list_of_links:

        l.save()

def list_of_dict_to_links(dicts):
    list_of_dicts = []
    for d in dicts:
        list_of_dicts.append(Link(d))
    return list_of_dicts

def dher(text):
    dh = "$$$$$$$$$$$$$$$$$$"
    match = re.search(r'<b>(.*?)</b>', text)
    if match:
        dh = match.group(1)
    if dh == "העשרים":
        dh = "העשרים שכל מחויב המציאות בבחינת עצמו"
    # print(dh)
    return dh

sections = ["Introduction, Letter to R Joseph son of Judah", "Introduction, Prefatory Remarks",
                "Introduction, Introduction",
                "Part 1", "Part 2 Introduction", "Part 2", "Part 3 Introduction", "Part 3"]
# sections = ["Part 2 Introduction", "Part 2", "Part 3 Introduction", "Part 3"]


def local_pipeline():
    from sources.functions import match_ref_interface
    # from linking_utilities.dibur_hamatchil_matcher import *
    links = []
    # for daf in comments:
    #     print(daf)
    #     actual_daf = AddressTalmud.toStr('en', daf)
    #     links += match_ref_interface("Eruvin {}".format(actual_daf), "Chidushei HaMeiri on Eruvin {}".format(actual_daf), comments[daf], lambda x: x.split(), dher)
    # post_link(links)
    for sec in sections:
        print(sec)
        r_string_comm = "Efodi on Guide for the Perplexed, {}".format(sec)
        r_string_base = "Guide for the Perplexed, {}".format(sec)
        if sec == 'Part 1':
            for i in range(1, 76):
                r_string_comm_spec = r_string_comm + " " + str(i)
                r_string_base_spec = r_string_base + ":" + str(i)
                comments = Ref(r_string_comm_spec).text("he")
                links += match_ref_interface(r_string_base_spec, r_string_comm_spec,
                                             comments, lambda x: x.split(), dher)
            continue

        if sec == 'Part 2':
            for i in range(1, 48):
                r_string_comm_spec = r_string_comm + " " + str(i)
                r_string_base_spec = r_string_base + ":" + str(i)
                comments = Ref(r_string_comm_spec).text("he")
                links += match_ref_interface(r_string_base_spec, r_string_comm_spec,
                                             comments, lambda x: x.split(), dher)
            continue

        if sec == 'Part 3':
            for i in range(1, 54):
                r_string_comm_spec = r_string_comm + " " + str(i)
                r_string_base_spec = r_string_base + ":" + str(i)
                comments = Ref(r_string_comm_spec).text("he")
                links += match_ref_interface(r_string_base_spec, r_string_comm_spec,
                                             comments, lambda x: x.split(), dher)
            continue

        comments = Ref(r_string_comm).text("he")
        links += match_ref_interface(r_string_base, r_string_comm,
                                     comments, lambda x: x.split(), dher)

    for l in links:
        # find the last index of the space
        if "Efodi on Guide for the Perplexed, Part 1" in l["refs"][0] or "Efodi on Guide for the Perplexed, Part 2" in \
                l["refs"][0] or "Efodi on Guide for the Perplexed, Part 3" in l["refs"][0]:
            index = l["refs"][0].rfind(" ")

            # replace the last space with a colon
            l["refs"][0] = l["refs"][0][:index] + ":" + l["refs"][0][index + 1:]
    with open("links_list.json", "w") as f:
        # Write the list of dictionaries to the file as JSON
        json.dump(links, f, ensure_ascii=False, indent=2)
    links = list_of_dict_to_links(links)
    insert_links_to_db(links)

def cauldron_pipeline():
    with open('links_list.json') as f:
        links = json.load(f)
    links = list_of_dict_to_links(links)
    insert_links_to_db(links)

def clean():
    query = {"refs": {"$regex" : "Efodi on Guide for the Perplexed"}}
    list_of_links = LinkSet(query).array()
    for l in list_of_links:
        l.delete()

if __name__ == '__main__':
    print("hello world")
    clean()
    cauldron_pipeline()
    # post_link(links)







