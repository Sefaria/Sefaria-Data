# encoding=utf-8

"""
expression to grab every "spring": u'<b>\u05d4?\u05de\u05e2\u05d9\u05d9?\u05df.*:</b>'
this seems to grab the "rivers": u'\u05de\u05e2\u05d9\u05df ([\u05d0-\u05ea]{1,2}) - \u05e0\u05d4\u05e8 (- )?([\u05d0-\u05ea]{1,2})'
"""
import re
import bleach
import codecs
import urllib2
from bs4 import BeautifulSoup
from sources.functions import post_index, post_text
from sefaria.datatype.jagged_array import JaggedArray
from sefaria.model.schema import SchemaNode, JaggedArrayNode
from parsing_utilities.util import getGematria, file_to_ja, ja_to_xml


def get_text(from_disk=True):
    if from_disk:
        with codecs.open('chesed_le-avraham.htm', 'r', 'windows-1255') as infile:
            return infile.read()
    else:
        response = urllib2.urlopen('http://www.hebrew.grimoar.cz/azulaj/chesed_le-avraham.htm')
        return codecs.decode(response.read(), 'windows-1255')


def test_expression(pattern):
    """
    test a regular expression object to see if how well it grabs all "springs" and "rivers"
    :param pattern: regular expression string
    :return: List of missed "rivers", expressed as a tuple: (spring, river)
    """
    regex = re.compile(pattern)
    split = get_text().splitlines()
    matches = filter(None, [regex.search(match) for match in split])
    issues = []
    print u'last_match: {}'.format(matches[-1].group())

    expected_spring, expected_river = 1, 1
    for match in matches:
        spring, river = getGematria(match.group(1)), getGematria(match.group(3))
        if spring > expected_spring:
            expected_river = 1
            expected_spring = spring
        if river > expected_river:
            while river > expected_river:
                issues.append((expected_spring, expected_river))
                expected_river += 1
        expected_river += 1
    return issues


def parse_body():

    def cleaner(section):
        bleached = [bleach.clean(segment, tags=[], strip=True) for segment in section]
        return filter(lambda x: None if len(x) == 0 else x, bleached)

    my_text = get_text().splitlines()[:1795]  # A new part begins at this line
    expressions = [u'<b>\u05d4?\u05de\u05e2\u05d9\u05d9?\u05df.*:</b>',
                   u'\u05de\u05e2\u05d9\u05df ([\u05d0-\u05ea]{1,2}) - \u05e0\u05d4\u05e8 (- )?([\u05d0-\u05ea]{1,2})']
    parsed = file_to_ja(3, my_text, expressions, cleaner)
    return parsed.array()


def parse_intro():
    with open('chesed_le-avraham.htm') as infile:
        soup = BeautifulSoup(infile, 'html.parser')
    intro = soup.find('div', class_='intro')
    data = intro.text.splitlines()
    return filter(lambda x: x if len(x) > 0 else None, data)


def parse_shokets():
    with open('chesed_le-avraham.htm') as infile:
        soup = BeautifulSoup(infile, 'html.parser')
    raw_shokets = soup.find('div', class_='shokets').text.splitlines()
    raw_shokets = filter(lambda x: x if len(x) > 0 else None, raw_shokets)

    pattern = ur'(\u05d4\u05e9\u05d5?\u05e7\u05ea [\u05d0-\u05ea]{1,2})( - (.*))?:'
    parsed = JaggedArray([[]])
    shoket, paragraph = -1, -1

    for line in raw_shokets:
        new_section = re.search(pattern, line)
        if new_section is None:
            if shoket >= 0:
                paragraph += 1
                parsed.set_element([shoket, paragraph], line)
        else:
            shoket += 1
            paragraph = -1
            if new_section.group(3) is not None:
                paragraph += 1
                parsed.set_element([shoket, paragraph], u'<b>{}</b>'.format(new_section.group(3)))

    return parsed.array()


def build_alt_struct():
    return None


def construct_index():
    root = SchemaNode()
    root.add_title('Chesed LeAvraham', 'en', primary=True)
    root.add_title(u'חסד לאברהם', 'he', primary=True)
    root.key = 'Chesed LeAvraham'

    intro = JaggedArrayNode()
    intro.add_title('Introduction', 'en', primary=True)
    intro.add_title(u'הקדמה', 'he', primary=True)
    intro.key = 'Introduction'
    intro.depth = 1
    intro.sectionNames = ['Paragraph']
    intro.addressTypes = ['Integer']
    intro.validate()
    root.append(intro)

    even = JaggedArrayNode()
    even.add_title('Even Shetiya', 'en', primary=True)
    even.add_title(u'אבן שתיה', 'he', primary=True)
    even.key = 'Even Shetiya'
    even.sectionNames = ['Maayan']
    even.depth = 1
    even.addressTypes = ['Integer']

    maayanot = [u'עין כל', u'עין הקורא', u'עין הארץ', u'עין יעקב', u'עין משפט', u'עין גנים', u'עין גדי']
    for i, title in enumerate(maayanot):
        node = JaggedArrayNode()
        node.add_title('Maayan {}'.format(i+1), 'en', primary=True)
        node.add_title(title, 'he', primary=True)
        node.key = 'Maayan {}'.format(i+1)
        node.depth = 2
        node.sectionNames = ['Nahar', 'Paragraph']
        node.addressTypes = ['Integer', 'Integer']
        node.validate()
        even.append(node)
    even.validate()
    root.append(even)

    breichat = JaggedArrayNode()
    breichat.add_title('Breichat Avraham', 'en', primary=True)
    breichat.add_title(u'בריכת אברהם', 'he', primary=True)
    breichat.key = 'Breichat Avraham'
    breichat.depth = 2
    breichat.sectionNames = ['Shoket', 'Paragraph']
    breichat.addressTypes = ['Integer', 'Integer']
    breichat.validate()
    root.append(breichat)

    root.validate()
    return {
        'title': 'Chesed LeAvraham',
        'categories': ['Kabbalah'],
        'schema': root.serialize()
    }


def upload():
    post_index(construct_index())
    version = {
        'versionTitle': 'Placeholder',
        'versionSource': 'http://www.hebrew.grimoar.cz/azulaj/chesed_le-avraham.htm',
        'language': 'he',
        'text': parse_intro()
    }
    post_text('Chesed LeAvraham, Introduction', version)
    body = parse_body()
    for i, part in enumerate(body):
        version['text'] = part
        post_text('Chesed LeAvraham, Even Shetiya, Maayan {}'.format(i+1), version)
    version['text'] = parse_shokets()
    post_text('Chesed LeAvraham, Breichat Avraham', version, index_count='on')

upload()
