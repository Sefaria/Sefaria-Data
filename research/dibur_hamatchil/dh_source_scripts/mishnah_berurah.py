# -*- coding: utf-8 -*-
import re
import codecs
from collections import OrderedDict
import json,csv,unicodecsv
from data_utilities import dibur_hamatchil_matcher
from sefaria.model import *
from sefaria.utils import hebrew
from sefaria.system.exceptions import DuplicateRecordError

from sources.functions import post_link

def getSimanNum(ref):
    return ref.normal().split(" ")[-1]

def base_tokenizer(str):
    punc_pat = re.compile(r"(\.|,|:|;)$")

    str = re.sub(r"\([^\(\)]+\)", "", str)
    str = re.sub(r"''",r'"',str) # looks like double apostrophe in shulchan arukh is meant to be a quote
    str = re.sub(r"</?[a-z]+>", "", str)  # get rid of html tags
    str = hebrew.strip_cantillation(str, strip_vowels=True)
    word_list = re.split(r"\s+", str)
    word_list = [re.sub(punc_pat,"",w).strip() for w in word_list if len(re.sub(punc_pat,"",w).strip()) > 0]  # remove empty strings and punctuation at the end of a word
    return word_list

def rashi_filter(str):
    return dh_extraction_method(str) != ''


def dh_extraction_method(str):
    #searches for '(blah) other blah -' or '{blah} other blah -'
    m = re.search(r"((\([^\(]+\))|(\{[^\{]+\}))([^–]+)–", str)
    if m is None:
        m = re.search(r"((\([^\(]+\))|(\{[^\{]+\}))([^-]+)-", str)
    if m:
        dh = m.group(4).strip()
        return dh.replace("וכו'","")
    else:
        return ""

def match():
    mb = library.get_index("Mishnah Berurah")
    oc = library.get_index("Shulchan Arukh, Orach Chayim")

    mbRefList = mb.all_section_refs()
    ocRefList = oc.all_section_refs()
    mbInd = 0

    num_matched = 0
    num_searched = 0

    link_list = []
    log = open("mishnah_berurah.log","w")
    rt_log = open("rashei_tevot.csv","w")
    rt_log_csv = unicodecsv.DictWriter(rt_log, fieldnames=["abbrev","expanded","context_before","context_after"])
    rt_log_csv.writeheader()
    for ocRef in ocRefList:
        ocSiman = getSimanNum(ocRef)
        while getSimanNum(mbRefList[mbInd]) != ocSiman:
            mbInd += 1
        mbRef = mbRefList[mbInd]
        mbSiman = getSimanNum(mbRef)
        print("----- SIMAN {} -----".format(ocSiman))
        log.write("----- SIMAN {} -----\n".format(ocSiman))
        octc = TextChunk(ocRef,"he")
        mbtc = TextChunk(mbRef,"he")
        try:
            matched = dibur_hamatchil_matcher.match_ref(octc,mbtc,base_tokenizer=base_tokenizer,dh_extract_method=dh_extraction_method,verbose=True,with_abbrev_matches=True,rashi_filter=rashi_filter)
        except ValueError:
            continue
        if 'comment_refs' not in matched:
            continue

        ref_map = [(base,comment) for base,comment in zip(matched['matches'],matched['comment_refs'])]
        abbrevs = [am for seg in matched['abbrevs'] for am in seg]
        for am in abbrevs:
            rt_log_csv.writerow({'abbrev':dibur_hamatchil_matcher.cleanAbbrev(am.abbrev), 'expanded':' '.join(am.expanded), 'context_before':' '.join(am.contextBefore), 'context_after':' '.join(am.contextAfter)})

        temp_link_list = [l for l in ref_map if not l[0] is None and not l[1] is None]
        link_list += temp_link_list
        unlink_list = [ul[1] for ul in ref_map if ul[0] is None or ul[1] is None]
        for r in ref_map:
            if not r[0] is None: num_matched+=1

        num_searched += len(ref_map)

        print("MATCHES - {}".format(ref_map))
        print("ACCURACY - {}%".format(round(1.0*num_matched/num_searched,5)*100))
        log.write("MATCHES - {}\n".format(temp_link_list))
        log.write("NOT FOUND - {}\n".format(unlink_list))
        log.write("ACCURACY - {}%\n".format(round(1.0*num_matched/num_searched,5)*100))


    doc = {"link_list":[[link[0].normal(),link[1].normal()] for link in link_list]}
    fp = codecs.open("mishnah_berurah_links.json", "w",encoding='utf-8')
    json.dump(doc, fp, indent=4, encoding='utf-8', ensure_ascii=False)
    fp.close()
    log.close()
    rt_log.close()

def save_links():
    with open("Mishnah Berurah found.csv","r") as f:
        r = csv.reader(f)
        for row in r:
            link_obj = {"auto":False,"refs":row,"anchorText":"","generated_by":"dibur_hamatchil_matcher review","type":"commentary"}
            try:
                Link(link_obj).save()
            except DuplicateRecordError:
                pass #poopy

def make_better_log_file():
    nf = open("mishnah_berurah_not_found1.csv","w")
    with open("mishnah_berurah.log","r") as f:
        for line in f:
            m = re.match(r"NOT FOUND - \[(.+)\]",line)
            if m:
                match = m.group(1)
                match_list = match.split(", ")
                for yo in match_list:
                    ym = re.match(r"Ref\(\'(.+)\'\)",yo)
                    nf.write("{},\n".format(ym.group(1)))

    nf.close()

def save_links_post_request():
    query = {"generated_by":"dibur_hamatchil_matcher review","auto":False}
    ls = LinkSet(query)
    links = [l.contents() for l in ls]
    post_link(links)

def deal_with_abbrevs():
    abbrev_dict = OrderedDict()
    abbrevfile = open("rashei_tevot.csv",'rb')
    abbrevcsv = unicodecsv.DictReader(abbrevfile)
    for row in abbrevcsv:
        abbrev = row['abbrev']
        expanded = row['expanded']
        if abbrev not in abbrev_dict:
            abbrev_dict[abbrev] = {}

        if expanded not in abbrev_dict[abbrev]:
            abbrev_dict[abbrev][expanded] = 0
        abbrev_dict[abbrev][expanded] += 1
    abbrevfile.close()
    objStr = json.dumps(abbrev_dict, indent=4, ensure_ascii=False)
    with open('all_mishnah_berurah_abbrevs.json', "w") as f:
        f.write(objStr.encode('utf-8'))

    print('Num Abbrevs {}'.format(len(abbrev_dict)))




match()
#save_links()
#make_better_log_file()
#save_links_post_request()
#deal_with_abbrevs()