# encoding=utf-8

import os
import argparse
import requests
import unicodecsv
from sources import functions
from sefaria.model import *
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


def shulchan_arukh_index(server='http://localhost:8000', *args, **kwargs):
    original_index = functions.get_index_api(u"Shulchan Arukh, Yoreh De'ah", server=server)
    alt_struct = get_alt_struct(u"Shulchan Arukh, Yorhe De'ah")
    if 'alt_structs' not in original_index:
        original_index['alt_structs'] = {}
    original_index['alt_structs']['Topic'] = alt_struct
    return original_index


def add_siman_headers(ja):
    xml_simanim = root.get_base_text().get_simanim()
    text_simanim = iter(ja)
    for xml_siman in xml_simanim:
        text_siman = text_simanim.next()
        for title in xml_siman.Tag.find_all('title'):
            title_text = re.sub(u'\s*$', u'', title.text)
            if title_text == u'':
                continue
            if re.search(u'@', title_text) is not None:
                print u"Weird mark at Siman {}".format(xml_siman.num)
            seif_index = int(title['found_after'])
            text_siman[seif_index] = u'<b>{}</b><br>{}'.format(title_text, text_siman[seif_index])


def generic_cleaner(ja, clean_callback):
    assert isinstance(ja, list)
    for i, item in enumerate(ja):
        if isinstance(item, list):
            generic_cleaner(item, clean_callback)
        elif isinstance(item, basestring):
            ja[i] = clean_callback(item)
        else:
            raise TypeError
