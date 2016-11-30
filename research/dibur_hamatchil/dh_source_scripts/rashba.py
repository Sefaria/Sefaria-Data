# -*- coding: utf-8 -*-

#dibur hamatchil tokenizer
#- dh is bolded and ends with period
#- not necessarily at the beginning of comment and it seems the bolding isn't totally exact
#- there are vachuleys in dh, so maybe cut it off before that
import re
from sefaria.model import *
from data_utilities import dibur_hamatchil_matcher

def tokenize_words(str):
    str = str.replace(u"־", " ")
    str = re.sub(r"</?.+>", "", str)  # get rid of html tags
    str = re.sub(r"\([^\(\)]+\)", "", str)  # get rid of refs
    str = str.replace("'", '"')
    word_list = filter(bool, re.split(r"[\s\:\-\,\.\;\(\)\[\]\{\}]", str))
    return word_list

def dh_extraction_method(str):
    bold_list = re.findall(ur'<b>(.+?)</b>',str)
    if len(bold_list) > 0:
        bold = bold_list[0]
        #if u"וכו'" in bold:
        #    bold = bold[:bold.index(u"וכו'")]
        bold = re.sub(ur'[\,\.\:\;]',u'',bold)
        return bold
    else:
        return str


def dh_split(dh):
    max_sub_dh_len = 8
    min_sub_dh_len = 5

    dh_split = dh.split(u"וכו'")
    #dh_split = dh.split(u'yo')
    sub_dhs = []
    for vchu_block in dh_split:
        vchu_split = re.split(ur'\s+',vchu_block)
        if len(vchu_split) > max_sub_dh_len:
            vchu_block = u' '.join(vchu_split[:max_sub_dh_len])
        sub_dhs.append(vchu_block)
    return sub_dhs

def rashi_filter(text):
    text_list = re.split(ur'\s+',text.strip())
    return u'ירושלמי' not in text_list[0]

    """
    for vchu_block in dh_split:
        vchu_split = re.split(ur'\s+',vchu_block.strip())


        if len(vchu_split) < min_sub_dh_len:
            split_len = len(vchu_split)
        else:
            split_len = -1
            for test_len in range(max_sub_dh_len,min_sub_dh_len-1,-1):
                remainder = len(vchu_split) % test_len
                if remainder >= min_sub_dh_len or remainder == 0:
                    split_len = test_len
                    break
            if split_len == -1: #there's no number that solves these constraints. just consider is one chunk
                split_len = len(vchu_split)
        i = 0
        while i < len(vchu_split):
            sub_dhs.append(u' '.join(vchu_split[i:i+split_len]))
            i += split_len

    if len(sub_dhs) > 1:
        return sub_dhs
    else:
        return None
    """

def match():
    link_list = []
    num_matched = 0
    num_searched = 0

    rashba = library.get_index("Rashba on Berakhot")
    gemara = library.get_index("Berakhot")

    rashba_ref_list =  rashba.all_section_refs()
    gemara_ref_list = gemara.all_section_refs()

    gemara_ind = 0
    for rashba_ref in rashba_ref_list:
        while gemara_ref_list[gemara_ind].normal_last_section() != rashba_ref.normal_last_section():
            gemara_ind += 1
        gemara_ref = gemara_ref_list[gemara_ind]

        rashba_tc = TextChunk(rashba_ref,"he")

        # let's extend the range of gemara_tc to account for weird rashba stuff
        num_refs_to_expand = 2

        gemara_ref_before = gemara_ref.prev_section_ref()
        gemara_ref_after = gemara_ref.next_section_ref()
        if gemara_ref_before and len(gemara_ref_before.all_subrefs()) >= num_refs_to_expand:
            gemara_ref = gemara_ref_before.all_subrefs()[-num_refs_to_expand].to(gemara_ref)
        if gemara_ref_after and len(gemara_ref_after.all_subrefs()) >= num_refs_to_expand:
            gemara_ref = gemara_ref.to(gemara_ref_after.all_subrefs()[num_refs_to_expand - 1])

        gemara_tc = TextChunk(gemara_ref,"he")





        ref_map_with_abbrevs = dibur_hamatchil_matcher.match_ref(gemara_tc, rashba_tc, base_tokenizer=tokenize_words,
                                                                 dh_extract_method=dh_extraction_method, verbose=True,
                                                                 with_abbrev_matches=True,dh_split=dh_split,
                                                                 boundaryFlexibility=10000,
                                                                 rashi_filter=rashi_filter)
        ref_map = [(tup[0], tup[1]) for tup in ref_map_with_abbrevs]

        temp_link_list = [l for l in ref_map if not l[0] is None and not l[1] is None]
        link_list += temp_link_list
        unlink_list = [ul[1] for ul in ref_map if ul[0] is None or ul[1] is None]
        for r in ref_map:
            if not r[0] is None: num_matched += 1

        num_searched += len(ref_map)

        print "MATCHES - {}".format(ref_map)
        print "ACCURACY - {}%".format(round(1.0 * num_matched / num_searched, 5) * 100)
        #log.write("MATCHES - {}\n".format(temp_link_list))
        #log.write("NOT FOUND - {}\n".format(unlink_list))
        #log.write("ACCURACY - {}%\n".format(round(1.0 * num_matched / num_searched, 5) * 100))

match()




"""
f(dh_list,split):
    dh_map_new_old = []
    new_dh_list = []
    for i,dh in enum(dh_list):
        if dh is large:
            sub_dhs = split(dh)
            new_dh_list += sub_dhs
            for sdh in sub_dhs:
                dh_map_new_old.append(i)
        else:
            new_dh_list = dh
            dh_map_new_old.append(None)
    matches = match(new_dh_list)
    new_matches = []
    i = 0
    while i < len(matches):
        if dh_map_new_old[i]:
            sub_m = []
            while i < len(matches) and dh_map_new_old[i]:
                sub_m.append(matches[i])
                i+=1
            new_matches.append(merge(sub_m))
        else:
            new_matches.append(matches[i])
            i+=1
    return new_matches
"""