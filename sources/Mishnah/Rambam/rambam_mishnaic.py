# encoding=utf-8

import os
import re
import codecs
import unicodecsv as csv
from bs4 import BeautifulSoup, Tag
from sefaria.datatype.jagged_array import JaggedArray
from sefaria.model.text import Ref, JaggedArrayNode
from data_utilities.sanity_checks import TagTester
from sources.functions import post_link, post_text, post_index
from data_utilities.util import get_cards_from_trello, numToHeb, ja_to_xml, getGematria, traverse_ja


def get_cards():
    with open('../trello_board.json') as board:
        return [card.replace(' on', '') for card in get_cards_from_trello('Parse Rambam Mishna Style', board)]


def standardize_files():

    def get_filename(dst):
        if dst == 'Rambam Pirkei Avot':
            org = 'Pirkei Avot'
        else:
            org = dst.replace(' Mishnah', '')
        return '{}.txt'.format(org)
    cards = get_cards()
    for card in cards:
        filename = get_filename(card)
        os.rename(filename, '{}.txt'.format(card))


def check_chapters():
    cards = get_cards()
    good_files, bad_files = [], []
    for card in cards:
        m_ref = Ref(card.replace('Rambam ', ''))
        with codecs.open('{}.txt'.format(card), 'r', 'utf-8') as infile:
            tester = TagTester(u'@00', infile, u'@00\u05e4\u05e8\u05e7')
            tags = tester.grab_each_header()
        if len(tags) == len(m_ref.all_subrefs()) or card == 'Rambam Pirkei Avot':
            good_files.append(card)
        else:
            bad_files.append(card)
    return {
        'good': good_files,
        'bad': bad_files
    }


def test_insert_chapters(filename, expected):
    with codecs.open(filename, 'r', 'utf-8') as infile:
        tester = TagTester(u'@22', infile, u'^@22\u05d0( |$)')
        if len(tester.grab_each_header()) == expected:
            return True
        else:
            return False


def insert_chapter_marker(filename, safe_mode=False):
    with codecs.open(filename, 'r', 'utf-8') as infile:
        lines = infile.readlines()
    count = 0
    new_lines = []
    for line in lines:
        if re.search(u'^@22\u05d0( |$)', line) is not None:
            count += 1
            new_lines.append(u'@00\u05e4\u05e8\u05e7 {}\n{}'.format(numToHeb(count), line))
        else:
            new_lines.append(line)
    if safe_mode:
        filename += '.tmp'
    with codecs.open(filename, 'w', 'utf-8') as outfile:
        outfile.writelines(new_lines)


def replace_in_file(filename, pattern, replacement, safe_mode=False):
    with codecs.open(filename, 'r', 'utf-8') as infile:
        lines = infile.readlines()

    new_lines = []
    for line in lines:
        new_lines.append(re.sub(pattern, replacement, line))
    if safe_mode:
        filename += '.tmp'
    with codecs.open(filename, 'w', 'utf-8') as outfile:
        outfile.writelines(new_lines)


def remove_blank_lines(filename, safe_mode=False):
    with codecs.open(filename, 'r', 'utf-8') as infile:
        lines = infile.readlines()
    new_lines = filter(None, [None if line.isspace() else line.lstrip() for line in lines])

    if safe_mode:
        filename += '.tmp'
    with codecs.open(filename, 'w', 'utf-8') as outfile:
        outfile.writelines(new_lines)


def align_files():
    cards = get_cards()
    for card in cards:
        name = '{}.txt'.format(card)
        replace_in_file(name, ur'@22([\u05d0-\u05ea]{1,2})', ur'\n@22\1\n')
        replace_in_file(name, ur'@11', ur'\n@11')
        remove_blank_lines(name)


def check_mishnayot():
    cards = get_cards()
    success, failure = [], []
    for card in cards:
        with codecs.open('{}.txt'.format(card), 'r', 'utf-8') as infile:
            tester = TagTester(u'@22', infile, u'@22([\u05d0-\u05ea]{1,2})')
            result = tester.in_order_many_sections(end_tag=u'@00', capture_group=1)
        if result[0] == 'SUCCESS':
            success.append(card)
        else:
            print 'failure: {}'.format(card)
            print len(result[1])

    print 'successes: {}'.format(len(success))
    print 'failures: {}'.format(len(failure))
    print 'total: {}'.format(len(cards))
    for item in failure:
        print item


def parser(name):
    with codecs.open('{}.txt'.format(name), 'r', 'utf-8') as infile:
        lines = infile.readlines()
    parsed_text = JaggedArray([[[]]])
    links = []
    chapter, mishnah, comment = -1, -1, -1
    for line in lines:
        if re.match(ur'@00\u05e4\u05e8\u05e7', line) is not None:
            chapter += 1
            comment = -1
            continue

        elif re.match(ur'@22', line) is not None:
            mishnah = getGematria(re.match(ur'@22([\u05d0-\u05ea]{1,2})', line).group(1)) - 1
            comment = -1
            continue

        elif re.match(ur'@11' ,line) is not None:
            comment += 1
            line = re.sub(ur'@[1-9]{2}(\(|\[)?[\u05d0-\u05ea]{1,2}(\)|\])', u'', line)
            line = re.sub(ur'@[0-9]{2}', u'', line)
            parsed_text.set_element((chapter, mishnah, comment), line, pad=u'')
            links.append({
                'refs': ('{} {}:{}:{}'.format(name, chapter+1, mishnah+1, comment+1),
                         '{} {}:{}'.format(name.replace('Rambam ', ''), chapter+1, mishnah+1)),
                'type': 'commentary',
                'auto': True,
                'generated_by': 'Mishnaic Rambam Parse Script'
            })
    return {'parsed': parsed_text.array(), 'links': links}


def parse_and_upload():
    cards = get_cards()
    links = []
    for card in cards:
        node = JaggedArrayNode()
        node.add_title(card, 'en', primary=True)
        node.add_title(u'רמב"ם ' + Ref(card.replace('Rambam ', '')).he_normal(), 'he', primary=True)
        node.key = card
        node.depth = 3
        node.addressTypes = ['Integer', 'Integer', 'Integer']
        node.sectionNames = ['Chapter', 'Mishnah', 'Comment']
        node.validate()
        node.toc_zoom = 2

        index = {
            'title': card,
            'categories': ['Commentary2', 'Mishnah', 'Rambam'],
            'schema': node.serialize(),
        }

        parsed = parser(card)
        links.extend(parsed['links'])
        version = {
            'versionTitle': u'Vilna Edition',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957',
            'language': 'he',
            'text': parsed['parsed']
        }
        print 'posting {}'.format(card)
        post_index(index)
        post_text(card, version, index_count='on')
    post_link(links)


def xmlify(filename):
    """
    create an xml representation of the text files
    :param filename: str name of file
    """
    with codecs.open(filename, 'r', 'utf-8') as infile:
        raw_rambam = infile.read()

    chap_index = [getGematria(i.group(1)) for i in re.finditer(ur'@00\u05e4\u05e8\u05e7 ([\u05d0-\u05ea]{1,2})', raw_rambam)]
    chapters = re.split(ur'@00\u05e4\u05e8\u05e7 [\u05d0-\u05ea]{1,2}', raw_rambam)[1:]
    assert len(chap_index) == len(chapters)

    soup = BeautifulSoup(u'<root></root>', 'xml')
    for index, chapter in zip(chap_index, chapters):
        x_chapter = soup.new_tag('chapter', num=unicode(index))
        soup.root.append(x_chapter)

        v_indices = [getGematria(i.group(1)) for i in re.finditer(ur'@22([\u05d0-\u05ea]{1,2})', chapter)]
        verses = re.split(ur'@22[\u05d0-\u05ea]{1,2}', chapter)[1:]
        assert len(v_indices) == len(verses)

        for v_index, verse in zip(v_indices, verses):
            x_verse = soup.new_tag('verse', num=unicode(v_index))
            comments = verse.splitlines()
            for i, comment in enumerate(comments[1:]):
                x_comment = soup.new_tag('comment', num=unicode(i+1))
                x_comment.append(comment)
                x_verse.append(x_comment)

            x_chapter.append(x_verse)
    with codecs.open('./xml/{}'.format(filename.replace('.txt', '.xml')), 'w', 'utf-8') as outfile:
        outfile.write(unicode(soup.prettify()))


class Root:

    def __init__(self, infile_name):
        with codecs.open(infile_name, 'r', 'utf-8') as infile:
            self._soup = BeautifulSoup(infile, 'xml')
        self._Tag = self._soup.root

    def get_chapters(self):
        return [Chapter(c) for c in self._Tag.find_all('chapter', recursive=False)]

    def get_mathces(self, pattern, group=0):
        return filter(None, [chapter.get_matches(pattern, group) for chapter in self.get_chapters()])

class Chapter:

    def __init__(self, chapter):
        """
        :param chapter: Tag
        """
        self._Tag = chapter

    def get_verses(self):
        return [Verse(v) for v in self._Tag.find_all('verse', recursive=False)]

    def get_matches(self, pattern, group=0):
        matches = filter(None, [verse.get_matches(pattern, group) for verse in self.get_verses()])
        if len(matches) == 0:
            return None
        else:
            return {'num': self._Tag['num'], 'verses': matches}

class Verse:

    def __init__(self, verse):
        """
        :param verse: Tag
        """
        self._Tag = verse

    def get_comments(self):
        return [Comment(c) for c in self._Tag.find_all('comment', recursive=False)]

    def get_matches(self, pattern, group=0):
        matches = filter(None, [comment.get_matches(pattern, group) for comment in self.get_comments()])
        if len(matches) == 0:
            return None
        else:
            return {'num': self._Tag['num'], 'comments': matches}

class Comment:
    def __init__(self, comment):
        self._Tag = comment

    def get_matches(self, pattern, group=0):
        match = re.search(pattern, self._Tag.text)
        if match is None:
            return None
        else:
            return {'num': self._Tag['num'], 'text': match.group(group)}
