# coding=utf-8

import re
import json
from sefaria.model import JaggedArrayNode
from data_utilities.util import getGematria
from sefaria.datatype.jagged_array import JaggedArray
from sources.functions import post_index, post_link, post_text


def construct_index():
    node = JaggedArrayNode()
    node.default = True
    node.key = 'default'
    node.add_structure(["Chapter", "Mishnah", "Paragraph"])
    node.validate()

    with open('original_index.json') as infile:
        index = json.load(infile)
    index['schema']['nodes'][1] = node.serialize()
    return index


def restructure_text():
    with open('Derech Chaim text.json') as infile:
        version = json.load(infile)
    my_text = version['text'][u'']

    pattern = re.compile(u'^\u05de\u05e9\u05e0\u05d4 ([\u05d0-\u05ea]{1,2})$')
    parsed = JaggedArray([[[]]])
    for chap_index, chapter in enumerate(my_text):
        current_mishnah, current_comment = 0, 0

        for line in chapter:
            match  = pattern.search(line)
            if match is None:  # This is a regular comment
                parsed.set_element([chap_index, current_mishnah, current_comment], line, pad=[])
                current_comment += 1
            else:
                m_value = getGematria(match.group(1)) - 1
                if m_value > current_mishnah:  # This condition allows for intro text to appear before first mishnah mark
                    current_mishnah = m_value
                    current_comment = 0
    return parsed.array()


def build_links(text_array):
    links = []
    for chap_index, chapter in enumerate(text_array):
        for m_index, mishnah in enumerate(chapter):
            if len(mishnah) == 0:
                continue
            avot_ref = u'Pirkei Avot {}:{}'.format(chap_index+1, m_index+1)
            derch_ref = u'Derech Chaim {}:{}:1-{}'.format(chap_index+1, m_index+1, len(mishnah))
            links.append({
                'refs': [avot_ref, derch_ref],
                'type': 'commentary',
                'auto': True,
                'generated_by': 'Derech Chaim Refactor'
            })
    return links


def get_intro():
    with open('Derech Chaim text.json') as infile:
        version = json.load(infile)
    return version['text']["Author's Introduction"]


def post():
    post_index(construct_index())
    base_text = restructure_text()
    links = build_links(base_text)
    version = {
        'versionTitle': u'Derech Chaim, Maharal',
        'versionSource': u'http://mobile.tora.ws/',
        'language': 'he',
        'text': base_text
    }
    post_text("Derech Chaim", version)
    version['text'] = get_intro()
    post_text("Derech Chaim, Author's Introduction", version, index_count='on')
    post_link(links)

