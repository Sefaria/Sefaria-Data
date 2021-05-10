# -*- coding: utf-8 -*-
import django
django.setup()

import string
from sources.functions import *
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
from sources.Scripts.commentatorToCommentatorLinking import tokenizer, get_score
from data_utilities.dibur_hamatchil_matcher import *
from sefaria.utils.hebrew import strip_cantillation
import math
import random

def get_zip_ys(): #lista_listb(text_a, text_b):
    '''
    this is a specific func for Yalkut Shimoni that zips the Torah Perek devsion with the Torah Perakim TC
    :return: list of tuples, (ys perek ,torah perek)
    '''
    ys = library.get_index('Yalkut Shimoni on Torah')
    ys_books = ys.get_alt_struct_nodes()
    books = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']
    # for ys_b, book in (ys_books, books):
    #     perakim = library.get_index(book).all_section_refs()
    #     pear = zip(ys_b.refs, perakim)
    peared = [list(zip(library.get_index(book).all_section_refs(), map(lambda r: Ref(r) if r else None, ys_b.refs))) for ys_b, book in zip(ys_books, books)]
    return peared


def get_zip_parashot_refs(ind_name, only_first_seg_comment=False):
    """

    :param ind_name: index that has an sturct with parashot
    :return:
    """
    ind = library.get_index(ind_name)
    nodes = [node["key"] for node in ind.schema["nodes"]]
    peared = []
    for node in nodes:
        try:
            r_parasha = Ref(f"Parashat {node}")
            r_comment = Ref(f"{ind_name}, {node}")
        except:
            continue
        if only_first_seg_comment:
            r_comment = r_comment.all_segment_refs()[0]
            # r_comment_seg = r_comment.all_segment_refs()[0]
        # else:
        #     r_comment_seg = r_comment
        pair = (r_parasha, r_comment)
        print(pair)
        peared.append(pair)
    return peared


def tok(st):
    import string
    from sefaria.utils.hebrew import strip_cantillation

    st = strip_cantillation(st, strip_vowels=True)
    st = re.sub(f'[{string.punctuation}־]', ' ', st)
    st = st.split()
    return st


def get_matches(coupled_refs):
    """

    :param coupled_refs: base_ref, comment_ref
    :return:
    """
    match_list = best_reflinks_for_maximum_dh(coupled_refs[0], coupled_refs[1], tokenizer=tok, max_dh_len=7, min_dh_len=3) # use *zip also itertools.izip(*iterables)
    return match_list


def link2url(link):
    ref1, ref2 = link.refs
    url = re.sub(" ", "_", f'www.sefaria.org/{ref1}?lang=he&p2={ref2}&lang2=he')
    return url


def link_options_to_links(link_options, link_type='', post=False, qa_url=True, max_score = 500):
    links=[]
    for link_option in link_options:
        link = Link({"type": link_type,
            "refs": [link_option[0].normal(), link_option[1].normal()],
            "generated_by": "yalkut_shimoni_linker",
            "auto": True
             })
        score = link_option[3].score
        if score < max_score:
            links.append(link)
        else:
            link_options.remove(link_option)
        if qa_url:
            # print(f'www.sefaria.org/{link_option[0]}?lang=he&p2={link_option[1]}&lang2=he&aliyot2=0')
            print(link_option[3].score)
            print(link2url(link))
            matched_wds_1 = link_option[3].textMatched
            matched_wds_2 = link_option[3].textToMatch
            if matched_wds_1 != matched_wds_2:
                print(f"{matched_wds_1} | {matched_wds_2}")

    if post:
        post_link(links)
    return links, link_options


if __name__ == '__main__':
    peared = get_zip_ys()
    book =random.sample(range(5), 1)[0]
    pear = peared[book][random.sample(range(len(peared[book])), 1)[0]]
    for torah, ys in peared[book]:
        matches = get_matches((torah, ys))
        link_options_to_links(matches, link_type="Midrash")
    # peared = get_zip_parashot_refs("Degel Machaneh Ephraim")
    # peared = get_zip_parashot_refs("Ohev Yisrael")
    # # print(len(peared))
    # cnt_links = 0
    # for torah, dme in peared:
    # #     matches = get_matches((torah, dme))
    #     matches_dict = match_ref(torah.text('he'), dme.text('he'),
    #                     base_tokenizer=tok,
    #                     dh_extract_method=lambda st: [x for x in re.split("<b>(.*?)<.b>", st) if x][0])
    #     raw_matches = list(zip(matches_dict['matches'], matches_dict['comment_refs']))
    #     matches = [m for m in raw_matches if m[0] and m[1]]
    #     links = link_options_to_links(matches, link_type='Chasidut', post=True)
    #     cnt_links += len(links)
    # print(cnt_links)
    #

