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


def grab_dh(text, start_tag, end_tag):
    """
    for a given string grab the text that rests between start_tag and end_tag
    :param text:
    :param start_tag:
    :param end_tag:
    :return: the text identified as the dh. Will return None if one cannot be identified.
    """

    start_reg = re.compile(start_tag)
    end_reg = re.compile(end_tag)

    start = start_reg.search(text)
    if not start:
        return None

    end = end_reg.search(text[start.end():])
    if not end:
        return None

    # add the text that goes from the end of the start tag to the beginning of the end tag
    return text[start.end():end.start()+start.end()]


def grab_all_dh(comment_tag, start_tag, end_tag):
    """
    Grabs all dh in a file
    :param comment_tag:
    :param start_tag:
    :param end_tag:
    :return: Dictionary with the text and line_number fields
    """

    data = []
    comment_reg = re.compile(comment_tag)

    with codecs.open(filename, 'r', 'utf-8') as infile:

        for index, line in enumerate(infile):

            if comment_reg.search(line):
                dh = grab_dh(line, start_tag, end_tag)

                if dh:
                    data.append({'text': dh, 'line_number': index+1})

                else:
                    print 'bad line at {}'.format(index+1)

    return data
