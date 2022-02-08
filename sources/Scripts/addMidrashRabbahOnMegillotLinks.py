# -*- coding: utf-8 -*-
import django
django.setup()

import string
from sources.functions import *
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
from sources.Scripts.commentatorToCommentatorLinking import tokenizer, get_score
from data_utilities.dibur_hamatchil_matcher import *
from sefaria.utils.hebrew import strip_cantillation


def addMidrashRabbahMegillotLinks(midrash_name):
    search_perek = 1
    links = []
    midrash_index = library.get_index(midrash_name)
    megillah_name = midrash_name.replace(" Rabbah", "")
    rows = []
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
                if u"Petichta" in comment_ref.normal():
                    continue
                location_index = len(comment_ref.normal().split()) - 1
                row = {'rabbah_ref': comment_ref.normal()}
                if megillah_name in comment_ref.normal() and u"Petichta" not in comment_ref.normal():
                    # if not search_perek:
                    #     search_perek, comment = comment_ref.normal().split()[location_index].split(":")
                    match = megillah_match(comment_ref, megillah_name, search_perek)
                else:
                    match = megillah_match(comment_ref, megillah_name)

                # if not match:
                #     match = megillah_match(comment_ref, megillah_name)
                #     if match:
                #         print(f"3rd time the charm {comment_ref}")
                if match:
                    perek, pasuk = match
                    megillah_ref = "{} {}:{}".format(megillah_name, perek, pasuk)
                    link = {"refs": [comment_ref.normal(), megillah_ref],
                            "generated_by": "midrash_rabbah_to_megillot_linker",
                            "auto": True,
                            "type": "quotation_auto"}
                    # links.append(link)
                else:
                    print(f"didn't find a match for {comment_ref}")
                q = {'$and': [{'refs': comment_ref.normal()}, {'refs': {'$regex': f'^{megillah_name} \d'}}]}
                ls_perek = LinkSet(q)
                if ls_perek.count():
                    search_perek = re.search(f'{megillah_name} (\d+):', ls_perek[0].refs[0]).group(1)
                    row['matcher'] = ''
                else:
                    row['matcher'] = megillah_ref
                    links.append(link)
                rows.append(row)

    write_to_csv(rows, 'matcher_links_2')
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
            print("Match was bad for {}".format(comment_ref.normal()))
            return 0
        location_index = len(max_match.a.mesechta.split()) - 1
        perek, pasuk = max_match.a.ref.normal().split()[location_index].split(":")
        print("Match found.")
        return perek, pasuk



    matcher2 = ParallelMatcher(tokenizer=tokenizer, min_words_in_match=2, ngram_size=3, only_match_first=True,
                              all_to_all=False, min_distance_between_matches=0, verbose=False,
                              calculate_score=get_score, max_words_between=3, dh_extract_method=get_around_name)
    results2 = matcher2.match(tref_list=ref_list, return_obj=True, comment_index_list=[0])
    match_dict2 = {match: match.score for match in results2}
    if match_dict2:
        max_match2 = max(match_dict2, key=match_dict2.get)
        if max_match2.score < 0:
            print(" (2nd try) Match was bad for {}".format(comment_ref.normal()))
            return 0
        location_index = len(max_match2.a.mesechta.split()) - 1
        perek, pasuk = max_match2.a.ref.normal().split()[location_index].split(":")
        print("(2nd try) Match found.")
        return perek, pasuk

    print("No match was found for {}".format(comment_ref.normal()))
    return 0


def get_around_name(text):
    return " ".join(text.split()[0:15] + text.split()[len(text.split())-15:])


def tok(st):
    st = strip_cantillation(st, strip_vowels=True)
    st = re.sub(f'[{string.punctuation}־]', ' ', st)
    st = st.split()
    return st


def get_link_option(pasuk, comment_ref):
    match = get_maximum_dh(base_text=TextChunk(pasuk, lang='he'), comment=TextChunk(comment_ref, lang='he').text,
                           tokenizer=tok, max_dh_len=7)
    link_option = (comment_ref, pasuk, match)
    return link_option


def eichah_DH_match(base_text, comment):
    link_options =[]
    flo = []
    chapter = Ref(base_text)
    comment_text = Ref(comment)
    for pasuk in chapter.all_segment_refs():
        for comment_ref in comment_text.all_segment_refs():
            link_option = get_link_option(pasuk, comment_ref)
            link_options.append(link_option)

    for comment_ref in comment_text.all_segment_refs():
        final_link_option = min([t for t in link_options if t[0] == comment_ref and t[2]], default=None, key=lambda t: t[2].score)
        if final_link_option:
            flo.append(final_link_option)
    return flo


def post_links(query):
    linkset = LinkSet(query)
    links = [l.contents() for l in linkset]
    post_link(links)
    return links


def link_options_to_links(link_options, post=False):
    links=[]
    for link_option in link_options:
        link = Link({"type": 'midrash',
            "refs": [link_option[0].normal(), link_option[1].normal()],
            "generated_by": "midrash_rabbah_to_megillot_linker"
             })
        links.append(link.contents())
    if post:
        post_link(links)
    return links

def based_on_old_linking(megillah):
    same = None
    links = []
    rows = []
    midrash_index = library.get_index(f'{megillah} Rabbah')
    perek_refs = midrash_index.all_section_refs()
    for perek_ref in perek_refs:
        for comment_ref in perek_ref.all_subrefs():
            if u"Petichta" in comment_ref.normal():
                continue
            q = {'$and': [{'refs.1': comment_ref.normal()}, {'refs.0': {'$regex': f'^{megillah} \d'}}]}
            ls = LinkSet(q)
            row = {
                'rabbah_ref': comment_ref.normal(),
                'rabbah_text': comment_ref.text('he').text,
                'current_links': [l.refs[0] for l in ls]
            }
            ls_count = ls.count()
            if not ls_count:
                assert same is not None
                link = {
                    "refs": [comment_ref.normal(), same],
                    "generated_by": "midrash_rabbah_to_megillot_linker",
                    "auto": True,
                    "type": "Quotation_auto"
                }
                row['simple'] = same
                links.append(link)
            elif ls_count>1:
                print(f'{comment_ref.normal()}: {[l.refs[0] for l in ls]}')
            elif ls_count == 1:
                same = ls[0].refs[0]
            rows.append(row)
    print([l['refs'] for l in links], '\n', len(links))
    # post_link(links)
    write_to_csv(rows, f'{megillah}_rabbah_{megillah}_links')


def write_to_csv(rows, file_name):
    with open(f'{file_name}.csv', 'a') as csv_file:
        writer = csv.DictWriter(csv_file, ['rabbah_ref', 'rabbah_text', 'current_links', 'simple', 'matcher'])  # fieldnames = obj_list[0].keys())
        writer.writeheader()
        writer.writerows(rows)

if __name__ == '__main__':

    result = addMidrashRabbahMegillotLinks("Esther Rabbah")
    # link_options = eichah_DH_match('Lamentations 2', 'Eichah Rabbah.2')
    # links = link_options_to_links(link_options, post=False)
    # Eichah_query = {"generated_by": {"$regex": "midrash_rabbah.*"}, "$and": [{"refs": {"$regex":"Eichah.*"}}]}
    # post_links(Eichah_query)
    # Ref_base, Ref_comm, dh, match
    # final_link_matches = best_reflinks_for_maximum_dh(Ref('Lamentations 1'), Ref('Eichah Rabbah.1'), tokenizer=tok, max_dh_len=7)
    # print(dh)
    # dh_length = len(dh.split())
    # comment_text = TextChunk(Ref_comm, lang="he").text
    # print(f'<em>{comment_text[0:dh_length]}<\em>{comment_text[dh_length::]}') #wrong approach
    based_on_old_linking('Esther')
    pass