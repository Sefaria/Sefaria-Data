# encoding=utf-8

import re
import unicodecsv
import bisect
import bleach
import django
django.setup()
from sefaria.model import *
from data_utilities.dibur_hamatchil_matcher import match_ref
from sefaria.system.database import db
from sefaria.system.exceptions import InputError, BookNameError
from sefaria.utils.hebrew import strip_cantillation
import unicodedata

MAX_SHEET_LEN = 100


def clean(s):
    s = unicodedata.normalize("NFD", s)
    s = strip_cantillation(s, strip_vowels=True)
    s = re.sub(u"(^|\s)(?:\u05d4['\u05f3])($|\s)", u"\1יהוה\2", s)
    s = re.sub(ur"[,'\":?.!;־״׳]", u" ", s)
    s = re.sub(ur"\([^)]+\)", u" ", s)
    #s = re.sub(ur"\((?:\d{1,3}|[\u05d0-\u05ea]{1,3})\)", u" ", s)  # sefaria automatically adds pasuk markers. remove them
    s = bleach.clean(s, strip=True, tags=()).strip()
    s = u" ".join(s.split())
    return s


def tokenizer(s):
    return clean(s).split()


def get_token_info_for_ref(r, lang):
    tc = TextChunk(r, lang)
    ref_index_list, ref_list, total_len = tc.text_index_map(tokenizer)
    word_list = [w for seg in tc.ja().flatten_to_array() for w in tokenizer(seg)]
    word_index_list = reduce(lambda a, b: a + [len(b) + a[-1] + 1], word_list, [0])  # last element is extraneous but who cares
    actual_text = u" ".join(word_list)
    return ref_index_list, ref_list, word_index_list, actual_text


def refine_ref_by_text(ref, en, he, lenDiff=20, alwaysCheck=False, truncateSheet=True, **kwargs):
    """
    Given a ref, determine if the text associated with it matches the text of the ref
    :param ref: Ref
    :param en: english text of source sheet. can be empty string
    :param he: hebrew text of source sheet. can be empty string
    :param lenDiff: len diff b/w sheet text and ref text above which we dont consider them equal
    :param alwaysCheck: bool, True to ignore `lenDiff` and instead always check if the sheet matches the ref
    :param truncateSheet: bool, True if you want to truncate long sheets. a good optimization if you know the sheet text matches the ref very exactly
    :return: either True if text matches ref, None if you couldn't find a better ref or a refined ref
    """
    dominant_lang = "en" if len(he) == 0 or ((1.0*len(en)) / len(he) > 7.0) else "he"  # only choose english if its way longer
    sheet_text = en if len(he) == 0 or ((1.0*len(en)) / len(he) > 7.0) else he
    ref_index_list, ref_list, word_index_list, actual_text = get_token_info_for_ref(ref, dominant_lang)
    if len(word_index_list) == 0 or len(ref_list) == 0:
        return None
    if abs(len(sheet_text) - len(actual_text)) < lenDiff and not alwaysCheck:
        if len(ref_list) == 1 and ref_list[0].normal() != ref.normal():
            return ref_list[0]  # if there's only ref in the section, return it
        return True
    if len(sheet_text) > MAX_SHEET_LEN and truncateSheet:
        start_sheet_text = sheet_text[:sheet_text.find(u" ", min(len(sheet_text)/2, MAX_SHEET_LEN))]
        end_sheet_text = sheet_text[sheet_text.find(u" ", max(len(sheet_text)/2, len(sheet_text)-MAX_SHEET_LEN))+1:]
        start_ref = find_subref(start_sheet_text, ref, dominant_lang, **kwargs)
        end_ref = find_subref(end_sheet_text, ref, dominant_lang, **kwargs)
        if start_ref is not None and end_ref is not None:
            new_ref = start_ref.to(end_ref)
        else:
            new_ref = None
    else:
        new_ref = find_subref(sheet_text, ref, dominant_lang, **kwargs)

    if new_ref is None and ref.is_segment_level():
        #print "Trying section ref"
        return refine_ref_by_text(ref.section_ref(), en, he)
    #print u"Original:", ref
    #print u"New:", new_ref
    return new_ref


def find_subref(sheet_text, ref, lang, vtitle=None, tried_adding_refs_at_end_of_section=False, **kwargs):
    tc = TextChunk(ref, lang, vtitle=vtitle)
    matches = match_ref(tc, [sheet_text], tokenizer, dh_extract_method=clean, with_num_abbrevs=False, lang=lang, dh_split=lambda dh: re.split(ur"\s*\.\.\.\s*", dh), **kwargs)
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
    #print sheet["title"]
    #print sheet["id"]
    for s in sheet["sources"]:
        mutate_subsources(sheet["id"], s, action)


def mutate_subsources(id, source, action):
    ref = source.get("ref", "")
    he = source.get("text", {}).get("he", "")
    he = u" ".join(tokenizer(he))
    en = source.get("text", {}).get("en", "")
    en = u" ".join(tokenizer(en))
    if not ref:
        return
    try:
        ref_obj = Ref(ref)
        new_ref = action(ref_obj, en, he)
    except InputError as e:
        return

    if new_ref:
        new_ref = new_ref.normal()
        old_ref = ref_obj.normal()
        if new_ref != old_ref:
            pass

    if "subsources" in source:
        print "subsources"
        for s in source["subsources"]:
            mutate_subsources(id, s, action)



