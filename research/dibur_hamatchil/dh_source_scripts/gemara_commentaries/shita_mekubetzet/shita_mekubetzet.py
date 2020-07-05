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
        elif "כו'" in bold:
            bold = bold[:bold.index("כו'")]
        bold = re.sub(r'[\,\.\:\;]','',bold)
        return bold
    else:
        return s


def rashi_filter(text):
    dh = dh_extraction_method(text)
    return 'ז"ל' not in dh and 'רשב"א' not in dh

def match():
    mesechtot = ["Beitzah", "Ketubot", "Nedarim","Nazir","Sotah","Bava Kamma","Bava Metzia","Bava Batra"]
    gcm = GemaraCommentaryMatcher("Shita Mekubetzet on", mesechtot)
    gcm.match(dh_extraction_method, tokenize_words, rashi_filter, "out", "not_found")

match()

