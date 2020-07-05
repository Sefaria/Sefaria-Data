# -*- coding: utf-8 -*-

import django
django.setup()
#dibur hamatchil tokenizer
#- dh is bolded except when the Perek is the first word. then strip until the first line break.
# strip out matni and gem
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
        try:
            bold = bold_list[0] if 'פרק' not in bold_list[0] else bold_list[1]
        except IndexError:
            return ' '.join(s.split()[:12])
        if "וכו'" in bold:
            bold = bold[:bold.index("וכו'")]
        elif "כו'" in bold:
            bold = bold[:bold.index("כו'")]
        bold = re.sub(r'[\,\.\:\;]','',bold)
        return bold
    else:
        return ' '.join(s.split()[:12])

def rashi_filter(text):
    bold_list = re.findall(r'<b>(.+?)</b>', text)
    return len(bold_list) > 1 or (len(bold_list) == 1 and 'פרק' not in bold_list[0])

def match():
    # mesechtot = ["Berakhot","Eruvin","Rosh Hashanah", "Yoma", "Makkot","Avodah Zarah","Niddah"]
    mesechtot = ["Sukkah", "Taanit"]
    gcm = GemaraCommentaryMatcher("Ritva on", mesechtot)
    # gcm.match(dh_extraction_method, tokenize_words, rashi_filter, "out", "not_found")
    gcm.match(dh_extraction_method, tokenize_words, None, "out", "not_found")

match()

