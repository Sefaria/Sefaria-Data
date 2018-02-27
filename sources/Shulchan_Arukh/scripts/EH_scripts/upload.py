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
from sources.Shulchan_Arukh.ShulchanArukh import *

def get_schema(en_title, he_title):
    root_node = SchemaNode()
    root_node.add_primary_titles(en_title, he_title)

    default_node = JaggedArrayNode()
    default_node.default = True
    default_node.key = 'default'
    default_node.add_structure(["Siman", "Seif"])
    root_node.append(default_node)

    if en_title == u"Turei Zahav" or en_title == u"Pithei Teshuva":
        name_node = JaggedArrayNode()
        name_node.add_primary_titles(u"Shemot Anashim V'Nashim", u"שמות אנשים ונשים")
        name_node.add_structure(["Seif"])
        root_node.append(name_node)

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--title", default=None)
    parser.add_argument("-s", "--server", default="http://localhost:8000")
    parser.add_argument("-v", "--verbose", action='store_true', default=False)
    parser.add_argument("-a", "--add_term", action='store_true', default=False)
    user_args = parser.parse_args()

    root = Root('../../Even_HaEzer.xml')
    commentaries = root.get_commentaries()
    root.populate_comment_store()

    base_text_title = u"Shulchan Arukh, Even HaEzer"
    he_base_title = u"שולחן ערוך אבן העזר"

    """
    Instead of getting a book ja, we'll get a dict mapping nodes to jagged arrays. We'll then feed each ja through the
    uploader. 
    """

    # if base text:
        # {'book_name', 'he_book_name',
        # <book_name>: root.get_base_text().render(),
        # <Seder HaGet>: commentaries.get_commentary_by_title("Seder HaGet")
        # ...<Seder Halitzah>: ...
    #     }
    if user_args.title is None:
        book_data = {
            'book_name': base_text_title,
            'he_book_name': he_base_title,
            base_text_title: root.get_base_text().render(),
            u'{}, {}'.format(base_text_title, u'Seder HaGet'):
                commentaries.get_commentary_by_title('Seder HaGet').render(),
            u'{}, {}'.format(base_text_title, u'Seder Halitzah'):
                commentaries.get_commentary_by_title('Seder Halitzah').render(),
        }

    else:
        book_data = {
            'book_name': u'{} on {}'.format(user_args.title, base_text_title)
        }

# else:
    # {
    #   'book_name', 'he_book_name',
    #    <get_relevant_xmls>,
    #    <render them>
    # }
