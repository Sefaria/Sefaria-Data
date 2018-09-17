# encoding=utf-8

import re
import cProfile
import pstats
import unicodedata
import sys
import unicodecsv
import django
django.setup()
from sefaria.model import *
from data_utilities.dibur_hamatchil_matcher import match_ref
from sefaria.system.database import db
from sefaria.system.exceptions import InputError
from sefaria.utils.hebrew import strip_cantillation

MAX_SHEET_LEN = 100


def clean(s):
    if len(s) == 0:
        return s
    s = unicodedata.normalize("NFD", s)
    s = strip_cantillation(s, strip_vowels=True)

    # please forgive me...
    # replace common hashem replacements with the tetragrammaton
    s = re.sub(ur"(^|\s)([\u05de\u05e9\u05d5\u05db\u05dc\u05d1]?)(?:\u05d4['\u05f3]|\u05d9\u05d9)($|\s)", ur"\1\2\u05d9\u05d4\u05d5\u05d4\3", s)


    s = re.sub(ur"[,'\":?!;־״׳]", u" ", s)  # purposefully leave out period so we can replace ... later on
    s = re.sub(ur"\([^)]+\)", u" ", s)
    s = re.sub(ur"<[^>]+>", u"", s)
    s = u" ".join(s.split())
    return s


def tokenizer(s):
    return clean(s).split()


def refine_ref_by_text(ref, en, he, truncate_sheet=True, **kwargs):
    """
    Given a ref, determine if the text associated with it matches the text of the ref
    :param ref: Ref
    :param en: english text of source sheet. can be empty string
    :param he: hebrew text of source sheet. can be empty string
    :param truncate_sheet: bool, True if you want to truncate long sheets. a good optimization if you know the sheet text matches the ref very exactly
    :return: either None if you couldn't find a better ref or a refined ref
    """
    dominant_lang = "en" if (len(he) == 0 and len(en) > 0) or (0 < len(he) <= 10 and ((1.0*len(en)) / len(he) > 10.0)) else "he"  # only choose english if its way longer
    sheet_text = en if (len(he) == 0 and len(en) > 0) or (0 < len(he) <= 10 and ((1.0*len(en)) / len(he) > 10.0)) else he
    if len(sheet_text) > MAX_SHEET_LEN and truncate_sheet:
        start_sheet_text = sheet_text[:sheet_text.find(u" ", min(len(sheet_text)/2, MAX_SHEET_LEN))]
        end_sheet_text = sheet_text[sheet_text.find(u" ", max(len(sheet_text)/2, len(sheet_text)-MAX_SHEET_LEN))+1:]
        start_ref = find_subref(start_sheet_text, ref, dominant_lang, **kwargs)
        if start_ref is None:
            new_ref = None
        else:
            end_ref = find_subref(end_sheet_text, ref, dominant_lang, **kwargs)
            if end_ref is not None:
                new_ref = start_ref.to(end_ref)
            else:
                new_ref = None
    else:
        new_ref = find_subref(sheet_text, ref, dominant_lang, **kwargs)

    if new_ref is None and ref.is_segment_level():
        return refine_ref_by_text(ref.section_ref(), en, he)

    return new_ref


def find_subref(sheet_text, ref, lang, vtitle=None, tried_adding_refs_at_end_of_section=False, **kwargs):
    try:
        tc = TextChunk(ref, lang, vtitle=vtitle)
        matches = match_ref(tc, [sheet_text], tokenizer, dh_extract_method=clean, with_num_abbrevs=False, lang=lang, rashi_skips=2, dh_split=lambda dh: re.split(ur"\s*\.\.\.\s*", dh), **kwargs)
    except IndexError:
        # thrown if base text is empty
        matches = {"matches": []}
    except ValueError:
        matches = {"matches": []}
    found_ref = None
    for r in matches["matches"]:
        if r is not None:
            found_ref = r
            break
    if found_ref is None:
        if ref.primary_category == "Tanakh" and lang == "en" and vtitle is None:
            return find_subref(sheet_text, ref, lang, "The Holy Scriptures: A New Translation (JPS 1917)")
        elif ref.primary_category == "Talmud" and vtitle is None:
            if lang == "he":
                return find_subref(sheet_text, ref, lang, "Wikisource Talmud Bavli")
            else:
                return find_subref(sheet_text, ref, lang, "Sefaria Community Translation")
        elif ref.primary_category == "Talmud" and ref.is_section_level() and not tried_adding_refs_at_end_of_section:
            # you tried wiki and it didn't work
            # you're running out of options, what do you do?
            # add first and last seg from prev and next daf!!!
            prev_daf = ref.prev_section_ref()
            next_daf = ref.next_section_ref()
            start_ref = prev_daf.all_segment_refs()[-1] if prev_daf is not None else ref
            end_ref = next_daf.all_segment_refs()[0] if next_daf is not None else ref
            new_ref = start_ref.to(end_ref)
            return find_subref(sheet_text, new_ref, lang, tried_adding_refs_at_end_of_section=True)
    return found_ref


def mutate_sheet(sheet, action):
    rows = []
    for s in sheet["sources"]:
        rows += mutate_subsources(sheet["id"], s, action)

    return rows


def mutate_subsources(id, source, action):
    ref = source.get("ref", u"")
    he = source.get("text", {}).get("he", u"")
    he = u" ".join(tokenizer(he))
    en = source.get("text", {}).get("en", u"")
    en = u" ".join(tokenizer(en))
    new_ref_list = []
    if not ref:
        return new_ref_list
    try:
        ref_obj = Ref(ref)
        new_ref = action(ref_obj, en, he)
    except InputError as e:
        return new_ref_list

    if new_ref is not None and new_ref is not True:
        new_ref = new_ref.normal()
        old_ref = ref_obj.normal()
        if new_ref != old_ref:
            new_ref_list += [{"Id": str(id), "Old Ref": old_ref, "New Ref": new_ref, "Url": "https://www.sefaria.org/sheets/{}".format(id)}]

    if "subsources" in source:
        print "subsources"
        for s in source["subsources"]:
            new_ref_list += mutate_subsources(id, s, action)

    return new_ref_list


def run():
    # ids = [1697, 2636, 8689, 11419, 13255, 16085, 18838, 26981, 27226, 31603, 31844, 35830, 49364, 50853, 57106, 65498,
    #        85003, 90289, 92571, 101667, 105718]
    ids = db.sheets.find({"status": "public"}).distinct("id")
    rows = []
    for i, id in enumerate(ids):
        if i % 50 == 0:
            print "{}/{}".format(i, len(ids))
        sheet = db.sheets.find_one({"id": id})
        if not sheet:
            print "continue"
            continue
        rows += mutate_sheet(sheet, refine_ref_by_text)
    with open("yoyo.csv", "wb") as fout:
        csv = unicodecsv.DictWriter(fout, ["Id", "Url", "Old Ref", "New Ref"])
        csv.writeheader()
        csv.writerows(rows)

if __name__ == '__main__':
    profiling = False
    if profiling:
        print "Profiling...\n"
        cProfile.run("run()", "stats")
        p = pstats.Stats("stats")
        sys.stdout = sys.__stdout__
        p.strip_dirs().sort_stats("cumulative").print_stats()
    else:
        run()
