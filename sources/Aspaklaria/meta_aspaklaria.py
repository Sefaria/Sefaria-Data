#encoding=utf-8

import django
django.setup()

from aspaklaria_connect import client


db = client.aspaklaria


def list_authors():
    authors = []
    documents = db.aspaklaria_source.find({})
    for doc in documents:
        if not doc['author'] in authors:
            authors.append(doc['author'])
    return authors


def stats(sham=None, author=None, caught=None):
    query = {}
    if author:
        query['author'] = u'{}'.format(author)
    if caught is not None:
        query['ref'] = {'$exists': caught}
    if sham is not None:
        query['is_sham']= sham
    query_cnt = db.aspaklaria_source.count_documents(query)
    return query_cnt


def percentages(author=None):
    print u"per {}".format(author) if author else u"for all"
    # caught
    caught = stats(author=author, caught=True)*100.0/stats(author=author)*1.0
    print "caught/all: {}%".format(caught)
    # caught without Shams
    if stats(sham=False, author=author):
        caught_ns = stats(sham=False, author=author, caught=True)*100.0/stats(sham=False, author=author)*1.0
        print "ignore shams, caught/all: {}%".format(caught_ns)
    else:
        caught_ns = 1.0
        print "all the refs are Shams"
    # shams = shams/all (per Author)
    shams = stats(sham=True, author=author, caught=None)*100.0/stats(author=author)*1.0
    print "shams/all: {}%".format(shams)
    # caught shams out of all shams
    all_shams = stats(author=author, sham=True)*1.0
    if all_shams:
        caught_shams = stats(sham=True, author=author, caught=True)*100.0/all_shams*1.0
        print "caught_shams/all_shams: {}%".format(caught_shams)
    else:
        caught_shams= 0.0

    return [caught, caught_ns, shams, caught_shams]


if __name__ == "__main__":

    authors = list_authors()
    percentages()
    print '_________________________'
    empty_authors = []
    for auth in authors:
        perc = percentages(auth)
        if not perc[0]:
            empty_authors.append(auth)
    for auth in empty_authors:
        print auth
