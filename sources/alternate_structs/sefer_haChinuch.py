# encoding=utf-8

import csv
import codecs
import json
import urllib
import urllib2
from urllib2 import HTTPError
from sources.local_settings import *


def get_data(filename):

    with codecs.open(filename, 'r', 'utf-8') as data_file:

        data = []
        data_reader = csv.reader(data_file, delimiter=',')

        for row in data_reader:

            data.append({
                'Parsha': row[0],
                'ref': row[1]
            })

    return data


def construct_alt_struct(data_file):

    struct = {'nodes': []}

    for title in get_data(data_file):

        node = {
            'depth': 0,
            'sharedTitle': title['Parsha'],
            'nodeType': 'ArrayMapNode',
            'wholeRef': 'Sefer HaChinukh.{}'.format(title['ref']),
            'includeSections': True
        }

        struct['nodes'].append(node)

    return struct


def post_index(index):
    url = SEFARIA_SERVER+'/api/v2/raw/index/Sefer_HaChinukh'
    indexJSON = json.dumps(index)
    values = {
        'json': indexJSON,
        'apikey': API_KEY
    }
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        print response.read()
    except HTTPError as e:
        print "error"

s = construct_alt_struct('Chinuch_by_Parsha.csv')
data = {
        'Parsha': s
}

raw = urllib2.urlopen('http://www.sefaria.org/api/v2/raw/index/Sefer_HaChinukh')
index = json.load(raw)
index['alt_structs'] = data

post_index(index)
