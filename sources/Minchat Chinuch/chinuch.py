# encoding=utf-8
import re
import codecs
from data_utilities.sanity_checks import TagTester
from data_utilities import util

filename = 'Minchat_Chinuch.txt'
"""
מקרא:

@44 קישור ואות לינוך.
@66מצב אות רגיל.
@55 ציטוט מודש.
@88 סוגרים.
@30 מצוה.
@29 סוף מצוה.

"""


def check_chapters():
    with codecs.open('Minchat_Chinuch.txt', 'r', 'utf-8') as chinuch:
        test = TagTester(u'@30', chinuch, u'@30מצוה ([\u05d0-\u05ea"]{1,5})')

        index = 1

        for header in test.grab_each_header(capture_group=1):

            header = header.replace(u'"', u'')
            count = util.getGematria(header)

            if count != index:
                print util.numToHeb(index)
                index = count
            index += 1


def check_segments():

    segments = []

    infile = codecs.open(filename, 'r', 'utf-8')

    headers = TagTester(u'@30', infile, u'@30מצוה ([\u05d0-\u05ea"]{1,5})').grab_each_header()
    tester = TagTester(u'@44', infile, u'@44\(([\u05d0-\u05ea]{1,2})\)')

    while not tester.eof:

        segments.append(tester.grab_each_header(u'@30מצוה ([\u05d0-\u05ea"]{1,5})', 1))

    infile.close()

    for sec_number, section in enumerate(segments):

        index = 1

        for title in section:

            title = title.replace(u'"', u'')
            count = util.getGematria(title)

            if count != index:

                print headers[sec_number-1]
                print util.numToHeb(index)
                index = count
            index += 1


def tag_position(text, pattern, position):
    """
    Given a line of text, check if the given pattern can be found at the word of specified position
    :param text: text to be examined
    :param pattern: pattern to search for
    :param position: Word number pattern is expected to appear
    :return: True of False
    """

    expression = re.compile(pattern)

    words = text.split()

    if expression.search(words[position]):
        return True
    else:
        return False


def analyze_lines(pattern, condition, *args):
    """
    Outputs a list of lines that contain pattern but don't satisfy condition
    :param pattern: Pattern to identify lines of interest
    :param condition: Condition lines are expected to fulfill
    :return: List of dictionaries with line numbers and text where lines don't meet condition
    """

    expression = re.compile(pattern)
    bad_lines = []
    count = 0

    with codecs.open(filename, 'r', 'utf-8') as thefile:

        for line_num, line in enumerate(thefile):

            if expression.search(line):
                if not condition(line, *args):
                    data = {
                        'line number': line_num,
                        'text': line
                    }
                    count += 1
                    bad_lines.append(data)
    print '{} bad lines'.format(count)

    return bad_lines

