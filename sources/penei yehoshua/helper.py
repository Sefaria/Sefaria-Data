#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from data_utilities.dibur_hamatchil_matcher import *

#Helper functions to be used for Talmud commentaries such as Penei Yehoshua.
#The main function to call is get_links()


def get_comments_and_map(comments, keyword):
    flags = {"Tosafot": [u"""תוספות""", u"""בתוספות""", u"""תוספת""", u"""תוס'""", u"""בתוס'"""],
             "Rashi": [u"""פירש"י""", u"""רש"י"""],
             "Gemara": [u"""מתניתין""", u"""במתניתין""", u"""בגמרא""", u"""גמרא""", u"""בגמ'"""]}
    relevant_comments = []
    map_comments_to_relevant_comments = {} #index comment is found in "comments"
                                          # to index comment is found in "relevant_comments"
    prev_flag = False
    same_text_flags = [u"""שם""", u"""בד"ה""", u"""שם בא"ד""", u"""בא"ד"""]
    for comm_n, comment in enumerate(comments):
        first_word = comment.split()[0].replace("<b>", "").replace("</b>", "")
        first_two_words = u" ".join(comment.split()[0:2]).replace("<b>", "").replace("</b>", "")
        if prev_flag and (match_is_second_para(comment) or first_word in same_text_flags or
                          first_two_words in same_text_flags):
            relevant_comments.append(comment)
            map_comments_to_relevant_comments[len(relevant_comments) - 1] = comm_n
            prev_flag = True
        else:
            found = False
            for flag in flags[keyword]:
                if (first_word in flag or flag in first_word):
                    relevant_comments.append(comment)
                    map_comments_to_relevant_comments[len(relevant_comments) - 1] = comm_n
                    prev_flag = True
                    found = True
                    break
            if not found:
                prev_flag = False
    return relevant_comments, map_comments_to_relevant_comments

second_para_terms = ["ונראה", "ולפי", "ובספר", """לפ"ז""", "אבל", "שוב", "ואפשר",
    '\xd7\x95\xd7\x9e\xd7\x99\xd7\x94\xd7\x95', '\xd7\x9e\xd7\x99\xd7\x94\xd7\x95', '\xd7\x90\xd7\x9e\xd7\xa0\xd7\x9d', '\xd7\x95\xd7\x99\xd7\xa9', '\xd7\x90\xd7\x9a', '\xd7\x90\xd7\x9c\xd7\x90', '\xd7\x95\xd7\x9c\xd7\x9b\xd7\x90\xd7\x95\xd7\xa8\xd7\x94', '\xd7\x95\xd7\xa0\xd7\x9c\xd7\xa2"\xd7\x93', '\xd7\x95\xd7\xa2\xd7\x95\xd7\x93', '\xd7\x95\xd7\x9c\xd7\xa4"\xd7\x96', '\xd7\x9b\xd7\x9c', '\xd7\x92\xd7\x9d', '\xd7\x95\xd7\x9e\xd7\x94', '\xd7\x95\xd7\x9e"\xd7\xa9', '\xd7\x95\xd7\x94\xd7\xa0\xd7\x94', '\xd7\x95\xd7\x90\xd7\x9b\xd7\xaa\xd7\x99', '\xd7\x95\xd7\x91\xd7\x96\xd7\x94', '\xd7\xaa\xd7\x95', '\xd7\xa2\xd7\x95\xd7\x93']
second_para_terms = [term.decode('utf-8') for term in second_para_terms]
links_found = {}
def match_is_second_para(comment):
    comment_first_word = comment.replace("<b>", "").replace("</b>", "").split()[0]
    for term in second_para_terms:
        if term == comment_first_word or term == u"""בא"ד""" or term == u"""שם בא"ד""":
            return True
    return False

def create_ranges(comments, matches):
    # first_segment = Ref("{} {}".format(title, AddressTalmud.toStr("en", daf))).all_segment_refs()[0]
    # if matches[0] is None:
    #     matches[0] = first_segment
    #what I need to do is to go through the comments and when I find one that is a second paragraph and its previous
    #comment ISN'T a second paragraph
    for match_n, match in enumerate(matches):
      if not match and matches[match_n-1]:
        next_one = match_n
        #when a match is a second paragraph, you want to include it but when it isn't, you want to leave it as None
        while next_one < len(matches) and not matches[next_one] and match_is_second_para(comments[next_one]):
            next_one += 1
        #if not matches[next_one] and next_one == len(matches) - 1:
        #    matches[next_one] = Ref("{} {}".format(title, AddressTalmud.toStr("en", daf))).all_segment_refs()[-1]
        if next_one != match_n:
            for i in range(match_n-1, next_one):
                matches[i] = matches[match_n-1]
    return matches

def create_ranged_link(links, range_counter, create_base_link):
    comm_link = links.pop()
    if create_base_link:
        base_link = links.pop()
    penei_ref = comm_link["refs"][1]
    assert penei_ref.startswith("Penei")
    segment = int(penei_ref.split(":")[-1])
    new_penei_ref = penei_ref + "-" + str(range_counter + segment)
    comm_link["refs"][1] = new_penei_ref
    links.append(comm_link)
    if create_base_link:
        base_link["refs"][1] = new_penei_ref
        links.append(base_link)


def create_ranged_links(matches, index_title, daf, comm_map, create_base_link=False):
    range_counter = 0
    prev_comm = None
    links = []
    for match_n, comm_ref in enumerate(matches):
        if comm_ref and comm_ref == prev_comm:
            range_counter += 1
            prev_comm = comm_ref
        elif comm_ref and range_counter > 0:
            create_ranged_link(links, range_counter, create_base_link)
            range_counter = 0
            prev_comm = None
        if comm_ref and range_counter is 0 and comm_ref != prev_comm:
            penei_ref = "{} {}:{}".format(index_title, daf, 1 + comm_map[match_n])
            comm_link = {"refs": [comm_ref.normal(), penei_ref], "type": "Commentary", "auto": True,
                         "generated_by": "penei_yehoshua_batch_ii"}
            links.append(comm_link)
            if create_base_link:
                base_ref = ":".join(comm_ref.normal().split(" on ")[-1].split(":")[0:-1])
                base_link = {"refs": [base_ref, penei_ref], "type": "Commentary", "auto": True,
                             "generated_by": "penei_yehoshua_batch_ii"}
                links.append(base_link)

            prev_comm = comm_ref

    if prev_comm and range_counter > 0:
        create_ranged_link(links, range_counter, create_base_link)

    return links

def check_for_doubles(links):
    penei_dict = {}
    links_wout_doubles = []
    #first go through and only add penei range refs.  then go through and only check non-range penei refs and
    #dont add them if they're already there
    for n, link in enumerate(links):
        penei_ref = Ref(link["refs"][1])
        if penei_ref.is_range():
            for ref in penei_ref.range_list():
                if ref not in penei_dict.keys():
                    penei_dict[ref] = []
                penei_dict[ref].append(link["refs"][0])
                if link not in links_wout_doubles:
                    links_wout_doubles.append(link)

    for n, link in enumerate(links):
        penei_ref = Ref(link["refs"][1])
        other_ref = link["refs"][0]
        if not penei_ref.is_range() and \
                (penei_ref not in penei_dict.keys() or other_ref not in penei_dict[penei_ref]):
            links_wout_doubles.append(link)

    return links_wout_doubles


def get_comments_and_map_for_gemara(orig_comments, comments_by_type):
    non_gemara_comments = []
    gemara_map = {}
    for type, comments in comments_by_type.items():
        non_gemara_comments += [c for c in comments]
    gemara_comments = [c for c in orig_comments if c not in non_gemara_comments]
    for i, c in enumerate(orig_comments):
        if c not in non_gemara_comments:
            gemara_map[len(gemara_map)] = i
    return gemara_comments, gemara_map


def get_links(comments, index_title, daf, dh_extract_method):
    links_in_daf = []
    comm_maps = {"Tosafot": {}, "Rashi": {}, "Gemara": {}}
    comments_by_type = {"Tosafot": {}, "Rashi": {}, "Gemara": {}}
    comments = [c[:-2] for c in comments if c != "\r\n"]
    comments = [comment.replace(u'""', u'"') for comment in comments]
    for type in ["Tosafot", "Rashi"]:
        comments_by_type[type], comm_maps[type] = get_comments_and_map(comments, type)
    comments_by_type["Gemara"], comm_maps["Gemara"] = get_comments_and_map_for_gemara(comments, comments_by_type)
    ref = index_title.split(" on ")[-1] + " " + daf
    tosafot_ref = "Tosafot on {}".format(ref)
    rashi_ref = "Rashi on {}".format(ref)
    base_text = TextChunk(Ref(ref), lang='he')
    tosafot_base_text = TextChunk(Ref(tosafot_ref), lang='he')
    rashi_base_text = TextChunk(Ref(rashi_ref), lang='he')
    comm_matches = {"Tosafot": [], "Rashi": []}
    if comments_by_type["Tosafot"]:
        comm_matches["Tosafot"] = match_ref(tosafot_base_text, comments_by_type["Tosafot"], lambda x: x.split(),
                                            dh_extract_method=dh_extract_method)
    if comments_by_type["Rashi"]:
        comm_matches["Rashi"] = match_ref(rashi_base_text, comments_by_type["Rashi"], lambda x: x.split(),
                                          dh_extract_method=dh_extract_method)

    for comm_type, matches in comm_matches.items():
        comm_map = comm_maps[comm_type]
        if not matches or not comm_map:
            continue
        matches = create_ranges(comments_by_type[comm_type], matches["matches"])
        links_in_daf += create_ranged_links(matches, index_title, daf, comm_map, create_base_link=True)

    matches = match_ref(base_text, comments_by_type["Gemara"], lambda x: x.split(), dh_extract_method=dh_extract_method)
    matches = create_ranges(comments_by_type["Gemara"], matches["matches"])
    if comm_maps["Gemara"]:
        links_in_daf += create_ranged_links(matches, index_title, daf, comm_maps["Gemara"])

    return check_for_doubles(links_in_daf)