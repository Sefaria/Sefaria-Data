# -*- coding: utf-8 -*-

__author__ = 'Izzy'

import os
import sys
import json
import urllib
import urllib2
from urllib2 import HTTPError
import re
from numpy import mean
import timeit
import unicodedata

sys.path.append("C:\\Users\\Izzy\\git\\Sefaria-Project")
from sefaria.model import *
from sefaria.system import exceptions

server = "localhost:8000"
# server = "dev.sefaria.org"
# search_server = "http://search.sefaria.org:788"
search_server = "http://localhost:9200"
folder = "n_grams"
apikey = 'iRa0Y51Rq5X81VqxXYD46ovvfayvW6CK9hQgyyKa3GY'

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
linked_hits = 0
unlinked_hits = 0


def remove_punctuation(terms):
    """ Remove punctuation from a series of n-grams.

    :param terms: list of strings
    :return: list of strings with punctuation removed
    """
    new_terms = []
    table = dict.fromkeys(i for i in xrange(sys.maxunicode)
                          if unicodedata.category(unichr(i)).startswith('P'))
    for term in terms:
        new_terms.append(term.translate(table))
    return new_terms


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
                refs = link_dict["refs"]
                if refs:
                    try:
                        ref0 = Ref(refs[0])
                        ref1 = Ref(refs[1])
                        if ref0.is_bavli() and ref1.is_bavli():
                            if refs not in masoret_hashas_links:
                                masoret_hashas_links.append(refs)
                    except exceptions.InputError as e:
                        pass
    return masoret_hashas_links


def score_result(result, count_avg):
    """ Using given heuristics, give each result a value representing its likely importance as a link

    :param result: String representing shared text between two sources
    :param count_avg: Average of the number of times each n-gram in the result was found in the data set
    :returns: Score as integer
    """
    word_list = result.split(" ")
    score = (len(word_list) - 6) * 10
    score -= (count_avg * 10)
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
    cite_count = len(library.get_refs_in_string(result, "he"))  # Number of Biblical citations in text
    score -= (20 * cite_count)
    return score


def format_search_term(search_term):
    """ Format search term to be URL friendly

    :param search_term: String
    :returns: Unicode string
    """
    special_chars = ['\\', '+', '-', '=', '&&', '||', '>', '<', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~', '*',
                     '?',
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
                # ref_range keeps track of the source of every word in the current text_chunk,
                # so a range can be constructed for every n-gram
                ref_range += [current_ref] * len(word_list)
                # Text is appended to the text_chunk until it is large enough to be broken into n-grams
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
        print 'Error code: ', e.code, " because ", e.reason, " for ", search_term.encode('utf-8')


def score_and_add_result(sources, locations, terms, counts):
    """ Given the data representing a textual link, give it a score and output it in the "results" format

    :param sources: List of Strings where sources[i] is the ref for terms[i]
    :param locations: List of Strings representing refs that these terms were found on
    :param terms: List of n-grams as Strings
    :param counts: List of integers where counts[i] is the number of times terms[i] was found in the database
    :return: A result, which is a map containing the source, location, text, and score of a link
    """
    count_avg = int(mean(counts))
    text = terms[0]
    for term in terms[1:]:
        text += " " + term.split()[-1]
    score = score_result(text, count_avg)
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

    if locations[-1] == locations[0]:
        location_range = locations[0]
    else:
        if '-' in locations[0]:
            location_range = locations[0].split("-")[0]
        else:
            location_range = locations[0]
        if "-" in locations[-1]:
            location_range += ("-" + locations[-1].split('-')[1])
        else:
            location_range += ("-" + locations[-1].split(" ")[-1])
    scored_result = {"source": source_range, "location": location_range, "text": text, "score": score}
    return scored_result


def split_hit(hit):
    """ Given a hit where some of the n-grams in it have been removed to make a result,
    break the hit down into the reamining lists of contiguous n-grams

    :param hit: A map of strings to lists where every list has the same number of indices and each index represents a
    single n-gram in the contiguous chunk of n-grams
    :return: A list of new hits constructed from 'hit'
    """
    new_hits = []
    new_terms = []
    new_refs = []
    new_counts = []
    new_dupes = []
    for i in xrange(len(hit["duplicates"])):
        if hit["duplicates"][i] >= 0:
            new_terms.append(hit["terms"][i])
            new_refs.append(hit["refs"][i])
            new_counts.append(hit["counts"][i])
            new_dupes.append(hit["duplicates"][i])
        elif new_terms and new_refs and new_counts and new_dupes:
            new_hits.append({"terms": new_terms, "refs": new_refs, "counts": new_counts, "duplicates": new_dupes})
            new_terms = []
            new_refs = []
            new_counts = []
            new_dupes = []
    if new_terms and new_refs and new_counts and new_dupes:
        new_hits.append({"terms": new_terms, "refs": new_refs, "counts": new_counts, "duplicates": new_dupes})
    return new_hits


def find_reverse_hit(this_hit, those_hits):
    """ Find if the given hit from A to B has text which is a subset of the list of hits from B to A

    :param this_hit: A hit from source A to location B
    :param those_hits: The list of hits from source B to location A
    :return result: None if no overlapping text is found, a result generated by score_and_add_result() otherwise.
    :return hit_to_delete: None if no overlapping text is found,
    the hit in those_hits that was matched with this_hit otherwise.
    """
    result = None
    hit_to_delete = None
    this_term = remove_punctuation(this_hit["terms"])
    for that_hit in those_hits:
        that_term = remove_punctuation(["terms"])
        if any(this_term == that_term[i:i + len(this_term)] for i in xrange(len(that_term))):
            terms = this_hit["terms"]
            sources = this_hit["refs"]
            counts = this_hit["counts"]
            locations = []
            for x in xrange(len(this_hit["terms"])):
                i = that_hit["terms"].index(this_hit["terms"][x])
                this_hit["duplicates"][x] -= 1
                that_hit["duplicates"][i] -= 1
                locations.append(that_hit["refs"][i])
            hit_to_delete = that_hit
            result = score_and_add_result(sources, locations, terms, counts)
            break
        elif any(that_term == this_term[i:i + len(that_term)] for i in xrange(len(this_term))):
            terms = that_hit["terms"]
            sources = that_hit["refs"]
            counts = that_hit["counts"]
            locations = []
            for x in xrange(len(that_hit["terms"])):
                i = this_hit["terms"].index(that_hit["terms"][x])
                that_hit["duplicates"][x] -= 1
                this_hit["duplicates"][i] -= 1
                locations.append(this_hit["refs"][i])
            hit_to_delete = that_hit
            result = score_and_add_result(sources, locations, terms, counts)
            break
    return result, hit_to_delete


def merge_hits(hits):
    """ For every hit where the source is a refstring A with daf and line numbers and the location is a
    refstring B which is a daf, try to find a hit from B to A and then merge the hits so that both source
    and location have line numbers.

    :param hits: A mapping of all Dafs in the Bavli to a the hits found on that daf,
    stored as a dictionary from the daf where the hit was found to a list of hits.
    :return: A new mapping with the same structure as hits, but with lists of results instead of lists of hits.
    """
    global linked_hits
    global unlinked_hits
    all_results = {}
    for this_daf in hits.keys():
        for that_daf in hits[this_daf].keys():
            if that_daf != this_daf:
                for this_hit in sorted(hits[this_daf][that_daf], key=lambda x: -len(x["terms"])):
                    result = None
                    if that_daf in hits and this_daf in hits[that_daf]:
                        those_hits = sorted(hits[that_daf][this_daf], key=lambda x: -len(x["terms"]))
                        result, hit_to_delete = find_reverse_hit(this_hit, those_hits)

                    if result:
                        hits[this_daf][that_daf] += split_hit(this_hit)
                        hits[that_daf][this_daf] += split_hit(hit_to_delete)
                        hits[that_daf][this_daf].remove(hit_to_delete)
                        if not hits[that_daf][this_daf]:
                            del hits[that_daf][this_daf]
                        linked_hits += 1
                    else:
                        result = score_and_add_result(this_hit["refs"], [that_daf], this_hit["terms"],
                                                      this_hit["counts"])
                        for i in xrange(len(this_hit["duplicates"])):
                            this_hit["duplicates"][i] -= 1
                        hits[this_daf][that_daf] += split_hit(this_hit)
                        unlinked_hits += 1

                    if this_daf not in all_results:
                        all_results[this_daf] = {}
                    if that_daf not in all_results[this_daf]:
                        all_results[this_daf][that_daf] = []
                    all_results[this_daf][that_daf].append(result)
        del hits[this_daf]
    return all_results


def search_n_grams():
    """ Loads in the n-grams and searches every one in the Talmud.

    :return: A dictionary of dafs as Strings mapped to dictionaries of dafs to hits
    """
    global total_hits
    global most_hits
    hits = {}
    files = os.listdir(folder)
    for filename in files:
        tractate_hits = {}
        last_hits = set()  # Set of dafs where there were hits for the last search term.
        with open(folder + os.sep + filename, 'r') as gram_file:
            grams = gram_file.read()
            tractate_grams = json.loads(grams)
        sorted_grams = sorted(tractate_grams, key=lambda x: Ref(x).order_id())
        for ref in sorted_grams:
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
                                if hit_ref in current_hits:
                                    tractate_hits[hit_ref]["duplicates"][-1] += 1
                                else:
                                    tractate_hits[hit_ref]["refs"].append(ref)
                                    tractate_hits[hit_ref]["duplicates"].append(0)
                                    tractate_hits[hit_ref]["counts"].append(len(response["hits"]["hits"]))
                                    tractate_hits[hit_ref]["terms"].append(search_term)
                            else:
                                tractate_hits[hit_ref] = {"refs": [ref], "terms": [search_term], "duplicates": [0],
                                                          "counts": [len(response["hits"]["hits"])]}
                            current_hits.add(hit_ref)
                total_hits += hit_count
                most_hits = max(most_hits, hit_count)
                for result_daf in (last_hits - current_hits):
                    daf = Ref(tractate_hits[result_daf]["refs"][0]).section_ref()
                    if daf.is_spanning():
                        daf = daf.first_spanned_ref()
                    daf = daf.tref
                    if daf in hits:
                        if result_daf in hits[daf]:
                            hits[daf][result_daf].append(tractate_hits[result_daf])
                        else:
                            hits[daf][result_daf] = [tractate_hits[result_daf]]
                    else:
                        hits[daf] = {result_daf: [tractate_hits[result_daf]]}
                    del tractate_hits[result_daf]
                last_hits = current_hits
        for result_daf in last_hits:
            if result_daf in hits:
                daf = Ref(tractate_hits[result_daf]["refs"][0]).section_ref()
                if daf.is_spanning():
                    daf = daf.first_spanned_ref()
                if daf in hits:
                    if result_daf in hits[daf]:
                        hits[daf][result_daf].append(tractate_hits[result_daf])
                    else:
                        hits[daf][result_daf] = [tractate_hits[result_daf]]
                else:
                    hits[daf] = {result_daf: [tractate_hits[result_daf]]}
        print "Finished tractate " + filename.replace(".json", "")
    with open("all_hits.json", "w") as all_hits:
        json.dump(hits, all_hits)
    return hits


def output_profile(runtime, all_results):
    """ Print some statistics, as well as the 50 best results and 50 worst unqiue results to profile.txt

    :param runtime: Runtime for the algorithm in seconds
    :return: None.
    """
    all_results_list = []
    for daf in all_results:
        for location_daf in all_results[daf]:
            for result in all_results[daf][location_daf]:
                all_results_list.append(result)
    results = sorted(all_results_list, key=lambda x: -x["score"])
    worst_results = []
    phrases_seen = set()
    for result in results[::-1]:
        if result["text"] not in phrases_seen:
            phrases_seen.add(result["text"])
            worst_results.append(result)
        if len(worst_results) >= 50:
            break
    output = ["Runtime is " + str(runtime) + " seconds \n", "Most number of hits for one search is " + str(most_hits),
              "\nTotal number of hits for 6_grams is " + str(total_hits) + " and for 6+grams is " + str(
                  len(all_results_list)),
              "\nNumber of linked hits is " + str(linked_hits) + " and unlinked hits is " + str(unlinked_hits),
              "\n\n" + "Top ten best hits are: \n"]
    for result in results:
        output.append("Hit from {} to {} with text {} and score {} \n".format(result["source"], result["location"],
                                                                              result["text"].encode('utf-8'),
                                                                              result["score"]))
    """
    output.append("\n" + "Worst hits are: \n")
    for result in worst_results:
        output.append("Hit from {} to {} with text {} and score {} \n".format(result["source"], result["location"],
                                                                              result["text"].encode('utf-8'),
                                                                              result["score"]))

    """
    with open("profile.txt", 'w') as profile:
        profile.writelines(output)


def generate_masoret_hashas():
    """ Write dictionary of results to a json file and output other information to a text file.

    :return: None. Creates all_results.json with dictionary of daf to list of results for that daf.
    """
    start = timeit.default_timer()
    if os.path.isfile("all_hits.json"):
        with open("all_hits.json", "r") as all_hits_file:
            hits = json.load(all_hits_file)
    else:
        hits = search_n_grams()
    all_results = merge_hits(hits)
    stop = timeit.default_timer()
    output_profile(stop - start, all_results)
    with open("all_results.json", 'w') as results_file:
        json.dump(all_results, results_file)


def compare_masoret_hashas():
    """ Get existing masoret hashas links and look for them in all_results, scoring the ones that are found.

    :return: None.
    """
    links = get_masoret_hashas_links()
    with open("all_results.json", "r") as filename:
        all_results = json.load(filename)
    link_results = []
    sukkah_links = []
    found_count = 0
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
        # Check the previous daf as well, in case the hit spans multiple dafs.
        prev0 = Ref(daf0).prev_section_ref()
        prev1 = Ref(daf1).prev_section_ref()
        ref0 = Ref(link[0]).surrounding_ref(2)
        ref1 = Ref(link[1]).surrounding_ref(2)
        results = []
        if daf0 in all_results and daf1 in all_results[daf0]:
            results += all_results[daf0][daf1]
        if prev0 and prev0.tref in all_results and daf1 in all_results[prev0.tref]:
            results += all_results[prev0.tref][daf1]
        if daf1 in all_results and daf0 in all_results[daf1]:
            results += all_results[daf1][daf0]
        if prev1 and prev1.tref in all_results and daf0 in all_results[prev1.tref]:
            results += all_results[prev1.tref][daf0]
        for result in results:
            same_source0 = ref0.contains(Ref(result["source"])) or Ref(result["source"]).contains(ref0)
            same_location0 = ref1.contains(Ref(result["location"])) or Ref(result["location"]).contains(ref1)
            same_source1 = ref1.contains(Ref(result["source"])) or Ref(result["source"]).contains(ref1)
            same_location1 = ref0.contains(Ref(result["location"])) or Ref(result["location"]).contains(ref0)
            if (same_source0 and same_location0) or (same_source1 and same_location1):
                found_count += 1
                score = max(result["score"], score)
                sukkah_links.append(result)
        link_results.append((link, score))
    link_results = sorted(link_results, key=lambda x: x[1])
    positive_results = [x for x in link_results if x[1] is not None and x[1] >= 0]
    with open("link_results.txt", "w") as filename:
        filename.write(
            "{}/{} of the existing links have been found, and {} have non-negative scores \n".format(found_count,
                                                                                                     len(link_results),
                                                                                                     len(
                                                                                                         positive_results)))
        for link_result in link_results:
            if link_result[1] is None:
                filename.write("Link from {} to {} not found \n".format(link_result[0][0], link_result[0][1]))
            else:
                filename.write("Score is {} for link from {} to {} \n".format(link_result[1], link_result[0][0],
                                                                              link_result[0][1]))

    sukkah_results = []
    for daf in all_results:
        if "Sukkah" in daf:
            for result_daf in all_results[daf]:
                for result in all_results[daf][result_daf]:
                    if result not in sukkah_links:
                        sukkah_results.append(result)
        else:
            for result_daf in all_results[daf]:
                if "Sukkah" in result_daf:
                    for result in all_results[daf][result_daf]:
                        if result not in sukkah_links:
                            sukkah_results.append(result)
    sorted_sukkah = sorted(sukkah_results, key=lambda x: -x["score"])
    positive_sukkah = [x for x in sorted_sukkah if x["score"] >= 0]
    with open("sukkah_results.txt", "w") as filename:
        filename.write(
            "{} links were generated by this algorithm for Sukkah but are not in the existing Masoret Hashas links. \n".format(
                len(positive_sukkah)))
        for result in positive_sukkah:
            filename.write("Hit from {} to {} with text {} and score {} \n".format(result["source"], result["location"],
                                                                                   result["text"].encode('utf-8'),
                                                                                   result["score"]))


def post_links():
    """ Post contents of all_results as links to the database.

    :return: None
    """
    count = 0
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
            textjson = json.dumps(link)
            values = {
                'json': textjson,
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
