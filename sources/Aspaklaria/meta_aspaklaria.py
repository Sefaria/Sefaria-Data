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


def prct_shams():
    return


def prct_caught_refs():
    return


if __name__ == "__main__":

    authors = list_authors()

    print len(authors)
    for auth in authors:
        print auth

