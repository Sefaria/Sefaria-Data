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

class TestMarkChildren(object):

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
        assert unicode(v) == u'<volume num="1"><siman num="2">סימן שני\n</siman><siman num="1">סימן ראשון</siman></volume>'

    def test_out_of_order_enforced(self):
        raw_text = u'<volume num="1">@00ב\nסימן שני\n@00א\nסימן ראשון</volume>'
        v = Volume(BeautifulSoup(raw_text, 'xml').volume)
        v.mark_simanim(u'@00([\u05d0-\u05ea])', enforce_order=True)

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

    def test_cyclical_seifim(self):
        raw_text = u'<siman num="1">@00א\nsome text\n@00ב\nmore text\n@00ת\nfoo\n@00א\nbar</siman>'
        s = Siman(BeautifulSoup(raw_text, 'xml').siman)
        s.mark_cyclical_seifim(u'@00([\u05d0-\u05ea])')

        assert len(s.get_child()) == 4
        assert unicode(s) == u'<siman num="1"><seif label="1" num="1">some text\n</seif><seif label="2" num="2">more' \
                             u' text\n</seif><seif label="22" num="3">foo\n</seif><seif label="1" num="4">' \
                             u'bar</seif></siman>'

        rid_list = [u"b0-c1-si1-ord1;1", u"b0-c1-si1-ord2;2", u"b0-c1-si1-ord22;3", u"b0-c1-si1-ord1;4"]
        for seif, rid in zip(s.get_child(), rid_list):
            assert isinstance(seif, Seif)
            seif.set_rid(0, 1, 1, True)
            assert seif.rid == rid

class TestTextFormatting(object):

    def test_no_special_formatting(self):
        raw_text = u'<seif num="1">just some text</seif>'
        s = Seif(BeautifulSoup(raw_text, 'xml').seif)
        s.format_text('@33', '@34', 'ramah')
        assert unicode(s) == u'<seif num="1"><reg-text>just some text</reg-text></seif>'

    def test_simple_formatting(self):
        raw_text = u'<seif num="1">some @33bold @34text</seif>'
        s = Seif(BeautifulSoup(raw_text, 'xml').seif)
        s.format_text('@33', '@34', 'b')
        assert unicode(s) == u'<seif num="1"><reg-text>some </reg-text><b>bold </b><reg-text>text</reg-text></seif>'

    def test_start_formatting(self):
        raw_text = u'<seif num="1">@33bold text @34at the beginning</seif>'
        s = Seif(BeautifulSoup(raw_text, 'xml').seif)
        s.format_text('@33', '@34', 'b')
        assert unicode(s) == u'<seif num="1"><b>bold text </b><reg-text>at the beginning</reg-text></seif>'

    def test_end_formatting(self):
        raw_text = u'<seif num="1">the end is @33marked bold</seif>'
        s = Seif(BeautifulSoup(raw_text, 'xml').seif)
        s.format_text('@33', '@34', 'b')
        assert unicode(s) == u'<seif num="1"><reg-text>the end is </reg-text><b>marked bold</b></seif>'

    def test_random_end_tag(self):
        raw_text = u'<seif num="1">@34just some text</seif>'
        s = Seif(BeautifulSoup(raw_text, 'xml').seif)
        s.format_text('@33', '@34', 'b')
        assert unicode(s) == u'<seif num="1"><reg-text>just some text</reg-text></seif>'

    def test_double_start_tag(self):
        raw_text = u'<seif num="1">@33just @33some text</seif>'
        s = Seif(BeautifulSoup(raw_text, 'xml').seif)
        with pytest.raises(AssertionError):
            s.format_text('@33', '@34', 'b')

    def test_interspersed(self):
        raw_text = u'<seif num="1">@33just @34some @33text</seif>'
        s = Seif(BeautifulSoup(raw_text, 'xml').seif)
        s.format_text('@33', '@34', 'b')
        assert unicode(s) == u'<seif num="1"><b>just </b><reg-text>some </reg-text><b>text</b></seif>'

class TestXref(object):

    def test_single_mark(self):
        """
        This tests the basic functionality of marking the xrefs, as well as making sure the changes are making their way
        up the data tree.
        """
        basic_text = u'hello @33 world'
        full_text = u'<seif num="1"><reg-text>{}</reg-text></seif>'.format(basic_text)
        s = Seif(BeautifulSoup(full_text, 'xml').seif)
        for child in s.get_child():
            child.mark_references(0, 1, 1, '@33')

        assert len(s.get_child()) == 1
        for child in s.get_child():
            assert len(child.get_child()) == 1
        assert unicode(s) == u'<seif num="1"><reg-text>hello <xref id="b0-c1-si1-ord1">@33</xref> world</reg-text></seif>'

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

    def test_match_cyclical(self):
        raw_text = u'<seif num="1"><dh>some @33א random</dh><reg>random @33ב text @33א here</reg></seif>'
        s = Seif(BeautifulSoup(raw_text, 'xml').find('seif'))
        s.mark_references(0, 1, 1, u'@33([\u05d0-\u05ea])', group=1, cyclical=True)

        assert unicode(s) == u'<seif num="1"><dh>some <xref id="b0-c1-si1-ord1;1">@33א</xref> random</dh>' \
                             u'<reg>random <xref id="b0-c1-si1-ord2;2">@33ב</xref> text ' \
                             u'<xref id="b0-c1-si1-ord1;3">@33א</xref> here</reg></seif>'

    def test_straight_to_itag(self):
        raw_text = u'<seif num="1"><dh>some @33א random</dh><reg>random @33ב text @33ד here</reg></seif>'
        s = Seif(BeautifulSoup(raw_text, 'xml').find('seif'))
        s.convert_pattern_to_itag(u'author', ur'@\d{2}([\u05d0-\u05ea])', group=1)

        assert unicode(s) == u'<seif num="1"><dh>some <i data-commentator="author" data-order="1"/> random</dh>' \
                             u'<reg>random <i data-commentator="author" data-order="2"/> text ' \
                             u'<i data-commentator="author" data-order="4"/> here</reg></seif>'

    def test_marks_touching(self):
        raw_text = u'<seif num="1"><dh>some @33אrandom</dh><reg>random @33בtext @33דhere</reg></seif>'
        s = Seif(BeautifulSoup(raw_text, 'xml').find('seif'))
        s.convert_pattern_to_itag(u'author', ur'@\d{2}([\u05d0-\u05ea])', group=1)

        assert unicode(s) == u'<seif num="1"><dh>some <i data-commentator="author" data-order="1"/>random</dh>' \
                             u'<reg>random <i data-commentator="author" data-order="2"/>text ' \
                             u'<i data-commentator="author" data-order="4"/>here</reg></seif>'

def test_correct_marks():
    test_text = u'קצת @22א טקסט @22ט @22ג שאין @22ג @22ד @22ח לו\n @22ו משמעות'
    assert correct_marks(test_text, u'@22([\u05d0-\u05ea]{1,2})') == u'קצת @22א טקסט @22ב @22ג שאין @22ג @22ד @22ה לו\n @22ו משמעות'

    test_text = u'קצת @22ש טקסט @22כ ללא @22א משמעות'
    assert correct_marks(test_text, u'@22([\u05d0-\u05ea])', error_finder=out_of_order_he_letters) == u'קצת @22ש טקסט @22ת ללא @22א משמעות'

    test_text = u'קצת @22ת טקסט @22כ ללא @22ב משמעות'
    assert correct_marks(test_text, u'@22([\u05d0-\u05ea])',
                         error_finder=out_of_order_he_letters) == u'קצת @22ת טקסט @22א ללא @22ב משמעות'

    test_text = u'קצת @22א טקסט @22כ ללא @22ג משמעות'
    assert correct_marks(test_text, u'@22([\u05d0-\u05ea])',
                         error_finder=out_of_order_he_letters) == u'קצת @22א טקסט @22ב ללא @22ג משמעות'

def test_validate_double_refs():
    test_text = u'<siman num="1"><seif num="1">foo @22א bar @22א</seif></siman>'
    siman = Siman(BeautifulSoup(test_text, 'xml').find('siman'))
    assert not siman.validate_references(u'@22([\u05d0-\u05ea])', u'@22')

class TestCommentStore(object):

    def test_populate_comment_store(self):
        """
        Make sure the code properly passes down the entire tree
        """
        root = Root('test_document.xml')
        base_text = root.get_base_text()
        base_text.add_titles('Shulchan Arukh', u'שולחן ערוך')
        commentaries = root.get_commentaries()
        shach = commentaries.add_commentary('Shach', u'ש"ך')

        base_volume = u'<siman num="1"><seif num="1"><b>' \
                      u'some <xref id="b0-c1-s1-ord1"/> text</b></seif></siman>'
        shach_volume =  u'<siman num="1"><seif num="1" rid="b0-c1-s1-ord1"></seif><b>' \
                      u'some text</b></siman>'
        base_text.add_volume(base_volume, 1)
        shach.add_volume(shach_volume, 1)
        root.populate_comment_store()

        comment_store = CommentStore()
        assert comment_store.get("b0-c1-s1-ord1") is not None
        assert comment_store["b0-c1-s1-ord1"] == {
            'base_title': 'Shulchan Arukh',
            'siman': 1,
            'seif': [1],
            'commentator_title': 'Shach',
            'commentator_seif': 1,
            'commentator_siman': 1
        }
        comment_store.clear()

    def test_set_rid(self):
        root = Root('test_document.xml')
        base_text = root.get_base_text()
        base_text.add_titles('Shulchan Arukh', u'שולחן ערוך')
        commentaries = root.get_commentaries()
        shach = commentaries.add_commentary('Shach', u'ש"ך')

        volume_text = u'<siman num="1"><seif num="3"><b>some text</b></seif></siman>'
        volume = shach.add_volume(volume_text, 1)
        volume.set_rid_on_seifim()

        assert unicode(volume) == u'<volume num="1"><siman num="1"><seif num="3" rid="b0-c1-si1-ord3">' \
                                  u'<b>some text</b></seif></siman></volume>'

    def test_duplicate_xref(self):
        first_xref = Xref(BeautifulSoup('<xref id="abcd"/>', 'xml').find('xref'))
        first_xref.load_xrefs_to_commentstore('a', 1, 1)
        second_xref = Xref(BeautifulSoup('<xref id="abcd"/>', 'xml').find('xref'))
        second_xref.load_xrefs_to_commentstore('a', 1, 1)

        comment_store = CommentStore()
        assert comment_store['abcd'] == {
            'base_title': 'a',
            'siman': 1,
            'seif': [1]
        }

        third_xref = Xref(BeautifulSoup('<xref id="abcd"/>', 'xml').find('xref'))
        third_xref.load_xrefs_to_commentstore('a', 1, 2)
        assert comment_store['abcd'] == {
            'base_title': 'a',
            'siman': 1,
            'seif': [1,2]
        }
        CommentStore().clear()

    def test_no_matching_xref(self):
        seif = Seif(BeautifulSoup(u'<siman num="1" rid="abcd"/>', 'xml').find('siman'))
        with pytest.raises(MissingCommentError):
            seif.load_comments_to_commentstore('a', 1)
        CommentStore().clear()

    def test_duplicate_comment(self):
        Xref(BeautifulSoup('<xref id="abcd"/>', 'xml').find('xref')).load_xrefs_to_commentstore('a', 1, 1)
        Seif(BeautifulSoup(u'<siman num="1" rid="abcd"/>', 'xml').find('siman')).load_comments_to_commentstore('a', 1)
        with pytest.raises(DuplicateCommentError):
            Seif(BeautifulSoup(u'<siman num="2" rid="abcd"/>', 'xml').find('siman')).load_comments_to_commentstore('a', 1)
        CommentStore().clear()

    def test_cyclical_refs(self):
        c = CommentStore()
        c.clear()

        base_text = u'<seif num="1"><dh>some @33א random</dh><reg>random @33ת text @33א here</reg></seif>'
        commentary_text = u'<siman num="1">@00א\nsome text\n@00ת\nfoo\n@00א\nbar</siman>'

        base_seif = Seif(BeautifulSoup(base_text, 'xml').seif)
        base_seif.mark_references(0, 1, 1, u'@33([\u05d0-\u05ea])', group=1, cyclical=True)
        base_seif.load_xrefs_to_commentstore('foo', 1)

        commentary_siman = Siman(BeautifulSoup(commentary_text, 'xml').siman)
        commentary_siman.mark_cyclical_seifim(u'@00([\u05d0-\u05ea])')
        commentary_siman.set_rid_on_seifim(0, 1, True)
        commentary_siman.load_comments_to_commentstore('foo')

        assert len(c.keys()) == 3
        required_fields = ['base_title', 'siman', 'seif', 'commentator_title', 'commentator_siman', 'commentator_seif']
        for i in c:
            assert all([c[i].get(field) is not None for field in required_fields])

        c.clear()

