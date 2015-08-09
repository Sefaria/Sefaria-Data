# -*- coding: utf-8 -*-

__author__ = 'Izzy'

import os
import sys
import json
import urllib, urllib2
from urllib2 import HTTPError
import re
from numpy import mean
import timeit

from sefaria.model import *

# server = "sefaria.org"
server = "dev.sefaria.org"
# search_server = "http://search.sefaria.org:788"
search_server = "http://localhost:9200"
folder = "n_grams"
apikey = ''

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

# Counts to keep track of when printing interesting info about data set
most_hits = 0
total_hits = 0
total_hits_combined = 0

# Dictionary of daf to of results for n-grams from that daf
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


def score_result(result, count_avg):
    """ Using given heuristics, give each result a value representing its likely importance as a link

    :param hit: String representing shared text between two sources
    :param count_avg: Average of number of times a given n_gram is found in the Talmud for all n_grams in the hit
    :returns: Score as integer
    """
    word_list = result.split(" ")
    score = (len(word_list) - 6) * 10
    score -= count_avg
    amar_count = 0
    rav_count = 0
    chain_count = 0
    for word in word_list:
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
        if phrase in result:
            score -= 5
    cite_count = len(library.get_refs_in_string(result, "he"))
    score -= (20*cite_count)
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
    """ Break every line of the Talmud into n-grams, and maps them to the ref that they came from.

    :param n: Size of the grams to be generated
    :return: No return value. Writes the data to a json file for each tractate.
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
                word_list = text_line.split()
                text_chunk += word_list
                current_ref = text_obj["title"] + ":" + str(line + 1)
                ref_range += [current_ref] * len(word_list)     # ref_range keeps track of the source of every word in the current text_chunk, so a range can be constructed for every n-gram
                if len(text_chunk) >= n:   # Text is appended to the text_chunk until it is large enough to be broken into n-grams
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
    """ Generates ElasticSearch query for the given search term

    :param search_term: N-gram to be searched for in the Bavli.
    :return: A dictionary which is the response generated from the query.
    """
    formatted_term = format_search_term(search_term)
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
                               {"query": "{}".format(formatted_term), "default_operator": "AND", "fields": ["content"]}
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
    """

    :param hit_ref: The daf which the result was found on
    :param result: A chunk of text of size greater than n
    :return: None. Adds result to global all_results, or fills in the line numbers for an existing result
    """
    global all_results
    global total_hits_combined
    count_avg = int(mean(result["counts"]))
    text = result["term"]
    score = score_result(text, count_avg)
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
    else:   # If the result has already been generated from the other direction, find that result and add in a more precise location.
        flag = False
        for existing_result in all_results[hit_ref]:
            if ":" not in existing_result["location"] and Ref(existing_result["location"]).contains(Ref(source_range.split("-")[0])):
                if existing_result["text"] == text:
                    existing_result["location"] = source_range
                    flag = True
                    break
    if not flag:
        all_results.setdefault(daf, []).append(scored_result)
        total_hits_combined += 1


def search_n_grams():
    """ Loads in the n-grams and searches every one in the Talmud.

    :return: None. Loads the results into the global variable all_results
    """
    global total_hits
    global most_hits
    files = os.listdir(folder)
    for filename in files:
        tractate_hits = {}
        last_hits = set()    # Set of dafs where there were hits for the last search term.
        with open(folder + os.sep + filename, 'r') as gram_file:
            grams = gram_file.read()
            tractate_grams = json.loads(grams)
        sorted_grams = sorted(tractate_grams, key=lambda x: Ref(x).order_id())
        for ref in sorted_grams:
            print ref
            for search_term in tractate_grams[ref]:
                current_hits = set()
                hit_count = 0
                response = search_bavli(search_term)
                if response is not None:
                    for hit in response["hits"]["hits"]:
                        hit_ref = hit["_source"]["ref"]
                        if not Ref(hit_ref).contains(Ref(ref)):  # Skip hits to the daf where the search term is from
                            hit_count += 1
                            if hit_ref in tractate_hits:
                                tractate_hit = tractate_hits[hit_ref]
                                hit_num = tractate_hit["hit_number"]

                                # For each repeated hit on the same daf, append the last word of that term to each duplicate .
                                if hit_num < len(tractate_hit["dupes"]):
                                    tractate_hit["dupes"][hit_num]["refs"].append(ref)
                                    tractate_hit["dupes"][hit_num]["term"] += (u' ' + search_term.split(" ")[-1])
                                    tractate_hit["dupes"][hit_num]["counts"].append(len(response["hits"]["hits"]))

                                # If there has already been a hit to this daf from the same search_term, add a duplicate result.
                                else:
                                    tractate_hit["dupes"].append({"refs": [ref], "term": search_term,
                                                          "counts": [len(response["hits"]["hits"])]})
                                tractate_hit["hit_number"] += 1
                            else:
                                tractate_hits[hit_ref] = {"hit_number": 1, "dupes": [{"refs": [ref], "term": search_term,
                                                          "counts": [len(response["hits"]["hits"])]}]}
                            current_hits.add(hit_ref)
                total_hits += hit_count
                most_hits = max(most_hits, hit_count)

                # If a daf was not found on this iteration, there are no more contiguous n-grams, so you can add the results for that daf.
                for result in (last_hits - current_hits):
                    for dupe in tractate_hits[result]["dupes"]:
                        score_and_add_result(result, dupe)
                    del (tractate_hits[result])
                for result in current_hits:
                    tractate_hits[result]["hit_number"] = 0
                last_hits = current_hits
        for result in last_hits:
            score_and_add_result(result, tractate_hits[result])
        print "Finished tractate " + filename.replace(".json", "")


def output_profile(runtime):
    """ Print some statistics, as well as the 50 best and 50 worst results

    :param runtime: Runtime for the algorithm in seconds
    :return: None. Write output to profile.txt
    """
    global all_results
    all_results_list = []
    for daf in all_results:
        for result in all_results[daf]:
            all_results_list.append(result)
    results = sorted(all_results_list, key=lambda x: -x["score"])
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
    """ Fill all_results and then output to a json file.

    :return: None. Creates all_results.json with dictionary of daf to list of results for that daf.
    """
    start = timeit.default_timer()
    search_n_grams()
    stop = timeit.default_timer()
    output_profile(stop - start)
    with open("all_results.json", 'w') as results_file:
        json.dump(all_results, results_file)


def compare_masoret_hashas():
    """ Get existing masoret hashas links and look for them in all_results, scoring the ones that are found.

    :return: None. Outputs info to link_results.txt
    """
    global all_results
    links = get_masoret_hashas_links()
    with open("all_results.json", "r") as filename:
        all_results = json.load(filename)
    link_results = []
    for link in links:
        score = None
        if ":" in link[0]:
            daf0 = link[0].split(":")[0]
        else:
            daf0 = link[0]
        if ":" in link[1]:
            daf1 = link[1].split(":")[0]
        else:
            daf1 = link[1]
        try:
            ref0 = Ref(link[0]).surrounding_ref(2)
            ref1 = Ref(link[1]).surrounding_ref(2)
        except Exception as e:
            print e
        else:
            if daf0 in all_results:
                for result in all_results[daf0]:
                    same_source = ref0.contains(Ref(result["source"])) or any(Ref(result["source"]).contains(x) for x in ref0.split_spanning_ref())
                    same_location = ref1.contains(Ref(result["location"])) or any(Ref(result["location"]).contains(x) for x in ref1.split_spanning_ref())
                    if same_source and same_location:
                        score = max(result["score"], score)
            if daf1 in all_results:
                for result in all_results[daf1]:
                    same_source = ref1.contains(Ref(result["source"])) or any(Ref(result["source"]).contains(x) for x in ref1.split_spanning_ref())
                    same_location = ref0.contains(Ref(result["location"])) or any(Ref(result["location"]).contains(x) for x in ref0.split_spanning_ref())
                    if same_source and same_location:
                        score = max(result["score"], score)
        link_results.append((link,score))
    link_results = sorted(link_results, key=lambda x:x[1])
    with open("link_results.txt", "w") as filename:
        nones = 0
        for link_result in link_results:
            if link_result[1] is None:
                filename.write("Link from {} to {} not found \n".format(link_result[0][0], link_result[0][1]))
                nones += 1
            else:
                filename.write("Score is {} for link from {} to {} \n".format(link_result[1], link_result[0][0], link_result[0][1]))
        filename.write("There are {} links not found out of {} total links".format(nones, len(link_results)))


def post_links():
    """ Post contents of all_results as links to the database.

    :return:
    """
    count = 0
    global all_results
    with open("all_results.json", "r") as filename:
        all_results = json.load(filename)
    all_results_list = []
    for daf in all_results:
        for result in all_results[daf]:
            all_results_list.append(result)
    results = sorted(all_results_list, key=lambda x: -x["score"])
    url = 'http://' + server + '/api/links/'
    for result in results:
        if result["score"] < 100:
            print count
            return
        else:
            link = {"refs": [result["source"], result["location"]],
            "type": "mesorat hashas",
            "auto": True,
            "generated_by": "Masoret HaShas Script",
            }
            textJSON = json.dumps(link)
            values = {
                'json': textJSON,
                'apikey': apikey
            }
            data = urllib.urlencode(values)
            req = urllib2.Request(url, data)
            try:
                response = urllib2.urlopen(req)
                count += 1
            except HTTPError, e:
                print e


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
        elif "post" in arg:
            post_links()
        else:
            print "Unknown command"
    else:
        generate_masoret_hashas()
