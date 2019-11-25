# -*- coding: utf-8 -*-
import re, json, codecs, unicodecsv, heapq, random, regex, math, cProfile, pstats, time
from collections import defaultdict
from pymongo.errors import AutoReconnect
import django
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import PartialRefInputError, InputError, NoVersionFoundError
from sefaria.utils.hebrew import strip_cantillation
import sefaria.tracker as tracker
from sefaria import settings
from sefaria.system.database import db

"""
WARNING!!!!!!!!!!!!!
THERE'S AN ISSUE IN THIS SCRIPT THAT IT CAN POTENTIALLY REPLACE THE WRONG TEXT
E.G.
ואל אלהיה ורות א׳:ט״ז׳:ט״זמרה (רות א) עמך עמי וא-ל
"""

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
    source_text = re.sub(r"<[^>]+>", "", strip_cantillation(source_tc.text, strip_vowels=True))

    linkified = library._wrap_all_refs_in_string(title_nodes, reg, source_text, "he")

    snippets = []
    found_normal = found.normal()
    found_section_normal = re.match(r"^[^:]+", found_normal).group()
    for match in re.finditer("(<a [^>]+>)([^<]+)(</a>)", linkified):
        ref = get_tc(match.group(2), True)
        if ref.normal() == found_section_normal or ref.normal() == found_normal:
            if return_matches:
                snippets += [match]
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


def modify_tanakh_links_one(main_ref, section_map, error_file_csv, user):
    try:
        main_tc, main_oref, main_version = get_tc(main_ref)
        if main_tc.is_merged:
            # not really possible but whatevs
            return
        # to make it _savable
        main_tc._saveable = True
        new_main_text = main_tc.text
        edited = False
        for section_tref, segment_ref_dict in list(section_map.items()):
            section_oref = get_tc(section_tref, True)
            quoted_list_temp = sorted(list(segment_ref_dict.items()), key=lambda x: x[0])
            segment_ref_list = [segment_ref_dict.get(i, None) for i in range(quoted_list_temp[-1][0]+1)]
            # for r in segment_ref_list:
            #     if r is None:
            #         continue
            #     l = Link().load({"generated_by": "link_disambiguator", "refs": [main_ref, r.normal()]})
            #     if l and l.generated_by != "add_links_from_text":
            #         l.generated_by = "add_links_from_text"
            #         l.save()
            match_list = get_snippet_by_seg_ref(main_tc, section_oref, must_find_snippet=True, snip_size=65, return_matches=True)
            if match_list:
                if len(match_list) == len(segment_ref_list):
                    last_find = 0
                    for m, r in zip(match_list, segment_ref_list):
                        if r is None:
                            # None is how I represent a bad match
                            continue

                        original = m.group(2)
                        curr_find = new_main_text.find(original, last_find)
                        if curr_find == -1:
                            raise InputError("RefNotFound")
                        replacement = r.he_normal()
                        new_main_text = "{}{}{}".format(new_main_text[:curr_find], replacement, new_main_text[curr_find + len(original):])
                        edited = True
                        last_find = curr_find + len(replacement)


                else:
                    raise InputError("DiffLen")
        if edited:
            modify_text(user, main_oref, main_version.versionTitle, main_version.language, new_main_text, main_version.versionSource)
    except InputError as e:
        message = e.args[0]
        error_file_csv.writerow({"Quoting Ref": main_ref, "Error": message})


def modify_tanakh_links_all(start=0):
    error_file = open("link_disambiguatore_errors.csv", "wb")
    error_file_csv = unicodecsv.DictWriter(error_file, ["Quoting Ref", "Error"])
    total = 0
    user = db.apikeys.find_one({"key": "bi9SNdfZr9IBIHtDeKhF0bG7RPYVvVeIgDCBD8gpjjA"})["uid"]
    with open("unambiguous_links.json", "rb") as fin:
        cin = unicodecsv.DictReader(fin)
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

        for i, (k, v) in enumerate(mapping.items()):
            if i % 100 == 0:
                print("{}/{}".format(i, len(mapping)))
            if i < start:
                continue
            modify_tanakh_links_one(k, v, error_file_csv, user)
    error_file.close()

modify_tanakh_links_all(start=0)
# Rashi on Sanhedrin 61b:23:2 defaultdict(<type 'dict'>, {u'Leviticus 5': {0: Ref('Leviticus 5:18')}})
