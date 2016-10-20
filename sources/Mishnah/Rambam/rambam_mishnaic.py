# encoding=utf-8

import os
from data_utilities.util import get_cards_from_trello


def get_cards():
    with open('../trello_board.json') as board:
        return [card.replace(' on', '') for card in get_cards_from_trello('Parse Rambam Mishna Style', board)]


def standardize_files(safe_mode=False):

    def get_filename(dst):
        if dst == 'Rambam Pirkei Avot':
            org = 'Pirkei Avot'
        else:
            org = dst.replace(' Mishnah', '')
        return '{}.txt'.format(org)
    cards = get_cards()
    for card in cards:
        filename = get_filename(card)
        if safe_mode:
            os.rename(filename, '{}.txt.tmp'.format(card))
        else:
            os.rename(filename, '{}.txt'.format(card))

a = get_cards()
print 'number of card: {}'.format(len(a))
standardize_files(safe_mode=True)

