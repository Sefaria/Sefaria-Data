# -*- coding: utf-8 -*-

__author__ = 'Izzy'

import os
import sys
import json
import urllib2
from urllib2 import HTTPError
import re
from numpy import mean
import timeit

sys.path.append("C:\\Users\\Izzy\\git\\Sefaria-Project")
from sefaria.model import *

server = "sefaria.org"
# server = "localhost:8000"
# search_server = "http://search.sefaria.org:788"
search_server = "http://localhost:9200"
folder = "n_grams"

# List of words to look out for when scoring hits
ravs = [u"רב", u"רבי", u"רבה", u"רבא", u"ר'", u"רבן", u"שמואל", u"אביי", u'א"ר', u"רבין", u"מר", u"ריש לקיש"]
ravs +=[u"ל" + x for x in ravs]
ravs +=[u"ד" + x for x in ravs]
ravs +=[u"מ" + x for x in ravs]
ravs +=[u"ו" + x for x in ravs]
chain = [u"בן", u"בר", u"בריה", u"משמיה", u"בשם", u"משום"]
said = [u'א"ר', u"אמר", u"אומר", u"תני", u"תנן", u"תנא", u'א"ל']
phrases = [u"אלא אמר", u"לא שנו אלא", u"עד כאן לא קאמר", u"חייא בר אבא אמר רבי יוחנן", u"ראיה לדבר זכר לדבר",
           u"עד כאן לא קאמר", u"מאי שנא רישא ומאי שנא סיפא", u"אי איתמר הכי איתמר", u"שנא רישא ומאי שנא סיפא",
           u"הוא מותיב לה והוא מפרק לה", u"חייא בר אבא אמר ר' יוחנן"]

# Counts to keep track of when printing interesting info about data_set
most_hits = 0
total_hits = 0
total_hits_combined = 0

def score_hit(hit, count_avg):
    """ Using given heuristics, give each result a value representing its likely importance as a link

    :param hit: List of strings representing shared text between two sources
    :param count_avg: Average of number of times a given n_gram is found in the Talmud for all n_grams in the hit
    :returns: Score as integer
    """
    score = (len(hit) - 6) * 10
    score -= count_avg
    for word in hit:
        amar_count = 0
        rav_count = 0
        chain_count = 0
        if any(root in word for root in said):
            amar_count += 1
        if word in ravs:
            rav_count += 1
        if word in chain:
            chain_count += 1
    score -= (2*(amar_count-1))
    score -= (2*(rav_count-1))
    score -= (2*(chain_count-1))
    hit_string = " ".join(hit)
    for phrase in phrases:
        if phrase in hit_string:
            score-=5
    return score


def format_search_term(search_term):
    """ Format search term to be URL friendly

    :param search_term: String
    :returns: Unicode string
    """
    special_chars = ['+', '-', '=', '&&', '||', '>', '<', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~', '*', '?',
                     ':', '/']
    for char in special_chars:
        search_term = search_term.replace(char, '\\' + char)
    search_term = '"' + search_term + '"'
    return search_term.encode('utf-8')

def api_get_text(ref, lang=None, version=None):
    """ Get text through Sefaria API

    :param ref: String
    :param lang: String
    :param version: String
    :returns: Unicode string
    """
    ref = ref.replace(" ", "%20")
    ref_lang = ""
    ref_version = ""
    if lang is not None:
        ref_lang = "&lang=" + lang
    if version is not None:
        ref_version = "&version=" + version
    url = 'http://' + server + '/api/texts/%s?commentary=0&context=0%s%s' % (ref, ref_lang, ref_version)
    try:
        response = urllib2.urlopen(url)
        resp = json.loads(response.read())
        return resp
    except HTTPError, e:
        print 'Error code: ', e.code, " because ", e.reason


def get_tractates():
    tractates = []
    url = "http://{}/api/index".format(server)
    try:
        response = urllib2.urlopen(url)
        resp = response.read()
        resp_file = json.loads(resp)
        for section in resp_file:
            if section["category"] == "Talmud":
                for sub_section in section["contents"]:
                    if sub_section["category"] == "Bavli":
                        for seder in sub_section["contents"]:
                            for masechet in seder["contents"]:
                                tractates.append(masechet["title"])
    except HTTPError, e:
        print 'Error code: ', e.code, " because ", e.reason
    return tractates


def generate_n_grams(n):
    if not os.path.exists(folder):
        os.mkdir(folder)
    tractates = get_tractates()
    for tractate in tractates:
        grams = {}
        prev_gram = []
        ref = tractate
        while ref is not None:
            print ref
            text_obj = api_get_text(ref)
            gram_key = text_obj["sectionRef"]
            grams[gram_key] = []
            text = " ".join(text_obj.get("he"))
            text = re.sub(r"[,.:;]", "", text)
            # text = re.sub(r"\((?=[^\)\s,]+\s){1,3}[^\)]*,\s[^\)\s]{1,3}\)", "", text)
            text_list = text.split()
            count = 1
            while len(prev_gram) > 1:
                prev_gram.pop(0)
                new_gram = prev_gram + text_list[:count]
                formatted_gram = " ".join(new_gram)
                grams[gram_key].append(formatted_gram)
                count += 1
            gram_list = [text_list[i:i + n] for i in xrange(len(text_list) - n + 1)]
            for gram in gram_list:
                formatted_gram = " ".join(gram)
                grams[gram_key].append(formatted_gram)
            prev_gram = gram
            ref = text_obj.get("next")
        with open(folder + os.sep + tractate + ".json", 'w') as gram_file:
            json.dump(grams, gram_file)
        print "Hadran " + tractate


def search_bavli(search_term):
    url = '{}/sefaria/_search'.format(search_server)
    data = {"sort": [{"order": {}}],
            "highlight":
                {"pre_tags": ["<b>"], "post_tags": ["</b>"], "fields":
                    {"content": {"fragment_size": 200}}
                 },
            "size" : 500,
            "query":
                {"filtered":
                     {"query":
                          {"query_string":
                               {"query": "{}".format(search_term), "default_operator": "AND", "fields": ["content"]}
                           },
                      "filter":
                          {"or":
                               [{"regexp": {"path": "Talmud\\/Bavli.*"}}]
                           }
                      }
                 }
            }
    data = json.dumps(data)
    try:
        response = urllib2.urlopen(url, data)
        resp = response.read()
        resp_file = json.loads(resp)
        return resp_file
    except HTTPError, e:
        print 'Error code: ', e.code, " because ", e.reason, " for ", search_term


def aggregate_and_score_hits(hit_ref, hits):
    results = []
    sorted_hits = sorted(hits, key=lambda hit: Ref(hit[0]).order_id())
    result_counts = []
    result_terms = []
    result_sources = []
    for hit in sorted_hits:
        source = hit[0]
        term = hit[1].split(" ")
        count = hit[2]
        if result_terms and result_sources:
            if term != result_terms[-5:] and term[:5] == result_terms[-5:]:
                result_counts.append(count)
                result_terms.append(term[5])
                result_sources.append(source)
            else:
                count_avg = int(mean(result_counts))
                score = score_hit(result_terms, count_avg)
                source_range = result_sources[0]
                if result_sources[0] != result_sources[-1]:
                    source_range += (" - " + result_sources[-1])
                result = " ".join(result_terms)
                results.append([source_range, hit_ref, result, score])
                result_terms = term
                result_sources = [source]
                result_counts = [count]
        else:
            result_counts.append(count)
            result_sources.append(source)
            result_terms += term
    if result_terms and result_sources:
        count_avg = int(mean(result_counts))
        score = score_hit(result_terms, count_avg)
        source_range = result_sources[0]
        if result_sources[0] != result_sources[-1]:
                source_range += (" - " + result_sources[-1])
        result = " ".join(result_terms)
        results.append([source_range, hit_ref, result, score])
    return results

#Todo make a dictionary from tractate to hits, for the purpose of checking existing hits, then merge afterwards.
def search_n_grams():
    global total_hits
    global most_hits
    global total_hits_combined
    results = []
    files = os.listdir(folder)
    for filename in ["Sanhedrin.json", "Sotah.json"]:
        tractate_hits = {}
        with open(folder + os.sep + filename, 'r') as gram_file:
            grams = gram_file.read()
            tractate_grams = json.loads(grams)
        for ref in tractate_grams:
            print ref
            for search_term in tractate_grams[ref]:
                ref_hits =[]
                hit_count = 0
                formatted_term = format_search_term(search_term)
                response = search_bavli(formatted_term)
                if response is not None:
                    for hit in response["hits"]["hits"]:
                        if hit["_source"]["ref"] != ref:
                            hit_count += 1
                            ref_hits.append((hit["_source"]["ref"], ref, search_term))
                        else:
                            # print "Found text containing original n-gram"
                            pass
                else:
                    # print "None"
                    pass
                total_hits += hit_count
                most_hits = max(most_hits, hit_count)
                for hit in ref_hits:
                    tractate_hits.setdefault(hit[0], []).append((hit[1], hit[2], hit_count))
        for hit_ref in tractate_hits:
            tractate_results = aggregate_and_score_hits(hit_ref, tractate_hits[hit_ref])
            for result in tractate_results:
                if all(result[0] != x[0] and result[1] != x[1] and result[2] != x[2] for x in results):
                    results.append(result)
        print "Finished tractate " + filename.replace(".json","")
    total_hits_combined = len(results)
    return results


def output_profile(results, runtime):
    output = ["Runtime is " + str(runtime) + " seconds \n", "Most number of hits for one search is " + str(most_hits),
                  "\n Total number of hits for 6_grams is " + str(total_hits) + " and for 6+grams is " + str(
                      total_hits_combined), "\n" + "Top ten best hits are:"]
    for hit in results[:10]:
        output.append("\n Hit from " + hit[0].encode('utf-8') + " to " + hit[1].encode('utf-8') + " with text " + \
             hit[2].encode('utf-8') + " with score " + str(hit[3]))
    output.append("\n" + "Worst hits are:")
    for hit in results[-10:]:
        output.append("\n Hit from " + hit[0].encode('utf-8') + " to " + hit[1].encode('utf-8') + " with text " + \
            hit[2].encode('utf-8') + " with score " + str(hit[3]))
    with open("profile.txt", 'w') as profile:
        profile.writelines(output)

def generate_masoret_hashas():
    start = timeit.default_timer()
    results = search_n_grams()
    score_sorted_results = sorted(results, key=lambda hit: -hit[3])
    stop = timeit.default_timer()
    output_profile(score_sorted_results, stop - start)
    with open("all_results.txt", 'w') as all_results:
        for hit in score_sorted_results:
            all_results.write("Hit from " + hit[0].encode('utf-8') + " to " + hit[1].encode('utf-8') + " with text " + \
                hit[2].encode('utf-8') + " with score " + str(hit[3]) + "\n")



if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if "_grams" in arg:
            n_grams = arg.split("_")
            try:
                n = int(n_grams[0])
            except ValueError as e:
                print e
            else:
                if n > 0:
                    generate_n_grams(n)
                else:
                    print "Please provide valid value for n (n > 0)"
        else:
            print "Unknown command"
    else:
        generate_masoret_hashas()