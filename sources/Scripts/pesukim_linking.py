# -*- coding: utf-8 -*-
import django
django.setup()

import string
from sources.functions import *
from data_utilities.parallel_matcher import ParallelMatcher
from sources.Scripts.commentatorToCommentatorLinking import tokenizer, get_score
from data_utilities.dibur_hamatchil_matcher import *
from sefaria.utils.hebrew import strip_cantillation
import math
import random
from sefaria.model.link import update_link_language_availabiliy


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
    if 10 > len(ind.schema["nodes"]) >= 5:
        parasha_nodes = []
        books = True
        for b in ind.schema["nodes"]:
            parasha_nodes += b["nodes"]
    else:
        parasha_nodes = ind.schema["nodes"]
        books = False
    nodes = [node["key"] for node in parasha_nodes]

    peared = []
    for node in nodes:
        try:
            r_parasha = Ref(f"Parashat {node}")
            r_comment = Ref(f"{ind_name}, {f'{r_parasha.book}, ' if books else ''}{node}")
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
    st = re.sub('<.?b>', '', st)
    st = re.sub('עוד', '', st)
    st = st.split()
    return st


def get_matches(coupled_refs):
    """

    :param coupled_refs: base_ref, comment_ref
    :return:
    """
    match_list = best_reflinks_for_maximum_dh(coupled_refs[0], coupled_refs[1], tokenizer=tok, max_dh_len=12, min_dh_len=3)  # use *zip also itertools.izip(*iterables)
    return match_list


def link2url(link, sandbox="www"):
    if type(link) != Link:
        link = Link(link)
    ref1, ref2 = link.refs
    sandbox = f'{sandbox}.cauldron' if sandbox != 'www' else 'www'
    url = re.sub(" ", "_", f'{sandbox}.sefaria.org/{ref1}?lang=he&p2={ref2}&lang2=he')
    return url


def match_to_link_json(match, link_type='', generated_by=None, auto=True):
    link = {"type": link_type,
            "refs": [match[0].normal(), match[1].normal()],
            "auto": auto
             }
    if generated_by:
        link.update({"generated_by": generated_by})
    return link


def link_options_to_links(link_options, link_type='', post=False, qa_url=None, max_score=1000, min_score=0, max_dh = True, generated_by=""):
    links=[]
    for link_option in link_options:
        link = match_to_link_json(link_option, link_type=link_type, generated_by=generated_by, auto=True)
        if max_dh:
            # link = Link(link)
            score = link_option[3].score
            if score < max_score and score > min_score:
                links.append(link)
            else:
                link_options.remove(link_option)
        else:
            links.append(link)
        if qa_url:
            print(link2url(link, qa_url))
            if max_dh:
                print(link_option[3].score)
                matched_wds_1 = link_option[3].textMatched
                matched_wds_2 = link_option[3].textToMatch
                if matched_wds_1 != matched_wds_2:
                    print(f"{matched_wds_1} | {matched_wds_2}")

    if post and links:
        post_link(links)
    return links, link_options


def get_dme_linking(peared, post=True):
    ls_ys = LinkSet({"$and": [{"refs": {"$regex": "Degel Machaneh Ephraim.*"}},
                           {"generated_by": {"$ne": "yalkut_shimoni_linker"}}]})
    old_ys_links = [l["refs"][0] for l in ls_ys.contents()]
    cnt_topost_ys_links = 0
    for torah, dme in peared:
        topost_ys_links = []
    #     matches = get_matches((torah, dme))
        matches_dict = match_ref(torah.text('he'), dme.text('he'),
                        base_tokenizer=tok, dh_extract_method=lambda st:[x for x in re.split("<b>(.*?)<.b>", re.sub("וכו", ' ', st)) if x][0])
        raw_matches = list(zip(matches_dict['matches'], matches_dict['comment_refs']))
        matches = [m for m in raw_matches if m[0] and m[1]]
        matches2 = get_matches((torah, dme))
        links1, link_data1 = link_options_to_links(matches, link_type='chasidut', post=False, max_dh=False, generated_by="yalkut_shimoni_linker")  #, qa_url='chasidutlinking')
        links2, link_data2 = link_options_to_links(matches2, link_type='chasidut', post=False, max_dh=True, max_score=40, generated_by="yalkut_shimoni_linker")  #, qa_url='chasidutlinking')
        for link in links2:
            if link["refs"][1] in old_ys_links:
                links2.remove(link)
                continue  # this seg has a manual link already
            if link['refs'] in [l['refs'] for l in links1]:  # hence in both links1 and links2 => probabaly correct
                topost_ys_links.append(link)
                continue
            # only in links2
            link_dh = [l for l in links1 if l["refs"][1] == link["refs"][1]]
            if link_dh and Ref(link_dh[0]["refs"][0]).is_range():
                topost_ys_links.append(link_dh[0])
                links1.remove(link_dh[0])
                continue
            # last add the left links2:
            topost_ys_links.append(link)
        for link in links1: # not sure what to do with these, are they good links?
            if link["refs"][1] in old_ys_links:
                links1.remove(link)
                continue # this seg has a manual link already
            if link['refs'][1] not in [l['refs'][1] for l in links2]:
                topost_ys_links.append(link)
                print(link2url(link, "chasidutlinking"))
        if post:
            post_link(topost_ys_links)
        cnt_topost_ys_links += len(topost_ys_links)
    print(cnt_topost_ys_links)
    return cnt_topost_ys_links

def tweek_and_post_links(query):
    read_links = LinkSet(query)
    links = []
    for link in read_links:
        l = link.contents()
        l['generated_by'] = 'quotation_linker_dh'
        l['type'] = 'commentary'
        links.append(l)
    post_link(links)
    # update_link_language_availabiliy()

if __name__ == '__main__':
    # peared = get_zip_ys()
    # peared = get_zip_parashot_refs("Noam_Elimelech")
    # book =random.sample(range(5), 1)[0]
    # pear = peared[book][random.sample(range(len(peared[book])), 1)[0]]
    # # for torah, ys in peared[book]:
    # #     matches = get_matches((torah, ys))
    # #     link_options_to_links(matches, link_type="Midrash")
    # # peared = get_zip_parashot_refs("Ohev Yisrael")
    # # # print(len(peared))
    # topost_links = get_dme_linking(pear, post=False)
    # query = {"$and": [{"refs": {"$regex": "Degel Machaneh Ephraim.*"}}, {"generated_by": "yalkut_shimoni_linker"}]}
    query = {"$and": [{"refs": {"$regex": "Chiddushei HaRim on Torah.*"}}, {"type": "qutation"}]}
    tweek_and_post_links(query)

