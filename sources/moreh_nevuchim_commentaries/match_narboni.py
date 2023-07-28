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
import re


def extract_last_number(string):
    match = re.findall(r'\d+', string)
    if match:
        return int(match[-1])
    else:
        return None

def insert_links_to_db(list_of_links):
    for l in list_of_links:

        l.save()

def list_of_dict_to_links(dicts):
    list_of_dicts = []
    for d in dicts:
        list_of_dicts.append(Link(d))
    return list_of_dicts

def dher(text):
    # match = re.search(r'<b>(.*?)</b>', text)
    # if match:
    #     dh = match.group(1)
    text = text.replace('<b>', "")
    text = text.replace('</b>', "")
    text = text.split(" ")
    dh  = " ".join(text[:4])
    # print(dh)
    return dh


sections = ["Part 1", "Part 2 Introduction", "Part 2", "Part 3 Introduction", "Part 3"]
# sections = ["Part 2 Introduction", "Part 2", "Part 3 Introduction", "Part 3"]


def local_pipeline():
    from sources.functions import match_ref_interface
    # from linking_utilities.dibur_hamatchil_matcher import *
    links = []

    for sec in sections:
        print(sec)
        r_string_comm = "Narboni on Guide for the Perplexed, {}".format(sec)
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
        if "Narboni on Guide for the Perplexed, Part 1" in l["refs"][0] or "Crescas on Guide for the Perplexed, Part 2" in \
                l["refs"][0] or "Narboni on Guide for the Perplexed, Part 3" in l["refs"][0]:
            index = l["refs"][0].rfind(" ")

            # replace the last space with a colon
            l["refs"][0] = l["refs"][0][:index] + ":" + l["refs"][0][index + 1:]
    with open("narboni_dh_links.json", "w") as f:
        # Write the list of dictionaries to the file as JSON
        json.dump(links, f, ensure_ascii=False, indent=2)
    links = list_of_dict_to_links(links)
    insert_links_to_db(links)

def cauldron_pipeline():
    with open('narboni_dh_links.json') as f:
        links = json.load(f)
    links = list_of_dict_to_links(links)
    insert_links_to_db(links)

def clean():
    query = {"refs": {"$regex" : "Narboni on Guide for the Perplexed"}}
    # query = {"refs": {"$regex": "Narboni on Guide for the Perplexed"},
    #          "generated_by": "Guide for the Perplexed_to_Narboni"}
    list_of_links = LinkSet(query).array()
    for l in list_of_links:
        print(l)
        l.delete()
def exists_with_ref_x(list_of_dicts, x):
    for d in list_of_dicts:
        if d["refs"][0] == x:
            # return d
            return d
    return None

def check_neighbors(links, x, base_txt_ref):
    for d in list_of_dicts:
        if d["refs"][0] == x:
            # return d
            return d
    return None

def prev_element(lst, element):
    index = lst.index(element)
    if index > 0:
        return lst[index - 1]
    else:
        return None

def next_element(lst, element):
    index = lst.index(element)
    if index + 1 < len(lst):
        return lst[index+1]
    else:
        return None

def trim_last_num(string):
    match = re.search(r'\d+$', string)
    if match:
        string = string[: -len(match.group(0))]
    return string

def extract_last_number(string):
    return int(re.findall(r'\d+', string)[-1])
def replace_last_number(s, x):
    return re.sub(r'\d+(?=$)', str(x), s)
def find_ref_in_list(ref_string, list_of_refs):
    for ref in list_of_refs:
        if ref.tref == ref_string:
            return ref

    return None




def create_report():
    query = {"refs": {"$regex": "Narboni on Guide for the Perplexed"}}
    list_of_links = LinkSet(query).array()
    list_of_tuples = [("Narboni", "Guide for the Perplexed")]
    for sec in sections:
        r_string_comm = "Narboni on Guide for the Perplexed, {}".format(sec)
        r_string_base = "Guide for the Perplexed, {}".format(sec)
        all_refs_for_sec = Ref(r_string_comm).all_segment_refs()

        for r in all_refs_for_sec:

            basetext_linked_refs = [l.refs[0] for l in list_of_links if r.normal() == l.refs[1]] #+ [l.refs[1] for l in list_of_links if r_string_base in l.refs[1]]
            separator = ", "
            basetext_linked_refs_string = separator.join(basetext_linked_refs)
            list_of_tuples.append((r, basetext_linked_refs_string))
    with open("narboni_report.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(list_of_tuples)


def add_links_manually_to_db(list_of_ref_pairs): #first crescas second guide
    links = []
    for pair in list_of_ref_pairs:
        links.append({
            "refs": [
                pair[0],
                pair[1]
            ],
            "generated_by": "Guide for the Perplexed_to_Narboni",
            "type": "Commentary",
            "auto": True
        })

    links = list_of_dict_to_links(links)
    insert_links_to_db(links)

def add_missing_links(): #first crescas second guide
    new_links = []
    query = {"refs": {"$regex": "Narboni on Guide for the Perplexed"}}
    list_of_links = LinkSet(query).array()
    for sec in sections:
        r_string_comm = "Narboni on Guide for the Perplexed, {}".format(sec)
        r_string_base = "Guide for the Perplexed, {}".format(sec)
        all_refs_for_sec = Ref(r_string_comm).all_segment_refs()
        for r in all_refs_for_sec:
            if len([link for link in list_of_links if r.normal() == link.refs[1]]) == 0:
                print("hi")
                new_links.append({
                    "refs": [
                        Ref(trim_last_num(" ".join(r.normal().split()[2:]))[:-1]).as_ranged_segment_ref().normal(),
                        r.normal()
                    ],
                    "generated_by": "Guide for the Perplexed_to_Narboni",
                    "type": "Commentary",
                    "auto": True
                })
    new_links = list_of_dict_to_links(new_links)
    insert_links_to_db(new_links)

            #
            # basetext_linked_refs = [l.refs[0] for l in list_of_links if r.normal() == l.refs[1]]  # + [l.refs[1] for l in list_of_links if r_string_base in l.refs[1]]
            # separator = ", "
            # basetext_linked_refs_string = separator.join(basetext_linked_refs)


    #
    #
    # for pair in list_of_ref_pairs:
    #     links.append({
    #         "refs": [
    #             pair[0],
    #             pair[1]
    #         ],
    #         "generated_by": "Guide for the Perplexed_to_Narboni",
    #         "type": "Commentary",
    #         "auto": True
    #     })
    #
    # links = list_of_dict_to_links(links)
    # insert_links_to_db(links)



if __name__ == '__main__':
    print("hello world")
    # clean()
    # local_pipeline()
    # create_report()
    cauldron_pipeline()
    add_missing_links()
    print("hi")


    # post_link(links)







