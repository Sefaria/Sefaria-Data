# encoding=utf-8

import os
import pytest
from ShulchanArukh import *

def setup_module():
    Root.create_skeleton('test_document.xml')

def teardown_module():
    os.remove('test_document.xml')

def test_add_titles():
    root = Root('test_document.xml')
    base_text = root.get_base_text()
    base_text.add_titles('Shulchan Arukh', u'שולחן ערוך')

    assert unicode(root) == u'<root><base_text><en_title>Shulchan Arukh</en_title><he_title>שולחן ערוך</he_title>' \
                                u'</base_text><commentaries/></root>'

def test_add_commentary():
    root = Root('test_document.xml')
    commentaries = root.get_commentaries()
    shach = commentaries.add_commentary('Shach', u'ש"ך')

    assert isinstance(shach, Commentary)
    assert unicode(shach) == u'<commentary id="1"><en_title>Shach</en_title><he_title>ש"ך</he_title></commentary>'
    assert unicode(commentaries) == u'<commentaries>{}</commentaries>'.format(shach.Tag)
    assert unicode(root) == u'<root><base_text/>{}</root>'.format(unicode(commentaries.Tag))


class TestAddVolume(object):

    def test_add_volume(self):
        vol = 'some really interesting text'
        root = Root('test_document.xml')
        base_text = root.get_base_text()
        volume = base_text.add_volume(vol, 1)

        assert isinstance(volume, Volume)
        assert unicode(volume) == u'<volume num="1">some really interesting text</volume>'
        assert unicode(base_text) == u'<base_text>{}</base_text>'.format(unicode(volume))
        assert unicode(root) == u'<root>{}<commentaries/></root>'.format(unicode(base_text))

    def test_add_multiple_volumes(self):
        vol_a, vol_b, vol_c = 'first', 'second', 'third'
        root = Root('test_document.xml')
        base_text = root.get_base_text()
        v3 = base_text.add_volume(vol_c, 3)
        v1 = base_text.add_volume(vol_a, 1)
        v2 = base_text.add_volume(vol_b, 2)

        assert unicode(base_text) == u'<base_text>{}{}{}</base_text>'.format(unicode(v1), unicode(v2), unicode(v3))
        assert unicode(root) == u'<root>{}<commentaries/></root>'.format(unicode(base_text))

class TestMarkSimanim(object):

    def test_simple_mark(self):
        raw_text = u'<volume num="1">@00א\nסימן ראשון\n@00ב\nסימן שני</volume>'
        v = Volume(BeautifulSoup(raw_text, 'xml').volume)
        v.mark_simanim(u'@00([\u05d0-\u05ea])')

        assert len(v.get_child()) == 2
        assert unicode(v) == u'<volume num="1"><siman num="1">סימן ראשון\n</siman><siman num="2">סימן שני</siman></volume>'

    def test_out_of_order(self):
        raw_text = u'<volume num="1">@00ב\nסימן שני\n@00א\nסימן ראשון</volume>'
        v = Volume(BeautifulSoup(raw_text, 'xml').volume)
        v.mark_simanim(u'@00([\u05d0-\u05ea])')

        assert len(v.get_child()) == 2
        assert unicode(v) == u'<volume num="1"><siman num="1">סימן ראשון</siman><siman num="2">סימן שני\n</siman></volume>'

    def test_duplicate_siman(self):
        raw_text = u'<volume num="1">@00א\nסימן ראשון\n@00א\nסימן שני</volume>'
        v = Volume(BeautifulSoup(raw_text, 'xml').volume)
        with pytest.raises(DuplicateChildError):
            v.mark_simanim(u'@00([\u05d0-\u05ea])')

    def test_start_mark(self):
        raw_text = u'<volume num="1">some random stuff\nstart\n@00א\nסימן ראשון\n@00ב\nסימן שני</volume>'
        v = Volume(BeautifulSoup(raw_text, 'xml').volume)
        v.mark_simanim(u'@00([\u05d0-\u05ea])', start_mark=u'start')

        assert len(v.get_child()) == 2
        assert unicode(v) == u'<volume num="1"><siman num="1">סימן ראשון\n</siman><siman num="2">סימן שני</siman></volume>'

    def test_nonsense_before_first_mark(self):
        raw_text = u'<volume num="1">\n@00א\nסימן ראשון\n@00ב\nסימן שני</volume>'
        v = Volume(BeautifulSoup(raw_text, 'xml').volume)
        with pytest.raises(AssertionError):
            v.mark_simanim(u'@00([\u05d0-\u05ea])')

    def test_title(self):
        raw_text = u'<volume num="1">@11\nThe Title\n@00א\nסימן ראשון\n@00ב\nסימן שני</volume>'
        v = Volume(BeautifulSoup(raw_text, 'xml').volume)
        v.mark_simanim(u'@00([\u05d0-\u05ea])', specials={u'@11': {'name': 'title'}})

        assert len(v.get_child()) == 2
        assert unicode(v) == u'<volume num="1"><title found_after="0">The Title\n</title>' \
                             u'<siman num="1">סימן ראשון\n</siman><siman num="2">סימן שני</siman></volume>'

    def test_multi_line(self):
        raw_text = u'<volume num="1">@11\nSome\nlines\nof\ntext\n@12\n@00א\nסימן ראשון\n@00ב\nסימן שני</volume>'
        v = Volume(BeautifulSoup(raw_text, 'xml').volume)
        v.mark_simanim(u'@00([\u05d0-\u05ea])', specials={u'@11': {'name': 'intro', 'end': '@12'}})

        assert len(v.get_child()) == 2
        assert unicode(v) == u'<volume num="1"><intro found_after="0">Some\nlines\nof\ntext\n</intro>' \
                             u'<siman num="1">סימן ראשון\n</siman><siman num="2">סימן שני</siman></volume>'

    def test_between_segments(self):
        raw_text = u'<volume num="1">@00א\nסימן ראשון\n@11\nThe Title\n@00ב\nסימן שני</volume>'
        v = Volume(BeautifulSoup(raw_text, 'xml').volume)
        v.mark_simanim(u'@00([\u05d0-\u05ea])', specials={u'@11': {'name': 'title'}})

        assert len(v.get_child()) == 2
        assert unicode(v) == u'<volume num="1"><siman num="1">סימן ראשון\n</siman><title found_after="1">The Title\n' \
                             u'</title><siman num="2">סימן שני</siman></volume>'

    def test_multi_between_segments(self):
        raw_text = u'<volume num="1">@00א\nסימן ראשון\n@11\nSome\nlines\nof\ntext\n@12\n@00ב\nסימן שני</volume>'
        v = Volume(BeautifulSoup(raw_text, 'xml').volume)
        v.mark_simanim(u'@00([\u05d0-\u05ea])', specials={u'@11': {'name': 'intro', 'end': '@12'}})

        assert len(v.get_child()) == 2
        assert unicode(v) == u'<volume num="1"><siman num="1">סימן ראשון\n' \
                             u'</siman><intro found_after="1">Some\nlines\nof\ntext\n</intro>' \
                             u'<siman num="2">סימן שני</siman></volume>'

    def test_consecutive_specials(self):
        raw_text = u'<volume num="1">@00א\nסימן ראשון\n@11\nThe Title\n@33\nThe Intro\n@00ב\nסימן שני</volume>'
        v = Volume(BeautifulSoup(raw_text, 'xml').volume)
        v.mark_simanim(u'@00([\u05d0-\u05ea])', specials={u'@11': {'name': 'title'}, u'@33': {'name': 'intro'}})

        assert len(v.get_child()) == 2
        assert unicode(v) == u'<volume num="1"><siman num="1">סימן ראשון\n</siman><title found_after="1">The Title\n' \
                             u'</title><intro found_after="1">The Intro\n</intro><siman num="2">סימן שני</siman></volume>'

    def test_matches_two_specials(self):
        raw_text = u'<volume num="1">@00א\nסימן ראשון\n@11\nThe Title\n@1\nThe Intro\n@00ב\nסימן שני</volume>'
        v = Volume(BeautifulSoup(raw_text, 'xml').volume)
        with pytest.raises(AssertionError):
            v.mark_simanim(u'@00([\u05d0-\u05ea])', specials={u'@11': {'name': 'title'}, u'@1': {'name': 'intro'}})

    def test_special_at_end(self):
        raw_text = u'<volume num="1">@00א\nסימן ראשון\n@00ב\nסימן שני\n@11\nThe Title\n</volume>'
        v = Volume(BeautifulSoup(raw_text, 'xml').volume)
        v.mark_simanim(u'@00([\u05d0-\u05ea])', specials={u'@11': {'name': 'title'}})

        assert len(v.get_child()) == 2
        assert unicode(v) == u'<volume num="1"><siman num="1">סימן ראשון\n</siman><siman num="2">סימן שני\n</siman>' \
                             u'<title found_after="2">The Title\n</title></volume>'

    def test_multi_line_at_end(self):
        raw_text = u'<volume num="1">@00א\nסימן ראשון\n@00ב\nסימן שני\n@11\nThe\nmulti\nline\nTitle\n@12</volume>'
        v = Volume(BeautifulSoup(raw_text, 'xml').volume)
        v.mark_simanim(u'@00([\u05d0-\u05ea])', specials={u'@11': {'name': 'title', 'end': '@12'}})

        assert len(v.get_child()) == 2
        assert unicode(v) == u'<volume num="1"><siman num="1">סימן ראשון\n</siman><siman num="2">סימן שני\n</siman>' \
                             u'<title found_after="2">The\nmulti\nline\nTitle\n</title></volume>'

        # no end mark at end of file
        raw_text = u'<volume num="1">@00א\nסימן ראשון\n@00ב\nסימן שני\n@11\nThe\nmulti\nline\nTitle\n</volume>'
        v = Volume(BeautifulSoup(raw_text, 'xml').volume)
        v.mark_simanim(u'@00([\u05d0-\u05ea])', specials={u'@11': {'name': 'title', 'end': '@12'}})

        assert len(v.get_child()) == 2
        assert unicode(v) == u'<volume num="1"><siman num="1">סימן ראשון\n</siman><siman num="2">סימן שני\n</siman>' \
                             u'<title found_after="2">The\nmulti\nline\nTitle\n</title></volume>'

class TestTextFormatting(object):

    def test_no_special_formatting(self):
        raw_text = u'<seif>just some text</seif>'
        s = Seif(BeautifulSoup(raw_text, 'xml').seif)
        s.format_text('@33', '@34', 'ramah')
        assert unicode(s) == u'<seif><reg-text>just some text</reg-text></seif>'

    def test_simple_formatting(self):
        raw_text = u'<seif>some @33bold @34text</seif>'
        s = Seif(BeautifulSoup(raw_text, 'xml').seif)
        s.format_text('@33', '@34', 'b')
        assert unicode(s) == u'<seif><reg-text>some </reg-text><b>bold </b><reg-text>text</reg-text></seif>'

    def test_start_formatting(self):
        raw_text = u'<seif>@33bold text @34at the beginning</seif>'
        s = Seif(BeautifulSoup(raw_text, 'xml').seif)
        s.format_text('@33', '@34', 'b')
        assert unicode(s) == u'<seif><b>bold text </b><reg-text>at the beginning</reg-text></seif>'

    def test_end_formatting(self):
        raw_text = u'<seif>the end is @33marked bold</seif>'
        s = Seif(BeautifulSoup(raw_text, 'xml').seif)
        s.format_text('@33', '@34', 'b')
        assert unicode(s) == u'<seif><reg-text>the end is </reg-text><b>marked bold</b></seif>'

    def test_random_end_tag(self):
        raw_text = u'<seif>@34just some text</seif>'
        s = Seif(BeautifulSoup(raw_text, 'xml').seif)
        s.format_text('@33', '@34', 'b')
        assert unicode(s) == u'<seif><reg-text>just some text</reg-text></seif>'

    def test_double_start_tag(self):
        raw_text = u'<seif>@33just @33some text</seif>'
        s = Seif(BeautifulSoup(raw_text, 'xml').seif)
        with pytest.raises(AssertionError):
            s.format_text('@33', '@34', 'b')

    def test_interspersed(self):
        raw_text = u'<seif>@33just @34some @33text</seif>'
        s = Seif(BeautifulSoup(raw_text, 'xml').seif)
        s.format_text('@33', '@34', 'b')
        assert unicode(s) == u'<seif><b>just </b><reg-text>some </reg-text><b>text</b></seif>'

class TestXref(object):

    def test_single_mark(self):
        """
        This tests the basic functionality of marking the xrefs, as well as making sure the changes are making their way
        up the data tree.
        """
        basic_text = u'hello @33 world'
        full_text = u'<seif><reg-text>{}</reg-text></seif>'.format(basic_text)
        s = Seif(BeautifulSoup(full_text, 'xml').seif)
        for child in s.get_child():
            child.mark_references(0, 1, 1, '@33')

        assert len(s.get_child()) == 1
        for child in s.get_child():
            assert len(child.get_child()) == 1
        assert unicode(s) == u'<seif><reg-text>hello <xref id="b0-c1-si1-ord1">@33</xref> world</reg-text></seif>'

    def test_multiple(self):
        raw_text = u'<b>some @33 random @33 words @33 here</b>'
        b = TextElement(BeautifulSoup(raw_text, 'xml').find('b'))
        found = b.mark_references(0, 1, 1, '@33')

        assert found == 3
        assert len(b.get_child()) == 3
        assert unicode(b) == u'<b>some <xref id="b0-c1-si1-ord1">@33</xref> random <xref id="b0-c1-si1-ord2">@33</xref>' \
                             u' words <xref id="b0-c1-si1-ord3">@33</xref> here</b>'

    def test_group(self):
        raw_text = u'<b>some @33א random @33ג words</b>'
        b = TextElement(BeautifulSoup(raw_text, 'xml').find('b'))
        b.mark_references(0, 1, 1, u'@33([\u05d0-\u05da])', group=1)

        assert len(b.get_child()) == 2
        assert unicode(b) == u'<b>some <xref id="b0-c1-si1-ord1">@33א</xref> random ' \
                             u'<xref id="b0-c1-si1-ord3">@33ג</xref> words</b>'

    def test_found(self):
        raw_text = u'<b>some @33 random @33 words @33 here</b>'
        b = TextElement(BeautifulSoup(raw_text, 'xml').find('b'))
        b.mark_references(0, 1, 1, '@33', found=23)

        assert len(b.get_child()) == 3
        assert unicode(b) == u'<b>some <xref id="b0-c1-si1-ord24">@33</xref> random ' \
                             u'<xref id="b0-c1-si1-ord25">@33</xref> words <xref id="b0-c1-si1-ord26">@33</xref> here</b>'

    def test_other_xrefs(self):
        raw_text = u'<b>some @33 random <xref id="b0-c5-si1-ord15">@44</xref> words @33 here</b>'
        b = TextElement(BeautifulSoup(raw_text, 'xml').find('b'))
        b.mark_references(0, 1, 1, '@33')

        assert len(b.get_child()) == 3
        assert unicode(b) == u'<b>some <xref id="b0-c1-si1-ord1">@33</xref> random ' \
                             u'<xref id="b0-c5-si1-ord15">@44</xref> words <xref id="b0-c1-si1-ord2">@33</xref> here</b>'

    def test_match_old_xref(self):
        raw_text = u'<b>some @33 random <xref id="b0-c5-si1-ord15">@33</xref> words @33 here</b>'
        b = TextElement(BeautifulSoup(raw_text, 'xml').find('b'))
        with pytest.raises(AssertionError):
            b.mark_references(0, 1, 1, '@33')


