from sefaria.model import *
from data_utilities import dibur_hamatchil_matcher
import json, re

class GemaraCommentaryMatcher:

    def __init__(self, commentary_pattern, mes_list):
        all_mes = library.get_indexes_in_category("Bavli")
        william_boundary = all_mes.index("Bava Batra")
        self.all_william = all_mes[:william_boundary+1]
        self.all_not_william = all_mes[william_boundary:]
        self.mes_list = mes_list
        self.commentary_pattern = commentary_pattern

    def match(self, dh_extraction_method, base_tokenizer, rashi_filter, matched_dir, not_matched_dir):
        num_matched = 0
        num_searched = 0
        for mesechta in self.mes_list:
            link_list = []
            unlink_list = []
            comment = library.get_index("{} {}".format(self.commentary_pattern, mesechta))
            gemara = library.get_index("{}".format(mesechta))

            comment_ref_list = comment.all_section_refs()
            gemara_ref_list = gemara.all_section_refs()

            gemara_ind = 0
            for icomment, comment_ref in enumerate(comment_ref_list):
                while gemara_ref_list[gemara_ind].normal_last_section() != comment_ref.normal_last_section():
                    gemara_ind += 1
                gemara_ref = gemara_ref_list[gemara_ind]
                orig_gemara_ref = gemara_ref
                print u'----- {} Start ({}/{})-----'.format(orig_gemara_ref, icomment, len(comment_ref_list))
                comment_tc = TextChunk(comment_ref, "he")

                # let's extend the range of gemara_tc to account for weird rashba stuff
                num_refs_to_expand = 2

                gemara_ref_before = gemara_ref.prev_section_ref()
                gemara_ref_after = gemara_ref.next_section_ref()
                if gemara_ref_before and len(gemara_ref_before.all_subrefs()) >= num_refs_to_expand:
                    gemara_ref_expanded = gemara_ref_before.all_subrefs()[-num_refs_to_expand].to(gemara_ref)
                if gemara_ref_after and len(gemara_ref_after.all_subrefs()) >= num_refs_to_expand:
                    gemara_ref_expanded = gemara_ref.to(gemara_ref_after.all_subrefs()[num_refs_to_expand - 1])

                vtitle = 'William Davidson Edition - Aramaic' if mesechta in self.all_william else None
                try:
                    gemara_tc = TextChunk(gemara_ref_expanded, lang='he', vtitle=vtitle)
                except Exception:
                    gemara_tc = TextChunk(gemara_ref, lang='he', vtitle=vtitle)

                matched = dibur_hamatchil_matcher.match_ref(gemara_tc, comment_tc, base_tokenizer=base_tokenizer,
                                                            dh_extract_method=dh_extraction_method, verbose=False,
                                                            with_abbrev_matches=True,
                                                            boundaryFlexibility=10000,
                                                            char_threshold=0.4,
                                                            rashi_filter=rashi_filter)

                first_matches = matched['matches']
                match_indices = matched['match_word_indices']

                for i in range(1, 5):

                    # let's try again, but with shorter dhs and imposing order
                    start_pos = i * 2

                    def dh_extraction_method_short(s):
                        dh = dh_extraction_method(s)
                        dh_split = re.split(ur'\s+', dh)
                        if len(dh_split) > start_pos + 4:
                            dh = u' '.join(dh_split[start_pos:start_pos + 4])

                        return dh

                    matched = dibur_hamatchil_matcher.match_ref(gemara_tc, comment_tc, base_tokenizer=base_tokenizer,
                                                                dh_extract_method=dh_extraction_method_short,
                                                                verbose=False,
                                                                with_abbrev_matches=True,
                                                                boundaryFlexibility=4,
                                                                prev_matched_results=match_indices,
                                                                rashi_filter=rashi_filter)

                    match_indices = matched['match_word_indices']

                if 'comment_refs' not in matched:
                    print 'NO COMMENTS'
                    continue
                matches = matched['matches']
                comment_refs = matched['comment_refs']

                ref_map = zip(matches, comment_refs)

                temp_link_list = [[str(l[0]), str(l[1])] for l in ref_map if not l[0] is None and not l[1] is None]
                link_list += temp_link_list
                temp_unlink_list = [str(ul[1]) for ul in ref_map if ul[0] is None or ul[1] is None]
                unlink_list += temp_unlink_list
                for r in ref_map:
                    if not r[0] is None: num_matched += 1

                num_searched += len(ref_map)

                print "MATCHES - {}".format(ref_map)
                for first, second in zip(first_matches, matches):
                    if first is None and not second is None:
                        print u"GOT {}".format(second)

                print "ACCURACY - {}%".format(round(1.0 * num_matched / num_searched, 5) * 100)
                # log.write("MATCHES - {}\n".format(temp_link_list))
                # log.write("NOT FOUND - {}\n".format(unlink_list))
                # log.write("ACCURACY - {}%\n".format(round(1.0 * num_matched / num_searched, 5) * 100))
                print u'----- {} End -----'.format(orig_gemara_ref)

            with open('{}/{}.json'.format(matched_dir, mesechta), 'wb') as out:
                json.dump(link_list, out, indent=4)

            with open('{}/{}.json'.format(not_matched_dir, mesechta), 'wb') as out:
                json.dump(unlink_list, out, indent=4)


