# encoding=utf-8

import os
import argparse
import requests
import unicodecsv
from sefaria.model import *
from sources import functions
from os.path import dirname as loc
from sources.Shulchan_Arukh.ShulchanArukh import *

root_dir = loc(loc(loc(os.path.abspath(__file__))))
xml_loc = os.path.join(root_dir, 'Yoreh_Deah.xml')
root = Root(xml_loc)


def get_alt_struct(book_title):
    base_text = root.get_base_text()
    with open('Shulchan_Arukh_YD_titles.csv') as fp:
        reader = unicodecsv.DictReader(fp)
        rows = [row for row in reader]
    assert len(rows) == len(base_text.Tag.find_all('topic'))

    root_node = SchemaNode()
    root_node.add_primary_titles('Topic', u'נושא', key_as_title=False)
    for row in rows:
        node = ArrayMapNode()
        node.add_primary_titles(row['en'], row['he'])
        node.wholeRef = re.sub(u"Shulchan Arukh, Yoreh De'ah", book_title, row['reference'])
        node.includeSections = True
        root_node.append(node)
    return root_node.serialize()
