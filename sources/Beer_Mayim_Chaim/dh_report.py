# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'

from sources.functions import *
import os
from BeautifulSoup import *

from data_utilities.dibur_hamatchil_matcher import *
def match_report(dhs, perek_num, file):
    how_many = 0
    total = 0
    first_one = False
    perek_ref = "{} {}".format(file[0:-4].title(), perek_num)
    for pasuk_num in dhs.keys():
        dhs[pasuk_num] = [dh_extract_method(dh) for dh in dhs[pasuk_num]]
        pasuk_ref = TextChunk(Ref("{}:{}".format(perek_ref, pasuk_num)), lang='he', vtitle="Tanach with Text Only")
        results = match_ref(pasuk_ref, dhs[pasuk_num], lambda x: x.split(" "), word_threshold=0.55)
        print "{} -> {}".format(pasuk_ref._oref, results["matches"])
        for count, match in enumerate(results["matches"]):
            if match:
                how_many += 1
            total += 1
    summary = u"{} out of {}".format(how_many, total)
    print "{} -> {}".format(perek_ref, summary)







def dh_extract_method(str):
    orig = str
    str = str.replace(u'בד"ה', u'').replace(u'וכו', u'').replace(u"וגו'", u"").replace(".", "")
    tag_re = re.compile(u"<.*?>")
    close_tag_re = re.compile(u".*?(</.*?>)")
    if tag_re.match(str):
        str = str.replace(tag_re.match(str).group(0), "")
    if close_tag_re.match(str):
        str = str.replace(close_tag_re.match(str).group(1), "")
    num_re = re.compile(".*?({\d+})")
    if num_re.match(str):
        str = str.replace(num_re.match(str).group(1), "")

    return str


if __name__ == "__main__":
    '''
    iterate and count perek and pasuk
    '''
    files = [file for file in os.listdir(".") if file.endswith(".txt")]
    print files
    for file in files:
        dhs = {}
        perek_num = 0
        for line in open(file):
            line = line.decode('utf-8').replace("\r", "").replace("\n", "").replace("{1}", "").replace("{2}", "")
            if "$$" in line and len(line.split(" ")) < 4:
                if perek_num > 0:
                    match_report(dhs[perek_num], perek_num, file)
                perek_num = getGematria(line.split(" ")[0])
                if perek_num in dhs:
                    print "Problem in {}: Found perek {} twice".format(file, perek_num)
                dhs[perek_num] = {}
                pasuk_num = 0
            elif "%%" in line and len(line.split(" ")) < 4:
                pasuk_num = getGematria(line.split(" ")[0])
                if pasuk_num in dhs[perek_num]:
                    print "Problem in {}: In perek {}, found pasuk {} twice".format(file, perek_num, pasuk_num)
                dhs[perek_num][pasuk_num] = []
            elif "##" in line:
                continue
            elif perek_num > 0 and pasuk_num > 0:
                    first_word = first_word_with_period(line)
                    if first_word > 9:
                        dh = " ".join(line.split(" ")[0:9])
                    else:
                        dh = " ".join(line.split(" ")[0:first_word+1])
                    dhs[perek_num][pasuk_num].append(dh)