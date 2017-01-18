# -*- coding: utf-8 -*-

#dibur hamatchil tokenizer
#- dh is bolded and ends with period
#- not necessarily at the beginning of comment and it seems the bolding isn't totally exact
#- there are vachuleys in dh, so maybe cut it off before that
from research.dibur_hamatchil.dh_source_scripts.gemara_commentaries.gemara_commentary_matcher import *

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
        elif u"כו'" in bold:
            bold = bold[:bold.index(u"כו'")]
        bold = re.sub(ur'[\,\.\:\;]',u'',bold)
        return bold
    else:
        return s


def rashi_filter(text):
    dh = dh_extraction_method(text)
    return u'ז"ל' not in dh and u'רשב"א' not in dh

def match():
    mesechtot = ["Beitzah", "Ketubot", "Nedarim","Nazir","Sotah","Bava Kamma","Bava Metzia","Bava Batra"]
    gcm = GemaraCommentaryMatcher("Shita Mekubetzet on", mesechtot)
    gcm.match(dh_extraction_method, tokenize_words, rashi_filter, "out", "not_found")

match()

