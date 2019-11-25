
# coding: utf-8


import main as sefariaWord2Vec
from collections import defaultdict
from sefaria.system.database import db

from sefaria.model import *
from sefaria.model.topic import Topic, TopicsManager
from sefaria.system.exceptions import PartialRefInputError, NoVersionFoundError, InputError
from scipy import spatial
import re
import json
import codecs
from math import log as ln
from functools import reduce

def flatten(s):
    if len(s) == 0:
        return s
    if isinstance(s, str):
        return s
    while not isinstance(s[0], str):
        s = reduce(lambda a, b: a + b, s, [])
    return " ".join(s)

def tokenizer(s):
    s = re.sub(r'־', ' ', s)
    s = re.sub(r'\([^)]+\)', '', s)
    s = re.sub(r'\[[^\]]+\]', '', s)
    s = re.sub(r'[^ א-ת]', '', s)
    # remove are parenthetical text
    return s.split()

def tfidf(term_freq, doc_freq, doc_len):
    smoothingFactor = 10
    denom = smoothingFactor*doc_freq + doc_len
    return ln(smoothingFactor*term_freq + 1) - ln(denom)

def doEverything():
    model = sefariaWord2Vec.get_model("word2vec.bin")

    with codecs.open("idf.json", 'rb', encoding='utf8') as fin:
        idf = json.load(fin)

    topics = TopicsManager()
    SCORE_QUOTE = 0.2
    SCORE_WORD = 1
    SCORE_SHEET = 2

    my_topics = {}

    topic_list = topics.list()
    for itag, tag_dict in enumerate(topic_list):
        tag = tag_dict["tag"]
        print("TAG {} {}/{}".format(tag, itag, len(topic_list)))

        t = topics.get(tag)
        core_segs = t.contents()['sources']
        source_sheet_count_dict = {
            ref: count for ref, count in core_segs
        }
        keywords = {}
        seg_sheet_count = {}
        term = Term().load({'name': tag})
        if getattr(term, 'titles', False):
            hetitles = [x for x in term.titles if x['lang'] == 'he']
            hetitleVecs = [model[title['text']] for title in hetitles if title['text'] in model]
            if len(hetitleVecs) == 0:
                print("No titles in model for {}".format(tag))
                continue
        else:
            print("No term for {}".format(tag))
            continue

        potential_keywords = {}
        for seg, count in core_segs:
            r = Ref(seg)
            tc = TextChunk(r, 'he')
            text = flatten(tc.text)
            try:
                words = tokenizer(text)
            except TypeError as e:
                continue
            term_freqs = defaultdict(int)
            for w in words:
                term_freqs[w] += 1
            cosDists = [min([spatial.distance.cosine(model[w],titleVec) for titleVec in hetitleVecs])                 for w in words if w in model]
            tfidf_list = [tfidf(term_freqs[w], idf[w], len(words)) for w in words]
            for w, d, tf in zip(words, cosDists, tfidf_list):
                if w not in potential_keywords:
                    potential_keywords[w] = {"cosDist": d, "count": 1, "tfidf": tf}
                else:
                    potential_keywords[w]["count"] += 1

        for w, v in list(potential_keywords.items()):
            v["score"] = (v["cosDist"]**v["count"])*(-v["tfidf"])

        potential_keywords = [x for x in list(potential_keywords.items()) if x[1]["score"] < 3.5 and len(x[0]) > 2]
        potential_kw_dict = {
            x[0]: x[1]["score"] for x in potential_keywords
        }

        segs_to_search = set()
        for seg, count in core_segs:
            r = Ref(seg)
            for l in r.linkset():
                segs_to_search.add(l.refs[0])
                segs_to_search.add(l.refs[1])

        segs_to_search_dicts = {}
        for seg in segs_to_search:
            temp_seg_dict = {"score": 0.0}
            try:
                r = Ref(seg)
                tc = TextChunk(r, "he")
                words = tokenizer(flatten(tc.text))
                matched_words = set()
                for w in words:
                    temp_word_score = potential_kw_dict.get(w, 0.0) * SCORE_WORD
                    if 0 < temp_word_score < 0.5:
                        matched_words.add(w)
                    temp_seg_dict["score"] -= temp_word_score
                temp_seg_dict["score"] = temp_seg_dict["score"] / len(words) if temp_seg_dict["score"] != 0.0 else 0.0  # normalize word scores
                temp_seg_dict["score"] += source_sheet_count_dict.get(seg, 0.0) * SCORE_SHEET
                temp_seg_dict["base_score"] = temp_seg_dict["score"]
                temp_seg_dict["category"] = r.primary_category
                temp_seg_dict["matched_words"] = list(matched_words)
                temp_seg_dict["heRef"] = r.he_normal()
                try:
                    tp = r.index.best_time_period()
                    if not tp is None:
                        comp_start_date = int(tp.start)
                    else:
                        comp_start_date = 3000  # far in the future
                except UnicodeEncodeError as e:
                    comp_start_date = 3000
                temp_seg_dict["timeperiod"] = comp_start_date
                segs_to_search_dicts[seg] = temp_seg_dict
            except PartialRefInputError as e:
                continue
            except NoVersionFoundError as e:
                continue
            except TypeError as e:
                continue
            except InputError as e:
                continue
        for seg, temp_seg_dict in list(segs_to_search_dicts.items()):
            try:
                r = Ref(seg)
                links = reduce(lambda a, b: a | set(b.refs), r.linkset(), set())
                try:
                    links.remove(seg)  # no self-links
                except KeyError as e:
                    pass
                for l in links:
                    temp_seg_dict["score"] += segs_to_search_dicts.get(l, {}).get("base_score", 0.0) * SCORE_QUOTE
            except PartialRefInputError as e:
                pass

        segs_to_search_dict_items = [x for x in list(segs_to_search_dicts.items()) if x[1]["score"] > 2]
        segs_to_search_dict_items.sort(key=lambda x: -x[1]["score"])
        segs_to_search_dict_items = segs_to_search_dict_items[:20]
        my_topics[hetitles[0]['text']] = [
            {"ref": temp_seg_dict["heRef"], "score": temp_seg_dict["score"], "timeperiod": temp_seg_dict["timeperiod"], "category": temp_seg_dict["category"], "matched": temp_seg_dict["matched_words"]} for ref, temp_seg_dict  in segs_to_search_dict_items
        ]

    with codecs.open("my_topics.json", 'wb', encoding='utf8') as fout:
        json.dump(my_topics, fout, ensure_ascii=False, indent=2, encoding='utf8')

doEverything()


