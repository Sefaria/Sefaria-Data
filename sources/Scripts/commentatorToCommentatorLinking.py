# -*- coding: utf-8 -*-
import django
django.setup()
from sefaria.model import *
from data_utilities.dibur_hamatchil_matcher import *
from sources.functions import *
from sefaria.utils.hebrew import *
from data_utilities.parallel_matcher import ParallelMatcher
import unicodedata
import bleach
from data_utilities.weighted_levenshtein import WeightedLevenshtein
import functools


def getCommentatorToCommentatorLinks(base_text_index, to_link_name_he_list, to_link_index_en):
    to_link_name_he = to_link_name_he_list[0]
    curr_get_around_name = functools.partial(get_around_name, name=to_link_name_he)
    assert is_hebrew(to_link_name_he)
    links = []
    pasuk_refs = base_text_index.all_section_refs()
    for pasuk_ref in pasuk_refs:
        for dh_ref in pasuk_ref.all_subrefs():
            commentator_ref = ""
            text = dh_ref.text("he").text
            if "Introduction" in dh_ref.normal():
                continue
            if to_link_name_he == "Onkelos" or to_link_name_he == u"אונקלוס":
                if to_link_name_he in text:
                    commentator_ref = "{} {}:{}".format(to_link_index_en.get_title(), dh_ref.normal_sections()[0],
                                                        dh_ref.normal_sections()[1])
            else:
                if to_link_name_he in text:
                    pasuk, dh = getDhNum(dh_ref, to_link_name_he, to_link_index_en, curr_get_around_name)
                    if pasuk == -1 and dh == -1:
                        continue
                    commentator_ref = "{} {}:{}:{}".format(to_link_index_en.get_title(), dh_ref.normal_sections()[0],
                                                           pasuk, dh)
            if commentator_ref:
                link = {"refs": [dh_ref.normal(), commentator_ref],
                        "generated_by": "Commentator to Commentator Linker",
                        "auto": True,
                        "type": "Commentary"}
                links.append(link)
    if links:
        post_link(links, server=SEFARIA_SERVER)
    else:
        getCommentatorToCommentatorLinks(base_text_index, [to_link_name_he_list[1]], to_link_index_en)
    return links


def getDhNum(dh_ref, to_link_name_he, to_link_index_en, curr_get_around_name):
    commentator_ref = "{} {}:{}".format(to_link_index_en.get_title(), dh_ref.normal_sections()[0],
                                        dh_ref.normal_sections()[1])
    subrefs = Ref(commentator_ref).all_subrefs()
    if len(subrefs) == 1:
        print("(new)")
    base = dh_ref.text("he")
    text = Ref(commentator_ref).text("he")
    ref_list = [ref.normal() for ref in Ref(commentator_ref).all_subrefs()]
    ref_list.insert(0, dh_ref.normal())
    matcher = ParallelMatcher(tokenizer=tokenizer, min_words_in_match=4, ngram_size=5, all_to_all=False, only_match_first=True, min_distance_between_matches=0, verbose=False, calculate_score=get_score, dh_extract_method=curr_get_around_name)
    results = matcher.match(tref_list=ref_list, comment_index_list=[0], return_obj=True)
    match_dict = {match: match.score for match in results}
    if match_dict:
        max_match = max(match_dict, key=match_dict.get)
        if max_match.score > 0:
            print("second chance link: " + dh_ref.tref + " " + str(max_match.b.location) + " --> " + max_match.a.mesechta + " " + str(max_match.a.location))
            trash, pasuk, dh = max_match.a.mesechta.split(":")
            return pasuk, dh
        else:
            print("Match was bad for {}".format(dh_ref.normal()))

    matcher2 = ParallelMatcher(tokenizer=tokenizer, min_words_in_match=2, ngram_size=3, all_to_all=False,
                              only_match_first=True, min_distance_between_matches=0, verbose=False,
                              calculate_score=get_score, dh_extract_method=curr_get_around_name)
    commentator_ref2 = "{} {}".format(to_link_index_en.get_title(), dh_ref.normal_sections()[0])
    ref_list2 = [ref.normal() for pasuk_ref in Ref(commentator_ref2).all_subrefs() for ref in pasuk_ref.all_subrefs()]
    ref_list2.insert(0, dh_ref.normal())
    results2 = matcher2.match(tref_list=ref_list2, comment_index_list=[0], return_obj=True)
    match_dict2 = {match: match.score for match in results2}
    if match_dict2:
        max_match2 = max(match_dict2, key=match_dict2.get)
        if max_match2.score > 0:
            print("last resort link: " + dh_ref.tref + " " + str(max_match2.b.location) + " --> " + max_match2.a.mesechta + " " + str(max_match2.a.location))
            trash, pasuk, dh = max_match2.a.mesechta.split(":")
            return pasuk, dh
        print("Match was bad for {}".format(dh_ref.normal()))

    print("getDhNum didn't work for ref {}".format(dh_ref.tref))
    return -1, -1

def get_around_name(text, name):
    segments = text.split(name)
    index = 0
    new_segs = ""
    starting = False
    ending = False
    last = False
    for segment in segments:
        if not segments.index(segment) == len(segments) - 1:
            index += len(segment.split())
        else:
            break
        if index < 10:
            starting = True
        if index > len(text) - 12:
            ending = True
        if starting and ending:
            new_seg = segment
        elif starting:
            new_seg = " ".join(text.split()[0:index + 11])
        elif ending:
            new_seg = " ".join(text.split()[index - 10:])
        else:
            new_seg = " ".join(text.split()[index-10:index+11])
        new_segs += new_seg
    return new_segs


def clean(s):
    s = unicodedata.normalize("NFD", s)
    s = strip_cantillation(s, strip_vowels=True)
    s = re.sub(u"(^|\s)(?:\u05d4['\u05f3])($|\s)", u"\1יהוה\2", s)
    s = re.sub(u"[,'\":?.!;־״׳]", u" ", s)
    s = re.sub(u"\([^)]+\)", u" ", s)
    # s = re.sub(ur"\((?:\d{1,3}|[\u05d0-\u05ea]{1,3})\)", u" ", s)  # sefaria automatically adds pasuk markers. remove them
    s = re.sub(u"<[^>]+>", u" ", s)
    s = u" ".join(s.split())
    return s


def tokenizer(s):
    return clean(s).split()

def get_score(words_a, words_b):
    normalizingFactor = 100
    smoothingFactor = 1
    ImaginaryContenderPerWord = 22
    str_a = u" ".join(words_a)
    str_b = u" ".join(words_b)

    score_if_uneven = score_uneven(words_a, words_b)
    if score_if_uneven:
        return score_if_uneven

    levenshtein = WeightedLevenshtein()
    dist = levenshtein.calculate(str_a, str_b,normalize=False)
    score = 1.0 * (dist + smoothingFactor) / (len(str_a) + smoothingFactor) * normalizingFactor

    dumb_score = (ImaginaryContenderPerWord * len(words_a)) - score
    return dumb_score

def score_uneven(words_a, words_b):
    if len(words_a) > len(words_b):
        return get_max_score(words_a, words_b, len(words_b))
    elif len(words_a) < len(words_b):
        return get_max_score(words_b, words_a, len(words_a))

def get_max_score(words_gr, words_sm, word_range):
    index = 0
    scores = []
    levenshtein = WeightedLevenshtein()
    while index <= len(words_gr) - word_range:
        cur_window = words_gr[index:index + word_range]
        str_a = u" ".join(cur_window)
        str_b = u" ".join(words_sm)
        dist = levenshtein.calculate(str_a, str_b, normalize=False)
        score = 1.0 * (dist + smoothingFactor) / (len(str_a) + smoothingFactor) * normalizingFactor

        dumb_score = (ImaginaryContenderPerWord * len(str_a)) - score
        scores.append(dumb_score)
        index += 1
    return max(scores)


if __name__ == "__main__":
    books = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]
    commentators = [("Rashi on", [u"רש\"י", u"רש\'\'י"]), ("Ibn Ezra on", [u"רבי אברהם", u"ר\'\'א"]), ("Onkelos", [u"אונקלוס"])]
    for commentator, heb_name_list in commentators:
        for book in books:
            base = library.get_index("Ramban on {}".format(book))
            index = library.get_index("{} {}".format(commentator, book))
            result = getCommentatorToCommentatorLinks(base, heb_name_list, index)

