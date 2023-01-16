# encoding=utf-8

import re
import codecs
from sources.functions import post_text, post_index, post_link
from sefaria.model.schema import JaggedArrayNode, SchemaNode
from parsing_utilities.util import file_to_ja, multiple_replace, traverse_ja


def parse_yitzira():

    def cleaner(my_text):
        return filter(None,
                      [re.sub(u'@[0-9]{2}', u'', line) if re.search(u'@11', line) else None for line in my_text])

    with codecs.open('yitzira_mishna.txt', 'r', 'utf-8') as infile:
        return file_to_ja(2, infile, [u'@00\u05e4\u05e8\u05e7 [\u05d0-\u05ea]{1,2}'], cleaner).array()


def parse_general(filename):

    def cleaner(my_text):
        result = []
        for line in my_text:
            new_line = multiple_replace(line, {u'@31': u'<b>', u'@32': u'</b>'})
            new_line = re.sub(u'@[0-9]{2}', u'', new_line)
            result.append(new_line)
        return result

    regs = [u'@00\u05e4\u05e8\u05e7 [\u05d0-\u05ea]{1,2}', u'@22[\u05d0-\u05ea]{1,2}']
    with codecs.open(filename, 'r', 'utf-8') as infile:
        return file_to_ja(3, infile, regs, cleaner).array()


def post_yitzira():
    node = JaggedArrayNode()
    node.add_title('Sefer Yetzirah', 'en', primary=True)
    node.add_title(u'ספר יצירה', 'he', primary=True)
    node.key = 'Sefer Yetzirah'
    node.depth = 2
    node.addressTypes = ['Integer', 'Integer']
    node.sectionNames = ['Chapter', 'Mishnah']
    node.validate()

    y_index = {
        'title': 'Sefer Yetzirah',
        'categories': ['Kabbalah'],
        'language': 'he',
        'schema': node.serialize()
    }

    y_version = {
        'versionTitle': 'Sefer Yetzirah, Warsaw 1884',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001310968',
        'language': 'he',
        'text': parse_yitzira()
    }
    post_index(y_index)
    post_text("Sefer Yetzirah", y_version, index_count='on')


def linker(parsed_commentary, commentator_name):
    """
    Build up a list of links for a text where the commentator follows the base text exactly
    :param parsed_commentary: parsed text to link
    :param commentator_name: Name commentator as appears on the JaggedArrayNode to be linked
    :return: list of links
    """

    links = []
    for comment in traverse_ja(parsed_commentary):
        indices = [i + 1 for i in comment['indices']]
        links.append({
            'refs': ['Sefer Yetzirah {}:{}'.format(*indices[:-1]),
                     '{} {}:{}:{}'.format(commentator_name, *indices)],
            'type': 'commentary',
            'auto': True,
            'generated_by': 'Sefer Yetzirah Parse Script'
        })

    return links


def post_simple_commentaries():
    ramban_node, rasag_node = JaggedArrayNode(), JaggedArrayNode()
    ramban_text = parse_general('yitzira_ramban.txt')
    rasag_text = parse_general('yitzira_rasag.txt')

    ramban_node.add_title("Ramban on Sefer Yetzirah", 'en', primary=True)
    ramban_node.add_title(u'רמב"ן על ספר יצירה', 'he', primary=True)
    ramban_node.key = "Ramban on Sefer Yetzirah"
    ramban_node.addressTypes = ['Integer', 'Integer', 'Integer']
    ramban_node.sectionNames = ["Chapter", "Mishnah", "Comment"]
    ramban_node.toc_zoom = 2
    ramban_node.depth = 3
    ramban_node.validate()

    rasag_node.add_title("Rasag on Sefer Yetzirah", 'en', primary=True)
    rasag_node.add_title(u'רס"ג על ספר יצירה', 'he', primary=True)
    rasag_node.key = "Rasag on Sefer Yetzirah"
    rasag_node.addressTypes = ['Integer', 'Integer', 'Integer']
    rasag_node.sectionNames = ["Chapter", "Mishnah", "Comment"]
    rasag_node.toc_zoom = 2
    rasag_node.depth = 3
    rasag_node.validate()

    ramban_index = {
        "title": "Ramban on Sefer Yetzirah",
        "categories": ["Commentary2", "Kabbalah", "Ramban"],
        "language": "he",
        "schema": ramban_node.serialize()
    }
    post_index(ramban_index)
    post_text("Ramban on Sefer Yetzirah", {
        'versionTitle': 'Ramban on Sefer Yetzirah, Warsaw 1884',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001310968',
        'language': 'he',
        'text': ramban_text
    })

    rasag_index = {
        "title": "Rasag on Sefer Yetzirah",
        "categories": ["Commentary2", "Kabbalah", "Rasag"],
        "language": "he",
        "schema": rasag_node.serialize()
    }
    post_index(rasag_index)
    post_text("Rasag on Sefer Yetzirah", {
        'versionTitle': 'Rasage on Sefer Yetzirah, Warsaw 1884',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001310968',
        'language': 'he',
        'text': rasag_text
    })
    links = linker(ramban_text, "Ramban on Sefer Yetzirah")
    links.extend(linker(rasag_text, "Rasag on Sefer Yetzirah"))
    post_link(links)
