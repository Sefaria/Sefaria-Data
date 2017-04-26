# -*- coding: utf-8 -*-

from sefaria.model import *
from data_utilities.ibid import *




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


def test_ibid_find():
    string = u'''וילך איש מבית לוי רבותינו אמרו שהלך אחר עצת בתו (סוטה יב:). את בלהה (בראשית לה כב),
     דבלים (הושע א ג), לכו ונמכרנו לישמעאלים (בראשית שם כז), לכו ונכהו בלשון (שם יח יח), לכו נא ונוכחה (ישעיה א יח).'''
    refs = ibid_find_and_replace(string, lang='he', citing_only=False, replace=True)
    print refs

class TestIndexIbidFinder:

    @classmethod
    def setup_class(cls):
        index = library.get_index('Ramban on Genesis')
        cls.instance = IndexIbidFinder(index, assert_simple = True)

    def test_find_all_shams_in_st(self):
        st = u'''(שמות יא ט) בשלישי ברא שלש בריות אילנות ודשאים וגן עדן ועוד אמרו (שם י ו) אין לך כל עֵשֶׂב ועשב מלמטה שאין לו מזל ברקיע ומכה אותו ואומר לו גדל הדא הוא דכתיב (איוב לח לג)'''
        shams = self.instance.ibid_find_and_replace(st, 'he', citing_only=True)
        assert shams == [Ref('Exodus.11.9'), Ref('Exodus.10.6'), Ref('Job.38.33')]

        st = u'''(שמות יא ט) בשלישי ברא שלש בריות אילנות ודשאים וגן עדן ועוד אמרו (שם י) אין לך כל עֵשֶׂב ועשב מלמטה שאין לו מזל ברקיע ומכה אותו ואומר לו גדל הדא הוא דכתיב (שם)'''
        shams = self.instance.ibid_find_and_replace(st, 'he', citing_only=True)
        assert shams == [Ref('Exodus.11.9'), Ref('Exodus.11.10'),Ref('Exodus.11.10')]

def test_get_potential_refs():
    inst = CitationFinder()

    st = u'''(שמות יא ט) בשלישי ברא שלש בריות אילנות (שו"ע בלה בלה) ודשאים וגן עדן ועוד אמרו (שם י) אין לך כל עֵשֶׂב ועשב מלמטה שאין לו מזל (בראשית שגדכגדכג) ברקיע ומכה אותו ואומר לו גדל הדא הוא דכתיב (שם)'''
    st = u'(רמב"ם הלכות יסודי התורה פ"א ופ"ג)'
    refs, nons, shams = inst.get_potential_refs(st)
    print 'refs', refs
    print 'nons', nons
    print 'shams', shams

def test_get_ultimate_regex():
    inst = CitationFinder()
    test1 = u'(בראשית א:ב)'
    r = inst.get_ultimate_title_regex(u'בראשית','he')
    m = re.search(r, test1)
    assert m.group() == u'(בראשית א:ב)'

    test2 = u'(שם ג:ד)'
    r = inst.get_ultimate_title_regex(u'שם','he')
    m = re.search(r, test2)
    assert m.group() == u'(שם ג:ד)'

    test3 = u'(ב"ר פרק ג משנה ד)'
    r = inst.get_ultimate_title_regex(u'ב"ר','he')
    m = re.search(r, test3)
    assert m.group() == u'(ב"ר פרק ג משנה ד)'

    test4 = u'בראשית (ג:ד)'
    r = inst.get_ultimate_title_regex(u'בראשית','he')
    m = re.search(r, test4)
    assert m.group() == u'בראשית (ג:ד)'

    test5 = u'בראשית (שם:ד)'
    r = inst.get_ultimate_title_regex(u'בראשית','he')
    m = re.search(r, test5)
    assert m.group() == u'בראשית (שם:ד)'

    test6 = u'שבת (פח:)'
    r = inst.get_ultimate_title_regex(u'שבת','he')
    m = re.search(r, test6)
    assert m.group() == u'שבת (פח:)'

    test7 = u'((משנה ברכות (פרק ג משנה ה)'
    r = inst.get_ultimate_title_regex(u'משנה ברכות','he')
    m = re.search(r, test7)
    assert m.group() == u'משנה ברכות (פרק ג משנה ה)'

def test_build_refs():
    inst = CitationFinder()
    test1 = u'(בראשית א:ב)'
    title = u'בראשית'
    refs = library._internal_ref_from_string(title,test1,'he',False,True,inst.get_ultimate_title_regex(title, 'he', compiled=False))
    pass
#todo: test new class IndexIbidFinder
#todo: test ibidExceptions