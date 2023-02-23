import django

django.setup()

django.setup()
superuser_id = 171118
import csv
from sefaria.model import *
from sefaria.helper.schema import insert_last_child, reorder_children
from sefaria.helper.schema import remove_branch
from sefaria.tracker import modify_bulk_text
from sefaria.helper.category import create_category
from sefaria.system.database import db
import json
import re
# from linking_utilities.parallel_matcher import ParallelMatcher


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
    with open('shem_tov_parallel_matcher_links.json') as f:
        links = json.load(f)
    links = list_of_dict_to_links(links)
    insert_links_to_db(links)
    # with open('sandwich_links.json') as f:
    #     links = json.load(f)
    # links = list_of_dict_to_links(links)
    # insert_links_to_db(links)
    # with open('last_in_seg_links.json') as f:
    #     links = json.load(f)
    # links = list_of_dict_to_links(links)
    # insert_links_to_db(links)


def clean():
    query = {"refs": {"$regex": "Shem Tov on Guide for the Perplexed"}}
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
        return lst[index + 1]
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
        if i_minus_one + 1 < i and link["refs"][1] == prev_element(auto_links, link)["refs"][1]:
            # count += 1
            sandwich_links.append(
                {
                    "refs": [
                        trim_last_num(prev_comm_ref) + str(i_minus_one + 1),
                        prev_element(auto_links, link)["refs"][1]
                    ],
                    "generated_by": "Guide for the Perplexed_to_Efodi",
                    "type": "Commentary",
                    "auto": True
                }
            )
        if 'Efodi on Guide for the Perplexed, Part 1 10:1' in link["refs"][0]:
            a = 1
        possibly_missing_efodi_link_ref = replace_last_number(prev_element(auto_links, link)["refs"][0],
                                                              i_minus_one + 1)
        possibly_non_existing_more_ref = replace_last_number(prev_element(auto_links, link)["refs"][1], i_minus_one + 1)
        if i < i_minus_one and not exists_with_ref_x(auto_links, possibly_missing_efodi_link_ref) and find_ref_in_list(
                possibly_missing_efodi_link_ref, all_refs_comm) \
                and not find_ref_in_list(possibly_non_existing_more_ref, all_refs_base):
            # print("%%%%%%%%%%%%%")
            last_in_seg_links.append(
                {
                    "refs": [
                        possibly_missing_efodi_link_ref,
                        prev_element(auto_links, link)["refs"][1]
                    ],
                    "generated_by": "Guide for the Perplexed_to_Efodi",
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


# def create_report():
#     auto = []
#     sandwich_links = []
#     last_in_seg_links = []
#
#     with open('links_list.json') as f:
#         auto = json.load(f)
#
#     with open('inferred_links.json') as f:
#         sandwich_links = json.load(f)
#
#     with open('last_in_seg_links.json') as f:
#         last_in_seg_links = json.load(f)
#
#     tuples = []
#     tuples.append(
#         ("Efodi Ref", "Moreh Ref Script", "Moreh Ref Sandwich Heuristic", "Moreh Ref Last in Segment Heuristic"))
#     for sec in sections:
#         r_string_comm = "Efodi on Guide for the Perplexed, {}".format(sec)
#         r_string_base = "Guide for the Perplexed, {}".format(sec)
#         all_refs_for_sec = Ref(r_string_comm).all_segment_refs()
#
#         for r in all_refs_for_sec:
#             auto_ref = ''
#             sandwich_ref = ''
#             last_in_seg_ref = ''
#             d = exists_with_ref_x(auto, r.tref)
#             if d != None:
#                 auto_ref = d["refs"][1]
#             else:
#                 d = exists_with_ref_x(sandwich_links, r.tref)
#                 if d != None:
#                     sandwich_ref = d["refs"][1]
#                 else:
#                     d = exists_with_ref_x(last_in_seg_links, r.tref)
#                     if d != None:
#                         last_in_seg_ref = d["refs"][1]
#             tuples.append((r.tref, auto_ref, sandwich_ref, last_in_seg_ref))
#     with open("report.csv", "w", newline="") as file:
#         writer = csv.writer(file)
#         writer.writerows(tuples)

def create_report():
    query = {"refs": {"$regex": "Shem Tov on Guide for the Perplexed"}}
    list_of_links = LinkSet(query).array()
    list_of_tuples = [("Shem Tov", "Guide for the Perplexed")]
    for sec in sections:
        r_string_comm = "Shem Tov on Guide for the Perplexed, {}".format(sec)
        r_string_base = "Guide for the Perplexed, {}".format(sec)
        all_refs_for_sec = Ref(r_string_comm).all_segment_refs()

        for r in all_refs_for_sec:

            basetext_linked_refs = [l.refs[0] for l in list_of_links if r.normal() in l.refs[1]] #+ [l.refs[1] for l in list_of_links if r_string_base in l.refs[1]]
            separator = ", "
            basetext_linked_refs_string = separator.join(basetext_linked_refs)
            list_of_tuples.append((r, basetext_linked_refs_string))
    with open("shem_tov_report.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(list_of_tuples)


def tokenizer(s):
    # s = strip_cantillation(s, strip_vowels=True)
    s = re.sub(r'[:,.]', '', s)
    s = re.sub(r'\([^\)]*\)', ' ', s)
    s = re.sub(r'<[^>]*>', ' ', s)
    return s.split()


def print_parallel_matches(matches):
    for match in matches:
        a = match.a.ref
        b = match.b.ref
        print('{{{')
        print(a)
        # print(a.text('he').text)
        print(b)
        # print(b.text('he').text)
        print('}}}')


def matches_to_links(matches):
    matches = [[m.a.ref.tref, m.b.ref.tref] for m in matches]
    matches = list(set(tuple(inner_list) for inner_list in matches))
    links = []

    for m in matches:
        if '-' in m[0] or '-' in m[1]:
            continue
        links.append(
            {
                "refs": [
                    m[0],
                    m[1]
                ],
                "generated_by": "Guide for the Perplexed_to_Shem Tov",
                "type": "Commentary",
                "auto": True
            }
        )
    return links


def create_links():
    links = []
    # matcher = ParallelMatcher(tokenizer, verbose=False, all_to_all=False, min_words_in_match=5,
    #                           min_distance_between_matches=0,
    #                           only_match_first=True, ngram_size=5, max_words_between=7,
    #                           both_sides_have_min_words=True)
    matcher = ParallelMatcher(tokenizer, verbose=False, all_to_all=False, min_words_in_match=7,
                              min_distance_between_matches=0,
                              only_match_first=True, ngram_size=5, max_words_between=7,
                              both_sides_have_min_words=True)
    for sec in sections:
        print(sec)
        r_string_comm = "Shem Tov on Guide for the Perplexed, {}".format(sec)
        r_string_base = "Guide for the Perplexed, {}".format(sec)
        if sec == 'Part 1':
            for i in range(1, 76):
                r_string_comm_spec = r_string_comm + " " + str(i)
                r_string_base_spec = r_string_base + ":" + str(i)
                matches = matcher.match([r_string_comm_spec, r_string_base_spec], return_obj=True)
                clean = matches_to_links(matches)
                links += clean
            continue

        if sec == 'Part 2':
            for i in range(1, 48):
                r_string_comm_spec = r_string_comm + " " + str(i)
                r_string_base_spec = r_string_base + ":" + str(i)
                matches = matcher.match([r_string_comm_spec, r_string_base_spec], return_obj=True)
                links += matches_to_links(matches)
            continue

        if sec == 'Part 3':
            for i in range(1, 54):
                r_string_comm_spec = r_string_comm + " " + str(i)
                r_string_base_spec = r_string_base + ":" + str(i)
                matches = matcher.match([r_string_comm_spec, r_string_base_spec], return_obj=True)
                links += matches_to_links(matches)
            continue

        else:
            r_string_comm_spec = r_string_comm
            r_string_base_spec = r_string_base
            matches = matcher.match([r_string_comm_spec, r_string_base_spec], return_obj=True)
            links += matches_to_links(matches)

    with open("shem_tov_parallel_matcher_links.json", "w") as f:
        # Write the list of dictionaries to the file as JSON
        json.dump(links, f, ensure_ascii=False, indent=2)

    return list_of_dict_to_links(links)


if __name__ == '__main__':
    print("hello world")

    # # infer_links()
    # clean()
    # cauldron_pipeline()
    # # create_report()
    # # index = library.get_index("Guide for the Perplexed")

    # for sec in sections:
    #     print(sec)
    #     r_string_comm = "Efodi on Guide for the Perplexed, {}".format(sec)
    #     r_string_base = "Guide for the Perplexed, {}".format(sec)
    #     if sec == 'Part 1':
    #         for i in range(1, 76):
    #             r_string_comm_spec = r_string_comm + " " + str(i)
    #             r_string_base_spec = r_string_base + ":" + str(i)
    #             comments = Ref(r_string_comm_spec).text("he")
    #             links += match_ref_interface(r_string_base_spec, r_string_comm_spec,
    #                                          comments, lambda x: x.split(), dher)
    # matcher = ParallelMatcher(tokenizer, verbose=False, all_to_all=False, min_words_in_match=5,
    #                           min_distance_between_matches=0,
    #                           only_match_first=True, ngram_size=5, max_words_between=7, both_sides_have_min_words=True)
    # text = 'ואתה גם כן תמצא אריסטו יאמר בספר השמים והעולם'
    # a = Ref('Guide for the Perplexed, Part 2')
    # matches = matcher.match(["Shem Tov on Guide for the Perplexed, Introduction, Prefatory Remarks", 'Guide for the Perplexed, Introduction, Prefatory Remarks'], return_obj=True)
    # clean = clean_matches(matches)
    # # print_parallel_matches(matches)

    clean()
    cauldron_pipeline()
    # links = create_links()
    #
    # insert_links_to_db(links)
    #
    # create_report()
    print("hi")

    # post_link(links)
