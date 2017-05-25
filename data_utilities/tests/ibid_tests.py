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


def test_ignore_book():
    tracker = simple_tracker
    ref1 = Ref('Genesis 1:2')
    tracker.registerRef(ref1)
    tracker.ignore_book_name_keys()
    tracker.resolve(u"שם")
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)
    st = u'''פסחים בלה בלה בלה (דף לב:) ואז כל מיני מילים (שם) פסחים (כב:) (שם) (בראשית א:יב)'''
    refs_resolved = inst.find_in_segment(st, lang='he', citing_only=False, replace=True) # note: this ind (Genesis) is erelavent to the st...
    #should use the tr. to see what is going on there... not in the st davka.
    pass #the method works, the test looks not so good... to actually modulo test this.


def test_ibid_dict():
    test_dict = IbidDict()
    test_dict['1'] = 1
    test_dict['2'] = 2
    test_dict['1'] = 10
    assert  test_dict.items() == [('2',2),('1',10)]


def test_ibid_find():
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)
    string = u'''וילך איש מבית לוי רבותינו אמרו שהלך אחר עצת בתו (סוטה יב:). את בלהה (בראשית לה כב),
     דבלים (הושע א ג), לכו ונמכרנו לישמעאלים (בראשית שם כז), לכו ונכהו בלשון (שם יח יח), לכו נא ונוכחה (ישעיה א יח).'''
    refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    assert refs == [Ref("Sotah 12b"), Ref("Genesis 35:22"), Ref(u"הושע א:ג"), Ref(u"בראשית לה:כז"), Ref(u"בראשית יח:יח"), Ref(u"ישעיהו א:יח")]


def test_ibid_find_2():
    ind = library.get_index("Genesis")
    inst = IndexIbidFinder(ind)
    string = u"""ממלאים ממנו בשבת, [שם ועיין לקמן במצות עירובין בסוף הספר][שם ועיין לקמן במצות עירובין בסוף הספר] וגם אין מטלטלין """
    refs, _, _ = inst.find_in_segment(string, lang='he', citing_only=False, replace=True)
    assert refs == []

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

        test4 = u'בראשית (ג:ד)'
        t = u"בראשית"
        n = library.get_schema_node(t, 'he')
        r = CitationFinder.get_ultimate_title_regex(u'בראשית', n, 'he')
        m = re.search(r, test4)
        assert m.groupdict()[u"Title"] == u'בראשית'
        # assert m.groupdict()[u"Integer_Integer"] is not None
        assert m.groupdict()[u'a0'] == u'ג' and m.groupdict()[u'a1'] == u'ד'

    def test_get_ultimate_regex5(self):

        test5 = u'בראשית (שם:ד)'
        t = u'בראשית'
        n = library.get_schema_node(t, 'he')
        r = CitationFinder.get_ultimate_title_regex(t, n, 'he')
        m = re.search(r, test5)
        assert m.groupdict()[u"Title"] == u'בראשית'
        # assert m.groupdict()[u"Sham_Perek"] is not None
        assert m.groupdict()[u'a0'] == u'שם' and m.groupdict()[u'a1'] == u'ד'

    def test_get_ultimate_regex6(self):

        test6 = u'שבת (פח:)'
        t = u'שבת'
        n = library.get_schema_node(t, 'he')
        r = CitationFinder.get_ultimate_title_regex(t, n, 'he')
        m = re.search(r, test6)
        assert m.groupdict()[u"Title"] == u'שבת'
        # assert m.groupdict()[u'Talmud_Sham'] is not None
        assert m.groupdict()[u'a0'] == u'פח:'

    def test_get_ultimate_regex7(self):

        test7 = u'((משנה ברכות (פרק ג משנה ה)'
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
        # test13 = u"""[שם ועיין לקמן במצות עירובין בסוף הספר] """
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

    def test_smg(self):
        st = '''
א מצות עשה לעשות (א) בנגעי בתים כמשפט הכתוב בפרש׳ שנ׳ כי תבאו אל ארץ כנען אשר אני נותן לכם לאחוזה ונתתי נגע צרעת בבית ארץ אחוזתכם. ובא אשר לו הבית והגיד לכהן לאמר כנגע נראה לי בבית. וצוה הכהן ופנו את הבית בטרם יבא הכהן לראות את הנגע ולא יטמא כל אשר בבית ואחר כך יבא הכהן לראות את הבית. וראה את הנגע והנה הנגע בקירות הבית שקערורות ירקרקות או אדמדמות ומראיהן שפל מן הקיר. ויצא הכהן מן הבית אל פתח הבית והסגיר את הבית שבעת ימים. ושב הכהן ביום השביעי וראה והנה פשה הנגע בקירות הבית. וצוה הכהן וחלצו את האבנים אשר בהן הנגע והשליכו אתהן אל מחוץ לעיר אל מקום טמא. ואת הבית יקציע מבית סביב ושפכו את העפר אשר הקצו אל מחוץ לעיר אל מקום טמא. ולקחו אבנים אחרות והביאו אל תחת האבנים ועפר אחר יקח וטח את הבית ואם ישוב הנגע ופרח בבית אחר חלץ את האבנים ואחרי הקצות את הבית ואחרי הטוח. ובא הכהן וראה והנה פשה הנגע בבית צרעת ממארת היא בבית טמא הוא. ונתץ את הבית את אבניו ואת עציו ואת כל עפר הבית והוציא אל מחוץ לעיר אל מקום טמא. והבא אל הבית כל ימי הסגיר אותו יטמא עד הערב. והשוכב בבית יכבס בגדיו והאוכל בבית יכבס בגדיו. ואם בא יבא הכהן וראה והנה לא פשה הנגע בבית אחרי הטוח את הבית וטהר הכהן את הבית כי נרפא הנגע. ולקח לחטא את הבית שתי צפורים וגו׳. ותניא בת״כ [פרשת מצורע פ״ג ומביאה בפ״ק דיומא דף י״ב קצת בפרק המגרש דף פ״ב] אחוזה מטמאה בנגעים ואין ירושלים מטמאה בנגעים שלא נתחלקה לשבטים. ר׳ ישמעאל אומר אחוזתכם מטמאה בנגעי׳ ואין אחוזת גוים מטמאה בנגעי׳ וכשם שאין אחוזתם מטמאה בנגעים כך אין בגדיהם וגופם מטמא בנגעים. שנינו במס׳ נגעים בפ׳ י״ב כיצד ראיית נגע הבית בא אשר לו הבית והגיד לכהן לאמר כנגע נראה לי בבית ואפילו ת״ח ויודע שהוא נגע ודאי לא יגזור ויאמר נגע נראה לי בבית. וצוה הכהן ופנו את הבית אפי׳ חבילי עצים ואפי׳ חבילי קנים דברי רבי יהודא רבי מאיר אומר וכי מה מטמא לו אם תאמר כלי עציו ובגדיו ומתכותיו מטבלין והן טהורים על מה חסתה תורה על פכו ועל חרסו שאין להן טהרה במקוה אם כך חסה תורה על ממונן של רשעים קל וחומר על ממונם של צדיקים ואחר כך יבא הכהן לראות את הבית. [בת״כ דלעיל ובפ״ב דנגעים] ובית אפל אין פותחין בו חלונות לראות את נגעו שנאמ׳ כנגע נראה לי ולא לו ולנכרי׳ וראה את הנגע והנה הנגע בקירות הבית ותנן [בפ׳ י״ב דנגעים] ר׳ עקיבא אומר שיעורו שיראה כשני גריסין על שתי אבנים לא על אבן אחת רוחבו כגריס שקערורות שוקעות במראיהן ירקרקות או אדמדמות ירוק שבירוקין אדום שבאדומין. ומראיהן שפל מן הקיר ולא ממשן. ע״כ בתורת כהנים [בפרק הנזכר] שנינו במשנה [דלעיל] אינו הולך לא לתוך ביתו ומסגיר ולא עומד בתוך הבית שהנגע בתוכו ומסגיר אלא עומד פתח הבית שהנגע בתוכו ומסגיר שנאמר ויצא הכהן מן הבית אל פתח הבית וגו׳. שנינו שם [בפ׳ י״ג דף מ״ד ועניין הי״ג ימים שכתב בפ״ג דף ל״ח] הכהה בסוף שבוע ראשון או שהלך לו קולפו והוא טהור פי׳ קולפו שיקלף מקום הנגע בלבד. הפשה בראשון חולץ וקוצה אף הטיח שסביב אבני הנגע. הקצות כמו אשר קצצו וכן יקציע מעניין זה ואחר כך טח ונותן לו שבוע בין הכל י״ג יום שיום השביעי עולה לכאן ולכאן וכן בכל שני הסגירות שבנגעי׳ בת״כ דלעיל פ״ד ור״ש הביאה בפי׳ משנה פ׳ י״ב דלעיל] ומניין שנותן לו שבוע שנאמר אחר וטח את הבית ואם ישוב הנגע ופרח בבית ונא׳ למעלה ושב הכהן ביום השביעי מה שיבה האמורה למעלה בסוף שבוע אף שיבה זו כן ולא הפושה בראשון בלבד נותן לו שבוע אלא אפי׳ מצאו שעמד בעיניו בראשון ולא פשה מסגיר שבוע שני כאשר יתבאר. נחזור לסדר המקרא ואם ישוב הנגע ופרח בבית אחר חלץ וגו׳ ובא הכהן וראה והנה פשה וגו׳ ונתץ את הבית לשון המשנה [דלעיל] על זה חזר ינתץ לא חזר טעון צפרים ותניא בת״כ [בפ׳ הנזכר ובפי׳ ר״ש דלעיל] יכול יהא מקרא זה כמשמעו שלא יהא החוזר טמא אלא אם כן פשה נא׳ צרעת ממארת בבתים ונאמר צרעת ממארת בבגדים מה בגדים טימא החוזר אע״פ שלא פשה אף הבתים כן הא למדת שפשה האמור כאן אין זה מקומו וסדר המצוה הוא ואם ישוב הנגע ונתץ את הבית ואע״פ שלא פשה. אם כן למה בא המקרא הזה ובא הכהן וראה והנה פשה בא ללמד על העומד בעיניו בשבוע ראשון שמסגירו שבוע שני בא בסוף שבוע שני שהוא יום י״ג ומצאו שפשה מה יעשה לו יכול ינתץ מיד כמו שסמך לו ונתץ ת״ל ובא הכהן וראה והנה פשה ונאמר למעלה ושב הכהן ביום השביעי וראה והנה פשה ושיבה וביאה הכל ענין אחד הוא מה פשה האמורה בשיבה חולץ וקוצה וטח ונותן לו שבוע אף פשה האמורה בביאה חולץ וקוצה וטח ונותן לו שבוע להסגירו כך תניא בת״כ [שם כל הסוגיא מו״ס] ולשון המשנה [דלעיל] על זה עומד בראשון ופשה בשני חולץ וקוצה וטח ונותן לו שבוע ולסוף השבוע אם חזר הנגע ינתץ לא חזר טעון צפרים. מקומו של מקרא זה הוא בין והאוכל בבית ובין אם בא יבא הכהן ודבר בפני עצמו הוא. סתם ולא פירש אלא בעל פה והמקרא של אחריו ואם בא יבא בא ללמדנו שאם. הנגע עמד בעיניו בראשון ובשני שחולץ וקוצה וטח ונותן לו שבוע ולסוף השבוע השלישי שהוא יום י״ט שהרי יום שביעי עולה לכאן ולכאן וכן יום י״ג עולה לכאן ולכאן אם חזר הנגע ינתץ ואם לא חזר טעון צפרים שאין בנגעים יותר משלשה הסגרות. ולשון המקרא על אופניו לפי עניין זה הוא ובא הכהן וראה והנה פשה בשני וכו׳ ואם בא יבא וראה והנה לא פשה בשני ביאות הללו הסמוכות זו לזו על פי המדרש משפט אחד להם כאשר ביארנו. ואחרי הטוח את הבית כלומר אחר שחולץ וקוצה וטח ונתן לו שבוע וטהר הכהן את הבית בצפרים יכול אפי׳ חזר הנגע ת״ל כי נרפא הנגע לא טיהרתי אלא הרפוי שלא חזר אבל אם חזר ינתץ ופשט המקרא לפי עניין זה כי כמו ואם כמו ואת כי שטית וטהר את הבית אם נרפא הנגע. וגמרו של דבר אין נתיצה אלא בנגע החוזר אחר חליצה וקצוי וטיחה וטהרת הבית וטהרת האדם הכל מענין אחד כאשר בארנו למעלה [במ״ע ר״ל] אלא שהזאת הבית על המשקוף מבחוץ אף בנגעי בתים שנינו הפסיון הסמוך בכל שהו והרחוק כגריס והחוזר כשני גריסין ופירושו כאשר ביארנו למעלה [במ״ע רל״ח] תניא בת״כ [שם רפ״ד ור״ש מביאה בפי׳ פ׳ י״ב דנגעים]. וצוה וחלצו הצווי בכהן והחליצה בכל אדם. וחלצו מלמד שאם היה כותל בינו ובין חבירו שניהן חולצין שניהן קוצצין את העפר שניהם מביאין אבנים אחרות מכאן אמרו אוי לרשע או לשכנו. אבל בעל הבית לבדו מביא את העפר [שם] שנאמר ועפר יקח וטח את הבית אין חבירו מטפל עמו בטיחה. [שם] כשהוא אומר אבנים אחרות ועפר אחר מלמד שאינו נוטל אבנים ועפר מצד זה ונותן לצד זה ואינו טח בסיד אלא בעפר. וכשהוא אומר אל תחת האבנים מלמד שלא יתן אבן אחת תחת שתים ולא שתים תחת אחת. עוד דורש מכאן [בתחילת ת״כ בברייתא דר׳ ישמעאל כן בפ׳ י״ב דנגעים] שאין הבית מטמא בנגעים עד שיהו ב׳ אבנים ועצים ועפר. ובית סתם הנזכר בתחלת הפרשה הוא דבר הלמד מסופו. תניא בת״כ [ספ״ד דלעיל וכן בפ׳ י״ג דנגעים ובפ׳ מצות חליצה דף ק״ג] צרעת ממארת היא בבית טמא הוא. טמא מה ת״ל וכי טהור היה אלא לפי שמצינו בבית המוסגר שאינו מטמא אלא מתוכו שנא׳ והבא אל הבית כל ימי הסגיר אותו וגו׳ יכול אף המוחלט כן ת״ל טמא הוסיף לו טומאה על טומאתו שיהא כולו טמא ויטמא בין מתוכו בין מאחוריו [כך משמע בפרק י״ג דנגעים ובת״כ סוף פרשה תזריע ולעיל בסוף סי׳ רל״ח הביאו ע״ש] דין אבן המנוגעת ועצים ועפר כמצורע לכל דבר לטמא בביאה ובמשכב ובמושב. [בת״כ שם פ״ד ובתו׳ ס׳ פ״ז דנגעים] ויתרין עליו שמשתלחין חוץ לעיר אע״פ שאינה מוקפת חומה. תניא בת״כ [שם פ״ה] והבא אל הבית כשיכנס ראשו ורובו וצריך להתישב בעניין שבארנו באהלות לעיל במ״ע רל״א] והבא אל האהל אפילו משהו. ובפ״ב דשבועות דף י״ז] דורש מכאן טהור שנכנס לבית המנוגע דרך אחוריו אפי׳ נכנס כולו חוץ מחוטמו טהור שדרך ביאה אסרה תורה ומטעם זה פוטר שם טמא שנכנס להיכל דרך גגין [בת״כ דלעיל ובפי׳ ר״ש פ׳ י״ג דנגעים] כל ימי הסגיר אותו ולא ימים שקלף את נגעו יכול שאני מוציא את המוחלט שקלף את נגעו ת״ל כל ימי. יטמא עד הערב מלמד שאין מטמא בגדים יכול אפי׳ שהה כדי אכילת פרס ת״ל והאוכל בבית יכבס בגדיו אין לי אלא אוכל שוכב מניין ת״ל והשוכב בבית יכבס בגדיו לא אוכל ולא שוכב מניין ת״ל יכבס יכבס ריבה אם כן למה נאמר אוכל ושוכב ליתן שיעור לשוכב כאוכל ואחד השוכב או עומד אם שהה כדי אכילת פרס נטמאו בגדיו. שנינו במס׳ נגעים פי״ג מי שנכנס לבית המנוגע וכליו על כתיפיו וסנדליו וטבעותיו בידיו הוא והם טמאים מיד פי׳ שאף בהן אני קורא והבא אל הבית. הי׳ לבוש כליו וסנדליו ברגליו וטבעותיו בידיו הוא טמא מיד והם שבטלין אצל גופו אינם מטמאין אלא מגופו לפיכך הם טהורים עד שישהא בכדי אכילת פרס פת חיטין ולא פת שעורין מיסב ואכלה בלתן וכל השיעורין הל״מ [כדאיתא בפ״ק דסוכה דף ה׳] יש במד׳ ובתוספתא דנגעים [פ״י ור״ש הביאה בפי׳ פ׳ י״ב דנגעים] שהמספר לשון הרע באין נגעי׳ בביתו להוכיחו שיעשה תשו׳ אם עשה תשובה יטהר הבית ואם לא עשה תשובה ינתץ. ואם בכל זה לא שב באין נגעי׳ בכלי העור שלו שהוא יושב עליהם ומשתמש בהם אם עשה תשובה יטהרו ואם לאו ישרפו. ואם בכל זאת לא שב באין נגעים על בגדי׳ שהוא לובש אם עשה תשובה יטהרו ואם לאו ישרפו. ואם בכל זאת לא שב באין נגעים על גופו אם עשה תשובה יתרפא ואם לאו יהא מוחלט ובדד ישב. ותניא בת״כ [פ״ג] שיאמר לו הכהן דברי כיבושים בני אין הנגעים באין אלא על לשון הרע שכן מצינו במרים שלא נענשה אלא על לשון הרע שנאמ׳ השמר בנגע צרעת וגו׳ וסמיך ליה זכור אשר עשה ה׳ למרי׳ וכי מה עניין זה לזה אלא מלמד שלא נענשה אלא על לשון הרע והלא דברים ק״ו ומה מרים שדברה שלא בפניו של משה כך המדבר בגנותו של חבירו בפניו על אחת כמה וכמה. ר״ש בן אלעזר אומר אף על גסות הרוח נגעי׳ באין שכך מצינו בעוזיה מלך יהודא שבאו נגעים עליו על כך שנא׳ ובחזקתו גבה לבו וגו׳ ויבא אל היכל ה׳ להקטיר וגו׳ וכבר בארנו בסמל״ת הלכות לשון הרע [בסי׳ י״ט] וכל זה גורם דרך חטאים ומושב לצים ועל זה אמר דוד אשרי האיש אשר לא הלך בעצת רשעים ובדרך חטאים לא עמד ובמושב לצים לא ישב כי אם בתורת ה׳ חפצו ובתורתו יהגה יומם ולילה והיה כעץ שתול על פלגי מים אשר פריו יתן בעתו ועלהו לא יבול וכל אשר יעשה יצליח:'''
        node = library.get_index('Sefer Mitzvot Gadol').nodes
        CitationFinder.get_sham_ref_with_node(st, node, lang='he')
#todo: דסוכה (שם כ''ב)
#todo: test new class IndexIbidFinder
#todo: test ibidExceptions