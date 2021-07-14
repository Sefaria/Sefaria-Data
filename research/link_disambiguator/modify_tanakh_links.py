# -*- coding: utf-8 -*-
import re, json, codecs, csv, heapq, random, regex, math, cProfile, pstats, time
from collections import defaultdict
from pymongo.errors import AutoReconnect
from tqdm import tqdm
import django
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import PartialRefInputError, InputError, NoVersionFoundError
from sefaria.utils.hebrew import strip_cantillation
import sefaria.tracker as tracker
from sefaria import settings
from sefaria.system.database import db

ROOT = "data"
# ROOT = "research/link_disambiguator"

def get_tc(tref, just_ref=False, tries=0):
    try:
        main_oref = Ref(tref)
        if just_ref:
            return main_oref
        vset = VersionSet(main_oref.condition_query("he"), proj=main_oref.part_projection())
        if len(vset) < 1:
            raise InputError("VSET not equal to 1")
        main_version = vset[0]
        main_tc = main_oref.text("he", vtitle=main_version.versionTitle)
        return main_tc, main_oref, main_version
    except AutoReconnect:
        if tries < 200:
            time.sleep(0.24)
            return get_tc(tref, just_ref=just_ref, tries=tries+1)
        else:
            raise AutoReconnect("Tried so hard but got so many autoreconnects...")


"""
Copied and pasted from main.py to make this file independently runnable. not a great idea...
"""
def get_snippet_by_seg_ref(source_tc, found, must_find_snippet=False, snip_size=100, use_indicator_words=False, return_matches=False):
    """
    based off of library.get_wrapped_refs_string
    :param source:
    :param found:
    :param must_find_snippet: bool, True if you only want to return a str if you found a snippet
    :param snip_size int number of chars in snippet on each side
    :param use_indicator_words bool, True if you want to use hard-coded indicator words to determine which side of the ref the quote is on
    :return:
    """
    after_indicators = ["דכתיב", "ודכתיב", "וכתיב", "וכתוב", "שכתוב", "כשכתוב", "כדכתיב", "זל", "ז״ל", "ז''ל",
                       "ז\"ל", "אומרם", "כאמור", "ואומר", "אמר", "שנאמר", "בגמ'", "בגמ׳", "בפסוק", "לעיל", "ולעיל", "לקמן", "ולקמן", "בירושלמי",
                       "בבבלי", "שדרשו", "ששנינו", "שנינו", "ושנינו", "דשנינו", "כמש״כ", "כמש\"כ", "כמ״ש", "כמ\"ש",
                       "וכמש״כ", "וכמ\"ש", "וכמ״ש", "וכמש\"כ", "ע״ה", "ע\"ה", "מבואר", "כמבואר", "במתני׳",
                       "במתנ\'", "דתנן", "זכרונם לברכה", "זכר לברכה"]
    after_reg = r"(?:^|\s)(?:{})\s*[(\[]?$".format("|".join(after_indicators))
    after_indicators_far = ["דבפרק", "בפרק", "שבפרק", "פרק"]
    after_far_reg = r"(?:^|\s)(?{}:)(?=\s|$)".format("|".join(after_indicators_far))
    after_indicators_after = ["בד״ה", "בד\"ה", "ד״ה", "ד\"ה"]
    after_after_reg = r"^\s*(?:{})\s".format("|".join(after_indicators_after))
    punctuation = [",", ".", ":", "?", "!", "׃"]
    punctuation_after_reg = r"^\s*(?:{})\s".format("|".join(punctuation))
    punctuation_before_reg = r"(?:{})\s*$".format("|".join(punctuation))
    after_indicators_after_far = ["וגו׳", "וגו'", "וגו", "וכו׳", "וכו'", "וכו"]
    after_after_far_reg = r"(?:^|\s)(?{}:)(?=\s|$)".format("|".join(after_indicators_after_far))
    found_title = found.index.get_title("he")
    found_node = library.get_schema_node(found_title, "he")
    title_nodes = {t: found_node for t in found.index.all_titles("he")}
    all_reg = library.get_multi_title_regex_string(set(found.index.all_titles("he")), "he")
    reg = regex.compile(all_reg, regex.VERBOSE)
    if len(source_tc.text) == 0 or not isinstance(source_tc.text, str):
        print(source_tc._oref)
    source_text = re.sub(r"<[^>]+>", "", strip_cantillation(source_tc.text, strip_vowels=True))
    linkified = library._wrap_all_refs_in_string(title_nodes, reg, source_text, "he")

    snippets = []
    found_normal = found.normal()
    found_section_normal = re.match(r"^[^:]+", found_normal).group()
    for match in re.finditer("(<a [^>]+>)([^<]+)(</a>)", linkified):
        ref = Ref(match.group(2))
        # use split_spanning_ref in case where talmud ref is amudless. It's essentially a ranged ref across two amudim
        if len({found_section_normal, found_normal} & {temp_ref.normal() for temp_ref in ref.split_spanning_ref()}) > 0 or ref.normal() == found_normal or ref.normal() == found_section_normal:
            if return_matches:
                snippets += [(match, linkified)]
            else:
                start_snip_naive = match.start(1) - snip_size if match.start(1) >= snip_size else 0
                start_snip_space = linkified.rfind(" ", 0, start_snip_naive)
                start_snip_link = linkified.rfind("</a>", 0, match.start(1))
                start_snip = max(start_snip_space, start_snip_link)
                if start_snip == -1:
                    start_snip = start_snip_naive
                end_snip_naive = match.end(3) + snip_size if match.end(3) + snip_size <= len(linkified) else len(linkified)
                end_snip_space = linkified.find(" ", end_snip_naive)
                end_snip_link = linkified.find("<a ", match.end(3))
                end_snip = min(end_snip_space, end_snip_link)
                if end_snip == -1:
                    end_snip = end_snip_naive

                if use_indicator_words:
                    before_snippet = linkified[start_snip:match.start(1)]
                    if "ירושלמי" in before_snippet[-20:] and (len(ref.index.categories) < 2 or ref.index.categories[1] != 'Yerushalmi'):
                        # this guys not a yerushalmi but very likely should be
                        continue
                    after_snippet = linkified[match.end(3):end_snip]
                    if re.search(after_reg, before_snippet) is not None:
                        temp_snip = after_snippet
                        # print before_snippet
                    else:
                        temp_snip = linkified[start_snip:end_snip]
                else:
                    temp_snip = linkified[start_snip:end_snip]
                snippets += [re.sub(r"<[^>]+>", "", temp_snip)]

    if len(snippets) == 0:
        if must_find_snippet:
            return None
        return [source_text]

    return snippets


def modify_text(user, oref, versionTitle, language, text, versionSource, tries=0):
    try:
        tracker.modify_text(user, oref, versionTitle, language, text, versionSource, method="API", skip_links=False)
    except UnicodeEncodeError:
        print("UnicodeEncodeError: {}".format(oref.normal()))
        pass  # there seems to be unicode error in "/app/sefaria/system/varnish/wrapper.py", line 55
    except AutoReconnect:
        if tries < 200:
            modify_text(user, oref, versionTitle, language, text, versionSource, tries=tries+1)
        else:
            raise AutoReconnect("Tried so hard but got so many autoreconnects...")
    except AssertionError:
        pass


def wrap_chars_with_overlaps(s, chars_to_wrap, get_wrapped_text):
    chars_to_wrap.sort(key=lambda x: (x[0],x[0]-x[1]))
    for i, (start, end, metadata) in enumerate(chars_to_wrap):
        wrapped_text, start_added, end_added = get_wrapped_text(s[start:end], metadata)
        s = s[:start] + wrapped_text + s[end:]
        for j, (start2, end2, metadata2) in enumerate(chars_to_wrap[i+1:]):
            if start2 > end:
                start2 += end_added
            start2 += start_added
            if end2 > end:
                end2 += end_added
            end2 += start_added
            chars_to_wrap[i+j+1] = (start2, end2, metadata2)
    return s


def get_mapping_after_normalization(text, find_text_to_remove=None, removal_list=None):
    """
    Example.
        text = "a###b##c" find_text_to_remove = lambda x: [(m, '') for m in re.finditer(r'#+', x)]
        will return {1: 3, 2: 5}
        meaning by the 2nd index, 5 chars have been removed
        then if you have a range (0,3) in the normalized string "abc" you will know that maps to (0, 8) in the original string
    """
    if removal_list is None:
        removal_list = find_text_to_remove(text)
    total_removed = 0
    removal_map = {}
    for removal, subst in removal_list:
        try:
            start, end = removal
        except TypeError:
            # must be match object
            start, end = removal.start(), removal.end()
        normalized_text_index = (start - total_removed)
        total_removed += (end - start - len(subst))
        removal_map[normalized_text_index] = total_removed
    return removal_map

def convert_normalized_indices_to_unnormalized_indices(normalized_indices, removal_map):
    from bisect import bisect_right
    removal_keys = sorted(removal_map.keys())
    unnormalized_indices = []
    for start, end in normalized_indices:
        unnorm_start_index = bisect_right(removal_keys, start) - 1
        unnorm_end_index = bisect_right(removal_keys, end-1) - 1

        unnorm_start = start if unnorm_start_index < 0 else start + removal_map[removal_keys[unnorm_start_index]]
        unnorm_end = end if unnorm_end_index < 0 else end + removal_map[removal_keys[unnorm_end_index]]
        unnormalized_indices += [(unnorm_start, unnorm_end)]
    return unnormalized_indices

_version_cache = {}
def get_full_version(v):
    global _version_cache
    key = (v.title, v.versionTitle, v.language)
    if key not in _version_cache:
        full_v = Version().load({"title": v.title, "versionTitle": v.versionTitle, "language": v.language})
        _version_cache[key] = full_v
    return _version_cache[key]

def modify_tanakh_links_one(main_ref, section_map, error_file_csv):
    try:
        main_tc, main_oref, main_version = get_tc(main_ref)
        if main_tc.is_merged:
            # not really possible but whatevs
            return
        # to make it _savable
        main_tc._saveable = True
        new_main_text = main_tc.text
        def find_text_to_remove(s):
            for m in re.finditer(r"(<[^>]+>|[\u0591-\u05bd\u05bf-\u05c5\u05c7])", s):
                yield m, ''
        removal_map = get_mapping_after_normalization(main_tc.text, find_text_to_remove)
        edited = False
        for section_tref, segment_ref_dict in list(section_map.items()):
            section_oref = get_tc(section_tref, True)
            quoted_list_temp = sorted(list(segment_ref_dict.items()), key=lambda x: x[0])
            segment_ref_list = [segment_ref_dict.get(i, None) for i in range(quoted_list_temp[-1][0]+1)]
            match_list = get_snippet_by_seg_ref(main_tc, section_oref, must_find_snippet=True, snip_size=65, return_matches=True)
            if match_list:
                if len(match_list) == len(segment_ref_list):
                    chars_to_wrap = []
                    for (m, linkified_text), r in zip(match_list, segment_ref_list):
                        if r is None:
                            # None is how I represent a bad match
                            continue
                        cumulative_a_tag_offset = (m.start(2)-len(re.sub(r"<[^>]+>", "", linkified_text[:m.start(2)])))
                        unnorm_inds = convert_normalized_indices_to_unnormalized_indices([(m.start(2)-cumulative_a_tag_offset, m.end(2)-cumulative_a_tag_offset)], removal_map)[0]
                        chars_to_wrap += [(unnorm_inds[0],unnorm_inds[1], r.he_normal())]
                        main_tc_snippet = main_tc.text[chars_to_wrap[-1][0]:chars_to_wrap[-1][1]]
                        assert  strip_cantillation(main_tc_snippet, strip_vowels=True) == m.group(2), f"\n\n\n-----\nmain tc snippet:\n'{main_tc_snippet}'\nmatch group 2:\n'{m.group(2)}'\nRef: {main_tc._oref.normal()}"
                    def get_wrapped_text(text, replacement):
                        return replacement, (len(replacement) - len(text)), 0
                    new_main_text = wrap_chars_with_overlaps(new_main_text, chars_to_wrap, get_wrapped_text)
                    edited = new_main_text != main_tc.text
                else:
                    raise InputError("DiffLen")
        if edited:
            v = main_version
            return {
                "version": get_full_version(v),
                "tref": main_ref,
                "text": new_main_text
            }
    except InputError as e:
        message = e.args[0]
        error_file_csv.writerow({"Quoting Ref": main_ref, "Error": message})


def modify_tanakh_links_all(start=0, end=None):
    error_file = open(ROOT + "/link_disambiguatore_errors.csv", "w")
    error_file_csv = csv.DictWriter(error_file, ["Quoting Ref", "Error"])
    total = 0
    user = 5842
    all_modify_bulk_text_input = {}  # key = (title, vtitle, lang). value = {"version", "user", "text_map"}
    with open(ROOT + "/unambiguous_links.csv", "r") as fin:
        cin = csv.DictReader(fin)
        mapping = defaultdict(lambda: defaultdict(dict))
        for row in cin:
            total += 1
            quoted_ref = get_tc(row["Quoted Ref"], True)
            if quoted_ref.primary_category != "Tanakh":
                continue
            section_ref = quoted_ref.section_ref().normal()
            curr_dict = mapping[row["Quoting Ref"]][section_ref]
            if curr_dict.get(int(row["Quote Num"]), None) is not None and curr_dict.get(int(row["Quote Num"]), None) != quoted_ref:
                print("{} - {}==={} - {}".format(row["Quoting Ref"], row["Quoted Ref"], curr_dict.get(int(row["Quote Num"]), None),row["Quote Num"]))
            curr_dict[int(row["Quote Num"])] = quoted_ref
        print("Total {}".format(total))

        for i, (k, v) in enumerate(tqdm(mapping.items(), total=len(mapping))):
            if i < start:
                continue
            if end is not None and i > end:
                continue
            single_edit = modify_tanakh_links_one(k, v, error_file_csv)
            if single_edit is None: continue
            vers = single_edit['version']
            key = (vers.title, vers.versionTitle, vers.language)
            if key not in all_modify_bulk_text_input:
                all_modify_bulk_text_input[key] = {
                    "version": vers,
                    "user": user,
                    "text_map": {
                        single_edit["tref"]: single_edit["text"]
                    }
                }
            else:
                all_modify_bulk_text_input[key]["text_map"][single_edit["tref"]] = single_edit["text"]
    for func_input in tqdm(all_modify_bulk_text_input.values(), total=len(all_modify_bulk_text_input)):
        tracker.modify_bulk_text(skip_links=True, count_after=False, **func_input)
    error_file.close()

modify_tanakh_links_all(start=0)
# Rashi on Sanhedrin 61b:23:2 defaultdict(<type 'dict'>, {u'Leviticus 5': {0: Ref('Leviticus 5:18')}})
