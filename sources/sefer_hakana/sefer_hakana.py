# encoding=utf-8

import urllib2
import re
import bleach
import codecs
from sources.functions import post_text, post_index
from sefaria.model.schema import JaggedArrayNode, TitledTreeNode, ArrayMapNode


def get_text(from_url=False):
    if from_url:
        url = 'http://www.hebrew.grimoar.cz/anonym/sefer_ha-kana.htm'
        response = urllib2.urlopen(url)
        return response.read()
    else:
        with open('sefer_ha-kana.htm') as infile:
            return infile.read()


def parse():
    my_text = codecs.decode(get_text(), 'windows-1255').splitlines()
    root, chapter, titles = [], [], []
    found_beginning = False
    for line in my_text:

        if re.search(u'^ ?<b>', line):
            if found_beginning:
                root.append([u'{}.'.format(i) if not re.search(u':(>)?$', i) else i for i in chapter])
                chapter = []
            else:
                found_beginning = True
            chapter.append(bleach.clean(line, tags=['b'], strip=True))
            titles.append(bleach.clean(line, tags=[], strip=True))

        elif found_beginning:
            my_line = bleach.clean(line, tags=[], strip=True)
            if my_line.isspace() or len(my_line) == 0:
                continue
            my_line = re.sub(u'(\n|\r)', u'', my_line)
            chapter.extend(filter(lambda x: x if len(x) > 0 else None, my_line.split(u'.')))

        else:
            continue
    else:
        root.append(chapter)  # don't forget to add last chapter
    assert (len(root) == len(titles))
    return {
        'text': root,
        'titles': titles
    }


def build_index(titles):

    struct_node = JaggedArrayNode()
    struct_node.add_title('Sefer HaKana', 'en', primary=True)
    struct_node.add_title(u'ספר הקנה', 'he', primary=True)
    struct_node.key = 'Sefer HaKana'
    struct_node.depth = 2
    struct_node.addressTypes = ['Integer', 'Integer']
    struct_node.sectionNames = ['Chapter', 'Comment']
    struct_node.add_title('Sefer HaQana', 'en')
    struct_node.add_title('Sefer HaQanah', 'en')
    struct_node.add_title('Sefer Hakana', 'en')
    struct_node.add_title('Sefer HaKanah', 'en')
    struct_node.validate()

    alt_struct = TitledTreeNode()
    for index, title in enumerate(titles):
        i = index + 1
        node = ArrayMapNode()
        node.add_title('Chapter {}'.format(i), 'en', primary=True)
        node.add_title(title.replace(u'ד"ה ', u''), 'he', primary=True)
        node.depth = 0
        node.wholeRef = 'Sefer HaKana {}'.format(i)
        alt_struct.append(node)

    return {
        'title': 'Sefer HaKana',
        'categories': ['Kabbalah'],
        'schema': struct_node.serialize(),
        'alt_structs': {'Titles': alt_struct.serialize()}
    }


def post():
    parsed = parse()
    post_index(build_index(parsed['titles']))
    version = {
        'versionTitle': 'Sefer HaKana',
        'versionSource': 'http://www.hebrew.grimoar.cz/anonym/sefer_ha-kana.htm',
        'language': 'he',
        'text': parsed['text']
    }
    post_text('Sefer HaKana', version, index_count='on')
