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

def dh_extraction_method(s):
    s = re.sub(ur'\(.+?\)',u'',s)
    stop_phrases = []
    for phrase in stop_phrases:
        s = s.replace(phrase,u'')
    bold_list = re.findall(ur'<b>(.+?)</b>',s)
    if len(bold_list) > 0:
        bold = bold_list[0]
        if u"וכו'" in bold:
            bold = bold[:bold.index(u"וכו'")]
        bold = re.sub(ur'[\,\.\:\;]',u'',bold)
        return bold
    else:
        return s


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


def match():
    #mesechtot = ["Berakhot","Shabbat","Eruvin","Rosh Hashanah","Beitzah","Megillah","Yevamot","Ketubot","Nedarim",
    #             "Gittin","Kiddushin","Bava Metzia","Bava Batra","Shevuot","Avodah Zarah","Chullin","Niddah"]
    mesechtot = ["Shabbat"]

    link_list = []
    num_matched = 0
    num_searched = 0
    for mesechta in mesechtot:


        rashba = library.get_index("Rashba on {}".format(mesechta))
        gemara = library.get_index("{}".format(mesechta))

        rashba_ref_list =  rashba.all_section_refs()[:24]
        gemara_ref_list = gemara.all_section_refs()

        gemara_ind = 0
        for irashba, rashba_ref in enumerate(rashba_ref_list):
            while gemara_ref_list[gemara_ind].normal_last_section() != rashba_ref.normal_last_section():
                gemara_ind += 1
            gemara_ref = gemara_ref_list[gemara_ind]
            orig_gemara_ref = gemara_ref
            print u'----- {} Start ({}/{})-----'.format(orig_gemara_ref,irashba,len(rashba_ref_list))
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





            matched = dibur_hamatchil_matcher.match_ref(gemara_tc, rashba_tc, base_tokenizer=tokenize_words,
                                                                     dh_extract_method=dh_extraction_method, verbose=True,
                                                                     with_abbrev_matches=True,
                                                                     boundaryFlexibility=10000,
                                                                     rashi_filter=rashi_filter)

            first_matches = matched['matches']
            match_indices = matched['match_word_indices']

            for i in range(1,5):


                #let's try again, but with shorter dhs and imposing order
                start_pos = i * 2
                def dh_extraction_method_short(s):
                    dh = dh_extraction_method(s)
                    dh_split = re.split(ur'\s+', dh)
                    if len(dh_split) > start_pos + 4:
                        dh = u' '.join(dh_split[start_pos:start_pos+4])

                    return dh

                matched = dibur_hamatchil_matcher.match_ref(gemara_tc, rashba_tc, base_tokenizer=tokenize_words,
                                                                         dh_extract_method=dh_extraction_method_short, verbose=False,
                                                                         with_abbrev_matches=True,
                                                                         boundaryFlexibility=4,
                                                                         prev_matched_results=match_indices,
                                                                         rashi_filter=rashi_filter)

                match_indices = matched['match_word_indices']


            matches = matched['matches']
            comment_refs = matched['comment_refs']


            ref_map = zip(matches,comment_refs)

            temp_link_list = [l for l in ref_map if not l[0] is None and not l[1] is None]
            link_list += temp_link_list
            unlink_list = [ul[1] for ul in ref_map if ul[0] is None or ul[1] is None]
            for r in ref_map:
                if not r[0] is None: num_matched += 1

            num_searched += len(ref_map)

            print "MATCHES - {}".format(ref_map)
            for first,second in zip(first_matches,matches):
                if first is None and not second is None:
                    print u"GOT {}".format(second)

            print "ACCURACY - {}%".format(round(1.0 * num_matched / num_searched, 5) * 100)
            #log.write("MATCHES - {}\n".format(temp_link_list))
            #log.write("NOT FOUND - {}\n".format(unlink_list))
            #log.write("ACCURACY - {}%\n".format(round(1.0 * num_matched / num_searched, 5) * 100))
            print u'----- {} End -----'.format(orig_gemara_ref)


match()

