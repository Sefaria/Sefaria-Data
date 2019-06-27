#encoding=utf-8

import django
django.setup()

from sefaria.model import *
from aspaklaria_connect import client
from sefaria.system.database import db
import math
import codecs
import unicodecsv as csv

db_aspaklaria = client.aspaklaria


def list_authors(letter=u""):
    authors = []
    documents = db_aspaklaria.aspaklaria_source.find({"topic": {'$regex': u"^{}".format(letter)}})
    for doc in documents:
        if not doc['author'] in authors:
            authors.append(doc['author'])
    return authors


def stats(sham=None, author=None, caught=None, letter = None):
    query = {}
    if author:
        query['author'] = u'{}'.format(author)
    if caught is not None:
        query['ref'] = {'$exists': caught}
    if sham is not None:
        query['is_sham']= sham
    if letter:
        query['topic'] = {'$regex': u"^{}".format(letter)}
    query_cnt = db_aspaklaria.aspaklaria_source.count_documents(query)
    return query_cnt


def round_stats(x,y):
    ans = x*100.0/y*1.0
    ans = math.floor(ans*100)/100
    return ans


def percentages(author=None, letter = None):
    perc_doc = {}
    print u"per {}".format(author) if author else u"for all"
    print u"abs number of refs {}".format(stats(author=author, letter=letter))
    perc_doc['author'] = author
    perc_doc['abs'] = stats(author=author, letter=letter)
    # caught
    caught = round_stats(stats(author=author, caught=True, letter=letter),stats(author=author, letter=letter))
    print "caught/all: {}%".format(caught)
    perc_doc['caught/all'] = caught
    # caught without Shams
    if stats(sham=False, author=author, letter=letter):
        caught_ns = round_stats(stats(sham=False, author=author, caught=True, letter=letter),stats(sham=False, author=author, letter=letter))
        print "ignore shams, caught/all: {}%".format(caught_ns)
        perc_doc['ignore shams, caught/all'] = caught_ns
    else:
        caught_ns = 1.0
        print "all the refs are Shams"
        perc_doc['ignore shams, caught/all'] = 0.0
    # shams = shams/all (per Author)
    shams = round_stats(stats(sham=True, author=author, caught=None, letter=letter),stats(author=author, letter=letter))
    print "shams/all: {}%".format(shams)
    perc_doc['shams/all'] = shams
    # caught shams out of all shams
    all_shams = stats(author=author, sham=True, letter=letter)*1.0
    if all_shams:
        caught_shams = round_stats(stats(sham=True, author=author, caught=True, letter=letter),all_shams)
        print "caught_shams/all_shams: {}%".format(caught_shams)
        perc_doc['caught_shams/all_shams'] = caught_shams
    else:
        caught_shams = 0.0
    query_no_ref = { "author": u"{}".format(author), "ref": { "$exists": False}, "is_sham": False}
    curser = db_aspaklaria.aspaklaria_source.find(query_no_ref)
    for doc in curser:
        perc_doc['ex nr topic'] = doc['topic']
        perc_doc['ex nr raw_ref'] = doc['raw_ref']
        if 'index_guess' in doc.keys():
            perc_doc['ex nr index_guess'] = doc['index_guess']
        break
    query_ref = { "author": u"{}".format(author), "ref": { "$exists": True }, "is_sham": False}
    curser = db_aspaklaria.aspaklaria_source.find(query_ref)
    for doc in curser:
        perc_doc['ex topic'] = doc['topic']
        perc_doc['ex raw_ref'] = doc['raw_ref']
        perc_doc['ex ref'] = doc['ref']
        if 'index_guess' in doc.keys():
            perc_doc['ex index_guess'] = doc['index_guess']
        break
    return perc_doc #[caught, caught_ns, shams, caught_shams, ]


if __name__ == "__main__":
    #
    rows = []
    letter = u''
    authors = list_authors(letter=letter)
    percentages(letter=letter)

    print '_________________________'
    empty_authors = []
    for auth in authors:
        perc = percentages(auth, letter = letter)
        rows.append(perc)
        if not perc['caught/all']:
            empty_authors.append(auth)
            rows.append({'author': auth})
    for auth in empty_authors:
        print auth
    with codecs.open(u'aspaklariaStats_{}.csv'.format(2), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, ['author', 'abs', 'caught/all', 'ignore shams, caught/all', 'shams/all', 'caught_shams/all_shams', 'ex nr topic', 'ex nr raw_ref', 'ex nr index_guess','ex topic', 'ex raw_ref', 'ex ref', 'ex index_guess'])
        writer.writeheader()
        writer.writerows(rows)