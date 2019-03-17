#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from sefaria.model.schema import AddressTalmud
from sources.functions import *
import re
from sources.functions import getGematria, convertDictToArray
from data_utilities.dibur_hamatchil_matcher import *
second_para_terms = ["ונראה", "ולפי", "ובספר", """לפ"ז""", "אבל", "שוב", "ואפשר",
    '\xd7\x95\xd7\x9e\xd7\x99\xd7\x94\xd7\x95', '\xd7\x9e\xd7\x99\xd7\x94\xd7\x95', '\xd7\x90\xd7\x9e\xd7\xa0\xd7\x9d', '\xd7\x95\xd7\x99\xd7\xa9', '\xd7\x90\xd7\x9a', '\xd7\x90\xd7\x9c\xd7\x90', '\xd7\x95\xd7\x9c\xd7\x9b\xd7\x90\xd7\x95\xd7\xa8\xd7\x94', '\xd7\x95\xd7\xa0\xd7\x9c\xd7\xa2"\xd7\x93', '\xd7\x95\xd7\xa2\xd7\x95\xd7\x93', '\xd7\x95\xd7\x9c\xd7\xa4"\xd7\x96', '\xd7\x9b\xd7\x9c', '\xd7\x92\xd7\x9d', '\xd7\x95\xd7\x9e\xd7\x94', '\xd7\x95\xd7\x9e"\xd7\xa9', '\xd7\x95\xd7\x94\xd7\xa0\xd7\x94', '\xd7\x95\xd7\x90\xd7\x9b\xd7\xaa\xd7\x99', '\xd7\x95\xd7\x91\xd7\x96\xd7\x94', '\xd7\xaa\xd7\x95', '\xd7\xa2\xd7\x95\xd7\x93']
second_para_terms = [term.decode('utf-8') for term in second_para_terms]

def match_is_second_para(comment):
    comment_first_word = comment.replace("<b>", "").replace("</b>", "").split()[0]
    for term in second_para_terms:
        if term == comment_first_word or term == u"""בא"ד""" or term == u"""שם בא"ד""":
            return True
    return False

def create_ranges(orig, text, title, daf):
    comments = orig[daf]
    matches = text[daf]
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



def parse(line):
    if "30" in line:
        line = "<small>"+line.replace("30", "")+"</small>"
        return line
    line = line.replace("67", "<b>").replace("70", "<b>")
    line = line.replace("50", "</b>").replace("90", "<b>").replace("80", "</b>")
    if "<b>" in line and not "</b>" in line:
        line = line.split()[0]+"</b> "+" ".join(line.split()[1:])
    return line


def dh_extract(str):
    talmud_flag = [u"""מתניתין""", u"""במתניתין""", u"""בגמרא""", u"""גמרא"""]
    rashi_flag = [u"""פירש"י""", u"""רש"י"""]
    tosafot_flag = [u"""תוספות""", u"""תוספת""", u"""תוס'""", u"""בתוס'"""]
    pointing_flag = [u"""שם""", u"""בד"ה"""] + second_para_terms
    combined = talmud_flag + rashi_flag + tosafot_flag + pointing_flag
    str = str.replace("<b>", "").replace("</b>", "")
    if str.split()[0] in combined:
        str = u" ".join(str.split()[1:])
    str = str.replace(u"וכו'", u"")
    return " ".join(str.split()[0:5])



def add_line(line, daf, prev, full_text, text_dicts, map_full_text_to_commentary):
    talmud_flag = [u"""מתניתין""", u"""במתניתין""", u"""בגמרא""", u"""גמרא"""]
    rashi_flag = [u"""פירש"י""", u"""רש"י"""]
    tosafot_flag = [u"""תוספות""", u"""תוספת""", u"""תוס'""", u"""בתוס'"""]
    pointing_flag = [u"""שם""", u"""בד"ה""", u"""שם בא"ד""", u"""בא"ד"""] + second_para_terms

    full_text[daf].append(line)
    line_to_check = line.replace("<b>", "").replace("</b>", "")

    for flag_tuple in [("rashi", rashi_flag), ("tosafot", tosafot_flag), (prev, pointing_flag), ("gemara", talmud_flag)]:
        type, flags = flag_tuple
        for flag in flags:
            if flag in u" ".join(line_to_check.split()[0:2]):
                text_dicts[type][daf].append(line)
                map_full_text_to_commentary[daf].append(type)
                return type
    else:
        map_full_text_to_commentary[daf].append("gemara")
        text_dicts["gemara"][daf].append(line)
        return "gemara"


def create_index_and_post(full_intro, full_text):
    root = SchemaNode()
    root.add_primary_titles("Haflaah on Ketubot", u"הפלאה על כתובות")
    root.key = "haflaah"
    intro = JaggedArrayNode()
    intro.add_shared_term("Introduction")
    intro.add_structure(["Comment"])
    intro.key = "intro"
    root.append(intro)
    default = JaggedArrayNode()
    default.add_structure(["Daf", "Paragraph"], address_types=["Talmud", "Integer"])
    default.default = True
    default.key = "default"
    root.append(default)
    root.validate()
    index = {
        "schema": root.serialize(),
        "title": "Haflaah on Ketubot",
        "categories": ["Talmud", "Bavli", "Commentary"],
        "dependence": "Commentary",
        "base_text_titles": ["Ketubot"]
    }
    post_index(index, server=SEFARIA_SERVER)

    full_text = convertDictToArray(full_text)
    send_text = {
        "text": full_intro,
        "language": "he",
        "versionSource": "http://aleph.nli.org.il:80/F/?func=direct&doc_number=001880789&local_base=NNL01",
        "versionTitle": "Sefer Hafla'ah, Lemberg, 1860"
    }
    post_text("Haflaah on Ketubot, Introduction", send_text, server=SEFARIA_SERVER)

    send_text = {
        "text": full_text,
        "language": "he",
        "versionSource": "http://aleph.nli.org.il:80/F/?func=direct&doc_number=001880789&local_base=NNL01",
        "versionTitle": "Sefer Hafla'ah, Lemberg, 1860"
    }
    post_text("Haflaah on Ketubot", send_text, server=SEFARIA_SERVER)

def parse_intro():
    intro = []
    with open("intro") as f:
        text = []
        lines = [line for line in list(f) if line.split()]
        temp = ""
        for line_n, line in enumerate(lines):
            if not line:
                continue
            if temp:
                line = temp + " " + line
                temp = ""
                line = parse(line)
                intro.append(line)
                continue
            elif "61" in line:
                temp = line
                continue
            if len(line) > 4:
                line = parse(line)
                line = line.replace("40", "").replace("61", "")
                intro.append(line)
    return intro


def parse_main():
    with open("main.txt") as f:
        numbers = set()
        daf = 0
        full_text = {}
        text_dicts = {}
        text_dicts["gemara"] = {}
        text_dicts["rashi"] = {}
        text_dicts["tosafot"] = {}
        prev_dict = "gemara"
        map_full_text_to_commentary = {}
        lines = [line for line in list(f) if line.split()]
        for line_n, line in enumerate(lines):
            line = line.decode('utf-8')
            for num in re.findall(u"\d+", line):
                numbers.add(num)
            if line.split()[0].find("40") >= 0:
                if u"""ע"ב""" in line:
                    daf += 1
                    full_text[daf] = []
                    text_dicts["gemara"][daf] = []
                    text_dicts["tosafot"][daf] = []
                    text_dicts["rashi"][daf] = []
                    map_full_text_to_commentary[daf] = []
                elif u"דף" in line:
                    assert len(line.split()) == 2
                    new_daf = getGematria(line.split()[1]) * 2 - 1
                    assert new_daf > daf
                    daf = new_daf
                    full_text[daf] = []
                    text_dicts["gemara"][daf] = []
                    text_dicts["tosafot"][daf] = []
                    text_dicts["rashi"][daf] = []
                    map_full_text_to_commentary[daf] = []
            else:
                line = line.replace("\r", "").replace("\n", "")
                if len(line) > 2:
                    line = parse(line)
                    prev_dict = add_line(line, daf, prev_dict, full_text, text_dicts, map_full_text_to_commentary)
    return full_text, text_dicts, map_full_text_to_commentary

def find_matches(gemara, tosafot, rashi):
    # what needs to be done is to go through each dict and try to match everything, but check each segment that if it is בא"ד
    # ignore if it has a match and match it to previous segment's match
    # and if no match: link with previous segment (as a range) as if this comment really has no DH which is why it has no match

    nones = total = 0
    for pairs in [(tosafot, "Tosafot on Ketubot"), (gemara, "Ketubot"), (rashi, "Rashi on Ketubot")]:
        orig_dict = dict(pairs[0])
        which_dict = pairs[0]
        which_text = pairs[1]
        for daf in which_dict.keys():
            actual_daf = AddressTalmud.toStr("en", daf)
            base_text = TextChunk(Ref("{} {}".format(which_text, actual_daf)), lang='he')
            if not base_text.text:
                continue
            comments = which_dict[daf]
            results = match_ref(base_text, comments, lambda x: x.split(), dh_extract_method=dh_extract)
            for i, result_comment in enumerate(zip(results["matches"], comments)):
                result, comment = result_comment
                comment_wout_bold = comment.replace("<b>", "").replace("</b>", "")
                if u"""בא"ד""" in u" ".join(comment_wout_bold.split()[0:3]) \
                        or u"""שם בא"ד""" in u" ".join(comment_wout_bold.split()[0:3]):
                    results["matches"][i] = results["matches"][i - 1]
            which_dict[daf] = results["matches"]


        for daf in which_dict.keys():
             if which_dict[daf] and orig_dict[daf]:
                which_dict[daf] = create_ranges(orig_dict, which_dict, which_text, daf)
    return gemara, tosafot, rashi

def check_prev_link(temp_links, i, also_check_gemara=True):
    found_link = True
    prev_link = temp_links[i] if len(temp_links) > 0 else ""
    prev_comm_ref = prev_link["refs"][1] if isinstance(prev_link, dict) else ""
    if (prev_comm_ref != comm_ref and also_check_gemara) or (not also_check_gemara and not "extra_link" in prev_link):
        return temp_links, False
    prev_haflaah_ref = prev_link["refs"][0].split("-")[0]
    prev_haflaah_ref = prev_haflaah_ref + "-" + haflaah_ref.split(":")[-1]
    temp_links[i]["refs"][0] = prev_haflaah_ref
    if "extra_link" in temp_links[i]:
        del temp_links[i]["extra_link"]
    if titles[segment - 1] != "gemara" and also_check_gemara:
        temp_links, found_link = check_prev_link(temp_links, -2, also_check_gemara=False)
    return temp_links, found_link


intro = parse_intro()
full_text, text_dicts, map_full_text_to_commentaries = parse_main()
dicts = {}
dicts["gemara"] = {}
dicts["tosafot"] = {}
dicts["rashi"] = {}
dicts["gemara"], dicts["tosafot"], dicts["rashi"] = text_dicts["gemara"], text_dicts["tosafot"], text_dicts["rashi"]

dicts["gemara"], dicts["tosafot"], dicts["rashi"] = find_matches(dicts["gemara"], dicts["tosafot"], dicts["rashi"] )
create_index_and_post(intro, full_text)
links = []
#go through map_full_text_to_commentaries, create the one end of the link Haflaah on Ketubot 2a:1
#using the daf key and getting segment from the for loop enumeration
#then keep count rashi_n, tosafot_n, gemara_n = -1.  each time we find in map_full_text_to_commentaries a rashi,
#we increment rashi_n, say rashi[daf][rashi_n] is the other end of the link.  Yalaa! Link is done!

counts = {}
for daf, titles in map_full_text_to_commentaries.items():
    counts["rashi"] = -1
    counts["tosafot"] = -1
    counts["gemara"] = -1
    section_ref = "Haflaah on Ketubot {}".format(AddressTalmud.toStr("en", daf))
    temp_links = []
    for segment, title in enumerate(titles):
        haflaah_ref = "{}:{}".format(section_ref, segment+1)
        counts[title] += 1
        comm_ref = dicts[title][daf][counts[title]]
        if not comm_ref:
            temp_links.append(haflaah_ref)
            continue
        comm_ref = comm_ref.normal()
        temp_links, found_prev_link = check_prev_link(temp_links, -1)
        if found_prev_link:
            continue
        link = {"refs": [haflaah_ref, comm_ref], "auto": True, "generated_by": "haflaah", "type": "Commentary"}
        if title != "gemara": #need to add gemara link as well
            gemara_section_ref = Ref(comm_ref).section_ref()
            base_ref = gemara_section_ref.normal().replace("Rashi on ", "").replace("Tosafot on ", "")
            new_link = {"extra_link": True, "refs": [haflaah_ref, base_ref], "auto": True, "generated_by": "haflaah", "type": "Commentary"}
            temp_links.append(new_link)
        temp_links.append(link)

    for i, haflaah_ref in enumerate(temp_links):
        print haflaah_ref
        # if isinstance(haflaah_ref, str) and i == 0:
        #     q = 0
        #     while q < len(temp_links)-1 and isinstance(temp_links[q], str):
        #         q += 1
        #     if q < len(temp_links):
        #         ketubot_ref = temp_links[q]["refs"][1].split(":")[0]
        #         temp_links[i] = {"refs": [haflaah_ref, ketubot_ref], "auto": True, "generated_by": "haflaah",
        #                          "type": "Commentary"}
        if isinstance(haflaah_ref, str) and (0 <= i < len(temp_links)-1):
            cant_find = False
            prev_counter = next_counter = 0
            prev = temp_links[i-1-prev_counter]
            next = temp_links[i+1+next_counter]
            while isinstance(prev, dict) and not prev["refs"][1].startswith("Ketubot"):
                prev_counter -= 1
                if prev_counter == -1:
                    cant_find = True
                    break
                prev = temp_links[i-1-prev_counter]
            while not cant_find and isinstance(next, dict) and not next["refs"][1].startswith("Ketubot"):
                next_counter += 1
                if next_counter == len(temp_links):
                    cant_find = True
                    break
                next = temp_links[i+1+next_counter]
            if isinstance(prev, dict) and isinstance(next, dict) and cant_find is False:
                try:
                    comm_ref = Ref(prev["refs"][1]).to(Ref(next["refs"][1])).normal()
                    temp_links[i] = {"refs": [haflaah_ref, comm_ref], "auto": True, "generated_by": "haflaah", "type": "Commentary"}
                    print comm_ref
                except:
                    print "ACTUAL NONE"

    temp_links = [l for l in temp_links if isinstance(l, dict)]
    links += temp_links
post_link(links, server=SEFARIA_SERVER, VERBOSE=True)








