# -*- coding: utf-8 -*-

#dibur hamatchil tokenizer
#- dh is bolded and ends with period
#- not necessarily at the beginning of comment and it seems the bolding isn't totally exact
#- there are vachuleys in dh, so maybe cut it off before that
from research.dibur_hamatchil.dh_source_scripts.gemara_commentaries.gemara_commentary_matcher import *

def tokenize_words(str):
    str = str.replace("־", " ")
    str = re.sub(r"</?.+>", "", str)  # get rid of html tags
    str = re.sub(r"\([^\(\)]+\)", "", str)  # get rid of refs
    str = str.replace("'", '"')
    word_list = list(filter(bool, re.split(r"[\s\:\-\,\.\;\(\)\[\]\{\}]", str)))
    return word_list

def dh_extraction_method(s):
    s = re.sub(r'\(.+?\)','',s)
    stop_phrases = []
    for phrase in stop_phrases:
        s = s.replace(phrase,'')
    bold_list = re.findall(r'<b>(.+?)</b>',s)
    if len(bold_list) > 0:
        bold = bold_list[0]
        if "וכו'" in bold:
            bold = bold[:bold.index("וכו'")]
        bold = re.sub(r'[\,\.\:\;]','',bold)
        return bold
    else:
        return s


def dh_split(dh):
    max_sub_dh_len = 8
    min_sub_dh_len = 5

    dh_split = dh.split("וכו'")
    #dh_split = dh.split(u'yo')
    sub_dhs = []
    for vchu_block in dh_split:
        vchu_split = re.split(r'\s+',vchu_block)
        if len(vchu_split) > max_sub_dh_len:
            vchu_block = ' '.join(vchu_split[:max_sub_dh_len])
        sub_dhs.append(vchu_block)
    return sub_dhs

def rashi_filter(text):
    text_list = re.split(r'\s+',text.strip())
    return 'ירושלמי' not in text_list[0]


def match():
    mesechtot = ["Berakhot","Shabbat","Eruvin","Rosh Hashanah","Beitzah","Megillah","Yevamot","Ketubot","Nedarim",
               "Gittin","Kiddushin","Bava Metzia","Bava Batra", "Shevuot","Avodah Zarah","Chullin","Niddah"]

    gcm = GemaraCommentaryMatcher("Rashba on", mesechtot)
    gcm.match(dh_extraction_method, tokenize_words, rashi_filter, "out", "not_found")



match()

