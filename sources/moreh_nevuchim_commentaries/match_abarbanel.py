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
    dh = "$$$$$$$$$$$$$$$$$$"
    match = re.search(r'<b>(.*?)</b>', text)
    if match:
        dh = match.group(1)
        if "." in dh:
            dh = dh.split(".", 1)[0]
        dh = dh.replace("וכו", "")
        dh = dh.replace("'", "")

    # print(dh)
    return dh
def simple_tokenizer(text):
    """
    A simple tokenizer that splits text into tokens by whitespace,
    and removes apostrophes and periods from the tokens.
    """
    # Replace apostrophes and periods with empty strings
    text = text.replace("'", "")
    text = text.replace(".", "")
    text = text.replace("׳", "")
    text = text.replace("–", "")
    text = text.replace(";", "")
    # Split the text into tokens by whitespace
    tokens = text.split()
    return tokens

sections = ["Introduction, Letter to R Joseph son of Judah", "Introduction, Prefatory Remarks",
                "Introduction, Introduction",
                "Part 1", "Part 2", "Part 3"]
# sections = ["Part 2 Introduction", "Part 2", "Part 3 Introduction", "Part 3"]


def local_pipeline():
    from sources.functions import match_ref_interface
    # from linking_utilities.dibur_hamatchil_matcher import *
    links = []

    for sec in sections:
        print(sec)
        r_string_comm = "Abarbanel on Guide for the Perplexed, {}".format(sec)
        r_string_base = "Guide for the Perplexed, {}".format(sec)
        if sec == 'Part 1':
            for i in range(1, 76):
                r_string_comm_spec = r_string_comm + " " + str(i)
                r_string_base_spec = r_string_base + ":" + str(i)
                comments = Ref(r_string_comm_spec).text("he")
                links += match_ref_interface(r_string_base_spec, r_string_comm_spec,
                                             comments, simple_tokenizer, dher)
            continue

        if sec == 'Part 2':
            for i in range(1, 48):
                r_string_comm_spec = r_string_comm + " " + str(i)
                r_string_base_spec = r_string_base + ":" + str(i)
                comments = Ref(r_string_comm_spec).text("he")
                links += match_ref_interface(r_string_base_spec, r_string_comm_spec,
                                             comments, simple_tokenizer, dher)
            continue

        if sec == 'Part 3':
            for i in range(1, 54):
                r_string_comm_spec = r_string_comm + " " + str(i)
                r_string_base_spec = r_string_base + ":" + str(i)
                comments = Ref(r_string_comm_spec).text("he")
                links += match_ref_interface(r_string_base_spec, r_string_comm_spec,
                                             comments, simple_tokenizer, dher)
            continue

        comments = Ref(r_string_comm).text("he")
        links += match_ref_interface(r_string_base, r_string_comm,
                                     comments, simple_tokenizer, dher)

    for l in links:
        # find the last index of the space
        if "Abarbanel on Guide for the Perplexed, Part 1" in l["refs"][0] or "Abarbanel on Guide for the Perplexed, Part 2" in \
                l["refs"][0] or "Abarbanel on Guide for the Perplexed, Part 3" in l["refs"][0]:
            index = l["refs"][0].rfind(" ")

            # replace the last space with a colon
            l["refs"][0] = l["refs"][0][:index] + ":" + l["refs"][0][index + 1:]
    with open("abarbanel_dh_links.json", "w") as f:
        # Write the list of dictionaries to the file as JSON
        json.dump(links, f, ensure_ascii=False, indent=2)
    links = list_of_dict_to_links(links)
    insert_links_to_db(links)

def cauldron_pipeline():
    with open('abarbanel_dh_links.json') as f:
        links = json.load(f)
    links = list_of_dict_to_links(links)
    insert_links_to_db(links)
    # add_links_manually_to_db([
    #     ("Crescas on Guide for the Perplexed, Part 1 9:2", "Guide for the Perplexed, Part 1 9:3"),
    #     ("Crescas on Guide for the Perplexed, Part 1 70:3","Guide for the Perplexed, Part 1 70:4"),
    #     ("Crescas on Guide for the Perplexed, Part 3 3:6","Guide for the Perplexed, Part 3 3:1"),
    #     ("Crescas on Guide for the Perplexed, Part 3 3:7", "Guide for the Perplexed, Part 3 3:1"),
    #     ("Crescas on Guide for the Perplexed, Part 3 7:5",	"Guide for the Perplexed, Part 3 7:3"),
    # ]
    # )

def clean():
    query = {"refs": {"$regex" : "Abarbanel on Guide for the Perplexed"}, "generated_by": "Guide for the Perplexed_to_Abarbanel"}
    list_of_links = LinkSet(query).array()
    for l in list_of_links:
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
def infer_links():
    with open('links_list.json') as f:
        auto_links = json.load(f)

    sandwich_links = []
    last_in_seg_links = []
    all_refs_base = []
    all_refs_comm = []
    for sec in sections:
        r_string_base = "Guide for the Perplexed, {}".format(sec)
        all_refs_base += Ref(r_string_base).all_segment_refs()
        r_string_comm = "Efodi on Guide for the Perplexed, {}".format(sec)
        all_refs_comm += Ref(r_string_comm).all_segment_refs()
    last_segment_num = 0
    base_text_ref = ''
    count = 0
    # for sec in sections:
    #     r_string_comm = "Efodi on Guide for the Perplexed, {}".format(sec)
    #     refs_comm = Ref(r_string_comm).all_segment_refs()
    #     for r in refs_comm:
    #         if exists_with_ref_x(auto_links, r.tref) == None:
    #             count += 1
    #             if exists_with_ref_x(auto_links, prev_element(r).tref) and
    #                 r. exists_with_ref_x(auto_links, prev_element(r).tref)["refs"][1]
    for link in auto_links[1:]:
        prev_comm_ref = prev_element(auto_links, link)["refs"][0]
        curr_comm_ref = link["refs"][0]
        # next_comm_ref = next_element(auto_links, link)["refs"][0]


        i_minus_one = int(extract_last_number(prev_comm_ref))
        i = int(extract_last_number(curr_comm_ref))
        # i_plus_one = int(extract_last_number(next_comm_ref))
        if i_minus_one + 1 < i and link["refs"][1] ==  prev_element(auto_links, link)["refs"][1]:
            # count += 1
            sandwich_links.append(
                {
                    "refs": [
                        trim_last_num(prev_comm_ref) + str(i_minus_one+1),
                        prev_element(auto_links, link)["refs"][1]
                    ],
                    "generated_by": "Guide for the Perplexed_to_Efodi",
                    "type": "Commentary",
                    "auto": True
                }
            )
        if 'Efodi on Guide for the Perplexed, Part 1 10:1' in link["refs"][0]:
            a =1
        possibly_missing_efodi_link_ref = replace_last_number(prev_element(auto_links, link)["refs"][0], i_minus_one+1)
        possibly_non_existing_more_ref = replace_last_number(prev_element(auto_links, link)["refs"][1], i_minus_one+1)
        if i < i_minus_one and not exists_with_ref_x(auto_links, possibly_missing_efodi_link_ref) and find_ref_in_list(possibly_missing_efodi_link_ref, all_refs_comm) \
                and not find_ref_in_list(possibly_non_existing_more_ref, all_refs_base):
            # print("%%%%%%%%%%%%%")
            last_in_seg_links.append(
                {
                    "refs": [
                        possibly_missing_efodi_link_ref,
                        prev_element(auto_links, link)["refs"][1]
                    ],
                    "generated_by": "Guide for the Perplexed_to_Crescas",
                    "type": "Commentary",
                    "auto": True
                }
            )
            count += 1

    print(count)


    with open("sandwich_links.json", "w") as f:
        # Write the list of dictionaries to the file as JSON
        json.dump(sandwich_links, f, ensure_ascii=False, indent=2)
    with open("last_in_seg_links.json", "w") as f:
        # Write the list of dictionaries to the file as JSON
        json.dump(last_in_seg_links, f, ensure_ascii=False, indent=2)


def create_report():
    query = {"refs": {"$regex" : "Abarbanel on Guide for the Perplexed"}, "generated_by": "Guide for the Perplexed_to_Abarbanel"}
    list_of_links = LinkSet(query).array()
    list_of_tuples = [("Abarbanel", "Guide for the Perplexed")]
    for sec in sections:
        r_string_comm = "Abarbanel on Guide for the Perplexed, {}".format(sec)
        r_string_base = "Guide for the Perplexed, {}".format(sec)
        all_refs_for_sec = Ref(r_string_comm).all_segment_refs()

        for r in all_refs_for_sec:

            basetext_linked_refs = [l.refs[1] for l in list_of_links if r.normal() == l.refs[0]] #+ [l.refs[1] for l in list_of_links if r_string_base in l.refs[1]]
            separator = ", "
            basetext_linked_refs_string = separator.join(basetext_linked_refs)
            list_of_tuples.append((r, basetext_linked_refs_string))
    with open("abarbanel_report.csv", "w", newline="") as file:
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
            "generated_by": "Guide for the Perplexed_to_Abarbanel",
            "type": "Commentary",
            "auto": True
        })

    links = list_of_dict_to_links(links)
    insert_links_to_db(links)





if __name__ == '__main__':
    print("hello world")
    # infer_links()
    clean()
    # local_pipeline()
    # create_report()
    cauldron_pipeline()
    # index = library.get_index("Guide for the Perplexed")
    print("hi")


    # post_link(links)







