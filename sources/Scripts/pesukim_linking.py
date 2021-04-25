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


def link_options_to_links(link_options, post=False, qa_url = True):
    links=[]
    for link_option in link_options:
        link = Link({"type": 'midrash',
            "refs": [link_option[0].normal(), link_option[1].normal()],
            "generated_by": "yalkut_shimoni_linker"
             })
        links.append(link.contents())
        if qa_url:
            print(f'www.sefaria.org/{link_option[0]}?lang=he&p2={link_option[1]}&lang2=he&aliyot2=0')
    if post:
        post_link(links)
    return links


if __name__ == '__main__':
    import random
    peared = get_zip_ys()
    book =random.sample(range(5),1)[0]
    pear = peared[book][random.sample(range(len(peared[book])), 1)[0]]
    for torah, ys in peared[book]:
        matches = get_matches((torah, ys))
        link_options_to_links(matches)