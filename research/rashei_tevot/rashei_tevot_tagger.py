# -*- coding: utf-8 -*-
import re
from sefaria.model import *
from sefaria.utils import hebrew
from data_utilities.util import traverse_ja
from data_utilities.dibur_hamatchil_matcher import match_text

slinks = LinkSet({"refs":{"$all":[re.compile("^Mishnah Berurah"),re.compile("^Shulchan Arukh, Orach Chayim")]}})
print len(slinks)

"""
Trying to match versions of Shulchan Arukh

ocRef = Ref("Shulchan Arukh, Orach Chayim")
ocTextToratEmet = ocRef.text("he","Torat Emet 363")
ocTextWiki = ocRef.text("he","Wikisource Shulchan Aruch")

iterateWiki = traverse_ja(ocTextWiki.text)
iterateTe = traverse_ja(ocTextToratEmet.text)

def base_tokenizer(str):
    punc_pat = re.compile(ur"(\.|,|:)$")

    str = re.sub(ur"\([^\(\)]+\)", u"", str)
    str = re.sub(r"</?[a-z]+>", "", str)  # get rid of html tags
    str = hebrew.strip_cantillation(str, strip_vowels=True)
    word_list = re.split(ur"\s+", str)
    word_list = [re.sub(punc_pat,u"",w).strip() for w in word_list if len(re.sub(punc_pat,u"",w).strip()) > 0]  # remove empty strings and punctuation at the end of a word
    return word_list

for wikiSeg,teSeg in zip(iterateWiki,iterateTe):
    wikiSeg = wikiSeg["data"]
    teSeg = teSeg["data"]



    wikiList = base_tokenizer(wikiSeg)
    teList = base_tokenizer(teSeg)

    teCommentsList = []
    count = 0
    n = 10
    while count < len(teList):
        teCommentsList.append(u" ".join(teList[count:count+n]))
        count += n

    text_map,abbrev_map = match_text(wikiList,teCommentsList,verbose=True,with_abbrev_ranges=True)
    print "ABBREV LEN ", len([match for abbrev_map_inner in abbrev_map for match in abbrev_map_inner])
"""