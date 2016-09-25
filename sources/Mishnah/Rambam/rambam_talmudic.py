# encoding=utf-8

import re
import codecs
from data_utilities.util import get_cards_from_trello

with open('../trello_board.json') as board:
    cards = [card.replace(' on', '') for card in get_cards_from_trello('Parse Rambam Talmud style', board)]
"""
To open files:
for card in cards:
    with codecs.open('{}.txt'.format(card), 'r', 'utf-8') as infile:
        <code here>
"""


def check_header(lines):
    """
    Check that each @11 is followed by an @22 on the same or the following line
    :param lines: list of lines in file
    :return: Boolean
    """

    is_good = True
    previous_line = lines[0]
    for index, next_line in enumerate(lines[1:]):

        if re.match(u'@11', previous_line):
            if re.search(u'@22', previous_line):
                pass
            else:
                if re.search(u'@22', next_line):
                    pass
                else:
                    print 'bad line at {}'.format(index+1)
                    is_good = False
        previous_line = next_line
    return is_good


def align_header(filename):
    """
    Place @11 and @22 on the same line to make for easier parsing
    :param filename: name of file
    """

    with codecs.open(filename, 'r', 'utf-8') as infile:
        old_lines = infile.readlines()
    new_lines = []

    previous_line = old_lines[0]
    for index, next_line in enumerate(old_lines[1:]):

        if re.match(u'@11', previous_line):
            if re.search(u'@22', previous_line):
                pass
            else:
                if re.search(u'@22', next_line):
                    previous_line = previous_line.replace(u'\n', u'')
                else:
                    print 'bad line at {}'.format(index+1)
                    raise KeyboardInterrupt

        new_lines.append(previous_line)
        previous_line = next_line
    else:
        new_lines.append(previous_line)
    with codecs.open(filename+'.tmp', 'w', 'utf-8') as outfile:
        outfile.writelines(new_lines)


def format_reference(filename):
    """
    Ensure that each reference line contains an actual reference and that it is encapsulated inside parentheses. Calls
    str.rstrip() on each line to remove trailing spaces.
    DANGER: Will overwrite file!!!
    :param filename: path to file
    """

    with codecs.open(filename, 'r', 'utf-8') as infile:
        file_lines = [re.sub(u' +', u' ', line).replace(u' \n', u'\n') for line in infile]

    fixed_lines = []
    for line in file_lines:
        if re.match(u'@11', line):
            has_reference = re.search(u'@22', line)
            assert has_reference is not None

            ref = re.search(u'@22([\u05d0-\u05ea" ]+)$', line)
            if ref is not None:
                line = line.replace(ref.group(1), u'({})'.format(ref.group(1)))
        fixed_lines.append(line)

    with codecs.open(filename+'.tmp', 'w', 'utf-8') as outfile:
        outfile.writelines(fixed_lines)
