# -*- coding: utf-8 -*-
from sefaria.model import *
from data_utilities.ibid import BookIbidTracker, IbidDict




def setup_module(module):
    global em_tracker, simple_tracker
    em_tracker = BookIbidTracker()
    simple_tracker = BookIbidTracker(assert_simple=True)


def test_smag_sham():
    tracker = em_tracker

    line1 = Ref('Sefer Mitzvot Gadol, Volume One 290')
    index1 = 'Sefer Mitzvot Gadol, Volume One'
    sections1 = line1.sections

    index2 = None
    sections2 = [None]

    tracker.resolve(index1, sections1)
    resolved2 = tracker.resolve(index2, sections2)

    assert resolved2 == Ref('Sefer Mitzvot Gadol, Volume One 290')


def test_shulchan_arukh():
    tracker = em_tracker

    ref1 = Ref('Shulchan Arukh, Orach Chayim.539.1')
    tracker.registerRef(ref1)
    sham = ('Shulchan Arukh, Orach Chayim', (None,))
    resolved = tracker.resolve(sham[0], sham[1])
    assert resolved == Ref('Shulchan Arukh, Orach Chayim.539.1')

    sham = ('Shulchan Arukh, Orach Chayim', (None, 5))
    resolved = tracker.resolve(sham[0], sham[1])
    assert resolved == Ref('Shulchan Arukh, Orach Chayim.539.5')

    sham = (None, (None,))
    resolved = tracker.resolve(sham[0], sham[1])
    assert resolved == Ref('Shulchan Arukh, Orach Chayim.539.5')


def test_tur():
    tracker = em_tracker

    ref1 = Ref('Tur, Orach Chaim.22')
    tracker.registerRef(ref1)
    sham = ('Tur, Orach Chaim', (None,))
    resolved = tracker.resolve(sham[0], sham[1])
    assert resolved == Ref('Tur, Orach Chaim.22')

    sham = (None, (220,))
    resolved = tracker.resolve(sham[0], sham[1])
    assert resolved == Ref('Tur, Orach Chaim.220')

    sham = (None, (None,))
    resolved = tracker.resolve(sham[0], sham[1])
    assert resolved == Ref('Tur, Orach Chaim.220')

    # todo: sham = ('Tur, Orach Chaim', (220, None)). I want to write an error for this.
    # sham = (None, (220, None))
    # resolved = tracker.resolve(sham[0], sham[1])
    # assert resolved == Ref('Tur, Orach Chaim.220')


def test_rambam():
    tracker = em_tracker

    ref1 = Ref('Mishneh Torah, Rest on a Holiday.7.2')
    tracker.registerRef(ref1)
    sham = ('Mishneh Torah, Rest on a Holiday', (None,None))
    resolved = tracker.resolve(sham[0], sham[1])
    assert resolved == Ref('Mishneh Torah, Rest on a Holiday.7.2')

    sham = ('Mishneh Torah, Rest on a Holiday', (None, 5))
    resolved = tracker.resolve(sham[0], sham[1])
    assert resolved == Ref('Mishneh Torah, Rest on a Holiday.7.5')

    sham = (None, (None,))
    resolved = tracker.resolve(sham[0], sham[1])
    assert resolved == Ref('Mishneh Torah, Rest on a Holiday.7.5')

    #TODO: fix code so this test will pass
    sham = ('Mishneh Torah, Rest on a Holiday', (8,))
    resolved = tracker.resolve(sham[0], sham[1])
    assert resolved == Ref('Mishneh Torah, Rest on a Holiday.8')

def test_tanakh():
    tracker = simple_tracker

    ref1 = Ref('Genesis 21.1')
    tracker.registerRef(ref1)
    sham = ('Genesis', (None, 4))
    resolved = tracker.resolve(sham[0], sham[1])
    assert resolved == Ref('Genesis 21.4')


def test_talmud():
    tracker = simple_tracker

    ref1 = Ref('Shabbat 21a')
    tracker.registerRef(ref1)
    sham = ('Shabbat', (None,))
    resolved = tracker.resolve(sham[0], sham[1])
    assert resolved == Ref('Shabbat 21a')

    sham = (None, (None,))
    resolved = tracker.resolve(sham[0], sham[1])
    assert resolved == Ref('Shabbat 21a')


def test_ibid_dict():
    test_dict = IbidDict()
    test_dict['1'] = 1
    test_dict['2'] = 2
    test_dict['1'] = 10
    assert  test_dict.items() == [('2',2),('1',10)]
