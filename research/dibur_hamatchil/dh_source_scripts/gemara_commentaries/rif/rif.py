# -*- coding: utf-8 -*-

"""
you can't rely on daf segmenation
instead keep a running count of which comment you're up to, call it r and which gemara segment, g

r = 0
g = 0
rif_window = 10
gem_window = 100
while r < len(rif) - rif_window and g < len(gemara) - gem_window
    results = search([g:g+gem_window], r)
    last_rif_matched = 0
    for m in results['matches']

"""

from sefaria.model import *
from sefaria.system.exceptions import InputError
from linking_utilities import dibur_hamatchil_matcher
import json, re

mesechtot = ["Berakhot","Shabbat", "Eruvin","Pesachim","Rosh Hashanah","Yoma","Sukkah","Beitzah","Taanit","Megillah"
    ,"Moed Katan","Yevamot","Ketubot","Nedarim","Gittin","Kiddushin","Bava Kamma","Bava Metzia","Bava Batra","Sanhedrin",
             "Makkot","Shevuot","Avodah Zarah","Menachot","Chullin"]

mesechtot = ['Beitzah']
all_mes = library.get_indexes_in_category("Bavli")
william_boundary = all_mes.index("Bava Batra")
all_william = all_mes[:william_boundary + 1]

rif_window = 10
gem_window = 100

def tokenize_words(str):
    str = str.replace("־", " ")
    str = re.sub(r"</?.+>", "", str)  # get rid of html tags
    str = re.sub(r"\([^\(\)]+\)", "", str)  # get rid of refs
    str = str.replace("'", '"')
    word_list = list(filter(bool, re.split(r"[\s\:\-\,\.\;\(\)\[\]\{\}]", str)))
    return word_list

def dh_extraction_method(s):
    s = s.replace("־", " ")
    s = re.sub(r"</?.+>", "", s)  # get rid of html tags
    s = re.sub(r"\([^\(\)]+\)", "", s)  # get rid of refs

    s_words = re.split(r'\s+',s)
    s = ' '.join(s_words[:10])
    return s

for mes in mesechtot:
    print('---- {} ----'.format(mes))

    links = []
    rif = Ref("Rif {}".format(mes))
    gem = Ref("{}".format(mes))
    rif_segs = rif.text("he").nonempty_subrefs()
    vtitle = 'William Davidson Edition - Aramaic' if mes in all_william else None
    gem_segs = gem.text(lang="he",vtitle=vtitle).nonempty_subrefs()

    i_rif = 0
    i_gem = 0
    last_update_was_zero = False
    while i_rif < len(rif_segs) - rif_window and i_gem < len(gem_segs) - gem_window:
        temp_rif_tc = rif_segs[i_rif].to(rif_segs[i_rif + rif_window]).text("he")
        temp_gem_tc = gem_segs[i_gem].to(gem_segs[i_gem + gem_window]).text(lang="he", vtitle=vtitle)
        print("{}, {}, {}".format(temp_rif_tc, temp_gem_tc, len(links)))

        matched = dibur_hamatchil_matcher.match_ref(temp_gem_tc, temp_rif_tc, base_tokenizer=tokenize_words,
                                                    dh_extract_method=dh_extraction_method, verbose=False,
                                                    with_abbrev_matches=True)

        first_matches = matched['matches']
        match_indices = matched['match_word_indices']

        for i in range(1, 5):

            # let's try again, but with shorter dhs and imposing order
            start_pos = i * 2


            def dh_extraction_method_short(s):
                dh = dh_extraction_method(s)
                dh_split = re.split(r'\s+', dh)
                if len(dh_split) > start_pos + 4:
                    dh = ' '.join(dh_split[start_pos:start_pos + 4])

                return dh


            matched = dibur_hamatchil_matcher.match_ref(temp_gem_tc, temp_rif_tc, base_tokenizer=tokenize_words,
                                                        dh_extract_method=dh_extraction_method_short,
                                                        verbose=False,
                                                        with_abbrev_matches=True,
                                                        prev_matched_results=match_indices)

            match_indices = matched['match_word_indices']

        if 'comment_refs' not in matched:
            print('NO COMMENTS')
            continue
        matches = matched['matches']
        comment_refs = matched['comment_refs']

        last_comment_matched = 0
        for i, m in enumerate(matches):
            if m is None:
                last_comment_matched = i # TODO this will be stupid if first ref doesn't match anything
                break

        links += list(zip(comment_refs[:last_comment_matched], matches[:last_comment_matched]))
        if last_comment_matched == 0 and last_update_was_zero:
            i_rif += 1
            i_gem -= gem_window / 2
            print('BACKTRACK')
            last_update_was_zero = False
        else:
            i_rif += last_comment_matched
            i_gem += gem_window / 2
            last_update_was_zero = last_comment_matched == 0

    links_text = [[l[0].normal(), l[1].normal()] for l in links]
    print("{}/{}".format(len(links),len(rif_segs)))
    json.dump(links_text,open('rif.json','wb'))