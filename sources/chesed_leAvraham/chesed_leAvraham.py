# encoding=utf-8

"""
expression to grab every "spring": u'<b>\u05d4?\u05de\u05e2\u05d9\u05d9?\u05df.*:</b>'
this seems to grab the "rivers": u'\u05de\u05e2\u05d9\u05df ([\u05d0-\u05ea]{1,2}) - \u05e0\u05d4\u05e8 (- )?([\u05d0-\u05ea]{1,2})'
"""
import re
import codecs
import urllib2
from data_utilities.util import getGematria


def get_text():
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

trial = u'\u05de\u05e2\u05d9\u05df ([\u05d0-\u05ea]{1,2}) - \u05e0\u05d4\u05e8 (- )?([\u05d0-\u05ea]{1,2})'
stuff = test_expression(trial)
print len(stuff)
for thing in stuff:
    print thing
