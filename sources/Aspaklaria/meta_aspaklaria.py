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
    print u"per {}".format(author)
    # caught
    caught = stats(author=author, caught=True)*100.0/stats(author=author)*1.0
    print "caught/all: {}%".format(caught)
    # caught without Shams
    caught_ns = stats(sham=False, author=author, caught=True)*100.0/stats(sham=False, author=author)*1.0
    print "ignore shams, caught/all: {}%".format(caught_ns)
    # shams = shams/all (per Author)
    shams = stats(sham=True, author=author, caught=None)*100.0/stats(author=author)*1.0
    print "shams/all: {}%".format(shams)
    # caught shams out of all shams
    all_shams = stats(author=author, sham=True)*1.0
    if all_shams:
        caught_shams = stats(sham=True, author=author, caught=True)*100.0/all_shams*1.0
        print "caught_shams/all_shams: {}%".format(caught_shams)

    return


if __name__ == "__main__":

    authors = list_authors()
    percentages()
    print '_________________________'
    for auth in authors:
        percentages(auth)

