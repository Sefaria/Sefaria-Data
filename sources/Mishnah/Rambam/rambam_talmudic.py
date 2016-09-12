# encoding=utf-8

import re
import codecs
import os
from data_utilities.util import get_cards_from_trello

with open('../trello_board.json') as board:
    cards = [card.replace(' on', '') for card in get_cards_from_trello('Parse Rambam Talmud style', board)]


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
                continue
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
    with codecs.open(filename, 'w', 'utf-8') as outfile:
        outfile.writelines(new_lines)

for card in cards:
    with codecs.open('{}.txt'.format(card), 'r', 'utf-8') as infile:
        data = infile.readlines()
    r = check_header(data)
    if not r:
        print '{} is bad'.format(card)