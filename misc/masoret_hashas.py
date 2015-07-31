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
ravs += [u"ל" + x for x in ravs]
ravs += [u"ד" + x for x in ravs]
ravs += [u"מ" + x for x in ravs]
ravs += [u"ו" + x for x in ravs]
chain = [u"בן", u"בר", u"בריה", u"משמיה", u"בשם", u"משום"]
said = [u'א"ר', u"אמר", u"אומר", u"תני", u"תנן", u"תנא", u'א"ל']
phrases = [u"אלא אמר", u"לא שנו אלא", u"עד כאן לא קאמר", u"חייא בר אבא אמר רבי יוחנן", u"ראיה לדבר זכר לדבר",
           u"עד כאן לא קאמר", u"מאי שנא רישא ומאי שנא סיפא", u"אי איתמר הכי איתמר", u"שנא רישא ומאי שנא סיפא",
           u"הוא מותיב לה והוא מפרק לה", u"חייא בר אבא אמר ר' יוחנן"]

# Counts to keep track of when printing interesting info about data_set
most_hits = 0
total_hits = 0
total_hits_combined = 0

# Results for n-gram search
all_results = {}


def get_masoret_hashas_links():
    """ Gets all Mesorat Hashas type links in the Talmud from the database

    :return: List of links represented as tuples of reference strings
    """
    masoret_hashas_links = []
    tractates = get_tractates()
    for tractate in tractates:
        links = get_book_category_linkset(tractate, "Bavli")
        for link in links:
            link_dict = link.__dict__
            if link_dict["type"] == u"mesorat hashas":
                masoret_hashas_links.append(link_dict["refs"])
    return masoret_hashas_links


def score_hit(hit, count_avg):
    """ Using given heuristics, give each result a value representing its likely importance as a link

    :param hit: String representing shared text between two sources
    :param count_avg: Average of number of times a given n_gram is found in the Talmud for all n_grams in the hit
    :returns: Score as integer
    """
    hit_list = hit.split(" ")
    score = (len(hit_list) - 6) * 10
    score -= count_avg
    amar_count = 0
    rav_count = 0
    chain_count = 0
    for word in hit_list:
        if any(root in word for root in said):
            amar_count += 1
        if word in ravs:
            rav_count += 1
        if word in chain:
            chain_count += 1
    score -= (2 * (amar_count - 1))
    score -= (2 * (rav_count - 1))
    score -= (2 * (chain_count - 1))
    for phrase in phrases:
        if phrase in hit:
            score -= 5
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
    """ Get a list of the names of the tractates of the Talmud from the database

    :return: List of strings, which are the names of the tractates of the Talmud in order
    """
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
    """ Break every line of the Talmud into n-grams, and maps them to spanning refs.

    :param n: Size of the grams to be generated
    :return: No return value. Writes the data to a series of json files.
    """
    if not os.path.exists(folder):
        os.mkdir(folder)
    tractates = get_tractates()
    for tractate in tractates:
        grams = {}
        text_chunk = []
        ref_range = []
        ref = tractate
        while ref is not None:
            print ref
            text_obj = api_get_text(ref)
            text = text_obj.get("he")
            for line in range(len(text)):
                text_line = text[line]
                text_line = re.sub(r"[,.:;]", "", text_line)
                # text_line = re.sub(r"\((?=[^\)\s,]+\s){1,3}[^\)]*,\s[^\)\s]{1,3}\)", "", text_line)
                word_list = text_line.split()
                text_chunk += word_list
                current_ref = text_obj["title"] + ":" + str(line + 1)
                ref_range += [current_ref] * len(word_list)
                if len(text_chunk) >= n:
                    gram_list = [text_chunk[i:i + n] for i in xrange(len(text_chunk) - n + 1)]
                    ref_list = [ref_range[i:i + n] for i in xrange(len(ref_range) - n + 1)]
                    for i in range(len(gram_list)):
                        gram = gram_list[i]
                        refs = ref_list[i]
                        gram_key = refs[0]
                        if refs[0] != refs[-1]:
                            gram_key += "-" + refs[-1].split(" ")[-1]
                        formatted_gram = " ".join(gram)
                        grams.setdefault(gram_key, []).append(formatted_gram)
                    text_chunk = gram[1:]
                    ref_range = ref_range[-5:]
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
            "size": 500,
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


def score_and_add_result(hit_ref, result):
    if hit_ref == "Bava Kamma 62b" and any("57b:38" in x for x in result["refs"]):
        pass
    global total_hits_combined
    count_avg = int(mean(result["counts"]))
    text = result["term"]
    score = score_hit(text, count_avg)
    sources = result["refs"]
    daf = sources[0].split(":")[0]
    if sources[-1] == sources[0]:
        source_range = sources[0]
    else:
        if '-' in sources[0]:
            source_range = sources[0].split("-")[0]
        else:
            source_range = sources[0]
        if "-" in sources[-1]:
            source_range += ("-" + sources[-1].split('-')[1])
        else:
            source_range += ("-" + sources[-1].split(" ")[-1])
    scored_result = {"source": source_range, "location": hit_ref, "text": text, "score": score}
    flag = True
    if hit_ref not in all_results:
        all_results.setdefault(daf, []).append(scored_result)
        total_hits_combined += 1
    else:
        flag = False
        for existing_result in all_results[hit_ref]:
            if Ref(existing_result["location"]).contains(Ref(source_range.split("-")[0])) and existing_result["text"] in text:
                existing_result["location"] = source_range
                flag = True
                break
    if not flag:
        all_results.setdefault(daf, []).append(scored_result)
        total_hits_combined += 1


def search_n_grams():
    global total_hits
    global most_hits
    files = os.listdir(folder)
    for filename in files:
        tractate_hits = {}
        last_hits = set()
        with open(folder + os.sep + filename, 'r') as gram_file:
            grams = gram_file.read()
            tractate_grams = json.loads(grams)
        sorted_grams = sorted(tractate_grams, key=lambda x: Ref(x).order_id())
        for ref in sorted_grams:
            print ref
            for search_term in tractate_grams[ref]:
                current_hits = set()
                hit_count = 0
                formatted_term = format_search_term(search_term)
                response = search_bavli(formatted_term)
                if response is not None:
                    for hit in response["hits"]["hits"]:
                        hit_ref = hit["_source"]["ref"]
                        if not Ref(hit_ref).contains(Ref(ref)):
                            hit_count += 1
                            if hit_ref in tractate_hits:
                                tractate_hits[hit_ref]["refs"].append(ref)
                                tractate_hits[hit_ref]["term"] += (u' ' + search_term.split(" ")[-1])
                                tractate_hits[hit_ref]["counts"].append(len(response["hits"]["hits"]))
                            else:
                                tractate_hits[hit_ref] = {"refs": [ref], "term": search_term,
                                                          "counts": [len(response["hits"]["hits"])]}
                            current_hits.add(hit_ref)
                total_hits += hit_count
                most_hits = max(most_hits, hit_count)
                for result in (last_hits - current_hits):
                    score_and_add_result(result, tractate_hits[result])
                    del (tractate_hits[result])
                last_hits = current_hits
        for result in last_hits:
            score_and_add_result(result, tractate_hits[result])
        print "Finished tractate " + filename.replace(".json", "")


def output_profile(results, runtime):
    output = ["Runtime is " + str(runtime) + " seconds \n", "Most number of hits for one search is " + str(most_hits),
              "\nTotal number of hits for 6_grams is " + str(total_hits) + " and for 6+grams is " + str(
                  total_hits_combined), "\n\n" + "Top ten best hits are: \n"]
    for result in results[:50]:
        output.append("Hit from {} to {} with text {} and score {} \n".format(result["source"], result["location"],
                                                                              result["text"].encode('utf-8'),
                                                                              result["score"]))
    output.append("\n" + "Worst hits are: \n")
    for result in results[-50:]:
        output.append("Hit from {} to {} with text {} and score {} \n".format(result["source"], result["location"],
                                                                              result["text"].encode('utf-8'),
                                                                              result["score"]))
    with open("profile.txt", 'w') as profile:
        profile.writelines(output)


def generate_masoret_hashas():
    global all_results
    all_results_list = []
    start = timeit.default_timer()
    search_n_grams()
    for daf in all_results:
        for result in all_results[daf]:
            all_results_list.append(result)
    score_sorted_results = sorted(all_results_list, key=lambda hit: -hit["score"])
    stop = timeit.default_timer()
    output_profile(score_sorted_results, stop - start)
    with open("all_results.json", 'w') as results_file:
        json.dump(all_results, results_file)


def compare_masoret_hashas():
    global all_results
    all_results_list = []
    links = get_masoret_hashas_links()
    with open("all_results.json", "r") as filename:
        all_results = json.load(filename)
    link_results = []
    for link in links:
        score = None
        try:
            if ":" in link[0]:
                daf0 = link[0].split(":")[0]
            else:
                daf0 = link[0]
            if ":" in link[1]:
                daf1 = link[1].split(":")[0]
            else:
                daf1 = link[1]
            Ref(link[0])
            Ref(link[1])
        except Exception as e:
            print e
        else:
            if daf0 in all_results:
                for result in all_results[link[0].split(":")[0]]:
                    if Ref(result["source"]).contains(Ref(link[0])) and Ref(result["location"]).contains(Ref(link[1])):
                        score = max(result["score"], score)
            if daf1 in all_results:
                for result in all_results[link[1].split(":")[0]]:
                    if Ref(result["source"]).contains(Ref(link[1])) and Ref(result["location"]).contains(Ref(link[0])):
                        score = max(result["score"], score)
        link_results.append((link,score))
    link_results = sorted(link_results, key=lambda x:x[1])
    with open("link_results.txt", "w") as filename:
        nones = 0
        for link_result in link_results:
            if link_result[1] is None:
                filename.write("Link from {} to {} not found \n".format(link_result[0][0], link_result[0][1]))
                nones+=1
            else:
                filename.write("Score is {} for link from {} to {} \n".format(link_result[1], link_result[0][0], link_result[0][1]))
        filename.write("There are {} links not found out of {} total links".format(nones, len(link_results)))
    """
    for daf in all_results:
        # print daf
        for result in all_results[daf]:
            all_results_list.append(result)
    sorted_results = sorted(all_results_list, key=lambda x: -x["score"])
    output_profile(sorted_results, 0)
    """


if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "compare":
            compare_masoret_hashas()
        elif "_grams" in arg:
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
