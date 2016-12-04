# encoding=utf-8

"""
expression to grab every "spring": u'<b>\u05d4?\u05de\u05e2\u05d9\u05d9?\u05df.*:</b>'
this seems to grab the "rivers": u'\u05de\u05e2\u05d9\u05df ([\u05d0-\u05ea]{1,2}) - \u05e0\u05d4\u05e8 (- )?([\u05d0-\u05ea]{1,2})'
"""
import re
import codecs
import urllib2
import bleach
from data_utilities.util import getGematria, file_to_ja, ja_to_xml


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

    my_text = get_text().splitlines()[:1795]
    expressions = [u'<b>\u05d4?\u05de\u05e2\u05d9\u05d9?\u05df.*:</b>',
                   u'\u05de\u05e2\u05d9\u05df ([\u05d0-\u05ea]{1,2}) - \u05e0\u05d4\u05e8 (- )?([\u05d0-\u05ea]{1,2})']
    parsed = file_to_ja(3, my_text, expressions, cleaner)
    return parsed.array()


