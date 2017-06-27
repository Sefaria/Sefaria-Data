# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'

from sources.functions import *
import os
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
from BeautifulSoup import *
from data_utilities.util import set_ranges_between_refs
from data_utilities.util import WeightedLevenshtein


from data_utilities.dibur_hamatchil_matcher import *

def match_report(text, perek_num, file, matcher):
    how_many = 0
    total = 0
    first_one = False
    links = []
    perek_ref = "{} {}".format(file[0:-4].title(), perek_num)
    for pasuk_num in text[perek_num].keys():
        pasuk_ref = TextChunk(Ref("{}:{}".format(perek_ref, pasuk_num)), lang='he', vtitle="Tanach with Text Only")
        comm_ref = TextChunk(Ref("Be'er Mayim Chaim on Torah, {}:{}".format(perek_ref, pasuk_num)), lang='he')
        if comm_ref.text == []:
            continue
        print comm_ref
        orig_results = matcher.match(tc_list=[pasuk_ref, comm_ref], return_obj=True, comment_index_list=[1])
        results = matcher.filter_matches_by_score_and_duplicates(orig_results, min_score=40)
        results = set_ranges_between_refs(results, comm_ref._oref)
        results = [x.normal() for x in results]
        print results
        for result in results:
            links.append({
                "refs": [result, pasuk_ref._oref.normal()],
                "type": "Commentary",
                "auto": True,
                "generated_by": "beer"
            })
    post_link(links, server="http://proto.sefaria.org")




def dh_extract_method(line):
    orig = line
    first_word = first_word_with_period(line)
    if first_word > 9:
        dh = " ".join(line.split(" ")[0:9])
    else:
        dh = " ".join(line.split(" ")[0:first_word+1])
    dh = dh.replace(u'בד"ה', u'').replace(u'וכו', u'').replace(u"וגו'", u"").replace(".", "")
    tag_re = re.compile(u"<.*?>")
    close_tag_re = re.compile(u".*?(</.*?>)")
    if tag_re.match(dh):
        dh = dh.replace(tag_re.match(dh).group(0), "")
    if close_tag_re.match(dh):
        dh = dh.replace(close_tag_re.match(dh).group(1), "")
    num_re = re.compile(".*?({\d+})")
    if num_re.match(dh):
        dh = dh.replace(num_re.match(dh).group(1), "")
    return dh

def get_score(words_a, words_b):
    normalizingFactor = 100
    smoothingFactor = 1
    ImaginaryContenderPerWord = 22

    dist = WeightedLevenshtein().calculate(u" ".join(words_a), u" ".join(words_b),normalize=False)
    score = 1.0 * (dist + smoothingFactor) / (len(words_a) + smoothingFactor) * normalizingFactor

    dumb_score = (ImaginaryContenderPerWord * len(words_a)) - score
    return dumb_score

def create_schema():
    root = SchemaNode()
    root.add_primary_titles("Be'er Mayim Chaim on Torah", u"באר מים חיים על תורה")

    books = library.get_indexes_in_category("Torah", full_records=True)
    for book in books:
        en_name = book.get_title("en")
        he_name = book.get_title("he")
        node = JaggedArrayNode()
        node.toc_zoom = 2
        node.add_structure(["Chapter", "Paragraph", "Comment"])
        node.add_primary_titles(en_name, he_name)
        root.append(node)

    index = {
        "schema": root.serialize(),
        "dependence": "Commentary",
        "collective_title": "Be'er Mayim Chaim",
        "base_text_titles": ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"],
        "categories": ["Tanakh", "Commentary"],
        "title": u"Be'er Mayim Chaim on Torah"
        }
    post_index(index, server="http://proto.sefaria.org")

def beer_mayim_post(file, text):
    for perek_num in text.keys():
        text[perek_num] = convertDictToArray(text[perek_num])
    text = convertDictToArray(text)
    create_payload_and_post_text("Be'er Mayim Chaim on Torah, {}".format(file[0:-4].title()), text, "he",
        vtitle="Be'er Mayim Chaim, Jerusalem 1991.",
        vsource="http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001185750",
        server="http://proto.sefaria.org")

def tokenizer(str):
    return str.split(" ")

if __name__ == "__main__":
    '''
    iterate and count perek and pasuk
    '''
    #create_schema()
    files = [file for file in os.listdir(".") if file.endswith(".txt")]
    matcher = ParallelMatcher(tokenizer,max_words_between=1, min_words_in_match=3, ngram_size=3,dh_extract_method=dh_extract_method, parallelize=False, calculate_score=get_score,
                        all_to_all=False, verbose=False)
    for file in files:
        text = {}
        perek_num = 0
        pasuk_num = 0
        for line in open(file):
            line = line.decode('utf-8').replace("\r", "").replace("\n", "").replace("{1}", "").replace("{2}", "")
            if "$$" in line and len(line.split(" ")) < 4:
                if perek_num > 0:
                    match_report(text, perek_num, file, matcher)
                perek_num = getGematria(line.split(" ") [0])
                if perek_num in text:
                    print "Problem in {}: Found perek {} twice".format(file, perek_num)
                text[perek_num] = {}
                pasuk_num = 0
            elif "%%" in line and len(line.split(" ")) < 4:
                pasuk_num = getGematria(line.split(" ")[0])
                if pasuk_num in text[perek_num]:
                    print "Problem in {}: In perek {}, found pasuk {} twice".format(file, perek_num, pasuk_num)
                text[perek_num][pasuk_num] = []
            elif "##" in line:
                continue
            elif perek_num > 0 and pasuk_num > 0:
                text[perek_num][pasuk_num].append(line)
        beer_mayim_post(file, text)