# -*- coding: utf-8 -*-

import pytest

from sefaria.model import *
from sefaria.helper.splice import SegmentSplicer, SegmentMap, SectionSplicer, BlankSegment


def test_splice_mode_equivalence():
    n = SegmentSplicer().splice_next_into_this(Ref("Shabbat 45b:11"))
    assert n == SegmentSplicer().splice_this_into_next(Ref("Shabbat 45b:11"))
    assert n == SegmentSplicer().splice_prev_into_this(Ref("Shabbat 45b:12"))
    assert n == SegmentSplicer().splice_this_into_prev(Ref("Shabbat 45b:12"))


def test_join_rewrite():
    n = SegmentSplicer().splice_next_into_this(Ref("Shabbat 45b:11"))
    assert n._needs_rewrite(Ref("Shabbat 45b:15"))
    assert n._needs_rewrite(Ref("Shabbat 45b:12"))
    assert not n._needs_rewrite(Ref("Shabbat 45b:9"))
    assert not n._needs_rewrite(Ref("Shabbat 45b:11"))
    assert not n._needs_rewrite(Ref("Shabbat 45b"))
    assert not n._needs_rewrite(Ref("Shabbat 44b:11"))
    assert not n._needs_rewrite(Ref("Shabbat 46b:11"))

    assert not n._needs_rewrite(Ref("Rif Shabbat 45b:15"))

    assert n._needs_rewrite(Ref("Rashi on Shabbat 45b:15"), commentary=True)
    assert n._needs_rewrite(Ref("Rashi on Shabbat 45b:12"), commentary=True)
    assert n._needs_rewrite(Ref("Rashi on Shabbat 45b:15:2"), commentary=True)
    assert n._needs_rewrite(Ref("Rashi on Shabbat 45b:12:1"), commentary=True)
    assert not n._needs_rewrite(Ref("Rashi on Shabbat 45b:9"), commentary=True)
    assert not n._needs_rewrite(Ref("Rashi on Shabbat 45b:11"), commentary=True)
    assert not n._needs_rewrite(Ref("Rashi on Shabbat 45b"), commentary=True)
    assert not n._needs_rewrite(Ref("Rashi on Shabbat 44b:11"), commentary=True)
    assert not n._needs_rewrite(Ref("Rashi on Shabbat 46b:11"), commentary=True)

    assert n._rewrite(Ref("Shabbat 45b:15")) == Ref("Shabbat 45b:14")
    assert n._rewrite(Ref("Shabbat 45b:12")) == Ref("Shabbat 45b:11")

    assert n._rewrite(Ref("Rashi on Shabbat 45b:15:1"), commentary=True) == Ref("Rashi on Shabbat 45b:14:1")
    assert n._rewrite(Ref("Rashi on Shabbat 45b:15"), commentary=True) == Ref("Rashi on Shabbat 45b:14")
    assert n._rewrite(Ref("Rashi on Shabbat 45b:12:1"), commentary=True) == Ref("Rashi on Shabbat 45b:11:2")  # There's already one comment on 11


def test_page_spanning_rewrite():
    n = SegmentSplicer().splice_this_into_next(Ref("Meilah 19b:1"))
    assert n._needs_rewrite(Ref("Meilah 19b:41-20a:5"))
    assert n._rewrite(Ref("Meilah 19b:41-20a:5")) == Ref("Meilah 19b:40-20a:5")

    n = SegmentSplicer().insert_blank_segment_after(Ref("Meilah 19b:1"))
    assert n._needs_rewrite(Ref("Meilah 19b:41-20a:5"))
    assert n._rewrite(Ref("Meilah 19b:41-20a:5")) == Ref("Meilah 19b:42-20a:5")


def test_insert_rewrite():
    n = SegmentSplicer().insert_blank_segment_after(Ref("Shabbat 45b:11"))
    assert n._needs_rewrite(Ref("Shabbat 45b:15"))
    assert n._needs_rewrite(Ref("Shabbat 45b:12"))
    assert not n._needs_rewrite(Ref("Shabbat 45b:9"))
    assert not n._needs_rewrite(Ref("Shabbat 45b:11"))
    assert not n._needs_rewrite(Ref("Shabbat 45b"))
    assert not n._needs_rewrite(Ref("Shabbat 44b:11"))
    assert not n._needs_rewrite(Ref("Shabbat 46b:11"))

    assert not n._needs_rewrite(Ref("Rif Shabbat 45b:15"))

    assert n._needs_rewrite(Ref("Rashi on Shabbat 45b:15"), commentary=True)
    assert n._needs_rewrite(Ref("Rashi on Shabbat 45b:12"), commentary=True)
    assert n._needs_rewrite(Ref("Rashi on Shabbat 45b:15:2"), commentary=True)
    assert n._needs_rewrite(Ref("Rashi on Shabbat 45b:12:1"), commentary=True)
    assert not n._needs_rewrite(Ref("Rashi on Shabbat 45b:9"), commentary=True)
    assert not n._needs_rewrite(Ref("Rashi on Shabbat 45b:11"), commentary=True)
    assert not n._needs_rewrite(Ref("Rashi on Shabbat 45b"), commentary=True)
    assert not n._needs_rewrite(Ref("Rashi on Shabbat 44b:11"), commentary=True)
    assert not n._needs_rewrite(Ref("Rashi on Shabbat 46b:11"), commentary=True)

    assert n._rewrite(Ref("Shabbat 45b:15")) == Ref("Shabbat 45b:16")
    assert n._rewrite(Ref("Shabbat 45b:12")) == Ref("Shabbat 45b:13")

    assert n._rewrite(Ref("Rashi on Shabbat 45b:15:1"), commentary=True) == Ref("Rashi on Shabbat 45b:16:1")
    assert n._rewrite(Ref("Rashi on Shabbat 45b:15"), commentary=True) == Ref("Rashi on Shabbat 45b:16")
    assert n._rewrite(Ref("Rashi on Shabbat 45b:12:1"), commentary=True) == Ref("Rashi on Shabbat 45b:13:1")


def test_page_spanning_range():
    n = SegmentSplicer().insert_blank_segment_after(Ref("Chagigah 20b:13"))
    assert n._needs_rewrite(Ref("Chagigah 20b:14-21a:1"))
    assert n._rewrite(Ref("Chagigah 20b:14-21a:1")) == Ref("Chagigah 20b:15-21a:1")

    n = SegmentSplicer().splice_this_into_next(Ref("Chagigah 20b:13"))
    assert n._needs_rewrite(Ref("Chagigah 20b:14-21a:1"))
    assert n._rewrite(Ref("Chagigah 20b:14-21a:1")) == Ref("Chagigah 20b:13-21a:1")


@pytest.mark.deep
def test_report():
    n = SegmentSplicer().splice_next_into_this(Ref("Shabbat 25b:11"))
    n.report()


def test_es_cleanup():
    n = SegmentSplicer().splice_next_into_this(Ref("Shabbat 65a:11"))
    n._report = True
    n._clean_elastisearch()


@pytest.mark.deep
def test_sheet_cleanup():
    n = SegmentSplicer().splice_next_into_this(Ref("Shabbat 25b:11"))
    n._report = True
    n._find_sheets()
    n._clean_sheets()


@pytest.mark.deep
def test_insert():
    n = SegmentSplicer().insert_blank_segment_after(Ref("Shabbat 25b:11"))
    n.report()


class TestSegmentMap(object):
    def test_immediately_follows_without_words(self):
        first = SegmentMap(Ref("Shabbat 7a:23"), Ref("Shabbat 7a:25"))
        second = SegmentMap(Ref("Shabbat 7a:26"), Ref("Shabbat 7a:28"))
        third = SegmentMap(Ref("Shabbat 7a:29"), Ref("Shabbat 7a:29"))
        fourth = SegmentMap(Ref("Shabbat 7a:30"), Ref("Shabbat 7a:31"))
        assert second.immediately_follows(first)
        assert third.immediately_follows(second)
        assert fourth.immediately_follows(third)
        assert not fourth.immediately_follows(second)
        assert not fourth.immediately_follows(first)

    def test_immediately_follows_with_words(self):
        first = SegmentMap(Ref("Shabbat 7a:23"), Ref("Shabbat 7a:25"), end_word=3)
        second = SegmentMap(Ref("Shabbat 7a:25"), Ref("Shabbat 7a:28"), start_word=4, end_word=6)
        third = SegmentMap(Ref("Shabbat 7a:28"), Ref("Shabbat 7a:28"), start_word=7, end_word=12)
        fourth = SegmentMap(Ref("Shabbat 7a:28"), Ref("Shabbat 7a:31"), start_word=13)
        assert second.immediately_follows(first)
        assert third.immediately_follows(second)
        assert fourth.immediately_follows(third)
        assert not fourth.immediately_follows(second)
        assert not fourth.immediately_follows(first)

        gapped_third = SegmentMap(Ref("Shabbat 7a:28"), Ref("Shabbat 7a:28"), start_word=8, end_word=11)
        assert not gapped_third.immediately_follows(second)
        assert not fourth.immediately_follows(gapped_third)

        overlapping_third = SegmentMap(Ref("Shabbat 7a:28"), Ref("Shabbat 7a:28"), start_word=6, end_word=13)
        assert not overlapping_third.immediately_follows(second)
        assert not fourth.immediately_follows(overlapping_third)

class TestSegmentMapPartialVerse(object):
    """
    Test Segment-boundary->middle, middle-middle, and middle->segment-boundary with
    Shabbat 2b:16
המוציא מרשות לרשות חייב מי לא עסקינן דקא מעייל מרה"ר לרה"י וקא קרי לה הוצאה

    Complete segment
    Shabbat 2b:17
    וטעמא מאי כל עקירת חפץ ממקומו תנא הוצאה קרי לה

    Test Previous Segment-boundary->middle, and middle->next segment boundary with:
    Shabbat 2b:18
אמר רבינא
    Shabbat 2b:19
מתניתין נמי דיקא דקתני יציאות וקא מפרש הכנסה לאלתר
    Shabbat 2b:20
ש"מ


    Test middle->next middle with:
    Shabbat 2b:23
א"ל רב מתנה לאביי
    Shabbat 2b:24
הא תמני הויין
    Shabbat 2b:25
תרתי סרי הויין


    """
    def setup_method(self, method):
        splicer = SectionSplicer()
        splicer.set_section(Ref("Shabbat 2b"))
        splicer.set_base_version("Wikisource Talmud Bavli", "he")
        splicer.set_segment_map(Ref("Shabbat 2b:1"), Ref("Shabbat 2b:15"))                              # 0
        splicer.set_segment_map(Ref("Shabbat 2b:16"), Ref("Shabbat 2b:16"), end_word=3)                 # 1
        splicer.set_segment_map(Ref("Shabbat 2b:16"), Ref("Shabbat 2b:16"), start_word=4, end_word=8)   # 2
        splicer.set_segment_map(Ref("Shabbat 2b:16"), Ref("Shabbat 2b:16"), start_word=9, end_word=9)   # 3
        splicer.set_segment_map(Ref("Shabbat 2b:16"), Ref("Shabbat 2b:16"), start_word=10)              # 4
        splicer.set_segment_map(Ref("Shabbat 2b:17"), Ref("Shabbat 2b:17"))                             # 5
        splicer.set_segment_map(Ref("Shabbat 2b:18"), Ref("Shabbat 2b:19"), end_word=4)                 # 6
        splicer.set_segment_map(Ref("Shabbat 2b:19"), Ref("Shabbat 2b:20"), start_word=5)               # 7
        splicer.set_segment_map(Ref("Shabbat 2b:21"), Ref("Shabbat 2b:23"), end_word=2)                 # 8
        splicer.set_segment_map(Ref("Shabbat 2b:23"), Ref("Shabbat 2b:24"), start_word=3, end_word=2)   # 9
        splicer.set_segment_map(Ref("Shabbat 2b:24"), Ref("Shabbat 2b:29"), start_word=3)               # 10
        self.splicer = splicer

    def test_correct_text(self):
        tc = TextChunk(Ref("Shabbat 2b"), "he", "Wikisource Talmud Bavli")

        assert self.splicer.segment_maps[1].get_text(tc) == u"המוציא מרשות לרשות"
        assert self.splicer.segment_maps[2].get_text(tc) == u"חייב מי לא עסקינן דקא"
        assert self.splicer.segment_maps[3].get_text(tc) == u"מעייל"
        assert self.splicer.segment_maps[4].get_text(tc) == u'מרה"ר לרה"י וקא קרי לה הוצאה'

        assert self.splicer.segment_maps[5].get_text(tc) == u"וטעמא מאי כל עקירת חפץ ממקומו תנא הוצאה קרי לה"

        assert self.splicer.segment_maps[6].get_text(tc) == u"אמר רבינא מתניתין נמי דיקא דקתני"
        assert self.splicer.segment_maps[7].get_text(tc) == u'יציאות וקא מפרש הכנסה לאלתר ש"מ'

        assert self.splicer.segment_maps[9].get_text(tc) == u"מתנה לאביי הא תמני"


class TestSegmentMapAdjustment(object):
    def setup_method(self, method):
        splicer = SectionSplicer()
        splicer.set_section(Ref("Shabbat 2b"))
        splicer.set_base_version("Wikisource Talmud Bavli", "he")
        splicer.set_segment_map(Ref("Shabbat 2b:1"), Ref("Shabbat 2b:2"))
        splicer.set_segment_map(Ref("Shabbat 2b:3"), Ref("Shabbat 2b:5"))
        splicer.set_segment_map(Ref("Shabbat 2b:6"), Ref("Shabbat 2b:12"), end_word=2)
        splicer.set_segment_map(Ref("Shabbat 2b:12"), Ref("Shabbat 2b:15"), start_word=3, end_word=3)
        splicer.set_segment_map(Ref("Shabbat 2b:15"), Ref("Shabbat 2b:17"), start_word=4)
        splicer.set_segment_map(Ref("Shabbat 2b:18"), Ref("Shabbat 2b:18"), end_word=3)
        splicer.set_segment_map(Ref("Shabbat 2b:18"), Ref("Shabbat 2b:18"), start_word=4, end_word=8)
        splicer.set_segment_map(Ref("Shabbat 2b:18"), Ref("Shabbat 2b:29"), start_word=9)
        self.splicer = splicer

    def test_adjustment(self):
        assert len(self.splicer.adjusted_segment_maps)  # Did it derive the new ones?

        target = [
            SegmentMap(Ref("Shabbat 2b:1"), Ref("Shabbat 2b:2")),
            SegmentMap(Ref("Shabbat 2b:3"), Ref("Shabbat 2b:5")),
            SegmentMap(Ref("Shabbat 2b:6"), Ref("Shabbat 2b:12")),
            SegmentMap(Ref("Shabbat 2b:13"), Ref("Shabbat 2b:15")),
            SegmentMap(Ref("Shabbat 2b:16"), Ref("Shabbat 2b:17")),
            SegmentMap(Ref("Shabbat 2b:18"), Ref("Shabbat 2b:18")),
            BlankSegment(),
            SegmentMap(Ref("Shabbat 2b:19"), Ref("Shabbat 2b:29")),
        ]

        assert self.splicer.adjusted_segment_maps == target

    def test_get_segment_lookup_dictionary(self):
        d = self.splicer.get_segment_lookup_dictionary()
        assert d[Ref("Shabbat 2b:16")] == [Ref("Shabbat 2b:5")]
        assert d[Ref("Shabbat 2b:4")] == [Ref("Shabbat 2b:2")]
        assert d[Ref("Shabbat 2b:22")] == [Ref("Shabbat 2b:8")]
        assert d[Ref("Shabbat 2b:15")] == [Ref("Shabbat 2b:4"), Ref("Shabbat 2b:5")]
        assert d[Ref("Shabbat 2b:18")] == [Ref("Shabbat 2b:6"), Ref("Shabbat 2b:7"), Ref("Shabbat 2b:8")]
