# -*- coding: utf-8 -*-
"""
This file contains our ES quality testing suite
it is meant to create a test index, make test queries, and evaluate the quality of responses
"""
import bleach
import re
import codecs
import unicodecsv
import pageranklowram
import json
import logging
import math
from collections import defaultdict, OrderedDict
from sefaria.model import *
from sefaria.settings import SEARCH_ADMIN
from sefaria.system.exceptions import InputError
from sefaria.system.exceptions import NoVersionFoundError
from sefaria.utils.hebrew import strip_cantillation
from pyelasticsearch import ElasticSearch
from pyelasticsearch import ElasticHttpError
from pyelasticsearch import bulk_chunks


logging.disable(logging.WARNING)

es = ElasticSearch(SEARCH_ADMIN)
TEST_INDEX_NAME = "test"

pagerank_dict = {r: v for r, v in json.load(open("pagerank.txt","rb"))}

test_he_query_list = [
    'וידבר יהוה אל משה לאמר',
    'ארבע שנכנס',
    'מוקצה מחמת מיאוס',
    'לא בשבים היא',
    'עשרת הדיברות',
    'נעשה ונשמע',
    'ברוך שם כבוד מלכותו לעולם ועד',
    'צער בעלי חיים',
    'ט״ו בשבט',
    'ט״ו באב',
    'תפילין',
    'יצר הרע',
    'עם הארץ',
    'קל וחמר',
    'חנוכה',
    'עבד עברי',
    'מקלל אביו ואמו',
    'מעשה אבות סימן לבנים',
    'תיקון עולם',
    'בית המקדש',
    'בן יקיר',
    'אשה סוטה',
    'עינוי יום כיפור',
    'פרסום הנס',
    'ברית שלום',
    'יעקב ועשו',
    'ברכה לבטלה',
    'ענני הכבוד',
    'עץ חיים',
    'גיד הנשה',
    'גיהנם',
    'אור לגויים',
    'עבודה זרה',
    'יד חזקה',
    'סנה',
    'יום כיפור',
    'יום הכיפורים',
    'ודברת בם',
    'מצות עשה',
    'חמץ ומצה',
    'בל יראה ובל ימצא',
    'ממזר',
    'שמנה שרצים',
    'דוד המלך',
    'קדיש שלם',
    'סיחון ועוג',
    'חכמים זכרונם לברכה',
    'שומר חינם',
    'בן יומו',
    'חייב ממון',
    'תקנת רבנו גרשום',
    'ברכת המזון',
    'מאכל בן דורסאי',
    'ספק ספיקא',
    'מעשה מרכבה',
    'בין השמשות',
    'גזירת שוה',
    'מאמתי קורין',
    'רשות הרבים',
    'בעל מום',
    'עולם הבא'
]

test_en_query_list = [
    'queen esther',
    'purim',
    'chanukah',
    'sukkot',
    'love',
    'shofar',
    'community',
    'teshuva',
    'yom kippur',
    'leadership',
    'prayer',
    'stranger',
    'world to come',
    'noah',
    'tikkun olam',
    'forgiveness',
    'menorah',
    'jesus',
    'burning bush',
    'messiah',
    'olive oil',
    'creation',
    'thanksgiving offering',
    'temple jerusalem'
]

def clear_index():
    """
    Delete the search index.
    """
    try:
        es.delete_index(TEST_INDEX_NAME)
    except Exception, e:
        print "Error deleting Elasticsearch Index named %s" % TEST_INDEX_NAME
        print e


def make_index():
    try:
        clear_index()
    except ElasticHttpError:
        print "Failed to delete non-existent index: {}".format(TEST_INDEX_NAME)

    settings = {
        "index": {
            "analysis": {
                "analyzer": {
                    "original": {
                        "tokenizer": "standard",
                        "filter": [
                                "standard",
                                "lowercase",
                                "icu_normalizer",
                                "icu_folding",
                                "icu_collation"
                                ]
                    }
                }
            }
        }
    }

    print 'CReating index {}'.format(TEST_INDEX_NAME)
    es.create_index(TEST_INDEX_NAME, settings)
    make_mapping()


def make_mapping():
    """
    Settings mapping for the text document type.
    """
    text_mapping = {
        'a': {
            'properties': {
                'hebmorph-standard': {
                    'type': 'string',
                    'analyzer': 'hebrew'
                },
                'hebmorph-exact': {
                    'type': 'string',
                    'analyzer': 'hebrew',
                    'search_analyzer': 'hebrew_exact'
                },
                'ngram': {
                    'type': 'string',
                    'analyzer': 'sefaria-ngram'
                },
                'infreq': {
                    'type': 'string',
                    'analyzer': 'sefaria-infreq'
                },
                'original': {
                    'type': 'string',
                    'analyzer': 'original'
                },
                'aggresive-ngram': {
                    'type': 'string',
                    'analyzer': 'sefaria-aggresive-ngram'
                },
                "order": {
                    'type': 'string',
                    'index': 'not_analyzed'
                },
                "ref": {
                    'type': 'string',
                    'index': 'not_analyzed'
                }
            }
        }
    }
    es.put_mapping(TEST_INDEX_NAME, "a", text_mapping)

def orderid2int(orderid):
    orderid += '0' * (7 - len(orderid))

    max_num = sum([255 * (2 ** (8 * (len(orderid)-i-1))) for i, c in enumerate(orderid)])
    return math.log(max_num - sum([ord(c) * (2 ** (8 * (len(orderid)-i-1))) for i, c in enumerate(orderid)]))


def index_all(merged=False, skip=0):
    if skip == 0:
        make_index()
    index_all_sections(skip=skip, merged=merged)


def make_text_index_document(tref, version, lang):
    """
    Create a document for indexing from the text specified by ref/version/lang
    """
    oref = Ref(tref)
    text = TextFamily(oref, context=0, commentary=False, version=version, lang=lang).contents()

    content = text["he"] if lang == 'he' else text["text"]
    if not content:
        # Don't bother indexing if there's no content
        return False

    if isinstance(content, list):
        content = " ".join(content)

    content = bleach.clean(content, strip=True, tags=())
    content = strip_cantillation(content,strip_vowels=True)
    return {
        "ref": oref.normal(),
        "ref_order": oref.order_id(),
        "ref_order_int": orderid2int(oref.order_id()),
        "pagerank": math.log(pagerank_dict[oref.normal()]) + 20 if oref.normal() in pagerank_dict else 1.0,
        "pagerank-original": pagerank_dict[oref.normal()] if oref.normal() in pagerank_dict else 1E-8,
        "version": version,
        "lang": lang,
        "hebmorph-standard": content,
        "hebmorph-exact": content,
        "ngram": content,
        "infreq": content,
        "aggresive-ngram": content,
        "original": content
    }


def index_all_sections(skip=0, merged=False):
    for chunk in bulk_chunks(get_all_documents(skip=skip, merged=merged), bytes_per_chunk=15E6):
        es.bulk(chunk, doc_type='a', index=TEST_INDEX_NAME)


def get_all_documents(skip=0, merged=False):
    """
    Step through refs of all sections of available text and index each.
    """
    refs = library.ref_list()

    print "Beginning index of %d refs." % len(refs)

    bulk_requests = []
    for i in range(skip, len(refs)):
        if i % 100 == 0:
            print "{}/{}".format(i, len(refs))
        docs = index_text(refs[i], merged=merged)
        for doc in docs:
            #bulk_request += "{\"index\":{\"_index\":\"{}\",\"_type\":a,\"_id\":{}}}\n".format(TEST_INDEX_NAME,doc_obj['id'])
            #bulk_request += "{}\n".format(doc_obj['doc'])
            yield es.index_op(doc)



def index_text(oref, version=None, lang=None, bavli_amud=True, merged=False):
    """
    Index the text designated by ref.
    If no version and lang are given, this function will be called for each available version.
    If `merged` is true, and lang is given, it will index a merged version of this document

    :param str index_name: The index name, as provided by `get_new_and_current_index_names`
    :param str oref: Currently assumes ref is at section level.
    :param str version: Version being indexed
    :param str lang: Language of version being indexed
    :param bool bavli_amud:  Is this Bavli? Bavli text is indexed by section, not segment.
    :param bool merged: is this a merged index?
    :return:
    """
    assert isinstance(oref, Ref)
    oref = oref.default_child_ref()

    # Recall this function for each specific text version, if none provided
    if merged and version:
        raise InputError("index_text() called with version title and merged flag.")
    if not merged and not (version and lang):
        docs = []
        for v in oref.version_list():
            doc = index_text(oref, version=v["versionTitle"], lang=v["language"], bavli_amud=bavli_amud)
            if doc:
                docs += doc
        return docs
    elif merged and not lang:
        docs = []
        for l in ["he", "en"]:
            doc = index_text(oref, lang=l, bavli_amud=bavli_amud, merged=merged)
            if doc:
                docs += doc
        return docs

    # Index each segment of this document individually
    padded_oref = oref.padded_ref()
    if bavli_amud and padded_oref.is_bavli() and False:  # DON'T DO THIS - Index bavli by amud. and commentaries by line
        pass
    elif len(padded_oref.sections) < len(padded_oref.index_node.sectionNames):
        try:
            t = TextChunk(oref, lang=lang, vtitle=version) if not merged else TextChunk(oref, lang=lang)
        except NoVersionFoundError:
            return

        docs = []
        for ref in oref.subrefs(len(t.text)):
            docs += index_text(ref, version=version, lang=lang, bavli_amud=bavli_amud, merged=merged)
        return docs # Returning at this level prevents indexing of full chapters

    '''   Can't get here after the return above
    # Don't try to index docs with depth 3
    if len(oref.sections) < len(oref.index_node.sectionNames) - 1:
        return
    '''
    bulk_request = ""
    # Index this document as a whole
    try:
        doc = make_text_index_document(oref.normal(), version, lang)
    except Exception as e:
        print u"Error making index document {} / {} / {} : {}".format(oref.normal(), version, lang, e.message)
        return []

    if doc:
        #doc['_id'] = make_text_doc_id(oref.normal(), version, lang)
        return [doc]
    else:
        return []


def make_text_doc_id(ref, version, lang):
    """
    Returns a doc id string for indexing based on ref, versiona and lang.

    [HACK] Since Elasticsearch chokes on non-ascii ids, hebrew titles are converted
    into a number using unicode_number. This mapping should be unique, but actually isn't.
    (any tips welcome)
    """
    if not version:
        version = "merged"
    else:
        try:
            version.decode('ascii')
        except Exception, e:
            version = str(unicode_number(version))

    id = "%s (%s [%s])" % (ref, version, lang)
    return id


def unicode_number(u):
    """
    Returns a number corresponding to the sum value
    of each unicode character in u
    """
    n = 0
    for i in range(len(u)):
        n += ord(u[i])
    return n


def query(q, fields, query_type, size):
    """

    :param q: query string
    :param fields: string or list of fields to query
    :param query_type: so far, multi_match, match and match_phrase are supported
    :param size: max num docs to ret
    :return: query results from ES
    """

    q = re.sub('(\S)"(\S)', '\1\u05f4\2', q)  # Replace internal quotes with gershaim.

    if query_type == "multi_match":
        full_query = {

          "query":{
            "function_score":{
            "query": {
                "multi_match": {
                    "type": "most_fields",
                    "query": q,
                    "fields": fields
                }
            },
            "field_value_factor": {
                "field": "pagerank"
            }}
        }}
        fields = fields[0]
    else:
        full_query = {
            "query": {
                "function_score": {
                    "query": {
                        "{}".format(query_type): {
                            "{}".format(fields): q
                        }
                },
                    "field_value_factor": {
                        "field": "pagerank"
                    }
            }

            }
        }

    full_query["highlight"] = {
        "pre_tags": ["<b>"],
        "post_tags": ["</b>"],
        "fields": {
            "{}".format(fields): {"fragment_size": 200}
        }
    }
    """
    {
      "size": 200,
      "query": {
        "function_score": {
          "query": {
            "match_phrase": {
              "hebmorph-standard": "וידבר יהוה אל־משה לאמר"
            }
          },
          "field_value_factor": {
            "field": "pagerank"
          }
        }
      }
    }
    """
    full_query['size'] = size
    res = es.search(full_query, index=TEST_INDEX_NAME, doc_type="a")

    return res


def query_result_to_csv_rows(results, field):
    """

    :param result: result as returned by ES
    :param field: field that's highlighted
    :return:
    """

    return [{
        "Score": result["_score"],
        "Lang": result["_source"]["lang"],
        "Ref": result["_source"]["ref"],
        "Content": result["highlight"][field][0],
        "Version": result["_source"]["version"],
        "Field": field
        } for result in results['hits']['hits']]


def generate_manual_train_set():
    """
    generates csv files for manual labeling of query quality
    :return:
    """
    query_settings = [
        ('match', 'hebmorph-standard'),
        ('match','hebmorph-exact'),
        ('match', 'original'),
        ('match', 'aggresive-ngram'),
        ('match_phrase', 'hebmorph-standard'),
        ('match_phrase', 'hebmorph-exact'),
        ('match_phrase', 'original'),
        ('match_phrase', 'aggresive-ngram'),
        ('multi_match', ['ngram', 'hebmorph-standard']),
        ('multi_match', ['infreq', 'hebmorph-standard'])
    ]

    max_size = 30

    test_query_list = test_en_query_list + test_he_query_list

    for i, q in enumerate(test_query_list):
        print "{}/{}".format(i, len(test_query_list))
        results_dict = defaultdict(list)
        for query_type, fields in query_settings:
            results = query(q, fields, query_type, max_size)
            field = fields if isinstance(fields, str) else fields[0]
            result_rows = query_result_to_csv_rows(results, field)
            for row in result_rows:
                results_dict[row['Ref']] += [row]


        html_doc = u'<html><head><link rel="stylesheet" type="text/css" href="noahstyle.css"></head><body><table>'
        f = open('training_files/{}.csv'.format(q),'wb')
        csv = unicodecsv.DictWriter(f, ['Score', 'Ref', 'Version', 'Lang', 'Content', 'Field'])
        csv.writeheader()

        for irow, (ref, dicts) in enumerate(results_dict.items()):
            best = sorted(dicts, key=lambda x: x['Score'])[-1]
            if irow == 0:
                html_doc += u"<tr><td>{}</td></tr>".format(u"</td><td>".join([unicode(k) for k in best.keys()]))
            html_doc += u"<tr><td>{}</td></tr>".format(u"</td><td>".join([unicode(v) for v in best.values()]))
            #best['Content'] = re.sub(ur'<.+?>', u'', best['Content'])
            csv.writerow(best)
        f.close()

        html_doc += u"</table></body></html>"
        h = codecs.open('html/{}.html'.format(q),'wb',encoding='utf8')
        h.write(html_doc)
        h.close()



def init_pagerank_graph():
    """

    :return: graph which is a double dict. the keys of both dicts are refs. the values are the number of incoming links
    between outer key and inner key
    """
    graph = OrderedDict()
    all_links = LinkSet().array()  # LinkSet({"type": re.compile(ur"(commentary|quotation)")}).array()
    all_ref_strs = set()
    for i, link in enumerate(all_links):
        if i % 1000 == 0:
            print "{}/{}".format(i,len(all_links))

        try:
            #TODO there's a known issue that a lot of refs don't have order_ids (in which case it's Z). This hopefully doesn't affect the graph too much
            refs = [Ref(r) for r in link.refs]
            older_ref, newer_ref = (refs[0], refs[1]) if refs[0].order_id() < refs[1].order_id() else (refs[1], refs[0])

            old_str = older_ref.normal()
            new_str = newer_ref.normal()
            all_ref_strs.add(old_str)
            all_ref_strs.add(new_str)
            if old_str not in graph:
                graph[old_str] = {}

            if new_str == old_str or (older_ref.is_tanach() and newer_ref.is_tanach()):
                # self link
                continue

            if new_str not in graph[older_ref.normal()]:
                graph[older_ref.normal()][new_str] = 0
            graph[older_ref.normal()][new_str] += 1
        except InputError:
            pass

    for ref in all_ref_strs:
        if ref not in graph:
            graph[ref] = {}

    return graph


def calculate_pagerank():
    graph = init_pagerank_graph()
    ranked = pageranklowram.pagerank(graph, 0.9999, verbose=True, tolerance=0.00005)
    f = open("pagerank.txt","wb")
    sorted_ranking = sorted(list(dict(ranked).items()), key=lambda x: x[1])
    json.dump(sorted_ranking,f,indent=4)
    f.close()


#index_all(merged=False, skip=0)
#yo = query('אמר',['ngram','ngram.hebmorph'],True)
#print yo



#{'a':{},'b':{'c':1,'a':1},'c':{'a':1},'d':{'a':1,'b':1,'c':1}}
#yo = pagerank.powerIteration({'a':{'b':1,'c':1,'d':1},'b':{'d':1},'c':{'b':1,'d':1},'d':{}},0.0001)
#print yo['a']
#print yo['b']

#init_pagerank_graph()
#calculate_pagerank()

"""
{
  "size": 200,
  "query": {
    "function_score": {
      "query": {
        "match_phrase": {
          "hebmorph-standard": "וידבר יהוה אל־משה לאמר"
        }
      },
      "field_value_factor": {
        "field": "pagerank"
      }
    }
  }
}
"""

generate_manual_train_set()