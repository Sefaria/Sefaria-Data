import django

django.setup()

django.setup()
superuser_id = 171118
import csv
from sefaria.model import *
from sefaria.system.database import db
from sefaria.model.schema import AddressTalmud
import time
from datetime import datetime, timezone
from sefaria.system.database import db
from sources.functions import post_index




if __name__ == '__main__':
    print("hello world")
    # index = library.get_index("Jerusalem Talmud Niddah")
    index = post_index({"title": "Jerusalem Talmud Niddah"}, method='GET', server='https://www.sefaria.org')
    vilna = index['alt_structs']['Vilna']

    new_chpater = {'nodeType': 'ArrayMapNode', 'depth': 1,
                   'wholeRef': 'Jerusalem Talmud Niddah 4:1:1-7:1', 'addressTypes': ['Talmud'], 'sectionNames': ['Daf'],
                   'refs': ['Jerusalem Talmud Niddah 4:1:1-6:1', 'Jerusalem Talmud Niddah 4:6:1-7:1'],
                   'startingAddress': '12b', 'match_templates': [],
                   'titles': [{'text': 'Chapter 4', 'lang': 'en', 'primary': True}, {'text': 'בנות כותים', 'lang': 'he', 'primary': True}]}
    vilna['nodes'].append(new_chpater)

    post_index(index, server='https://www.sefaria.org')

    print(vilna)










