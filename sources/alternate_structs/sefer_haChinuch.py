# encoding=utf-8

import csv
import codecs
import urllib2
from urllib2 import HTTPError, URLError
from sefaria.model import *
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


