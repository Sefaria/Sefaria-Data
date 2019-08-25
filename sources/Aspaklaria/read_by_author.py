#encoding=utf-8

import django
django.setup()

from parse_aspaklaria import *
from aspaklaria_connect import client
import unicodecsv as csv
import codecs


db_aspaklaria = client.aspaklaria


def read_csv(filename):
    """
    reads topic names from csv and returns them as a list (in order)
    :param filename: csv file to read topic names from
    :return:rows with a topic column and types columns
    """
    rows = []
    with open(filename) as csvfile:
        file_reader = csv.DictReader(csvfile)
        for row in file_reader:
            rows.append(row)
    return rows

def add_sources(rows):
    for row in rows:
        refs_curser = db_aspaklaria.aspaklaria_source.find({"author": u"תנך", "topic": u"{}".format(row['topic'])})
        refs = []
        for ref in refs_curser:
            if not refs_curser:
                continue
            if u'ref' in ref.keys():
                print u"topic: {}, refs: {}".format(row['topic'], ref['ref'])
                refs.append(ref['ref'])
        hertzog_row = row
        hertzog_row['refs'] = refs
        db_aspaklaria.hertzog.insert_one(hertzog_row)

if __name__ == "__main__":
    add_sources(read_csv(u'tanakh_ppl_for_hertzog.csv'))
