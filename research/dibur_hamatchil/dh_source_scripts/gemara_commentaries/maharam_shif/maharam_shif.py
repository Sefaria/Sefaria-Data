# -*- coding: utf-8 -*-
from research.dibur_hamatchil.dh_source_scripts.gemara_commentaries.gemara_commentary_matcher import *
from collections import defaultdict

def split_daf_into_base_texts(rules, comment_tc):
    """

    :param TextChunk comment_tc: TextChunk of comment that we want to split up
    :param list rules: list of regex strings. they are applied one after another to comment_tc
    :return: list where each guy is ([list of refs],[list of ref contents])
    also returns a dict. the keys are explicit references to rashi and tos. the values are lists with elements that are the implicit refs
    """

    refs = comment_tc.nonempty_subrefs()
    ref_contents = comment_tc.ja().flatten_to_array()

    splitted = [[[],[]] for _ in rules]
    oto_dibur_dict = defaultdict(list)
    last_rule_matched = -1
    last_explicit_ref = None
    for iref, (r,rc) in enumerate(zip(refs, ref_contents)):
        did_match = False
        for irule, rule in enumerate(rules):
            if re.match(rule, rc):
                splitted[irule][0] += [r]
                splitted[irule][1] += [rc]
                last_rule_matched = irule
                last_explicit_ref = r
                did_match = True
                break

        # didn't match any rules
        if not did_match and last_rule_matched != -1:
            splitted[last_rule_matched][0] += [r]
            splitted[last_rule_matched][1] += [rc]
            # oto_dibur_dict[str(last_explicit_ref)] += [r]
        #else:
            #print "{} didn't match anything :(".format(r)

    return splitted, oto_dibur_dict

rules = [r"(^ב?גמ)|(^ב?משנה)",r'^.?רש"י',r"^ב?תוס"]

def gemara_tokenizer(s):
    s = s.replace("־", " ")
    s = s.replace("מתני' ",'')
    s = re.sub(r"</?.+>", "", s)  # get rid of html tags
    s = re.sub(r"\([^\(\)]+\)", "", s)  # get rid of refs
    s = s.replace("'", '"')
    word_list = list(filter(bool, re.split(r"[\s\:\-\,\.\;\(\)\[\]\{\}]", s)))
    return word_list

def rashi_tokenizer(s):
    #ssplit = s.split(u'-')
    #if len(ssplit) > 1:
    #    s = ssplit[1]
    return gemara_tokenizer(s)

def tosfos_tokenizer(s):
    return rashi_tokenizer(s)

def dh(s):
    s = re.sub(r'\(.+?\)','',s)
    stop_phrases = []
    for phrase in stop_phrases:
        s = s.replace(phrase,'')
    bold_list = re.findall(r'<b>(.+?)</b>',s)
    if len(bold_list) > 0:
        bold = bold_list[0]
        if "וכו'" in bold:
            bold = bold[:bold.index("וכו'")+1]
        elif "כו'" in bold:
            bold = bold[:bold.index("כו'")+1]
        bold = re.sub(r'[\,\.\:\;]','',bold)
        return bold
    else:
        return s

def tos_dh(s):
    s = re.sub(r'\(.+?\)','',s)
    s = re.sub(r'ב' r'?' r'ד"ה', '', s)
    stop_phrases = []
    for phrase in stop_phrases:
        s = s.replace(phrase,'')
    bold_list = re.findall(r'<b>(.+?)</b>',s)
    if len(bold_list) > 0:
        bold = bold_list[0]
        m = re.search(r'ו' r'?' "כו'",bold)
        if m: # there's a chu. which side do you choose?
            if len(bold) - m.end() > m.start():
                d = bold[m.end():]
            else:
                d = bold[:m.start()]
        else:
            d = bold

        return d

    else:
        return s


def match():
    mesechtot = ["Shabbat","Beitzah","Ketubot","Gittin","Bava Kamma","Bava Metzia","Bava Batra","Sanhedrin","Zevachim","Chullin"]
    gcm =  GemaraCommentaryMatcher("Maharam Shif on",mesechtot)
    gcm.match_multiple(["","Rashi on","Tosafot on"],split_daf_into_base_texts,rules,[dh,tos_dh,tos_dh],
                       [gemara_tokenizer,rashi_tokenizer,tosfos_tokenizer],[None,None,None],"out","not_found")

match()