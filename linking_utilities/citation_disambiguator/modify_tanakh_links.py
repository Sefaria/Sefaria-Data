import re, csv, time
import argparse
from typing import Dict, List, Optional
from collections import defaultdict
from pymongo.errors import AutoReconnect
from tqdm import tqdm
import django
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import InputError
from sefaria.utils.hebrew import strip_cantillation
import sefaria.tracker as tracker
from linking_utilities.citation_disambiguator.citation_disambiguator import get_snippet_by_seg_ref


def get_tc(tref, vtitle=None, just_ref=False, tries=0):
    try:
        main_oref = Ref(tref)
        if just_ref:
            return main_oref
        if vtitle is None:
            vset = main_oref.versionset()
            if len(vset) < 1:
                raise InputError("VSET not equal to 1")
            vtitle = vset[0].versionTitle
        main_tc = main_oref.text("he", vtitle=vtitle)
        return main_tc, main_oref, main_tc._versions[0]
    except AutoReconnect:
        if tries < 200:
            time.sleep(0.24)
            return get_tc(tref, vtitle=vtitle, just_ref=just_ref, tries=tries+1)
        else:
            raise AutoReconnect("Tried so hard but got so many autoreconnects...")


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
    from bisect import bisect_right, bisect_left
    removal_keys = sorted(removal_map.keys())
    unnormalized_indices = []
    for start, end in normalized_indices:
        unnorm_start_index = bisect_left(removal_keys, start) - 1
        unnorm_end_index = bisect_left(removal_keys, end - 1) - 1
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


def get_text_and_version_from_ref(oref, vtitle):
    main_tc, main_oref, main_version = get_tc(oref, vtitle=vtitle)
    assert not main_tc.is_merged
    return main_tc.text


def find_text_to_remove(s):
    for m in re.finditer(r"(<[^>]+>|[\u0591-\u05bd\u05bf-\u05c5\u05c7])", s):
        yield m, ''


def get_wrapped_text(text, replacement):
    return replacement, (len(replacement) - len(text)), 0


def convert_all_section_citations_to_segments(main_text, section_map):
    for section_tref, segment_ref_dict in list(section_map.items()):
        temp_main_text = convert_section_citation_to_segment_citation(main_text, section_tref, segment_ref_dict)
        if temp_main_text:
            main_text = temp_main_text
    return main_text


def convert_section_citation_to_segment_citation(main_text, section_tref, segment_ref_dict: Dict[int, Ref]):
    removal_map = get_mapping_after_normalization(main_text, find_text_to_remove)
    section_oref = get_tc(section_tref, just_ref=True)
    quoted_list_temp = sorted(list(segment_ref_dict.items()), key=lambda x: x[0])
    segment_ref_list = [segment_ref_dict.get(i, None) for i in range(quoted_list_temp[-1][0]+1)]
    match_list = get_snippet_by_seg_ref(main_text, section_oref, must_find_snippet=True, snip_size=65, return_matches=True)

    if not match_list:
        return None
    elif len(match_list) != len(segment_ref_list):
        raise InputError("DiffLen")

    chars_to_wrap = []
    for (m, linkified_text), r in zip(match_list, segment_ref_list):
        if r is None:
            # None is how I represent a bad match
            continue
        cumulative_a_tag_offset = (m.start(2)-len(re.sub(r"<[^>]+>", "", linkified_text[:m.start(2)])))
        unnorm_inds = convert_normalized_indices_to_unnormalized_indices([(m.start(2)-cumulative_a_tag_offset, m.end(2)-cumulative_a_tag_offset)], removal_map)[0]
        chars_to_wrap += [(unnorm_inds[0],unnorm_inds[1], r.he_normal())]
        main_tc_snippet = main_text[chars_to_wrap[-1][0]:chars_to_wrap[-1][1]]
        assert strip_cantillation(main_tc_snippet, strip_vowels=True) == m.group(2), f"\n\n\n-----\nmain tc snippet:\n'{main_tc_snippet}'\nmatch group 2:\n'{m.group(2)}'"
    return wrap_chars_with_overlaps(main_text, chars_to_wrap, get_wrapped_text)


def get_edit_for_quoting_segment(main_ref, section_map, error_file_csv, vtitle):
    try:
        orig_text, version_stub = get_text_and_version_from_ref(main_ref, vtitle)
        updated_text = convert_all_section_citations_to_segments(orig_text, section_map)
        if updated_text == orig_text:
            return None

        return {
            "version": get_full_version(version_stub),
            "tref": main_ref,
            "text": updated_text
        }
    except InputError as e:
        message = e.args[0]
        error_file_csv.writerow({"Quoting Ref": main_ref, "Error": message})


def modify_tanakh_links_all(input_filename, error_output_filename, start=0, end=None, min_num_citation=0):
    error_file = open(error_output_filename, "w")
    error_file_csv = csv.DictWriter(error_file, ["Quoting Ref", "Error"])
    total = 0
    user = 5842
    all_modify_bulk_text_input = {}  # key = (title, vtitle, lang). value = {"version", "user", "text_map"}
    with open(input_filename, "r") as fin:
        cin = csv.DictReader(fin)
        vtitle_mapping = {}
        mapping = defaultdict(lambda: defaultdict(dict))
        for row in cin:
            total += 1
            quoting_tref = row["Quoting Ref"]
            quoting_vtitle = row["Quoting Version Title"]
            quoted_tref = row["Quoted Ref"]
            quoted_ref = get_tc(quoted_tref, just_ref=True)
            if quoted_ref.primary_category != "Tanakh":
                continue
            vtitle_mapping[quoting_tref] = quoting_vtitle
            section_ref = quoted_ref.section_ref().normal()
            curr_dict = mapping[quoting_tref][section_ref]
            if curr_dict.get(int(row["Quote Num"]), None) is not None and curr_dict[int(row["Quote Num"])] != quoted_ref:
                print("{} - {}==={} - {}".format(quoting_tref, quoted_tref, curr_dict.get(int(row["Quote Num"]), None),row["Quote Num"]))
            curr_dict[int(row["Quote Num"])] = quoted_ref
        print("Total {}".format(total))

        for i, (quoting_tref, v) in enumerate(tqdm(mapping.items(), total=len(mapping))):
            if i < start:
                continue
            if end is not None and i > end:
                continue
            if len(v) < min_num_citation:
                continue
            single_edit = get_edit_for_quoting_segment(quoting_tref, v, error_file_csv, vtitle_mapping[quoting_tref])
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


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_filename')
    parser.add_argument('error_output_filename')
    parser.add_argument('--start', default=0, type=int)
    parser.add_argument('--end', default=None, type=int)
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    modify_tanakh_links_all(args.input_filename, args.error_output_filename, start=args.start, end=args.end)
