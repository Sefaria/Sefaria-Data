# encoding=utf-8

import os
import re
import codecs
from data_utilities.util import get_cards_from_trello, numToHeb
from sefaria.model.text import Ref, JaggedArrayNode
from data_utilities.sanity_checks import TagTester


def get_cards():
    with open('../trello_board.json') as board:
        return [card.replace(' on', '') for card in get_cards_from_trello('Parse Rambam Mishna Style', board)]


def standardize_files():

    def get_filename(dst):
        if dst == 'Rambam Pirkei Avot':
            org = 'Pirkei Avot'
        else:
            org = dst.replace(' Mishnah', '')
        return '{}.txt'.format(org)
    cards = get_cards()
    for card in cards:
        filename = get_filename(card)
        os.rename(filename, '{}.txt'.format(card))


def check_chapters():
    cards = get_cards()
    good_files, bad_files = [], []
    for card in cards:
        m_ref = Ref(card.replace('Rambam ', ''))
        with codecs.open('{}.txt'.format(card), 'r', 'utf-8') as infile:
            tester = TagTester(u'@00', infile, u'@00\u05e4\u05e8\u05e7')
            tags = tester.grab_each_header()
        if len(tags) == len(m_ref.all_subrefs()) or card == 'Rambam Pirkei Avot':
            good_files.append(card)
        else:
            bad_files.append(card)
    return {
        'good': good_files,
        'bad': bad_files
    }


def test_insert_chapters(filename, expected):
    with codecs.open(filename, 'r', 'utf-8') as infile:
        tester = TagTester(u'@22', infile, u'^@22\u05d0( |$)')
        if len(tester.grab_each_header()) == expected:
            return True
        else:
            return False


def insert_chapter_marker(filename, safe_mode=False):
    with codecs.open(filename, 'r', 'utf-8') as infile:
        lines = infile.readlines()
    count = 0
    new_lines = []
    for line in lines:
        if re.search(u'^@22\u05d0( |$)', line) is not None:
            count += 1
            new_lines.append(u'@00\u05e4\u05e8\u05e7 {}\n{}'.format(numToHeb(count), line))
        else:
            new_lines.append(line)
    if safe_mode:
        filename += '.tmp'
    with codecs.open(filename, 'w', 'utf-8') as outfile:
        outfile.writelines(new_lines)
