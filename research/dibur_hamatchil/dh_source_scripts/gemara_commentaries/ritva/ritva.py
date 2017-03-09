# -*- coding: utf-8 -*-

#dibur hamatchil tokenizer
#- dh is bolded except when the Perek is the first word. then strip until the first line break.
# strip out matni and gem
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
        bold = bold_list[0] if u'פרק' not in bold_list[0] else bold_list[1]
        if u"וכו'" in bold:
            bold = bold[:bold.index(u"וכו'")]
        elif u"כו'" in bold:
            bold = bold[:bold.index(u"כו'")]
        bold = re.sub(ur'[\,\.\:\;]',u'',bold)
        return bold
    else:
        return s

def rashi_filter(text):
    bold_list = re.findall(ur'<b>(.+?)</b>', text)
    return len(bold_list) > 1 or (len(bold_list) == 1 and u'פרק' not in bold_list[0])


def match():
    mesechtot = ["Berakhot","Eruvin","Rosh Hashanah", "Yoma", "Makkot","Avodah Zarah","Niddah"]
    gcm = GemaraCommentaryMatcher("Ritva on", mesechtot)
    gcm.match(dh_extraction_method, tokenize_words, rashi_filter, "out", "not_found")

match()

