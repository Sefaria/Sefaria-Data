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
    inst = IndexIbidFinder()
    string = u'''וילך איש מבית לוי רבותינו אמרו שהלך אחר עצת בתו (סוטה יב:). את בלהה (בראשית לה כב),
     דבלים (הושע א ג), לכו ונמכרנו לישמעאלים (בראשית שם כז), לכו ונכהו בלשון (שם יח יח), לכו נא ונוכחה (ישעיה א יח).'''
    refs = inst.segment_find_and_replace(string, lang='he', citing_only=False, replace=True)
    print refs

class TestIndexIbidFinder:

    @classmethod
    def setup_class(cls):
        index = library.get_index('Sefer HaChinukh')
        cls.instance = IndexIbidFinder(index, assert_simple = True)

    def test_find_all_shams_in_st(self):
        st = u'''(שמות יא ט) בשלישי ברא שלש בריות אילנות ודשאים וגן עדן ועוד אמרו (שם י ו) אין לך כל עֵשֶׂב ועשב מלמטה שאין לו מזל ברקיע ומכה אותו ואומר לו גדל הדא הוא דכתיב (איוב לח לג)'''
        shams = self.instance.segment_find_and_replace(st, 'he', citing_only=True)
        assert shams == [Ref('Exodus.11.9'), Ref('Exodus.10.6'), Ref('Job.38.33')]

        st = u'''(שמות יא ט) בשלישי ברא שלש בריות אילנות ודשאים וגן עדן ועוד אמרו (שם י) אין לך כל עֵשֶׂב ועשב מלמטה שאין לו מזל ברקיע ומכה אותו ואומר לו גדל הדא הוא דכתיב (שם)'''
        shams = self.instance.segment_find_and_replace(st, 'he', citing_only=True)
        assert shams == [Ref('Exodus.11.9'), Ref('Exodus.11.10'),Ref('Exodus.11.10')]

    def test_find_in_index(self):
        self.instance.index_find_and_replace()

def test_get_potential_refs():
    inst = CitationFinder()

    st = u'''(שמות יא ט) בשלישי ברא שלש בריות אילנות (שו"ע בלה בלה) ודשאים וגן עדן ועוד אמרו (שם י) אין לך כל עֵשֶׂב ועשב מלמטה שאין לו מזל (בראשית שגדכגדכג) ברקיע ומכה אותו ואומר לו גדל הדא הוא דכתיב (שם)'''
    # st = u'(רמב"ם הלכות יסודי התורה פ"א ופ"ג)'
    st = u'''(שם)'''
    allrefs = inst.get_potential_refs(st)
    print allrefs
    return

def test_get_ultimate_regex():
    inst = CitationFinder()
    test1 = u'(בראשית א:ב)'
    t = u'בראשית'
    n = library.get_schema_node(t, 'he')
    r = inst.get_ultimate_title_regex(t, n, 'he')
    m = re.search(r, test1)
    assert m.groupdict()[u"Title"] == u'בראשית'
    # assert m.groupdict()[u"Integer_Integer"] is not None
    assert m.groupdict()[u'a0'] == u'א' and m.groupdict()[u'a1'] == u'ב'

    test2 = u'(שם ג:ד)'
    r = inst.get_ultimate_title_regex(u'שם', None, 'he')
    #print r.pattern
    m = re.search(r, test2)
    assert m.groupdict()[u"Title"] == u'שם'
    # assert m.groupdict()[u"Integer_Integer"] is not None
    assert m.groupdict()[u'a0'] == u'ג' and m.groupdict()[u'a1'] == u'ד'

    test3 = u'(ב"ר פרק ג משנה ד)'
    r = inst.get_ultimate_title_regex(u'ב"ר', None, 'he')
    m = re.search(r, test3)
    assert m.groupdict()[u"Title"] == u'ב"ר'
    # assert m.groupdict()[u"Perek_Mishnah"] is not None
    assert m.groupdict()[u'a0'] == u'ג' and m.groupdict()[u'a1'] == u'ד'

    test4 = u'בראשית (ג:ד)'
    r = inst.get_ultimate_title_regex(u'בראשית', n, 'he')
    m = re.search(r, test4)
    assert m.groupdict()[u"Title"] == u'בראשית'
    # assert m.groupdict()[u"Integer_Integer"] is not None
    assert m.groupdict()[u'a0'] == u'ג' and m.groupdict()[u'a1'] == u'ד'

    test5 = u'בראשית (שם:ד)'
    t = u'בראשית'
    n = library.get_schema_node(t, 'he')
    r = inst.get_ultimate_title_regex(t, n, 'he')
    m = re.search(r, test5)
    assert m.groupdict()[u"Title"] == u'בראשית'
    # assert m.groupdict()[u"Sham_Perek"] is not None
    assert m.groupdict()[u'a0'] == u'שם' and m.groupdict()[u'a1'] == u'ד'

    test6 = u'שבת (פח:)'
    t = u'שבת'
    n = library.get_schema_node(t, 'he')
    r = inst.get_ultimate_title_regex(t, n, 'he')
    m = re.search(r, test6)
    assert m.groupdict()[u"Title"] == u'שבת'
    # assert m.groupdict()[u'Talmud_Sham'] is not None
    assert m.groupdict()[u'a0'] == u'פח:'

    test7 = u'((משנה ברכות (פרק ג משנה ה)'
    t = u'משנה ברכות'
    n = library.get_schema_node(t, 'he')
    r = inst.get_ultimate_title_regex(t, n, 'he')
    m = re.search(r, test7)
    assert m.groupdict()[u"Title"] == u'משנה ברכות' # or shouldn't this be simply ברכות?
    # assert m.groupdict()[u"Perek_Mishnah"] is not None
    assert m.groupdict()[u'a0'] == u'ג' and m.groupdict()[u'a1'] == u'ה'

    test8 = u'(בראשית שם)'
    t = u'בראשית'
    n = library.get_schema_node(t, 'he')
    r = inst.get_ultimate_title_regex(t, n, 'he')
    m = re.search(r, test8)
    assert m.groupdict()[u"Title"] == u'בראשית'
    # assert m.groupdict()[u"Sham_Perek"] is not None
    assert m.groupdict()[u'a0'] == u'שם'

    test9 = u'(משנה ברכות שם מ"ג)'
    t = u'משנה ברכות'
    n = library.get_schema_node(t, 'he')
    r = inst.get_ultimate_title_regex(t, n, 'he')
    m = re.search(r, test9)
    assert m.groupdict()[u"Title"] == u'משנה ברכות'
    # assert m.groupdict()[u"Sham_Perek"] is not None
    assert m.groupdict()[u'a0'] == u'שם' and m.groupdict()[u'a1'] == u'ג'

def test_build_refs():
    inst = CitationFinder()
    test1 = u'(בראשית א:ב)'
    title = u'בראשית'
    refs = library._internal_ref_from_string(title,test1,'he',False,True,inst.get_ultimate_title_regex(title, 'he', compiled=False))
    assert refs.group() == u'Genesis 1:2'

#todo: test new class IndexIbidFinder
#todo: test ibidExceptions