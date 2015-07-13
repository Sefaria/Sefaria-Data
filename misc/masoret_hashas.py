# -*- coding: utf-8 -*-

__author__ = 'Izzy'

import os
import sys
import json
import urllib2
from urllib2 import HTTPError
import re


from sefaria.model import *

server = "sefaria.org"
# server = "localhost:8000"
# search_server = "http://search.sefaria.org:788"
search_server = "http://localhost:9200"
folder = "n_grams"

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

# Here's where we use various heuristics to chop out the bad grams. Takes gram as list, not string!
def check_gram(gram):
    amar_count = 0
    rav_count = 0
    chain_count = 0
    for word in gram:
        if any(root in word for root in said):
            amar_count += 1
        if word in ravs:
            rav_count += 1
        if word in chain:
            chain_count += 1
    rabbinic_chain = amar_count > 1 or rav_count > 1 or chain_count > 1
    common_phrase = any(phrase in (" ".join(gram)) for phrase in phrases)
    return not (rabbinic_chain or common_phrase)


def format_search_term(search_term):
    special_chars = ['+', '-', '=', '&&', '||', '>', '<', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~', '*', '?',
                     ':', '/']
    for char in special_chars:
        search_term = search_term.replace(char, '\\' + char)
    search_term = '"' + search_term + '"'
    return search_term.encode('utf-8')

def api_get_text(ref, lang=None, version=None):
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


def search_bavli(search_term):
    url = '{}/sefaria/_search'.format(search_server)
    data = {"sort": [{"order": {}}],
            "highlight":
                {"pre_tags": ["<b>"], "post_tags": ["</b>"], "fields":
                    {"content": {"fragment_size": 200}}
                 },
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
            text = re.sub(r"\((?=[^\)\s,]+\s){1,3}[^\)]*,\s[^\)\s]{1,3}\)", "", text)
            text_list = text.split()
            count = 1
            while len(prev_gram) > 1:
                prev_gram.pop(0)
                new_gram = prev_gram + text_list[:count]
                if check_gram(new_gram):
                    formatted_gram = " ".join(new_gram)
                    grams[gram_key].append(formatted_gram)
                count += 1
            gram_list = [text_list[i:i + n] for i in xrange(len(text_list) - n + 1)]
            for gram in gram_list:
                if check_gram(gram):
                    formatted_gram = " ".join(gram)
                    grams[gram_key].append(formatted_gram)
            prev_gram = gram
            ref = text_obj.get("next")
        with open(folder + os.sep + tractate + ".json", 'w') as gram_file:
            json.dump(grams, gram_file)
        print "Hadran " + tractate


def search_n_grams():
    hits = []
    files = os.listdir(folder)
    # for filename in files:
    for filename in ["Tamid.json"]:
        with open(folder + os.sep + filename, 'r') as gram_file:
            grams = gram_file.read()
            tractate_grams = json.loads(grams)
        refs = sorted(tractate_grams.keys(), key=lambda ref_string: Ref(ref_string).order_id())
        for ref in refs:
            daf_hits = {}
            for search_term in tractate_grams[ref]:
                formatted_term = format_search_term(search_term)
                response = search_bavli(formatted_term)
                if response is not None:
                    for hit in response["hits"]["hits"]:
                        if hit["_source"]["ref"] != ref:
                            if hit["_source"]["ref"] in daf_hits:
                                daf_hits[hit["_source"]["ref"]].append(search_term)
                            else:
                                daf_hits[hit["_source"]["ref"]] = [search_term]
                        else:
                            # print "Found text containing original n-gram"
                            pass
                else:
                    # print "None"
                    pass
            sorted_hits = sorted(daf_hits.keys(), key=lambda hit_ref: Ref(hit_ref).order_id())
            for hit_ref in sorted_hits:
                if [hit_ref, ref, daf_hits[hit_ref]] not in hits:
                    hits.append([ref, hit_ref, daf_hits[hit_ref]])
    return hits


def generate_masoret_hashas():
    hits = search_n_grams()
    for hit in hits:
        print "Hit from " + hit[0].encode('utf-8') + " to " + hit[1].encode('utf-8') + " with text " + \
            (",".join(hit[2])).encode('utf-8')



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