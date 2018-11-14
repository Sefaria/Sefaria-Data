# -*- coding: utf-8 -*-
import django
django.setup()

from sefaria.model import *
from data_utilities.ibid import *
import pytest


def setup_module(module):
    global em_tracker, simple_tracker
    em_tracker = BookIbidTracker()
    simple_tracker = BookIbidTracker(assert_simple=True)


def test_smag_sham():
    tracker = em_tracker

    line1 = Ref('Sefer Mitzvot Gadol, Negative Commandments 290')
    index1 = 'Sefer Mitzvot Gadol, Negative Commandments'
    sections1 = line1.sections

    index2 = None
    sections2 = [None]

    tracker.resolve(index1, sections1)
    resolved2 = tracker.resolve(index2, sections2)

    assert resolved2 == Ref('Sefer Mitzvot Gadol, Negative Commandments 290')


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


def test_ignore_book():
    tracker = simple_tracker
    ref1 = Ref('Genesis 1:2')
    tracker.registerRef(ref1)
    tracker.ignore_book_name_keys()
    with pytest.raises(IbidKeyNotFoundException):
        tracker.resolve(None, match_str=u'(שם)')


def test_ibid_dict():
    test_dict = IbidDict()
    test_dict['1'] = 1
    test_dict['2'] = 2
    test_dict['1'] = 10
    assert  test_dict.items() == [('2',2),('1',10)]


def test_ibid_find_1():
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)
    string = u'''וילך איש מבית לוי רבותינו אמרו שהלך אחר עצת בתו (סוטה יב:). את בלהה (בראשית לה כב),
     דבלים (הושע א ג), לכו ונמכרנו לישמעאלים (בראשית שם כז), לכו ונכהו בלשון (שם יח יח), לכו נא ונוכחה (ישעיה א יח).'''
    refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    assert refs == [Ref("Sotah 12b"), Ref("Genesis 35:22"), Ref(u"הושע א:ג"), Ref(u"בראשית לה:כז"), Ref(u"בראשית יח:יח"),  Ref(u"ישעיהו א:יח")]


def test_ibid_find_2():
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)
    string = u"""ממלאים ממנו בשבת, [שם ועיין לקמן במצות עירובין בסוף הספר][שם ועיין לקמן במצות עירובין בסוף הספר] וגם אין מטלטלין """
    refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    assert refs == []


def test_ibid_find_3():
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)
    string = u"""היי (שבת כב:) ועוד דברים. וגם שבת [שם] ועוד דברים."""
    refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    assert refs == [Ref('Shabbat 22b'), Ref('Shabbat 22b')]

    string = u"""היי (שבת כב:) ועוד. אז אמרו (חולין כב:) לצחוק. ואז שבת [שם] סתם? או לא"""
    refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    assert refs == [Ref('Shabbat 22b'), Ref('Chullin 22b'), Ref('Shabbat 22b')]


def test_ibid_find_4():
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)
    string = u"(מלכים א ח יג) בלה בלה. (שם בפסוק כז)" # testing that it doesn't read 'ב' of 'בפסוק' as 2.
    refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    assert refs == [Ref("I Kings 8:13")]


def test_ibid_find_5():
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)

    string = u'''ולשון רבותינו משנה (ביצה ב) פתין גריצים וחיורי ואמרו ירושלמי (שם) רבנין שמעין לה מן ה'''
    refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    assert refs == []

    # string = u'''התפילין. מ"ש הר"ב דשבת לאו זמן תפילין לא פסק כן בריש פרק בתרא דעירובין ושם אאריך בס"ד ועוד עיין בסוף פרק קמא דביצה. ומה שכתב דאיתקש תפילין למזוזה פירש רש"י דכתיב (דברים ו) וקשרתם וכתבתם. ומ"ש קא משמע לן. וטעמא דתפילין אתקשו בפרשת ראשונה לת"ת דכתיב (שם) ושננתם וגו' וקשרתם. וכן בשניה (שם יא) והיו לטוטפות וגו'. ולמדתם וגו'. ואילו למזוזה הפסיק ביניהם בשניה בת"ת. גמ' פרק קמא דקדושין (דף לד:):'''
    # refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    # assert refs == []


def test_ibid_find_6():
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)

    string = u'''ולשון רבותינו (ביצה ב) פתין גריצים וחיורי ואמרו ירושלמי (שם) רבנין שמעין לה מן ה'''
    refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    assert refs == [Ref('Beitzah 2a')]


def test_ibid_find_7():
    # The difference between test6^ is the Yerushalmi out of parenthesis
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)

    string = u'''ולשון רבותינו (ביצה ב) פתין גריצים וחיורי ואמרו (ירושלמי שם) רבנין שמעין לה מן ה'''
    refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    assert refs == [Ref('Beitzah 2a')]


def test_ibid_find_8():
    # The difference between test6^ is the Yerushalmi out of parenthesis
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)

    string = u'''ולשון רבותינו (ביצה ב) פתין גריצים וחיורי ואמרו (שם) רבנין שמעין לה מן ה'''
    refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    assert refs == [Ref('Beitzah 2a'), Ref('Beitzah 2a')]


def test_ibid_find_9():
    # The difference between test6^ is the Yerushalmi out of parenthesis
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)

    string = u'''(בראשית א ב) ולשון רבותינו משנה (ביצה ב ו) פתין גריצים וחיורי ואמרו (שם) רבנין שמעין לה מן ה'''
    refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    print refs
    assert refs == [Ref('Genesis 1:2')]


def test_ibid_find_10():
    # The difference between test6^ is the Yerushalmi out of parenthesis
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)

    string = u'''(בבא קמא ע"ז ע"ב)'''
    refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    print refs
    assert refs == [Ref('Bava Kamma 77b')]


def test_ibid_find_11():
    # The difference between test6^ is the Yerushalmi out of parenthesis
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)

    string = u'''(סנהדרין ע"ז ע"א)'''
    refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    print refs
    assert refs == [Ref('Sanhedrin 77a')]


def test_ibid_find_12():
    # The difference between test6^ is the Yerushalmi out of parenthesis
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)

    string = u''' סנהדרין (ע"ז ע"א)'''
    refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    print refs
    assert refs == [Ref('Sanhedrin 77a')]


def test_ibid_find_13():
    # The difference between test6^ is the Yerushalmi out of parenthesis
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)

    string = u'''(ע"ז ע"ו ע"ב) וכן ראה (שם ע"א) '''
    refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    print refs
    assert refs == [Ref('Avodah Zarah 76b'), Ref('Avodah Zarah 71a')] # todo: fix it so that Ref('Avodah Zarah 76a')


def test_ibid_find_13_1():
    # The difference between test6^ is the Yerushalmi out of parenthesis
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)

    string = u'''(סנהדרין ע"ו ע"ב) וכן ראה (שם ע"ז ע"א) '''
    refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    print refs
    assert refs == [Ref('Sanhedrin 76b'), Ref('Sanhedrin 77a')]


def test_ibid_find_14():
    # The difference between test6^ is the Yerushalmi out of parenthesis
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)

    string = u''' בראשית (מ"ב ד ה) '''
    refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    print refs
    assert refs == [Ref('Genesis 42:4')]


def test_ibid_find_15():
    # The difference between test6^ is the Yerushalmi out of parenthesis
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)

    string = u''' (בראשית כ ה) וכן שם (מ"ב ד ה)'''
    refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    print refs
    assert refs == [Ref('Genesis 20:5'), Ref('Genesis 42:4')]


def test_ibid_find_16(): #todo: what would you really want in this test?
    # The difference between test6^ is the Yerushalmi out of parenthesis
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)

    string = u''' (מ"ב ג יג) (בראשית כ ה) ושוב במלכים שם (מ"ב ג ד)'''
    refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    print refs
    assert refs == [Ref('II Kings 3:13'), Ref('Genesis 20:5'), Ref('Genesis 42:3')]
#
# def test_ibid_find_Mekhilta():
#     # Fails todo: catch Mekhilta
#     # The difference between test6^ is the Yerushalmi out of parenthesis
#     ind = library.get_index("Genesis")
#     inst = IndexIbidFinder(ind)
#
#     string = u'איתא במכילתא לשמות י"ב מ'
#     refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
#     print refs
#     assert refs == [Ref('''Mekhilta d'Rabbi Yishmael.12.40''')]

# def test_ibid_pasuk():
#     ind = library.get_index("Genesis")
#     inst = IndexIbidFinder(ind)
#
#     string = u''' בבראשית (יא, ג) בהמשך (בפסוק ז) '''
#     refs, _, _ = inst.find_in_segment(string)
#     assert refs == [Ref('Genesis 11:3'), Ref('Genesis 11:7')]


def test_ibid_prefixes():
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)

    string = u''' (כמו שנאמר בחומש שמות א:ב) '''
    refs, _, _ = inst.find_in_segment(string)
    assert refs == [Ref('Exodus 1:2')]

    string = u''' (רמ"א א:ב) '''
    refs, _, _ = inst.find_in_segment(string)
    assert refs == []

    string = u'''(בראשית לא, א) וכן (כשם א, י)'''
    refs, _, _ = inst.find_in_segment(string)
    assert refs == [Ref('Genesis 31:1')]

    string = u'''(בראשית לא, א) וכן כשם (א, י)'''
    refs, _, _ = inst.find_in_segment(string)
    assert refs == [Ref('Genesis 31:1')]

    string = u'''(בראשית לא, א) וכן שם (א, י)'''
    refs, _, _ = inst.find_in_segment(string)
    assert refs == [Ref('Genesis 31:1'), Ref('Genesis 1:10')]

def test_ibid_alttitle_br():
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)
    string = u''' ובבראשית רבה (לט ז) ואשר אמרו עוד (בב"ר שם) בתחילה'''
    refs, _, _ = inst.find_in_segment(string)
    assert refs == [Ref('Bereishit Rabbah 39:7'), Ref('Bereishit Rabbah 39:7')]

    string = u''' מדרש רבה בראשית (לט ז) ואשר אמרו עוד (בב"ר שם) בתחילה'''
    refs, _, _ = inst.find_in_segment(string)
    assert refs == [Ref('Bereishit Rabbah 39:7'), Ref('Bereishit Rabbah 39:7')]

    string = u'''רש"י על בראשית כ א'''
    refs, _, _ = inst.find_in_segment(string)
    assert refs == [Ref('Rashi on Genesis 20:1')]

class TestIndexIbidFinder:

    @classmethod
    def setup_class(cls):
        index = library.get_index('Sefer HaChinukh')
        cls.instance = IndexIbidFinder(index, assert_simple = True)

    def test_find_all_shams_in_st(self):
        st = u'''(שמות יא ט) בשלישי ברא שלש בריות אילנות ודשאים וגן עדן ועוד אמרו (שם י ו) אין לך כל עֵשֶׂב ועשב מלמטה שאין לו מזל ברקיע ומכה אותו ואומר לו גדל הדא הוא דכתיב (איוב לח לג)'''
        shams, _, _ = self.instance.find_in_segment(st, 'he', citing_only=True)
        assert shams == [Ref('Exodus.11.9'), Ref('Exodus.10.6'), Ref('Job.38.33')]

        st = u'''(שמות יא ט) בשלישי ברא שלש בריות אילנות ודשאים וגן עדן ועוד אמרו (שם י) אין לך כל עֵשֶׂב ועשב מלמטה שאין לו מזל ברקיע ומכה אותו ואומר לו גדל הדא הוא דכתיב (שם)'''
        shams, _, _ = self.instance.find_in_segment(st, 'he', citing_only=True)
        assert shams == [Ref('Exodus.11.9'), Ref('Exodus.11.10'), Ref('Exodus.11.10')]

    def test_find_in_index(self):
        pass
        #to test this we need to create a fake index
        # self.instance.index_find_and_replace()

    def test_get_sham_ref_with_node(self):
        st = u"(פסחים צו, א)(שם ה, א)"
        refs, _, _ = self.instance.find_in_segment(st, 'he', citing_only=True)
        assert refs == [Ref('Pesachim 96a'), Ref('Pesachim 5a')]

        st = u'''(פסחים כא:)(שמות כא ב)(שם ג:)'''
        allrefs, _, _ = self.instance.find_in_segment(st, 'he', citing_only=True)
        # assert allrefs == [Ref('Pesachim 21b'), Ref('Exodus 21:2'), Ref('Pesachim 3b')]

        st = u'''(שמות כב ב)(שמות ל)(שם ה)'''
        allrefs, _, _ = self.instance.find_in_segment(st, 'he', citing_only=True)
        assert allrefs == [Ref('Exodus 22:2'), Ref('Exodus 30'), Ref('Exodus 5')]

        st = u'''כי בוחר אתה לבן ישי (שמואל א כ ל) והחזיק לו (שם ב טו ה) ורבים כן או פירושו'''
        allrefs, _, _ = self.instance.find_in_segment(st, 'he', citing_only=True)
        assert allrefs == [Ref('I Samuel 20:30'), Ref('II Samuel 15:5')]
        print allrefs

        st = u'''כי בוחר אתה לבן ישי (שמואל א כ ל) והחזיק לו (שם טו ה) ורבים כן או פירושו'''
        allrefs, _, _ = self.instance.find_in_segment(st, 'he', citing_only=True)
        assert allrefs == [Ref('I Samuel 20:30'), Ref('I Samuel 15:5')]
        print allrefs

        st = u'''כי בוחר אתה לבן ישי (שמואל א כ ל) והחזיק לו (שם ה) ורבים כן או פירושו'''
        allrefs, _, _ = self.instance.find_in_segment(st, 'he', citing_only=True)
        assert allrefs == [Ref('I Samuel 20:30'), Ref('I Samuel 20:5')]
        print allrefs

        index = library.get_index('Genesis')
        instance = IndexIbidFinder(index, assert_simple=True)
        st = u'''כי בוחר אתה לבן ישי (דברי הימים א כ א) והחזיק לו (שם ב יד) ורבים כן או פירושו'''
        allrefs, _, _ = instance.find_in_segment(st, 'he', citing_only=True)
        print allrefs
        assert allrefs == [Ref('I Chronicles 20:1'), Ref('I Chronicles 2:14')]

        index = library.get_index('Genesis')
        instance = IndexIbidFinder(index, assert_simple=True)
        st = u'''כי בוחר אתה לבן ישי (דברי הימים א כ א) והחזיק לו (שם ב ב ב) ורבים כן או פירושו'''
        allrefs, _, _ = instance.find_in_segment(st, 'he', citing_only=True)
        print allrefs
        assert allrefs == [Ref('I Chronicles 20:1'), Ref('II Chronicles 2:2')]


        index = library.get_index('Genesis')
        instance = IndexIbidFinder(index, assert_simple=True)
        st = u'''כי בוחר אתה לבן ישי (דברי הימים א כ א) והחזיק לו ב (שם ב ב ב) ורבים כן או פירושו'''
        allrefs, _, _ = instance.find_in_segment(st, 'he', citing_only=True)
        print allrefs
        assert allrefs == [Ref('I Chronicles 20:1'), Ref('II Chronicles 2:2')]



def test_get_potential_refs():
    inst = CitationFinder()

    st = u'''(שמות יא ט) בשלישי ברא שלש בריות אילנות (אורח חיים ק) ודשאים וגן עדן ועוד אמרו (שם י) אין לך כל עֵשֶׂב (שמות שם כז) ועשב מלמטה שאין לו מזל (ברכות י:) ברקיע ומכה אותו ואומר לו גדל הדא הוא דכתיב (שם)'''
    allrefs = inst.get_potential_refs(st)
    ref0 = (Ref('Exodus 11:9'), (1, 12), 0)
    ref1 = (Ref('Shulchan Arukh, Orach Chayim 100'), (41, 54), 0)
    ref2 = (u'(שם י)', (80, 86), 2)
    ref3 = ([u'Exodus', [None, 27]], (104, 116), 2)
    ref4 = (Ref('Berakhot 10b'), (140, 150), 0)
    ref5 = (u'(שם)', (194, 198), 2)
    assumed = [ref0, ref1, ref2, ref3, ref4, ref5]
    for i in range(len(allrefs)):
        assert allrefs[i][0] == assumed[i][0]


class TestGetUltimateRegex:

    def test_get_ultimate_regex1(self):
        test1 = u'(בראשית א:ב)'
        t = u'בראשית'
        n = library.get_schema_node(t, 'he')
        r = CitationFinder.get_ultimate_title_regex(t, n, 'he')
        m = re.search(r, test1)
        assert m.groupdict()[u"Title"] == u'בראשית'
        # assert m.groupdict()[u"Integer_Integer"] is not None
        assert m.groupdict()[u'a0'] == u'א' and m.groupdict()[u'a1'] == u'ב'

    def test_get_ultimate_regex2(self):
        test2 = u'(שם ג:ד)'
        r = CitationFinder.get_ultimate_title_regex(u'שם', None, 'he')
        m = re.search(r, test2)
        assert m.groupdict()[u"Title"] == u'שם'
        # assert m.groupdict()[u"Integer_Integer"] is not None
        assert m.groupdict()[u'a0'] == u'ג' and m.groupdict()[u'a1'] == u'ד'

    def test_get_ultimate_regex3(self):

        test3 = u'(ב"ר פרק ג משנה ד)'
        r = CitationFinder.get_ultimate_title_regex(u'ב"ר', None, 'he')
        m = re.search(r, test3)
        assert m.groupdict()[u"Title"] == u'ב"ר'
        # assert m.groupdict()[u"Perek_Mishnah"] is not None
        assert m.groupdict()[u'a0'] == u'ג' and m.groupdict()[u'a1'] == u'ד'

    def test_get_ultimate_regex4(self):

        test4 = u' בראשית (ג:ד)'
        t = u"בראשית"
        n = library.get_schema_node(t, 'he')
        r = CitationFinder.get_ultimate_title_regex(u'בראשית', n, 'he')
        m = re.search(r, test4)
        assert m.groupdict()[u"Title"] == u'בראשית'
        # assert m.groupdict()[u"Integer_Integer"] is not None
        assert m.groupdict()[u'a0'] == u'ג' and m.groupdict()[u'a1'] == u'ד'

    def test_get_ultimate_regex5(self):

        test5 = u' בראשית (שם:ד )'
        t = u'בראשית'
        n = library.get_schema_node(t, 'he')
        r = CitationFinder.get_ultimate_title_regex(t, n, 'he')
        m = re.search(r, test5)
        assert m.groupdict()[u"Title"] == u'בראשית'
        # assert m.groupdict()[u"Sham_Perek"] is not None
        assert m.groupdict()[u'a0'] == u'שם' and m.groupdict()[u'a1'] == u'ד'

    def test_get_ultimate_regex6(self):

        test6 = u' שבת (פח:)'
        t = u'שבת'
        n = library.get_schema_node(t, 'he')
        r = CitationFinder.get_ultimate_title_regex(t, n, 'he')
        m = re.search(r, test6)
        assert m.groupdict()[u"Title"] == u'שבת'
        # assert m.groupdict()[u'Talmud_Sham'] is not None
        assert m.groupdict()[u'a0'] == u'פח:'

    def test_get_ultimate_regex7(self):

        test7 = u'(( משנה ברכות (פרק ג משנה ה)'
        t = u'משנה ברכות'
        n = library.get_schema_node(t, 'he')
        r = CitationFinder.get_ultimate_title_regex(t, n, 'he')
        m = re.search(r, test7)
        assert m.groupdict()[u"Title"] == u'משנה ברכות' # or shouldn't this be simply ברכות?
        # assert m.groupdict()[u"Perek_Mishnah"] is not None
        assert m.groupdict()[u'a0'] == u'ג' and m.groupdict()[u'a1'] == u'ה'

    def test_get_ultimate_regex8(self):

        test8 = u'(בראשית שם)'
        t = u'בראשית'
        n = library.get_schema_node(t, 'he')
        r = CitationFinder.get_ultimate_title_regex(t, n, 'he')
        m = re.search(r, test8)
        assert m.groupdict()[u"Title"] == u'בראשית'
        # assert m.groupdict()[u"Sham_Perek"] is not None
        assert m.groupdict()[u'a0'] == u'שם'

    def test_get_ultimate_regex9(self):

        test9 = u'(משנה ברכות שם מ"ג)'
        t = u'משנה ברכות'
        n = library.get_schema_node(t, 'he')
        r = CitationFinder.get_ultimate_title_regex(t, n, 'he')
        m = re.search(r, test9)
        assert m.groupdict()[u"Title"] == u'משנה ברכות'
        # assert m.groupdict()[u"Sham_Perek"] is not None
        assert m.groupdict()[u'a0'] == u'שם' and m.groupdict()[u'a1'] == u'ג'

    def test_get_ultimate_regex10(self):

        test10 = u'(בראשית י)'
        t = u'בראשית'
        n = library.get_schema_node(t, 'he')
        r = CitationFinder.get_ultimate_title_regex(t, n, 'he')
        m = re.search(r, test10)
        assert m.groupdict()[u"Title"] == u'בראשית'
        # assert m.groupdict()[u"Sham_Perek"] is not None
        assert m.groupdict()[u'a0'] == u'י' and m.groupdict()[u'a1'] == None

    def test_get_ultimate_regex11(self):

        test11 = u'(שם י)'
        t = u'שם'
        n = library.get_schema_node(t, 'he')
        r = CitationFinder.get_ultimate_title_regex(t, n, 'he')
        m = re.search(r, test11)
        assert m.groupdict()[u"Title"] == u'שם'
        # assert m.groupdict()[u"Sham_Perek"] is not None
        assert m.groupdict()[u'a0'] == u'י' and m.groupdict()[u'a1'] == None

    def test_get_ultimate_regex12(self):

        test12 = u'(שם שם י)'
        t = u'שם'
        n = library.get_schema_node(t, 'he')
        r = CitationFinder.get_ultimate_title_regex(t, n, 'he')
        m = re.search(r, test12)
        assert m.groupdict()[u"Title"] == u'שם'
        # assert m.groupdict()[u"Sham_Perek"] is not None
        assert m.groupdict()[u'a0'] == u'שם' and m.groupdict()[u'a1'] == u'י'

    def test_get_ultimate_regex13(self):
        test13 = u"""ממלאים ממנו בשבת, [שם ועיין לקמן במצות עירובין בסוף הספר][שם ועיין לקמן במצות עירובין בסוף הספר] וגם אין מטלטלין """
        t = u'עירובין'
        n = library.get_schema_node(t, 'he')
        r = CitationFinder.get_ultimate_title_regex(t, n, 'he')
        m = re.search(r, test13)
        assert m is None
        t = u'שם'
        n = library.get_schema_node(t, 'he')
        r = CitationFinder.get_ultimate_title_regex(t, n, 'he')
        m = re.search(r, test13)
        assert m is None

    def test_get_ultimate_regex14(self):
        test14 = u'''(שם סימן שס"א סעי' ג)'''
        t = u'שם'
        n = library.get_schema_node(t, 'he')
        r = CitationFinder.get_ultimate_title_regex(t, n, 'he')
        m = re.search(r, test14)
        assert m.groupdict()[u"Title"] == u'שם'
        # assert m.groupdict()[u"Integer_Integer"] is not None
        assert m.groupdict()[u'a0'] == u'שס"א' and m.groupdict()[u'a1'] == u'ג'

    def test_get_ultimate_regex15(self):
        test15 = u'''(שם סי' ר)'''
        t = u'שם'
        n = library.get_schema_node(t, 'he')
        r = CitationFinder.get_ultimate_title_regex(t, n, 'he')
        m = re.search(r, test15)
        assert m.groupdict()[u"Title"] == u'שם'
        # assert m.groupdict()[u"Integer_Integer"] is not None
        assert m.groupdict()[u'a0'] == u'ר' and m.groupdict()[u'a1'] == None

    def test_get_ultimate_regex16(self):
        test15 = u'(משנה תורה, הלכות מגילה פ"א הלכה ד)'
        t = u'משנה תורה, הלכות מגילה'
        n = library.get_schema_node(t, 'he')
        r = CitationFinder.get_ultimate_title_regex(t, n, 'he')
        m = re.search(r, test15)
        assert m.groupdict()[u"Title"] == u'משנה תורה, הלכות מגילה'
        # assert m.groupdict()[u"Integer_Integer"] is not None
        assert m.groupdict()[u'a0'] == u'א' and m.groupdict()[u'a1'] == u'ד'




#todo: דסוכה (שם כ''ב)
#todo: test new class IndexIbidFinder
#todo: test ibidExceptions