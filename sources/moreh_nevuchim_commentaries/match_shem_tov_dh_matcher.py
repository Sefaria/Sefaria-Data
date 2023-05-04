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
    text = text.replace('<b>', '')
    text = text.replace('</b>', '')
    # match = re.search(r'<b>(.*?)</b>', text)
    # if match:
    #     dh = match.group(1)
    # if dh == "העשרים":
    #     dh = "העשרים שכל מחויב המציאות בבחינת עצמו"
    if "דע כי ראה והביט וחזה" in text:
        a = 4
    dh = text[0:40]
    dh = dh.replace("ואמרו",'')
    dh = dh.replace("ואמר הרב", '')
    dh = dh.replace("אמר הרב", '')

    dh = dh.split('.')[0]
    dh = dh.split("'וכו'")[0]
    # print(dh)
    return dh

sections = ["Introduction, Letter to R Joseph son of Judah", "Introduction, Prefatory Remarks",
                "Introduction, Introduction",
                "Part 1", "Part 2 Introduction", "Part 2", "Part 3 Introduction", "Part 3"]
# sections = ["Part 2 Introduction", "Part 2", "Part 3 Introduction", "Part 3"]

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


def local_pipeline():
    from sources.functions import match_ref_interface
    # from linking_utilities.dibur_hamatchil_matcher import *
    links = []

    for sec in sections:
        print(sec)
        r_string_comm = "Shem Tov on Guide for the Perplexed, {}".format(sec)
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
        if "Shem Tov on Guide for the Perplexed, Part 1" in l["refs"][0] or "Shem Tov on Guide for the Perplexed, Part 2" in \
                l["refs"][0] or "Shem Tov on Guide for the Perplexed, Part 3" in l["refs"][0]:
            index = l["refs"][0].rfind(" ")

            # replace the last space with a colon
            l["refs"][0] = l["refs"][0][:index] + ":" + l["refs"][0][index + 1:]
    with open("shem_tov_dh_links.json", "w") as f:
        # Write the list of dictionaries to the file as JSON
        json.dump(links, f, ensure_ascii=False, indent=2)
    links = list_of_dict_to_links(links)
    insert_links_to_db(links)

def cauldron_pipeline():
    with open('shem_tov_dh_links.json') as f:
        links = json.load(f)
    links = list_of_dict_to_links(links)
    insert_links_to_db(links)
    # add_links_manually_to_db([
    #     ("Shem Tov on Guide for the Perplexed, Part 1 61:2", "Guide for the Perplexed, Part 1 61:1"),
    #     ("Shem Tov on Guide for the Perplexed, Part 2 26:4", "Guide for the Perplexed, Part 2 26:1"),
    #     ("Shem Tov on Guide for the Perplexed, Part 2 34:2", "Guide for the Perplexed, Part 2 34:1"),
    #     ("Shem Tov on Guide for the Perplexed, Part 3 14:2", "Guide for the Perplexed, Part 3 14:1"),
    #     ("Shem Tov on Guide for the Perplexed, Part 3 17:10", "Guide for the Perplexed, Part 3 17:11"),
    #     ("Shem Tov on Guide for the Perplexed, Part 3 20:4", "Guide for the Perplexed, Part 3 20:4"),
    #     ("Shem Tov on Guide for the Perplexed, Part 3 29:3", "Guide for the Perplexed, Part 3 29:3"),
    #     ("Shem Tov on Guide for the Perplexed, Part 3 29:4", "Guide for the Perplexed, Part 3 29:3"),
    #     ("Shem Tov on Guide for the Perplexed, Part 3 45:5", "Guide for the Perplexed, Part 3 45:6"),
    #     ("Shem Tov on Guide for the Perplexed, Part 3 48:3", "Guide for the Perplexed, Part 3 48:8")
    #
    # ]
    add_links_manually_to_db([
        ("Shem Tov on Guide for the Perplexed, Part 1 2:9", "Guide for the Perplexed, Part 1 2:5"),
        ("Shem Tov on Guide for the Perplexed, Part 1 35:2", "Guide for the Perplexed, Part 1 35:1"),
        ("Shem Tov on Guide for the Perplexed, Part 1 35:3", "Guide for the Perplexed, Part 1 35:1"),
        ("Shem Tov on Guide for the Perplexed, Part 1 71:6", "Guide for the Perplexed, Part 1 71:5"),
        ("Shem Tov on Guide for the Perplexed, Part 1 73:5", "Guide for the Perplexed, Part 1 73:15"),
        ("Shem Tov on Guide for the Perplexed, Part 1 74:12", "Guide for the Perplexed, Part 1 74:10"),
        ("Shem Tov on Guide for the Perplexed, Part 2 24:6", "Guide for the Perplexed, Part 2 24:4"),
        # ("Shem Tov on Guide for the Perplexed, Part 2 26:5", "Guide for the Perplexed, Part 2 26:3"),
        # ("Shem Tov on Guide for the Perplexed, Part 3 20:6", "Guide for the Perplexed, Part 3 20:5"),
        ("Shem Tov on Guide for the Perplexed, Part 3 22:2", "Guide for the Perplexed, Part 3 22:1"),
        ("Shem Tov on Guide for the Perplexed, Part 3 47:3", "Guide for the Perplexed, Part 3 47:5")
    ]

    )


def clean():
    query = {"refs": {"$regex": "Shem Tov on Guide for the Perplexed"}, "generated_by": "Guide for the Perplexed_to_Shem"}
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



def create_report():
    query = {"refs": {"$regex": "Shem Tov on Guide for the Perplexed"}}
    list_of_links = LinkSet(query).array()
    list_of_tuples = [("Shem Tov", "Guide for the Perplexed")]
    for sec in sections:
        r_string_comm = "Shem Tov on Guide for the Perplexed, {}".format(sec)
        r_string_base = "Guide for the Perplexed, {}".format(sec)
        all_refs_for_sec = Ref(r_string_comm).all_segment_refs()

        for r in all_refs_for_sec:

            basetext_linked_refs = [l.refs[0] for l in list_of_links if r.normal() == Ref(l.refs[1]).normal()] #+ [l.refs[1] for l in list_of_links if r_string_base in l.refs[1]]
            separator = ", "
            basetext_linked_refs_string = separator.join(basetext_linked_refs)
            list_of_tuples.append((r, basetext_linked_refs_string))
    with open("shem_tov_dh_matcher_report.csv", "w", newline="") as file:
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
            "generated_by": "Guide for the Perplexed_to_Shem",
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
    cauldron_pipeline()
    # create_report()
    # index = library.get_index("Guide for the Perplexed")
    print("hi")


    # post_link(links)







