# encoding=utf-8

import re
import urllib2
import codecs
from sefaria.datatype.jagged_array import JaggedArray
from bs4 import BeautifulSoup
from data_utilities.util import getGematria, ja_to_xml, traverse_ja
from sources import functions
from sefaria.model import *


url = 'https://he.wikisource.org/wiki/' \
      '%D7%AA%D7%A8%D7%92%D7%95%D7%9D_%D7%93%D7%91%D7%A8%D7%99_%D7%94%D7%99%D7%9E%D7%99%D7%9D'


def get_html(page_url):
    return urllib2.urlopen(page_url).read()


def get_content(page_url):
    soup = BeautifulSoup(get_html(page_url), 'html.parser')
    body = soup.body
    return body.find('div', id="mw-content-text")


def to_file(page_url):
    content = get_content(page_url)
    with codecs.open('targum(2).txt', 'w', 'utf-8') as outfile:
        for thing in content.strings:
            outfile.write(thing)


def ref_reg():
    return re.compile(u'^([\u05d0-\u05d1]) ([\u05d0-\u05ea]{1,2}):([\u05d0-\u05ea]{1,3})$')


def ref_to_indices(he_ref):

    match = ref_reg().search(he_ref)
    assert match is not None

    return [getGematria(match.group(i)) - 1 for i in range(1, 4)]


def parse(filename):
    with codecs.open(filename, 'r', 'utf-8') as infile:
        lines = infile.readlines()

    targum_ja = JaggedArray([[[]]])
    indices = None

    for line_num, line in enumerate(lines):

        if (line_num + 1) % 2 == 1:
            indices = ref_to_indices(line)
        else:
            text_value = u' '.join(line.split(u' ')[1:])
            targum_ja.set_element(indices, text_value)
    return targum_ja.array()


def sanity_check(i, ja):
    """
    :param i: 1 for chronicles 1, 2 for chronicles 2
    :param ja
    :return:
    """

    ref = Ref('{} Chronicles'.format(i))
    book = ja[i-1]
    chapters = ref.all_subrefs()

    if len(chapters) == len(book):
        print 'correct number of chapters'
    else:
        print 'missing chapter'

    for verse, translation in zip(chapters, book):

        if len(verse.all_subrefs()) == len(translation):
            continue
        else:
            print 'problem'


def build_index(i):

    assert i == 1 or i == 2
    if i == 1:
        he = u'א'
    else:
        he = u'ב'
    i = 'I' * i

    t_schema = JaggedArrayNode()
    t_schema.add_title('Aramaic Targum to {} Chronicles'.format(i), 'en', primary=True)
    t_schema.add_title(u'תרגום דברי הימים {}'.format(he), 'he', primary=True)
    t_schema.key = 'Aramaic Targum to {} Chronicles'.format(i)
    t_schema.addressTypes = ['Integer', 'Integer']
    t_schema.sectionNames = ['Chapter', 'Verse']
    t_schema.depth = 2
    t_schema.validate()

    return {
        'title': 'Aramaic Targum to {} Chronicles'.format(i),
        'categories': ['Tanakh', 'Targum'],
        'schema': t_schema.serialize()
    }


def build_links(parsed):

    bases = []
    for book_num, book in enumerate(parsed):
        for line in traverse_ja(book):
            bases.append('{} Chronicles {}:{}'.format('I'*(book_num+1), *[i+1 for i in line['indices']]))

    links = [{
        'refs': [base, 'Aramaic Targum to {}'.format(base)],
        'type': 'commentary2',
        'auto': False,
        'generated_by': 'Chronicles parse script'
    }for base in bases]

    return links


def post():
    parsed = parse('targum.txt')
    for i in range(1, 3):
        functions.post_index(build_index(i))
        version = {
            'versionTitle': 'Wikisource Aramaic Targum to Chronicles',
            'versionSource': url,
            'language': 'he',
            'text': parsed[i-1]
        }
        functions.post_text('Aramaic Targum to {} Chronicles'.format('I' * i), version)
    functions.post_link(build_links(parsed))

post()
