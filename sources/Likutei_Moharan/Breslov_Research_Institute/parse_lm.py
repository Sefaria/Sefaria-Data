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
import numpy
import bleach
import codecs
import unicodecsv
from tqdm import tqdm
from collections import OrderedDict
from matplotlib import pyplot as plt
from itertools import izip_longest
from xml.sax.saxutils import unescape, escape
from bs4 import BeautifulSoup, Tag, NavigableString

import django
django.setup()
from sefaria.model import *
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
            # print u"Unordered list found in {}".format(self.filename)
            pass

        for ul_tag in ul_tags:
            previous_p = ul_tag.previous_sibling
            assert previous_p.name == 'p'
            previous_p.append(ul_tag)

            for li in ul_tag.find_all('li'):
                li.unwrap()
            ul_tag.unwrap()

        everything = self.soup.body.find_all(True)
        for e in everything:
            tag_class = e.get(u'class', u'')
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
                # if en_p.text == "LIKUTEY MOHARAN #{}".format(self.number):
                if re.search(u"^LIKUTEY MOHARAN( II)? #{}".format(self.number), en_p.text):
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
            segment_text = segment.text
            if \
                    (re.search(ur'^\([^)]+\)$', segment_text)
                and
                    library.get_refs_in_string(segment_text, 'en', citing_only=True)) \
            or \
                    (re.search(u'^[a-z]', segment_text)
                and
                    re.search(u'[a-z]\s*$', segments[i-1].text)) \
            or \
                re.search(ur'(^\{.*\}$)|(^<.*>$)', segment_text.rstrip()):

                if i == 0:
                    continue
                bad_indices.append(i)
                # for child in segment.find_all(True):
                #     child.unwrap()
                # segment.string = u' {}'.format(u' '.join(segment.contents))
                segments[i-1].append(segment)
                segment.unwrap()
            elif not segment_text:
                bad_indices.append(i)

        # popping changes the index of all items to the right of the index which was popped.
        for i in reversed(bad_indices):
            segments.pop(i)

        # self._clean_segments(segments)
        self._get_en_segment_transitions(segments)
        # self.english_segments = [unescape(bleach.clean(unicode(s), tags=[], attributes={}, strip=True)) for s in segments]
        self.english_segments = [self.clean_segment(s) for s in segments]

    @staticmethod
    def clean_segment(raw_segment):
        """
        Consolidate duplicate segments, simplify html when needed, unwrap when extraneous.
        :param raw_segment:
        :return:
        """
        # '<' character gets preceded by a space
        # '>' character is never followed by a space
        raw_segment = re.sub(u'<', u' <', unicode(raw_segment))
        raw_segment = re.sub(u'>\s+', u'>', raw_segment)
        seg_soup = BeautifulSoup(raw_segment, 'xml')
        ptag = seg_soup.find('p')

        # kill source tags and anything that isn't a span
        bad_tags = ptag.find_all(lambda x: x.name != 'span')
        for bad_tag in bad_tags:
            bad_tag.unwrap()
        bad_tags = ptag.find_all(attrs={'class': re.compile(u'source', re.I)})
        for bad_tag in bad_tags:
            bad_tag.unwrap()

        bi_tags = ptag.find_all(attrs={'class': re.compile(u'LME-Bold-Italics|LME-verse-ital-bold')})
        for bi_tag in bi_tags:
            bi_tag['class'] = u'bi'
        i_tags = ptag.find_all(attrs={'class': re.compile(u'italics', re.I)})
        for i_tag in i_tags:
            i_tag.name = u'i'
            i_tag.attrs.clear()
        b_tags = ptag.find_all(attrs={'class': re.compile(u'bold', re.I)})
        for b_tag in b_tags:
            b_tag.name = u'b'
            b_tag.attrs.clear()
        bad_tags = ptag.find_all(lambda x: x.name == u'span' and x.attrs.get(u'class', u'') != u'bi')
        for bad_tag in bad_tags:
            bad_tag.unwrap()

        previous_tag = ptag.contents[0]
        current_tag = previous_tag.next_sibling
        while current_tag:
            if isinstance(previous_tag, Tag) and isinstance(current_tag, Tag):
                if previous_tag.name == current_tag.name:
                    previous_tag.append(current_tag)
                    current_tag.unwrap()
                    current_tag = previous_tag

                elif current_tag.name == u'span' and current_tag.attrs.get(u'class') == u'bi':
                    if previous_tag.name == u'i':
                        current_tag.name = u'b'
                    elif previous_tag.name == u'b':
                        current_tag.name = u'i'
                    current_tag.attrs.clear()
                    previous_tag.append(current_tag)

                    # just make sure there isn't a duplicate sitting inside the tag we just appended to
                    inner_sibling = current_tag.previous_sibling
                    if inner_sibling and inner_sibling.name == current_tag.name:
                        inner_sibling.append(current_tag)
                        current_tag.unwrap()
                    current_tag = previous_tag

                elif previous_tag.name == u'span' and previous_tag.attrs.get(u'class') == u'bi':
                    previous_tag.attrs.clear()
                    previous_tag.name = current_tag.name
                    if not previous_tag.string:
                        previous_tag.string = previous_tag.decode_contents()

                    if current_tag.name == u'i':
                        previous_tag.string.wrap(seg_soup.new_tag(u'b'))
                    elif current_tag.name == u'b':
                        previous_tag.string.wrap(seg_soup.new_tag(u'i'))

                    previous_tag.append(current_tag)
                    current_tag.unwrap()
                    current_tag = previous_tag

            previous_tag, current_tag = current_tag, current_tag.next_sibling

        fixed_segment = ptag.decode_contents()
        fixed_segment = re.sub(u'^\s+|\s+$', u'', fixed_segment)
        fixed_segment = re.sub(u'\s{2,}', u' ', fixed_segment)
        fixed_segment = re.sub(u'\s+((<\/[bi]>)+)\s*$', u'\g<1>', fixed_segment)

        return fixed_segment

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

                    if next_segment == 1 or next_segment == current_segment:
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
        chapter_reg = re.compile(ur'''\u05dc\u05d9\u05e7\u05d5\u05d8\u05d9 \u05de\u05d5\u05d4\u05e8[\u05f4"]\u05df\s(\u05ea\u05e0\u05d9\u05e0\u05d0\s)?\u05e1\u05d9\u05de\u05df\s(?P<chapter>[\u05d0-\u05ea"]{1,4})''')

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
                if re.search(u'Rashbam', he_p['class']):
                    continue
                segments.append(he_p)
            else:
                continue

        # if current segment ends on a Hebrew char, combine with the next segment
        bad_indices = []
        for i, (cur_segment, next_segment) in enumerate(zip(segments, segments[1:])):

            segment_text = cur_segment.text
            stripped_text = re.sub(u"[\u05b0-\u05C7]", u'', segment_text)  # strip nikkud
            if re.search(u'[\u05d0-\u05ea]\s*$', stripped_text):
                # merge this segment into this one
                bad_indices.append(i)
                for child in cur_segment.find_all(True):
                    child.unwrap()
                cur_segment.string = u'{} '.format(u' '.join(cur_segment.contents))
                next_segment.insert(0, cur_segment)
                cur_segment.unwrap()
            elif not segment_text:
                bad_indices.append(i)
        for i in reversed(bad_indices):
            segments.pop(i)

        assert len(segments) > 0
        self.hebrew_segments = [bleach.clean(s, tags=[], attributes={}, strip=True) for s in segments]

    def _allocate_to_sections(self):
        if len(self.english_segments) != len(self.hebrew_segments):
            # print u"Segment Mismatch in chapter {}:\n\t{} in English and {} in Hebrew"\
            #     .format(self.number, len(self.english_segments), len(self.hebrew_segments))
            pass


class CSVChapter(object):

    def __init__(self, input_data, chap_number):
        self._english_segments, self._hebrew_segments = None, None
        self.number = chap_number
        if isinstance(input_data, dict):
            self._load_from_data(input_data)
        elif isinstance(input_data, file):
            self._load_from_file(input_data)

    def _set_en_section_transitions(self):
        transition_list = []
        current_segment = 1

        for seg_num, segment in enumerate(self._english_segments):
            match = re.match(u'^(\d+)', segment)
            if not match:
                continue
            next_segment = int(match.group(1))

            if next_segment == 1 or next_segment == current_segment:
                pass
            elif next_segment - current_segment != 1:
                print "Bad section transition found in chapter {}".format(self.number)
                raise AssertionError
            else:
                transition_list.append(seg_num)
                current_segment = next_segment

        self._en_section_transitions = tuple(transition_list)

    def get_en_section_transitions(self):
        return self._en_section_transitions

    def _set_he_section_transitions(self):
        transition_list = []
        current_segment = 1

        for seg_num, segment in enumerate(self._hebrew_segments):
            match = re.match(u'^([\u05d0-\u05d8]|[\u05d9-\u05dc][\u05d0-\u05d8]?|\u05d8[\u05d5\u05d6])\.\s', segment)
            if not match:
                continue
            next_segment = getGematria(match.group(1))

            if next_segment == 1:
                pass
            elif next_segment - current_segment != 1:
                print "Bad hebrew section transition found in chapter {}".format(self.number)
                raise AssertionError
            else:
                transition_list.append(seg_num)
                current_segment = next_segment

        self._he_section_transitions = tuple(transition_list)

    def get_he_section_transitions(self):
        return self._he_section_transitions

    def get_english_segments(self):
        return self._english_segments

    def set_english_segments(self, segments):
        self._english_segments = tuple(segments)
        self._set_en_section_transitions()

    def del_english_segments(self):
        self._english_segments = None
        del self._en_section_transitions

    english_segments = property(get_english_segments, set_english_segments, del_english_segments)

    def get_hebrew_segments(self):
        return self._hebrew_segments

    def set_hebrew_segments(self, segments):
        self._hebrew_segments = tuple(segments)
        self._set_he_section_transitions()

    def del_hebrew_segments(self):
        self._hebrew_segments = None
        del self._he_section_transitions

    hebrew_segments = property(get_hebrew_segments, set_hebrew_segments, del_hebrew_segments)

    def _load_from_file(self, file_obj):
        reader = list(unicodecsv.DictReader(file_obj))
        english_segments = [row['English'] for row in reader]
        hebrew_segments = [row['Hebrew'] for row in reader]

        # clean out blank segments from the end
        while not english_segments[-1]:
            english_segments.pop()
        self.set_english_segments(english_segments)

        while not hebrew_segments[-1]:
            hebrew_segments.pop()
        self.set_hebrew_segments(hebrew_segments)

    def _load_from_data(self, segments):
        self.set_english_segments(segments['en'])
        self.set_hebrew_segments(segments['he'])

    def generate_html(self, test_mode=False):
        table_rows = [u'<tr><th>English</th><th>Hebrew</th></tr>']
        for en_seg, he_seg in izip_longest(self.english_segments, self.hebrew_segments, fillvalue=u''):
            table_rows.append(u'<tr><td>{}</td><td>{}</td></tr>'.format(escape(en_seg), he_seg))

        my_doc = u"<!DOCTYPE html><html><head><meta charset='utf-8'>" \
                 u"<link rel='stylesheet' type='text/css' href='styles.css'></head><body><table>{}</table>" \
                 u"</body</html>".format(u''.join(table_rows))

        if test_mode:
            filename = 'QA_files/Chapter{}_test_view.html'.format(self.number)
        else:
            filename = 'QA_files/Chapter{}_view.html'.format(self.number)

        with codecs.open(filename, 'w', 'utf-8') as fp:
            fp.write(my_doc)

    def dump_csv(self, test_mode=False):
        rows = [
            {
                'English': en_seg,
                'Hebrew': he_seg
            }
            for en_seg, he_seg in izip_longest(self.english_segments, self.hebrew_segments, fillvalue=u'')
        ]

        if test_mode:
            filename = 'QA_files/Chapter{}_data_test.csv'.format(self.number)
        else:
            filename = 'QA_files/Chapter{}_data.csv'.format(self.number)

        with open(filename, 'w') as fp:
            writer = unicodecsv.DictWriter(fp, ['English', 'Hebrew'])
            writer.writeheader()
            writer.writerows(rows)


def generate_csv_from_raw():
    part_1_files = [f for f in os.listdir(u'.') if re.search(u'^LM(?!II)\d+(-\d+)?\.html$', f)]

    chapters = [c for f in tqdm(part_1_files) for c in LMFile(f).chapters]
    chapters.sort(key=lambda x: x.number)

    for c in chapters:
        csv_chapter = CSVChapter({'en': c.english_segments, 'he': c.hebrew_segments}, c.number)
        csv_chapter.generate_html()
        csv_chapter.dump_csv()


def regenerate_html_for_chapter(chap_num):
    filename = 'QA_files/Chapter{}_data.csv'.format(chap_num)
    with open(filename) as fp:
        chapter = CSVChapter(fp, chap_num)
    chapter.generate_html()


def get_word_stats(chapters, graph=False):
    en_words, he_words = [], []
    for chap_num in chapters:
        with open('QA_files/Chapter{}_data.csv'.format(chap_num)) as fp:
            chapter = CSVChapter(fp, chap_num)
        assert len(chapter.english_segments) == len(chapter.hebrew_segments)

        en_words.extend(len(seg.split()) for seg in chapter.english_segments)
        he_words.extend(len(seg.split()) for seg in chapter.hebrew_segments)

    en_words, he_words = numpy.array(en_words, dtype=float), numpy.array(he_words, dtype=float)
    ratios = en_words / he_words
    logged_ratios = numpy.log(ratios)

    if graph:
        normalized_ratios = logged_ratios - logged_ratios.mean()
        from matplotlib import pyplot as plt
        # fig, axs = plt.subplots()
        # axs.hist(normalized_ratios, 20)
        plt.scatter(en_words, he_words)
        plt.show()

    return logged_ratios.mean(), logged_ratios.std()


def fit_function(chapters, graph=False):
    en_words, he_words = [], []
    for chap_num in chapters:
        with open('QA_files/Chapter{}_data.csv'.format(chap_num)) as fp:
            chapter = CSVChapter(fp, chap_num)
        assert len(chapter.english_segments) == len(chapter.hebrew_segments)

        en_words.extend(len(seg.split()) for seg in chapter.english_segments)
        he_words.extend(len(seg.split()) for seg in chapter.hebrew_segments)

    en_words, he_words = numpy.array(en_words), numpy.array(he_words)
    M = numpy.column_stack((en_words,))
    params = numpy.linalg.lstsq(M, he_words, rcond=None)[0]
    print params
    poly = numpy.poly1d([params, 0])

    if graph:
        _ = plt.plot(en_words, he_words, '.', en_words, poly(en_words))
        plt.show()

    return poly


def calculate_error(english, hebrew, polyfit):
    return numpy.sqrt(numpy.sum(numpy.power(hebrew - polyfit(english), 2)))


def find_merge(english, hebrew, polyfit):
    def assemble_merges(word_counts):
        count_list = []
        for i, count in enumerate(word_counts[1:], 1):
            temp = list(word_counts[:])
            temp[i-1] += count
            temp.pop(i)
            count_list.append((numpy.array(temp), i))
        return count_list

    length = min(len(english), len(hebrew))
    original_error = calculate_error(english[:length], hebrew[:length], polyfit)
    print original_error
    en_merges, he_merges = assemble_merges(english), assemble_merges(hebrew)

    length = min(len(english)-1, len(hebrew))
    en_improvements = [(calculate_error(m[0][:length], hebrew[:length], polyfit), m[1])
                       for m in en_merges]

    length = min(len(english), len(hebrew)-1)
    he_improvements = [(calculate_error(english[:length], m[0][:length], polyfit), m[1])
                       for m in he_merges]

    for e in en_improvements:
        print e

    best_en = min(en_improvements, key=lambda x: x[0])
    best_he = min(he_improvements, key=lambda x: x[0])

    return best_en, best_he


def generate_merge(chap_num, compare_method, lang, test_mode=True):
    with open('QA_files/Chapter{}_data.csv'.format(chap_num)) as fp:
        chapter = CSVChapter(fp, chap_num)

    english_segments = list(chapter.english_segments)
    hebrew_segments = list(chapter.hebrew_segments)
    e_counts = numpy.array([len(seg.split()) for seg in english_segments])
    h_counts = numpy.array([len(seg.split()) for seg in hebrew_segments])

    best_e, best_h = find_merge(e_counts, h_counts, compare_method)

    if lang == 'en':
        print best_e
        merge_index = best_e[1]

        merged_text = u' '.join(english_segments[merge_index-1:merge_index+1])
        print merged_text
        english_segments[merge_index-1] = merged_text
        english_segments.pop(merge_index)
        chapter.english_segments = english_segments

    elif lang == 'he':
        print best_h
        merge_index = best_h[1]
        merged_text = u' '.join(hebrew_segments[merge_index-1:merge_index+1])
        print merged_text
        hebrew_segments[merge_index-1] = merged_text
        hebrew_segments.pop(merge_index)
        chapter.hebrew_segments = hebrew_segments

    else:
        raise AttributeError("lang parameter must be 'en' or 'he'")
    chapter.generate_html(test_mode)


def standardize_lists(list_a, list_b):
    temp_list = []
    if len(list_a) > len(list_b):
        for value in list_b:
            other_value = min(list_a, key=lambda x: abs(value - x))
            temp_list.append(other_value)
            list_a.remove(other_value)
        list_a = temp_list

    elif len(list_b) > len(list_a):
        for value in list_a:
            other_value = min(list_b, key=lambda x: abs(value - x))
            temp_list.append(other_value)
            list_b.remove(other_value)
        list_b = temp_list

    return list_a, list_b


def get_merge_window(csv_chapter):
    """
    compares refs which appear in English and Hebrew to help narrow down the search window
    :param CSVChapter csv_chapter:
    :return: window_start, window_end, lang
    """
    en_refs, he_refs = OrderedDict(), OrderedDict()
    en_segments, he_segments = csv_chapter.english_segments, csv_chapter.hebrew_segments

    for seg_num, segment in enumerate(en_segments):
        refs = [r.normal() for r in library.get_refs_in_string(segment, 'en', citing_only=True)]
        for ref in refs:
            en_refs.setdefault(ref, list()).append(seg_num)

    for seg_num, segment in enumerate(he_segments):
        refs = [r.normal() for r in library.get_refs_in_string(segment, 'he', citing_only=True)]
        for ref in refs:
            if ref in en_refs:  # we only want refs that appear in both languages
                he_refs.setdefault(ref, list()).append(seg_num)

    # clear out en refs that did not show up in hebrew
    for ref in en_refs.keys():
        if ref not in he_refs:
            del en_refs[ref]
    assert len(en_refs) == len(he_refs)

    # make sure we have the same number of appearances of each ref
    for ref in en_refs.keys():
        en_refs[ref], he_refs[ref] = standardize_lists(en_refs[ref], he_refs[ref])
    en_refs = [(ref, segment) for ref, segs in en_refs.items() for segment in segs]
    en_refs.sort(key=lambda x: x[1])

    last_good_segment = 0
    for ref, en_seg in en_refs:
        he_seg = min(he_refs[ref], key=lambda x: abs(x-en_seg))
        if en_seg == he_seg:
            last_good_segment = en_seg
        elif abs(en_seg - he_seg) == 1:
            if en_seg > he_seg:
                window_close, lang = en_seg, 'en'
            else:
                window_close, lang = he_seg, 'he'
            break
        else:
            raise AssertionError("Chapter {}: Jump too big".format(csv_chapter.number))
    else:
        diff = abs(len(en_segments) - len(he_segments))
        if diff == 0:
            print "Chapter {}: No Merge needed".format(csv_chapter.number)
            last_good_segment, window_close, lang = len(en_segments), len(en_segments), 'en'
        elif diff > 1:
            raise AssertionError("Chapter {}: Jump too big".format(csv_chapter.number))
        else:
            if len(en_segments) > len(he_segments):
                window_close = len(en_segments) - 1  # the actual index of the last segment
                lang = 'en'
            else:
                window_close = len(he_segments) - 1
                lang = 'he'
    return last_good_segment, window_close, lang


def generate_files_for_editing():
    my_files = [f for f in os.listdir(u'./QA_files') if re.search(u'^Chapter\d+_data\.csv$', f)]
    chapters = []
    for f in my_files:
        cnumber = int(re.search(u'^Chapter(\d+)_data\.csv$', f).group(1))
        with open(u'./QA_files/{}'.format(f)) as fpointer:
            cfile = CSVChapter(fpointer, cnumber)
        chapters.append(cfile)
    chapters.sort(key=lambda x: x.number)
    start, end = -1, -1
    rows = []
    for chapter in chapters:
        if chapter.number % 50 == 1:
            start = chapter.number
        for num, (en_seg, he_seg) in enumerate(izip_longest(chapter.english_segments, chapter.hebrew_segments, fillvalue=u''), 1):
            rows.append({
                u'Chapter': chapter.number,
                u'Segment #': num,
                u'English': en_seg,
                u'Hebrew': he_seg
            })
        if chapter.number % 50 == 0 or chapter.number == chapters[-1].number:
            end = chapter.number
            with open('./manual_editing/Likutei_Moharan_{}-{}.csv'.format(start, end), 'w') as fp:
                writer = unicodecsv.DictWriter(fp, [u'Chapter', u'Segment #', u'English', u'Hebrew'])
                writer.writeheader()
                writer.writerows(rows)
            rows = []


filenames = [f for f in os.listdir(u'.') if re.match(u'^LM\d+(-\d+)?\.html$', f)]
p1_chapters = [chapter for f in tqdm(filenames) for chapter in LMFile(f).chapters]
p1_chapters.sort(key=lambda x: x.number)

filenames = [f for f in os.listdir(u'.') if re.match(u'^LMII\d+(-\d+)?\.html$', f)]
p2_chapters = [chapter for f in tqdm(filenames) for chapter in LMFile(f).chapters]
p2_chapters.sort(key=lambda x: x.number)
