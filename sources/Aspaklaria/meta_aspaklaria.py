#encoding=utf-8

import django
django.setup()

from sefaria.model import *
from aspaklaria_connect import client
from sefaria.system.database import db


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


def percentages(author=None, letter = None):
    print u"per {}".format(author) if author else u"for all"
    print u"abs number of refs {}".format(stats(author=author, letter=letter))
    # caught
    caught = stats(author=author, caught=True, letter=letter)*100.0/stats(author=author, letter=letter)*1.0
    print "caught/all: {}%".format(caught)
    # caught without Shams
    if stats(sham=False, author=author, letter=letter):
        caught_ns = stats(sham=False, author=author, caught=True, letter=letter)*100.0/stats(sham=False, author=author, letter=letter)*1.0
        print "ignore shams, caught/all: {}%".format(caught_ns)
    else:
        caught_ns = 1.0
        print "all the refs are Shams"
    # shams = shams/all (per Author)
    shams = stats(sham=True, author=author, caught=None, letter=letter)*100.0/stats(author=author, letter=letter)*1.0
    print "shams/all: {}%".format(shams)
    # caught shams out of all shams
    all_shams = stats(author=author, sham=True, letter=letter)*1.0
    if all_shams:
        caught_shams = stats(sham=True, author=author, caught=True, letter=letter)*100.0/all_shams*1.0
        print "caught_shams/all_shams: {}%".format(caught_shams)
    else:
        caught_shams= 0.0

    return [caught, caught_ns, shams, caught_shams]


if __name__ == "__main__":
    #
    letter = u'פ'
    authors = list_authors(letter=letter)
    percentages(letter=letter)

    print '_________________________'
    empty_authors = []
    for auth in authors:
        perc = percentages(auth, letter = letter)
        if not perc[0]:
            empty_authors.append(auth)
    for auth in empty_authors:
        print auth
