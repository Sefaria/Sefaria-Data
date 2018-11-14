# encoding=utf-8

"""
The data files for this project contain data which is under copyright and could not be shared to github.
For more details, please contact the developers.
The data from this project which has been uploaded to Sefaria  is released under CC-BY-NC


Parsing tips:
Run this regex to simplify the classes:
u'\s?(Para|Char)Override-\d{1,2}'

LME = Likutei Moharan English
LMH = Likutei Moharan Hebrew
LMN = Likutei Moharan Note

LME-FootRef -> These are the references to the footnotes. We want to decompose these.

LMH-styles_LMH-title -> This identifies a new chapter in Hebrew

LME-title -> New chapter in English

Each <p> tag will be it's own segment. Use the `LMH-section--` classes to identify the section.

The text will be depth 3 -> ["Chapter", "Section", "Segment"]. It's important to note that a different number of
sections may appear in the Hebrew and the English (chapter 2 for example has 6 sections in Hebrew but 9 in English).
The segments should roughly correlate between languages. Therefore, Therefore, I would like to first parse out the
segments into a list and then allocating the segments into chapters.

A Chapter class will be helpful. The LMFile will be responsible for identifying which chapters appear in the the file,
then will hand off parsing to the Chapter. The Chapter will extract the html relevant for the chapter in both English
and Hebrew. Once the English and Hebrew are both parsed into segments, and the section transitions are known, allocation
into sections is trivial.

"""

import re
import os
import bleach
from xml.sax.saxutils import unescape
from bs4 import BeautifulSoup, Tag, NavigableString

import django
django.setup()
from data_utilities.util import getGematria


class LMFile(object):

    def __init__(self, filename):
        self.filename = filename
        with open(self.filename) as fp:
            self.soup = BeautifulSoup(fp, 'xml', from_encoding='utf-8')
        self._preprocess_soup()
        self.chapters = [Chapter(n, self.soup) for n in self._get_chapter_numbers()]

    def _preprocess_soup(self):
        for d in list(self.soup.descendants):
            if isinstance(d, NavigableString) and re.match(u'^\s+$', d):
                d.extract()

        ul_tags = self.soup.body.find_all('ul')
        if ul_tags:
            print u"Unordered list found in {}".format(self.filename)

        for ul_tag in ul_tags:
            previous_p = ul_tag.previous_sibling
            assert previous_p.name == 'p'
            previous_p.append(ul_tag)

            for li in ul_tag.find_all('li'):
                li.unwrap()
            ul_tag.unwrap()

        everything = self.soup.body.find_all(True)
        for e in everything:
            tag_class = e['class']
            tag_class = re.sub(u'\s?(Para|Char)Override-\d{1,2}', u'', tag_class)
            e['class'] = tag_class
        for span in self.soup.body.find_all('span', attrs={'class': re.compile(u'^LME-FootRef')}):
            span.decompose()

    def _get_chapter_numbers(self):
        chap_match = re.search(u'LM(II)?(?P<start>\d+)-?(?P<end>\d+)?\.html', self.filename)
        if chap_match.group('end'):
            return range(int(chap_match.group('start')), int(chap_match.group('end')) + 1)
        else:
            return [int(chap_match.group('start'))]

    def parse_english(self):
        # kill footnotes; might be faster to run this on the body instead of each p


        p_finder = re.compile(u'^LME')
        p_tags = self.soup.body.find_all(u'p', attrs={'class': p_finder})
        chapters, cur_chap, cur_chap_num = [], [], None

        for p_tag in p_tags:

            if p_tag['class'] == u'LME-title':
                pass
        print p_tags[0].text


class Chapter(object):

    def __init__(self, number, soup):
        self.number = number
        self.english_segments = None
        self.hebrew_segments = None
        self.english_section_transitions = None
        self.hebrew_section_transitions = None  # not sure if I need this, but relatively easy to obtain
        self.english_chapter = None
        self.hebrew_chapter = None
        self._collect_english_segments(soup)
        self._collect_hebrew_segments(soup)
        self._allocate_to_sections()

    def _collect_english_segments(self, soup):
        """
        :param Beautifulsoup soup:
        :return:
        """
        assert isinstance(soup, BeautifulSoup)
        en_reg = re.compile(u'^LME')
        all_en_ps = soup.find_all('p', attrs={'class': en_reg})

        segments = []
        started = False

        for en_p in all_en_ps:
            if en_p['class'] == "LME-title":
                if en_p.string == "LIKUTEY MOHARAN #{}".format(self.number):
                    started = True
                else:
                    if started:  # we've moved to the next chapter, stop iterating
                        break

            elif started:
                segments.append(en_p)
            else:
                continue

        assert len(segments) > 0
        # handle sources that got their own segment
        bad_indices = []
        for i, segment in enumerate(segments):
            if segment['class'] == u'LME-verse-opening-source':
                assert i > 0
                bad_indices.append(i)
                for child in segment.find_all(True):
                    child.unwrap()
                segments[i-1].append(segment)
                segment.unwrap()

        # popping changes the index of all items to the right of the index which was popped.
        for i in reversed(bad_indices):
            segments.pop(i)

        # self._clean_segments(segments)
        self._get_en_segment_transitions(segments)
        self.english_segments = [unescape(bleach.clean(unicode(s), tags=[], attributes={}, strip=True)) for s in segments]

    def _clean_segments(self, raw_segments):
        """
        Consolidate duplicate segments, simplify html when needed, unwrap when extraneous.
        :param raw_segments:
        :return:
        """
        for segment in raw_segments:
            current_tag = segment.contents[0]
            while True:
                next_tag = current_tag.next_sibling
                if not next_tag:
                    break
                if (isinstance(current_tag, Tag) and isinstance(next_tag, Tag)) and \
                        (current_tag.name == next_tag.name and current_tag['class'] == next_tag['class']):
                    current_tag.append(next_tag)
                    next_tag.unwrap()
                    assert all(isinstance(i, NavigableString) for i in current_tag.contents)
                    current_tag.string = u' '.join(unicode(i) for i in current_tag.contents)
                else:
                    current_tag = next_tag

    def _get_en_segment_transitions(self, raw_segments):
        transition_list = []
        current_segment = 1  # we'll want to special-case 1 as text may appear before the 1st section marker

        for seg_num, segment in enumerate(raw_segments):
            if segment['class'] == u'LME-section':
                first_child = segment.contents[0]

                if isinstance(first_child, Tag) and first_child.name == u'span' and first_child['class'] == u'LME-Bold':
                    try:
                        next_segment = int(re.match(u'^(\d+)', segment.text).group(1))
                    except AttributeError:
                        continue

                    if next_segment == 1:
                        pass
                    elif next_segment - current_segment != 1:
                        print "Bad section transition found in chapter {}".format(self.number)
                        raise AssertionError
                    else:
                        transition_list.append(seg_num)
                        current_segment = next_segment
                    # first_child.decompose()  # get rid of section marks - those are implicit now
        self.english_section_transitions = transition_list

    def _collect_hebrew_segments(self, soup):
        assert isinstance(soup, BeautifulSoup)
        he_reg = re.compile(u'^LMH')
        all_he_ps = soup.find_all('p', attrs={'class': he_reg})

        segments = []
        started = False
        chapter_reg = re.compile(ur'''\u05dc\u05d9\u05e7\u05d5\u05d8\u05d9 \u05de\u05d5\u05d4\u05e8[\u05f4"]\u05df\s  # ליקוטי מוהר"ן
                                 \u05e1\u05d9\u05de\u05df\s  # סימן
                                 (?P<chapter>[\u05d0-\u05ea"]{1,4})''', re.X)
        chapter_reg = re.compile(ur'''\u05dc\u05d9\u05e7\u05d5\u05d8\u05d9 \u05de\u05d5\u05d4\u05e8[\u05f4"]\u05df\s\u05e1\u05d9\u05de\u05df\s(?P<chapter>[\u05d0-\u05ea"]{1,4})''')

        for he_p in all_he_ps:
            if he_p['class'] == u'LMH-styles_LMH-title':
                if not he_p.string:
                    raise AssertionError

                chapter_match = chapter_reg.match(he_p.string)
                if chapter_match:
                    if getGematria(chapter_match.group('chapter')) == self.number:
                        started = True

                    elif started:
                        break

            elif started:
                segments.append(he_p)
            else:
                continue

        assert len(segments) > 0
        self.hebrew_segments = segments

    def _allocate_to_sections(self):
        if len(self.english_segments) != len(self.hebrew_segments):
            print u"Segment Mismatch in chapter {}:\n\t{} in English and {} in Hebrew"\
                .format(self.number, len(self.english_segments), len(self.hebrew_segments))


part_1_files = [f for f in os.listdir(u'.') if re.search(u'^LM(?!II)\d+(-\d+)?\.html$', f)]
for f in sorted(part_1_files):
    print f
    my_file = LMFile(f)



