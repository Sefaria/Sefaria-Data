# -*- coding: utf-8 -*-

import django
django.setup()
import pytest
from django.urls import *
from django.core import urlresolvers


from parse_aspaklaria import *


class Test_Source_methods(object):

    # source = Source(u'...והאודם מן האשה שממנו העור והבשר והדם, והרוח והנפש והנשמה משל הקב"ה ושלשתן שותפין בו. (כלאים לט א)', u'לקח טוב')

    # @classmethod
    # def setup_class(cls):
    #     cls.source = Source(u'...והאודם מן האשה שממנו העור והבשר והדם, והרוח והנפש והנשמה משל הקב"ה ושלשתן שותפין בו. (כלאים לט א)', u'לקח טוב')

    def test_index(self):
        # global parser
        # parser = Parser()
        # source = Source(u'...והאודם מן האשה שממנו העור והבשר והדם, והרוח והנפש והנשמה משל הקב"ה ושלשתן שותפין בו. (כלאים לט א)', u'לקח טוב')
        # source.extract_indx() # it is called inside the Source init
        assert True

    dict_input = [
                    # {'author':u'', 'raw_text':u'', 'ref':Ref('')},
                    {'author': u'כוזרי', 'raw_text': u'(מאמר ב נד)', 'ref': Ref('Sefer Kuzari 2 54')},

                    {'author': u'תנך', 'raw_text': u'(ראה גם אהרן, ביאת מקדש)', 'ref':None},
                    {'author': u'משך חכמה', 'raw_text': u'(ויקרא כו ד)', 'ref': Ref('Meshech Hochma, Bekhukotai')},
                    {'author': u'תלמוד ירושלמי', 'raw_text': u'(ברכות לח א)', 'ref': Ref('Jerusalem Talmud Berakhot 38a')},
                    {'author': u'משנה תורה', 'raw_text': u'(ביכורים ז יב, וראה שם עוד)', 'ref': Ref('Mishneh Torah, First Fruits and other Gifts to Priests Outside the Sanctuary 7:12')},
                    {'author': u'משנה תורה', 'raw_text': u'(טומאת אוכלין א א, וראה שם עוד)', 'ref': Ref('Mishneh Torah, Defilement of Foods 1:1')},
                    {'author':u'משך חכמה', 'raw_text':u'(ויקרא כו א)', 'ref':Ref(u'משך חכמה, בהר')},
                    {'author':u'אבן עזרא', 'raw_text':u'(דברים יא כז)', 'ref':Ref('Ibn_Ezra_on_Deuteronomy.11.27')},
                    {'author': u"ר' בחיי", 'raw_text': u'(שולחן של ארבע שער א)', 'ref': Ref('Shulchan Shel Arba, Introduction')},
                    {'author':u'תלמוד בבלי', 'raw_text':u'(מועד ח ב, וראה שם עוד)', 'ref':Ref('Moed Katan 8b')},
                    {'author':u'מהר"ל', 'raw_text':u'טקסט (דרך חיים א ה)', 'ref':Ref('Derech Chaim 1:5') },
                    {'author':u'מדרש רבה', 'raw_text':u'טקסט (בראשית כז ג)', 'ref':Ref('Bereishit Rabbah 27:3') },
                    {'author':u'רמב"ן', 'raw_text':u'(רמב"ן, בראשית יח יא)', 'ref':Ref('Ramban on Genesis 18:11') },
                    {'author':u'ילקוט שמעוני', 'raw_text':u'(משלי פרק א, תתקכט)', 'ref':Ref('Yalkut Shimoni on Nach 929:1-932:6') },
                    {'author':u'בעל הטורים', 'raw_text':u'(דברים טו טז)', 'ref':Ref('Kitzur Baal Haturim on Deuteronomy 15:16') },
                    {'author':u'זהר חדש', 'raw_text':u'(בראשית תו)', 'ref':Ref('Zohar Chadash, Bereshit 406') },
                    {'author':u'מדרש רבה', 'raw_text':u'(דברים ח ג)', 'ref':Ref('Devarim Rabbah 8:3') },
                    {'author':u'ילקוט שמעוני', 'raw_text':u'(מלכים ב פרק יח, רצו)', 'ref':Ref('Yalkut Shimoni on Nach 234:8-239:1') },
                    {'author':u'ילקוט שמעוני', 'raw_text':u'(דניאל תתרסה)', 'ref':Ref('Yalkut Shimoni on Nach 1065') },
                    {'author':u'מורה נבוכים', 'raw_text':u'(חלק ג)', 'ref':Ref('Guide for the Perplexed, Part 3') },
                    {'author':u'מורה נבוכים', 'raw_text':u'(חלק ג פרק א)', 'ref':Ref('Guide for the Perplexed, Part 3') },
                    {'author':u'מורה נבוכים', 'raw_text':u'(פתיחה)', 'ref':Ref('Guide for the Perplexed, Introduction, Prefatory Remarks') },
                    {'author':u'אלשיך', 'raw_text':u'(במדבר א ג)', 'ref':Ref('Alshich on Torah, Numbers 1:3') },
                    {'author':u'אלשיך', 'raw_text':u'(רות א יד)', 'ref':Ref('Enei Moshe on Ruth 1:14') },
                    {'author':u'משנה תורה', 'raw_text':u'(ערכין ג טו)', 'ref':Ref('Mishneh Torah, Appraisals and Devoted Property 3:15') },
                    {'author':u'משנה תורה', 'raw_text':u'(נזקי ממון ב ז, וראה שם עוד)', 'ref':Ref('Mishneh Torah, Damages to Property 2:7') },
                    {'author':u'תרגום יונתן', 'raw_text':u' (תהלים כב כא)', 'ref':Ref('Aramaic Targum to Psalms 22:21') },
                    {'author':u'הגר"א', 'raw_text':u' (בראשית כב כא)', 'ref':Ref('Aderet Eliyahu, Genesis 22:21') },
                    {'author':u'לקח טוב', 'raw_text':u'(בראשית יג ה)', 'ref':Ref('Midrash Lekach Tov, Genesis 13:5') },
                    {'author':u'של"ה', 'raw_text':u'(תורה שבכתב נח, בסופו)', 'ref':Ref('Shenei Luchot HaBerit, Torah Shebikhtav, Noach') },
                    {'author':u'של"ה', 'raw_text':u'(בעשרה מאמרות מאמר ב)', 'ref':Ref('Shenei Luchot HaBerit, Asara Maamarot, Second Maamar') },
                    {'author':u'של"ה', 'raw_text':u'(מסכת חולין, וראה שם עוד)', 'ref':Ref('Shenei Luchot HaBerit, Aseret HaDibrot, Chullin') },
                    {'author':u'דרשות הר"ן', 'raw_text':u'(דרוש ז)', 'ref':Ref('Darashos HaRan 7') },
                    {'author':u'שפת אמת', 'raw_text':u'(שמות יתרו תרנ"ב)', 'ref':Ref('Sefat Emet, Exodus, Yitro') },
                    {'author':u'שפת אמת', 'raw_text':u'(פורים תרל"ד)', 'ref':Ref('Sefat Emet, Exodus, For Purim') },
                    {'author':u"ר' ירוחם", 'raw_text':u'(דעת תורה במדבר עמוד קסג)', 'ref':None },
                    {'author':u'אברבנאל', 'raw_text':u'(יהושע ח ל)', 'ref':None },
                    {'author':u'ספרי', 'raw_text':u'(האזינו שיג)', 'ref':Ref('Sifrei Devarim 306-341') },
                    {'author':u'ילקוט שמעוני', 'raw_text':u'(ויקרא פרק יא, תקלו)', 'ref':Ref('Yalkut Shimoni on Torah 427:2-479:15')}#Ref('Yalkut Shimoni on Torah 536') }, # Ref('Yalkut Shimoni on Torah 427:2-479:15')
                ]

    def organize_test_input_list(self, dict_input, firsts=None, print_ref=None):
        input_list = []
        if firsts or print_ref:
            if isinstance(firsts, unicode):
                firsts = [firsts]
            if isinstance(print_ref, unicode):
                print_ref = [print_ref]
            dict_dict_input = dict([(e['raw_text'], e) for e in dict_input])
            start = []
            end = []
            for k,v in dict_dict_input.items():
                if print_ref and [pr for pr in print_ref if re.search(pr, v['raw_text'])]:
                    dict_dict_input[k]['assert_ref'] = False
                if v['author'] in firsts:
                    start.append(dict_dict_input[k])
                else:
                    end.append(dict_dict_input[k])
            dict_input = start+end
        for e in dict_input:
            if 'assert_ref' not in e.keys():
                e['assert_ref'] = True
            input_list.append((e['raw_text'], e['author'], e['ref'], e['assert_ref']))
        return input_list

    @pytest.mark.parametrize('raw_text, author, sefaria_ref, assert_ref', organize_test_input_list(dict_input, dict_input, [u'תנך'], []))
    def test_all(self, raw_text, author, sefaria_ref, assert_ref):
        r = Source(raw_text, author).ref
        if assert_ref:
            assert r == sefaria_ref
        else:
            print u'Ref algo returns:', r

    def get_input(text):
        refs = []
        p3 = re.compile(u'(Ref\(.*?\))')
        for match in re.finditer(p3, text):
            tuple = (match.group(1))
            refs.append(tuple)
        all = []
        p3 = re.compile(u'.*?Source\((.*?\).+?u.*?)\)')
        for match in re.finditer(p3, text):
            tuple = (match.group(1))
            all.append(tuple)
        input = zip(all, refs)
        for x in input:
            print u'(', x[0], u',', x[1], u'),'
        return


    def test_individual_source(self):
        source = Source(u'(ויקרא פרק יא, תקלו)', u'ילקוט שמעוני')
        #note: Sifrei parashot titles need to change and be sharedTitle
        # assert source.ref == Ref(u"Midrash Lekach Tov, Genesis 13:5")
        print "&&&&&&&", source.ref
        # assert source.ref == Ref(u"Sifrei Devarim 306-341") note: this is not שיג we will use the PM for this as well. the resoen is this ref is a mash of 2 diffrent alt structures.

    def test_get_ref_mishneh_torah(self):
        source = Source(u'(ברכות ב ז)', u'משנה תורה')
        assert source.ref == Ref(u'Mishneh Torah, Blessings 2:7')
        source = Source(u'(עבודת כוכבים פרק א ב והלאה)', u'משנה תורה')
        assert source.ref == Ref(u'Mishneh Torah, Foreign Worship and Customs of the Nations 1:2')
        source = Source(u'(נדרים יא ו, וראה שם עוד)', u'משנה תורה')
        assert source.ref == Ref(u'Mishneh Torah, Vows 11:6')

        # for these we need to look for parts of the alt titles. and should see where to put the alt_table. 2 parts that should go some where.
        source = Source(u'(גזילה ו יא)', u'משנה תורה')
        assert source.ref == Ref(u'Mishneh Torah, Robbery and Lost Property 6:11')
        source = Source(u'(תפילין פרק א יג)', u'משנה תורה')
        assert source.ref == Ref(u'Mishneh Torah, Tefillin, Mezuzah and the Torah Scroll 1:13')
        source = Source(u'(לולב פרק ז כולו)', u'משנה תורה')
        assert source.ref == Ref(u'Mishneh Torah, Shofar, Sukkah and Lulav 7')
        source = Source(u'(אבלות פרק א יא)', u'משנה תורה')
        assert source.ref == Ref(u'Mishneh Torah, Mourning 1:11')


class Test_Sham_Parsing(object):

    t = Topic(u'מילת ראש')
    source1 = Source(u"וישאלו - ה' עשה דרך שאלה ולא מתנה, כדי שירדפו אחריהם. דבר אחר, וישאלו - לשון מתנה, כמו שאל ממני ואתנה. רעהו - מלמד שאחרי המכות היו המצרים כרעים לישראל. כלי כסף - במקום שהניחו להם ישראל בתיהם ושדותיהם וכליהם שלא יכלו לשאת. (שם יא ב)", u'חזקוני')
    source2 = Source(u'ושאלה אשה - במתנה גמורה, כלי כסף - לכבוד החג שתחוגו לי במדבר. (שמות ג כב)', u'חזקוני')
    t.all_a_citations = [AuthorCit(u'חזקוני').sources.extend([source1, source2])]

    def test_sham_complex_comm(self):
        t = Topic(u'מילת ראש')
        # create Sources
        source1 = Source(u'ושאלה אשה - במתנה גמורה, כלי כסף - לכבוד החג שתחוגו לי במדבר. (שמות ג כב)', u'חזקוני')
        source2 = Source(
            u"וישאלו - ה' עשה דרך שאלה ולא מתנה, כדי שירדפו אחריהם. דבר אחר, וישאלו - לשון מתנה, כמו שאל ממני ואתנה. רעהו - מלמד שאחרי המכות היו המצרים כרעים לישראל. כלי כסף - במקום שהניחו להם ישראל בתיהם ושדותיהם וכליהם שלא יכלו לשאת. (שם יא ב)",
            u'חזקוני')
        source3 = Source(u'ואנוש - ותקיף. (ירמיה יז ט)', u'תרגום יונתן')
        source4 = Source(u'ואנוש - לשון חולי. (שם)', u'רש"י')
        source5 = Source(u'ואנוש - כואב ביגון, או בדאגה או במחשבה. (שם)', u'רד"ק')
        source6 = Source(u'אמר החבר: מבלי ספק שהיה שמור בלבבות בפתחא והקמ"ץ (מאמר ג לא)', u'כוזרי')
        source7 = Source(u'אמר הכוזרי: ...כי נראה מקביעות הנקוד והטעמים (שם לב)', u'כוזרי')

        # create AuthorCit objs respectively
        chzkuni = AuthorCit(u'חזקוני')
        rashi =AuthorCit(u'רש"י')
        ty = AuthorCit(u'תרגום יונתן')
        radak = AuthorCit(u'רד"ק')
        kuzari = AuthorCit(u'כוזרי')

        # add sources to AuthorCit
        chzkuni.sources.extend([source1, source2])
        ty.sources.extend([source3])
        rashi.sources.extend([source4])
        radak.sources.extend([source5])
        kuzari.sources.extend([source6, source7])

        # add AuthorCit to topic
        t.all_a_citations.append(chzkuni)
        t.all_a_citations.append(ty)
        t.all_a_citations.append(rashi)
        t.all_a_citations.append(radak)
        t.all_a_citations.append(kuzari)

        # parse
        parse_refs(t)
        t.parse_shams()

        # assert
        assert t.all_a_citations[0].sources[1].ref == Ref(u"Chizkuni, Exodus 11:2")
        assert t.all_a_citations[2].sources[0].ref == Ref(u"Rashi on Jeremiah 17:9")
        assert t.all_a_citations[3].sources[0].ref == Ref(u'Radak on Jeremiah 17:9')
        assert t.all_a_citations
    def test_get_parasha(self):
        ref = Ref(u'שמות כ')
        # parser = Parser()
        table = Parser.perek_parasha_table()
        assert convert_perk_parasha(ref, table) == u'פרשת יתרו'
        ref = Ref(u'דברים יז ה')
        # parser = Parser()
        table = Parser.perek_parasha_table()
        assert convert_perk_parasha(ref, table) == u'פרשת שופטים'
        ref = Ref(u'ויקרא א ג')
        # parser = Parser()
        table = Parser.perek_parasha_table()
        assert convert_perk_parasha(ref, table) == u'פרשת ויקרא'
    def test_dh_matcher(self):
        from linking_utilities.dibur_hamatchil_matcher import match_ref
        base_tokenizer = lambda x: x.split()
        base_text = Ref(u'גיטין ז').text('he')
        n = 100  # len(''.join(base_text.text).split())
        comments = [u'צריך @33 למימרינהו בניחותא.', u'מי שיש לו צעקת לגימא על חבירו ודומם שוכן בסנה עושה לו דין. ', u'@11הדבר @33 יצא מפי רבי אלעזר ונתנוהו לגניבה בקולר. ', u'א“ל @33 האלהים מדרבנן אלא חסדא שמך וחסדאין מילך. ', u'מאי @33 זאת לא זאת. ', u'''דרש @33 רב עוירא וכו' מ“ד כה אמר ה' אם שלמים וכן רבים וכו' אם רואה אדם שמזונותיו מצומצמין יעשה מהן צדקה וכ“ש כשהן מרובין וכו‘.''']
        results = match_ref(base_text, comments, base_tokenizer, prev_matched_results=None, dh_extract_method=lambda x: x,verbose=False, word_threshold=0.27,char_threshold=0.2,
              with_abbrev_matches=False,with_num_abbrevs=True,boundaryFlexibility=n,dh_split=None, rashi_filter=None, strict_boundaries=None, place_all=False,
              create_ranges=False, place_consecutively=False, daf_skips=2, rashi_skips=1, overall=2, lang="he")
        print results['matches']


class Test_By_Topic(object):

    def test_by_topic(self):
        topic_file_path = u"009_TET_test/tevila.html"
        parse_by_topic(topic_file_path)