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
                # if re.search(u"^LIKUTEY MOHARAN #{}".format(self.number), en_p.text):
                if en_p.text == "LIKUTEY MOHARAN #{}".format(self.number):
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
                for child in segment.find_all(True):
                    child.unwrap()
                segment.string = u' {}'.format(u' '.join(segment.contents))
                segments[i-1].append(segment)
                segment.unwrap()
            elif not segment_text:
                bad_indices.append(i)

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
        self.number = chap_number
        if isinstance(input_data, dict):
            self._load_from_data(input_data)
        elif isinstance(input_data, file):
            self._load_from_file(input_data)

    def _load_from_file(self, file_obj):
        reader = list(unicodecsv.DictReader(file_obj))
        self.english_segments = [row['English'] for row in reader]
        self.hebrew_segments = [row['Hebrew'] for row in reader]

        # clean out blank segments from the end
        while not self.english_segments[-1]:
            self.english_segments.pop()
        while not self.hebrew_segments[-1]:
            self.hebrew_segments.pop()

    def _load_from_data(self, segments):
        self.english_segments = segments['en']
        self.hebrew_segments = segments['he']

    def generate_html(self):
        table_rows = [u'<tr><th>English</th><th>Hebrew</th></tr>']
        for en_seg, he_seg in izip_longest(self.english_segments, self.hebrew_segments, fillvalue=u''):
            table_rows.append(u'<tr><td>{}</td><td>{}</td></tr>'.format(escape(en_seg), he_seg))

        my_doc = u"<!DOCTYPE html><html><head><meta charset='utf-8'>" \
                 u"<link rel='stylesheet' type='text/css' href='styles.css'></head><body><table>{}</table>" \
                 u"</body</html>".format(u''.join(table_rows))
        with codecs.open('QA_files/Chapter{}_view.html'.format(self.number), 'w', 'utf-8') as fp:
            fp.write(my_doc)

    def dump_csv(self):
        rows = [
            {
                'English': en_seg,
                'Hebrew': he_seg
            }
            for en_seg, he_seg in izip_longest(self.english_segments, self.hebrew_segments, fillvalue=u'')
        ]
        with open('QA_files/Chapter{}_data.csv'.format(self.number), 'w') as fp:
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


my_func = fit_function([1, 3, 4], False)

with open('QA_files/Chapter8_data.csv') as fp:
    chapter6 = CSVChapter(fp, 8)

en6 = numpy.array([len(seg.split()) for seg in chapter6.english_segments])
he6 = numpy.array([len(seg.split()) for seg in chapter6.hebrew_segments])
rlength = min(len(en6), len(he6))
en6, he6 = en6[:rlength], he6[:rlength]

my_error = calculate_error(en6, he6, my_func)
# _ = plt.plot(numpy.arange(rlength), numpy.cumsum(my_error))
plt.show()

merge_en, merge_he = find_merge(en6, he6, my_func)
print merge_en
print chapter6.english_segments[merge_en[1]]

print merge_he
print chapter6.hebrew_segments[merge_he[1]]


# with open('QA_files/Chapter9_data.csv') as fp:
#     chapter9 = CSVChapter(fp, 6)
#
# en9 = numpy.array([len(seg.split()) for seg in chapter9.english_segments], dtype=float)
# he9 = numpy.array([len(seg.split()) for seg in chapter9.hebrew_segments], dtype=float)
# length = min(len(en9), len(he9))
# en9, he9 = en9[:length], he9[:length]
# # my_rats = en[:length] / he[:length]
# # logged_rats9 = numpy.log(my_rats)
# # print logged_rats9.mean(), logged_rats9.std()
#
# fig, axs = plt.subplots(1, 2)
# # axs[0].plot(range(len(logged_rats6)), abs(logged_rats6))
# # axs[1].plot(range(len(logged_rats9)), abs(logged_rats9))
# axs[0].scatter(en6, he6)
# axs[1].scatter(en9, he9)
# plt.show()
