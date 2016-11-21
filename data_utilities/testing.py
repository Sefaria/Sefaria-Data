# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'

#dibur hamatchil tokenizer
#- dh is bolded and ends with period
#- not necessarily at the beginning of comment and it seems the bolding isn't totally exact
#- there are vachuleys in dh, so maybe cut it off before that
import sys

sys.path.append('../')

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
    bold_list = re.findall(ur'<b>(.+)</b>',str)
    if len(bold_list) > 0:
        bold = bold_list[0]
        if u"וכו'" in bold:
            bold = bold[:bold.index(u"וכו'")]
        bold = re.sub(ur'[\,\.\:\;]',u'',bold)
        return bold
    else:
        return str

def match():
    link_list = []
    num_matched = 0
    num_searched = 0

    rashba = Ref("Rashi on Berakhot")
    gemara = library.get_index("Berakhot")

    rashba_ref_list = [ref for ref in rashba.all_subrefs() if ref.text('he').text != []]
    gemara_ref_list = gemara.all_section_refs()

    gemara_ind = 0
    for rashba_ref in rashba_ref_list:
        while gemara_ind < len(gemara_ref_list) and gemara_ref_list[gemara_ind].normal_last_section() != rashba_ref.normal_last_section():
            gemara_ind += 1
        gemara_ref = rashba_ref_list[gemara_ind]

        rashba_tc = TextChunk(rashba_ref,"he")
        gemara_tc = TextChunk(gemara_ref,"he")

        ref_map_with_abbrevs = dibur_hamatchil_matcher.match_ref(rashba_tc, gemara_tc,base_tokenizer=tokenize_words,
                                                                 dh_extract_method=dh_extraction_method, verbose=True,
                                                                 with_abbrev_matches=True)
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