# coding=utf-8

"""
Even HaEzer needs to be complex, due to the Get and Halitzah sections.
These sections will have the titles <book name>, Seder HaGet/Halitzah
Taz seems not to have Seder Halitzah
Even HaEzer needs to be made complex on prod.
"""

import os
import argparse
import requests
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
    title_suffix = u" on Shulchan Arukh, Even HaEzer"

    if en_title == u"Turei Zahav{}".format(title_suffix) or en_title == u"Pithei Teshuva{}".format(title_suffix):
        name_node = JaggedArrayNode()
        name_node.add_primary_titles(u"Shemot Anashim V'Nashim", u"שמות אנשים ונשים")
        name_node.add_structure(["Seif"])
        root_node.append(name_node)

    get_node = JaggedArrayNode()
    get_node.add_primary_titles("Seder HaGet", u"סדר הגט")
    get_node.add_structure(["Seif"])
    root_node.append(get_node)

    if en_title != u"Turei Zahav{}".format(title_suffix):  # Taz does not have commentary on Seder Halitzah
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
    links = []

    """
    Instead of getting a book ja, we'll get a dict mapping nodes to jagged arrays. We'll then feed each ja through the
    uploader. 
    """

    if user_args.title is None:
        book_name, he_book_name = base_text_title, he_base_title
        book_data = {
            base_text_title: root.get_base_text().render(),
            u'{}, {}'.format(base_text_title, u'Seder HaGet'):
                commentaries.get_commentary_by_title('Seder HaGet').render(),
            u'{}, {}'.format(base_text_title, u'Seder Halitzah'):
                commentaries.get_commentary_by_title('Seder Halitzah').render(),
        }
        book_index = shulchan_arukh_index(user_args.server)

    else:
        book_xml = commentaries.get_commentary_by_title(user_args.title)
        book_name = u'{} on {}'.format(user_args.title, base_text_title)
        he_book_name = u'{} על {}'.format(book_xml.titles['he'], he_base_title)
        book_data = {}
        book_parts = [i for i in commentaries.commentary_ids.keys() if re.search(u'{}.*'.format(user_args.title), i)]
        for part in book_parts:
            part_xml = commentaries.get_commentary_by_title(part)
            part_name = part.replace(user_args.title, u'{} on {}'.format(user_args.title, base_text_title))
            book_data[part_name] = part_xml.render()
            links += part_xml.collect_links()
        book_index = commentary_index(book_name, he_book_name, user_args.title)

        if user_args.add_term:
            functions.add_term(user_args.title, book_xml.titles['he'], server=user_args.server)

        functions.add_category(user_args.title, book_index['categories'], server=user_args.server)

    if user_args.verbose:
        print book_index
    functions.post_index(book_index, server=user_args.server)
    version = {
        "versionTitle": "Something Something Lemberg Something",
        "versionSource": "fie fi fo fum",
        "language": "he",
        "text": None
    }
    num_parts = len(book_data.items())
    for part_name, part_ja in book_data.items():
        if len(part_ja) == 1:
            version["text"] = part_ja[0]
        else:
            version["text"] = part_ja
        if num_parts == 1:    # We'll build the versionState at the last post
            print "building versionState"
            functions.post_text(part_name, version, index_count="on", server=user_args.server)
        else:
            print "not building versionState"
            functions.post_text(part_name, version, server=user_args.server)
        num_parts -= 1
    if links:
        functions.post_link(links, server=user_args.server)
    functions.post_flags({'ref': book_name, 'lang': 'he', 'vtitle': version['versionTitle']},
                         {'versionTitleInHebrew': u"""פי פיי פו פאם"""}, user_args.server)

    try:
        requests.post(os.environ['SLACK_URL'], json={'text': '{} uploaded successfully'.format(book_name)})
    except KeyError:
        pass


