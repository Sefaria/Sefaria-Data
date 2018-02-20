# coding=utf-8

"""
Even HaEzer needs to be complex, due to the Get and Halitzah sections.
These sections will have the titles <book name>, Seder HaGet/Halitzah
Taz seems not to have Seder Halitzah
Even HaEzer needs to be made complex on prod.
"""

import argparse
import unicodecsv
from sefaria.model import *
from sources import functions

def get_schema(en_title, he_title):
    root_node = SchemaNode()
    root_node.add_primary_titles(en_title, he_title)

    default_node = JaggedArrayNode()
    default_node.default = True
    default_node.key = 'default'
    default_node.add_structure(["Siman", "Seif"])
    root_node.append(default_node)

    get_node = JaggedArrayNode()
    get_node.add_primary_titles("Seder HaGet", u"סדר הגט")
    get_node.add_structure(["Seif"])
    root_node.append(get_node)

    if en_title != u"Turei Zahav":  # Taz does not have commentary on Seder Halitzah
        halitzah_node = JaggedArrayNode()
        halitzah_node.add_primary_titles("Seder Halitzah", u"סדר חליצה")
        halitzah_node.add_structure(["Seif"])
        root_node.append(halitzah_node)
    root_node.validate()
    return root_node.serialize()


def get_alt_struct(book_title):
    with open('Even_HaEzer_Topics.csv') as infile:
        reader = unicodecsv.DictReader(infile)
        rows = [row for row in reader]

    s_node = SchemaNode()
    s_node.add_primary_titles('Topic', u'נושא', key_as_title=False)
    for row in rows:
        node = ArrayMapNode()
        node.add_primary_titles(row['en'], row['he'])
        node.depth = 0
        node.includeSections = True
        start, end = row['start'], row['end']
        if start == end:
            node.wholeRef = u'{} {}'.format(book_title, start)
        else:
            node.wholeRef = u'{} {}-{}'.format(book_title, start, end)
        node.validate()
        s_node.append(node)
    return s_node.serialize()


def shulchan_arukh_index(server='http://localhost:8000', *args, **kwargs):
    original_index = functions.get_index_api("Shulchan Arukh, Even HaEzer", server=server)
    original_index['alt_structs'] = {'Topic': get_alt_struct("Shulchan Arukh, Even HaEzer")}
    return original_index


def commentary_index(en_title, he_title, commentator):
    return {
        "title": en_title,
        "categories": ["Halakhah", "Shulchan Arukh", "Commentary", commentator],
        "dependence": "Commentary",
        "collective_title": commentator,
        "alt_structs": {"Topic": get_alt_struct(en_title)},
        "schema": get_schema(en_title, he_title),
        "base_text_titles": ["Shulchan Arukh, Even HaEzer"]
    }


def generic_cleaner(ja, clean_callback):
    for i, siman in enumerate(ja):
        for j, seif in enumerate(siman):
            ja[i][j] = clean_callback(seif)



