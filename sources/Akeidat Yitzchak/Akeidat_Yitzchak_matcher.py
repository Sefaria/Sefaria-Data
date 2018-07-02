# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from sources.functions import *
from data_utilities.dibur_hamatchil_matcher import *
import re
import codecs
import pdb

sefer_ranges=[["Genesis",1,33], ["Exodus",34,56], ["Leviticus",57,71], ["Numbers",72,86], ["Deuteronomy",87,105] ]
def ay_filter(some_string):
    some_string = some_string.replace(u"\n","")
    if re.search(ur'<b>(.*?)</b>', some_string) is None:
        return False
    else:
        return True
def get_matching_refs():
	refs = []
	akeidat = library.get_index("Akeidat Yitzchak")
	
	for node in akeidat.alt_structs["Parsha"]["nodes"]:
		if "sharedTitle" in node:
			term = Term().load({'name': node["sharedTitle"]})
			base_ref = Ref(term.ref)
			akeida_ref = Ref(node["wholeRef"])
			refs.append({
				'base_ref': base_ref,
				'akeida_ref': akeida_ref
			})
			print "this is a ref: "+node["wholeRef"]
                print base_ref,akeida_ref
	return refs
def dh_extract_method(some_string):
    some_string = some_string.replace(u"\n","")
    some_string_list = some_string.split(u"וכו")
    if len(some_string_list)>5:
        some_string = some_string_list[0]
    return re.search(ur'<b>(.*?)</b>', some_string).group(1)

def base_tokenizer(some_string):
    return some_string.split(" ")

def get_links():
    matched_count = 0.00
    total = 0.00
    not_matched=[]
    """
    base_ref = TextChunk(Ref(sefer_ranges[book_index][0]),"he")
    akeida_ref = TextChunk(Ref("Akeidat Yitzchak, "+str(sefer_ranges[book_index][1])+"-"+str(sefer_ranges[book_index][2])),"he")
    """
    for match_refs in get_matching_refs():
        #print "matching... ",match_refs["base_ref"],match_refs["akeida_ref"]
        base_chunk = TextChunk(match_refs["base_ref"],"he","Tanach with Text Only")
        akeida_chunk = TextChunk(match_refs["akeida_ref"],"he","Akeidat Yitzchak, Pressburg 1849")
        word_count = match_refs["base_ref"].text('he').word_count()
        matches = match_ref(base_chunk,akeida_chunk,
            base_tokenizer,dh_extract_method=dh_extract_method,rashi_filter=ay_filter,verbose=True, boundaryFlexibility=word_count,char_threshold=0.4)
        if "comment_refs" in matches:
            for base, comment in zip(matches["matches"],matches["comment_refs"]):
                print base,comment
                if base:
                    matched_count+=1
                else:
                    not_matched.append(comment)
                total+=1
        else:
            not_matched.append(match_refs["akeida_ref"])
    print "Ratio: "+str(matched_count/total)
    print "Not Matched:"
    for nm in not_matched:
        print nm
get_links()
"""
for x in range(0,5):
    links = get_links(x)
    for link in links:
        print link
"""
