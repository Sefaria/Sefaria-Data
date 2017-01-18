# -*- coding: utf-8 -*-
from research.dibur_hamatchil.dh_source_scripts.gemara_commentaries.gemara_commentary_matcher import *

def split_daf_into_base_texts(comment_tc, rules):
    """

    :param TextChunk comment_tc: TextChunk of comment that we want to split up
    :param list rules: list of regex strings. they are applied one after another to comment_tc
    :return: list where each guy is [list of refs]
    """

    refs = comment_tc.nonempty_subrefs()
    ref_contents = comment_tc.ja().flatten_to_array()

    splitted = [[] for _ in rules]
    last_rule_matched = -1
    for iref, (r,rc) in enumerate(zip(refs, ref_contents)):
        did_match = False
        for irule, rule in enumerate(rules):
            if re.match(rule, rc):
                splitted[irule] += [r]
                last_rule_matched = irule
                did_match = True
                break

        # didn't match any rules
        if not did_match and last_rule_matched != -1:
            splitted[last_rule_matched] += [r]
        else:
            print "{} didn't match anything :(".format(r)

    return splitted


tc = Ref("Maharam Shif on Shabbat 131a").text("he")
rules = [ur"^ב?גמ'",ur'^ב?רש"י',ur"^ב?תוס"]

yo = split_daf_into_base_texts(tc, rules)
pass