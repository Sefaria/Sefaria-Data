# -*- coding: utf-8 -*-
import django
django.setup()
from sefaria.model import *
from sources.functions import *
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
from commentatorToCommentatorLinking import tokenizer, get_score


def addMidrashRabbahMegillotLinks(midrash_name):
    links = []
    midrash_index = library.get_index(midrash_name)
    megillah_name = midrash_name.replace(" Rabbah", "")

    if megillah_name == u"Shir HaShirim":
        pasuk_refs = midrash_index.all_section_refs()
        for comment_refs in pasuk_refs:
            for comment_ref in comment_refs.all_subrefs():
                location_index = len(comment_ref.normal().split()) - 1
                perek, pasuk, comment = comment_ref.normal().split()[location_index].split(":")

                megillah_ref = "{} {}:{}".format(megillah_name, perek, pasuk)
                link = {"refs": [comment_ref.normal(), megillah_ref],
                        "generated_by": "midrash_rabbah_to_megillot_linker",
                        "auto": True,
                        "type": "Midrash"}
                links.append(link)
    else:
        perek_refs = midrash_index.all_section_refs()
        for perek_ref in perek_refs:
            for comment_ref in perek_ref.all_subrefs():
                location_index = len(comment_ref.normal().split()) - 1
                if u"Eichah" in comment_ref.normal() and u"Petichta" not in comment_ref.normal():
                    perek, comment = comment_ref.normal().split()[location_index].split(":")
                    match = megillah_match(comment_ref, megillah_name, perek)
                else:
                    match = megillah_match(comment_ref, megillah_name)

                if match:
                    perek, pasuk = match
                    megillah_ref = "{} {}:{}".format(megillah_name, perek, pasuk)
                    link = {"refs": [comment_ref.normal(), megillah_ref],
                            "generated_by": "midrash_rabbah_to_megillot_linker",
                            "auto": True,
                            "type": "Midrash"}
                    links.append(link)
    post_link(links, server=SEFARIA_SERVER)
    return links

def megillah_match(comment_ref, megillah_name, perek=None, pasuk=None):
    if pasuk:
        matcher = ParallelMatcher(tokenizer=tokenizer, min_words_in_match=2, ngram_size=3, only_match_first=True, all_to_all=False, min_distance_between_matches=0, verbose=False, calculate_score=get_score, max_words_between=2, dh_extract_method=get_around_name)
        pasuk_ref_normal = "{} {}:{}".format(megillah_name, perek, pasuk)
        ref_list = [comment_ref.normal(), pasuk_ref_normal]
    elif perek:
        matcher = ParallelMatcher(tokenizer=tokenizer, min_words_in_match=3, ngram_size=4, only_match_first=True, all_to_all=False, min_distance_between_matches=0, verbose=False, calculate_score=get_score, max_words_between=3, dh_extract_method=get_around_name)
        ref_list = []
        perek_ref_normal = "{} {}".format(megillah_name, perek)
        perek_ref = Ref(perek_ref_normal)
        for pasuk_ref in perek_ref.all_subrefs():
            ref_list.append(pasuk_ref.normal())
        ref_list.insert(0, comment_ref.normal())
    else:
        matcher = ParallelMatcher(tokenizer=tokenizer, min_words_in_match=3, ngram_size=4, only_match_first=True, all_to_all=False, min_distance_between_matches=0, verbose=False, calculate_score=get_score, max_words_between=3, dh_extract_method=get_around_name)
        ref_list = []
        megillah_ref = Ref(megillah_name)
        for perek_ref in megillah_ref.all_subrefs():
            for pasuk_ref in perek_ref.all_subrefs():
                ref_list.append(pasuk_ref.normal())
        ref_list.insert(0, comment_ref.normal())

    results = matcher.match(tref_list=ref_list, return_obj=True, comment_index_list=[0])
    match_dict = {match: match.score for match in results}
    if match_dict:
        max_match = max(match_dict, key=match_dict.get)
        if max_match.score < 0:
            print "Match was bad for {}".format(comment_ref.normal())
            return 0
        location_index = len(max_match.a.mesechta.split()) - 1
        perek, pasuk = max_match.a.ref.normal().split()[location_index].split(":")
        print "Match found."
        return perek, pasuk



    matcher2 = ParallelMatcher(tokenizer=tokenizer, min_words_in_match=2, ngram_size=3, only_match_first=True,
                              all_to_all=False, min_distance_between_matches=0, verbose=False,
                              calculate_score=get_score, max_words_between=3, dh_extract_method=get_around_name)
    results2 = matcher2.match(tref_list=ref_list, return_obj=True, comment_index_list=[0])
    match_dict2 = {match: match.score for match in results2}
    if match_dict2:
        max_match2 = max(match_dict2, key=match_dict2.get)
        if max_match2.score < 0:
            print " (2nd try) Match was bad for {}".format(comment_ref.normal())
            return 0
        location_index = len(max_match2.a.mesechta.split()) - 1
        perek, pasuk = max_match2.a.ref.normal().split()[location_index].split(":")
        print "(2nd try) Match found."
        return perek, pasuk

    print "No match was found for {}".format(comment_ref.normal())
    return 0

def get_around_name(text):
    return " ".join(text.split()[0:15] + text.split()[len(text.split())-15:])


if __name__ == '__main__':
    result = addMidrashRabbahMegillotLinks("Eichah Rabbah")
