# encoding=utf-8

import DCXMLsubs
import os
import re
import bleach
import bisect
import codecs
import StringIO
import unicodecsv as csv
from bs4 import BeautifulSoup, Tag
from data_utilities.util import ja_to_xml, getGematria
from data_utilities.dibur_hamatchil_matcher import match_text
from sources.functions import post_text, post_index, post_link, post_term, add_category


class Collection:

    def __init__(self):
        self.file_map = self.get_file_mapping()
        self.commentaryIndices = []
        self.versionList = []
        self.linkSet = []
        self.base_indices = []
        self.terms = []

    @staticmethod
    def get_file_mapping():
        with open('file_to_index_map.csv') as infile:
            lines = infile.readlines()
        reader = csv.DictReader(lines)
        return [row for row in reader]

    def parse_file(self, filename, en_title, he_title, include_commentaries=True):

        root = DCXMLsubs.parse('XML/{}'.format(filename), silence=True)
        version = self.get_version_skeleton()
        version['text'] = root.getBaseTextArray()
        self.versionList.append({'ref': en_title, 'version': version})
        self.base_indices.append(root.get_base_index(en_title, he_title))

        if include_commentaries:
            commentaries = root.body.commentaries
            for commentary in commentaries.get_commentary():
                author = commentary.get_author()
                if author == 'UNKNOWN':
                    continue
                self.commentaryIndices.append(commentary.build_index(en_title, he_title))
                self.terms.append(commentary.get_term_dict())

                # if self.commentarySchemas.get(author) is None:
                #     self.commentarySchemas[author] = commentary.build_node()
                # self.commentarySchemas[author].append(root.commentary_ja_node(en_title, he_title))

                version = self.get_version_skeleton()
                if commentaries.is_linked_commentary(commentary):
                    version['text'] = commentary.parse_linked()
                else:
                    version['text'] = commentary.parse_unlinked()

                ref = '{} on {}'.format(DCXMLsubs.commentatorNames[author], en_title)
                self.versionList.append({'ref': ref, 'version': version})
            self.linkSet.extend(root.get_stored_links(en_title))

    def parse_collection(self, include_commentaries=True, handle_exceptions=True):
        """
        Parse entire collection
        :param include_commentaries: Set to False to skip all commentaries
        :param handle_exceptions: Used only for debugging and development, if set to False, will push through all
        exceptions and upload those files on which exceptions were not raised
        :return:
        """
        for mapping in self.file_map:
            assert isinstance(mapping, dict)
            self.parse_file(mapping['filename'], mapping['en_title'], mapping['he_title'], include_commentaries)


    @staticmethod
    def get_version_skeleton():
        return {
            'versionTitle': 'Talmud Bavli, Vilna 1883 ed.',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957',
            'language': 'he',
        }

    def post(self, server):
        for index in self.base_indices:
            post_index(index, weak_network=True, server=server)
        for index in self.commentaryIndices:
            post_index(index, server=server)
        for version in self.versionList:
            print version['ref']
            post_text(version['ref'], version['version'], index_count='on', weak_network=True, server=server)
        post_link(self.linkSet, server=server)

    def post_commentary_terms_and_categories(self, server):
        for term in self.terms:
            post_term(term, server=server)
        for index in self.commentaryIndices:
            category = index['categories']
            add_category(category[-1], category, server=server)


def check_chapters():
    xml_files = filter(lambda x: None if not re.search('\.xml$', x) else x, os.listdir('./XML'))
    for xml in xml_files:
        root = DCXMLsubs.parse("XML/{}".format(xml), silence=True)
        coms = root.body.commentaries
        if coms is not None:
            issues = root.check_commentary_chapters()
            if len(issues) > 0:
                print xml
                for issue in issues:
                    print u'commentary : {}'.format(issue.get_author())
                    issue.print_bad_chapters()


def basic_test_suite():
    root = DCXMLsubs.parse("XML/tractate-avot_drabi_natan-xml.xml", silence=True)
    basetext = root.getBaseTextArray()
    ja_to_xml(basetext, ['Section', 'Segment'], 'base_text.xml')
    # root.review_commentaries()
    # root.check_commentary_chapters()
    comms = root.body.commentaries
    for c in comms.get_commentary():
        if comms.is_linked_commentary(c) and c.get_author() != 'UNKNOWN':
            parsed = c.parse_linked()
            ja_to_xml(parsed, ['Chapter', 'Verse', 'Comment'], 'commentary.xml')
            break


def first_word_indices(string_list):
    """
    Get a list of indices representing the index of the first word of each string should the list be collapsed to a list
    of words
    :param string_list: list of strings
    :return: list of integers
    """
    indices = []
    for line in string_list:
        if len(indices) == 0:
            indices.append(len(line.split()))
        else:
            indices.append(len(line.split()) + indices[-1])
    return indices


def cleaner(input_string):
    assert isinstance(input_string, basestring)
    if len(input_string.split()) > 8:
        input_string = u' '.join(input_string.split()[:8])
    pattern = u'\u05d5?(\u05db|\u05d2)\u05d5\u05f3?'
    match = re.search(pattern, input_string)
    if match is None:
        return input_string
    if match.start() > 6 and (match.start() > len(input_string) / 2):
        return re.sub(u'\u05d5?(\u05db|\u05d2)\u05d5\u05f3?.*', u'', input_string, count=1)
    elif match.start() > 6 and (match.start() < len(input_string) / 2):
        return re.sub(u'.*?{}'.format(pattern), u'', input_string, count=1)
    else:
        return re.sub(pattern, u'', input_string)


def get_commentary_index(doc_root, commentator):
    assert isinstance(doc_root, DCXMLsubs.bookSub)
    for i, commentary in enumerate(doc_root.body.commentaries.get_commentary()):
        assert isinstance(commentary, DCXMLsubs.commentarySub)
        if commentary.author.get_valueOf_() == commentator:
            return i
    else:
        raise AttributeError("That commentator does not exist")


def fix_commentator(filename, commentator, overwrite=False):
    root = DCXMLsubs.parse("XML/{}.xml".format(filename), silence=True)
    base_text = root.getBaseTextArray()
    commentary = root.body.commentaries.commentary[get_commentary_index(root, commentator)]
    assert isinstance(commentary, DCXMLsubs.commentarySub)
    locations = []
    # assert len(base_text) == len(commentary.get_chapter())
    # counter = 1
    for comment_chapter in commentary.get_chapter():
        chapter_index = int(comment_chapter.num)
        base_chapter = base_text[chapter_index - 1]
        print 'fixing chapter {}'.format(chapter_index)

        book_text = [bleach.clean(segment, tags=[], strip=True) for segment in base_chapter]
        seg_indices = first_word_indices(book_text)
        word_list = u' '.join(book_text).split()
        dh_list = [re.sub(ur' (\.|:)', ur'\1', p.dh.get_valueOf_()) for p in comment_chapter.get_phrase()]
        matches = match_text(word_list, dh_list, dh_extract_method=cleaner, place_all=False, strict_boundaries=True, char_threshold=0.4)
        locations.append([bisect.bisect_right(seg_indices, match[0]) if match[0] >= 0 else match[0] for match in matches['matches']])

    commentary.set_verses(locations)
    commentary.correct_phrase_verses()

    if overwrite:
        outfile = filename
    else:
        outfile = '{}_test'.format(filename)
    # with codecs.open('XML/{}.xml'.format(outfile), 'w', 'utf-8') as out:
    #     root.export(out, level=1)
    clean_export(root, 'XML/{}.xml'.format(outfile))


def book_by_page(root_element):
    """
    Get the pages of the book. Helpful for matching where chapter is unknown.
    Generates a dictionary of dictionaries. The keys of the outer dictionary are the page numbers. The inner
    dictionaries have the keys "word_list", "chpt-vrs", "indices". "word_list" contains a list of all words on the page.
    "chpt-vrs" contains the chapters and verses of the verses on the page. "indices" contains the indices at which the
    verses end on the page. To find the verse of a phrase, search for the location of its match in the word_list.
    bisect_left() from that index to the indices,give the location of the appropriate chapter-verse information in
    the "chpt-vrs" list.
    :param DCXMLsubs.bookSub root_element:
    :return: dict
    """

    def add_words_to_page(page, words_to_add):
        """
        Add words to a page, and get the index at which the added words ended
        :param list page: list of words
        :param unicode words_to_add: string or unicode
        :return: length of page after addition - use bisect left to determine which verse this came from
        """
        words_to_add.replace(u'\n', u' ')
        page.extend(words_to_add.split())
        return len(page)

    page_numbers = root_element.get_page_numbers()
    pages = dict([(num, {
        'word_list': [],
        'chpt-vrs': [],
        'indices': []
    }) for num in page_numbers])

    iter_pages = iter(page_numbers)
    current_page = pages[iter_pages.next()]
    hit_last_page = False

    verses = root_element.get_base_verses()
    for verse in verses:
        container = []
        for content in verse.get_p()[0].content_:
            if content.getCategory() == content.CategoryText:
                container.append(content.getValue())
            elif content.getName() == "xref":
                continue
            elif content.getName() == "pgbrk":
                index = add_words_to_page(current_page['word_list'], u' '.join(container))
                current_page['chpt-vrs'].append(verse.num)
                current_page['indices'].append(index)
                container = []
                try:
                    current_page = pages[iter_pages.next()]
                except StopIteration:
                    if hit_last_page:
                        raise StopIteration("Hit last page more than once!")
                    hit_last_page = True
            else:
                raise AttributeError("Not text, xref or pgbrk")

        index = add_words_to_page(current_page['word_list'], u' '.join(container))
        current_page['chpt-vrs'].append(verse.num)
        current_page['indices'].append(index)

    return pages

def fix_commentator_by_page(filename, commentator, overwrite=False):

    root = DCXMLsubs.parse("XML/{}.xml".format(filename), silence=True)
    commentary = root.body.commentaries.commentary[get_commentary_index(root, commentator)]
    assert isinstance(commentary, DCXMLsubs.commentarySub)

    page_map = book_by_page(root)
    phrases_by_page = commentary.phrases_by_page()

    for page in phrases_by_page.keys():  # Not every page necessarily has a commentary phrase
        dh_list = [re.sub(ur' (\.|:)', ur'\1', phrase.dh.get_valueOf_()) for phrase in phrases_by_page[page]]

        matches = match_text(page_map[page]['word_list'], dh_list, dh_extract_method=cleaner, place_all=False,
                             strict_boundaries=True, char_threshold=0.4)

        locations = [bisect.bisect_left(page_map[page]['indices'], match[0]) if match[0] >= 0 else match[0]
                     for match in matches['matches']]

        for location, phrase in zip(locations, phrases_by_page[page]):
            if location == -1:
                phrase.subchap = '0'
            else:
                phrase.subchap = page_map[page]['chpt-vrs'][location]

    if not overwrite:
        filename += '_test'
    # with codecs.open("XML/{}.xml".format(filename), 'w', 'utf-8') as outfile:
    #     root.export(outfile, level=1)
    clean_export(root, "XML/{}.xml".format(filename))

def output_missing_links(filename):
    root = DCXMLsubs.parse('./XML/{}'.format(filename), silence=True)
    commentary = root.body.commentaries.get_commentary()[-1]
    for phrase in commentary.get_phrase():
        if DCXMLsubs.commentStore.get(phrase.id) is None:
            print phrase.id


def kill_internal_verses(filename, overwrite=True):
    """
    Some files have bad verse breakup in the Vilna printing. This method runs through a file, ensuring that for each
    chapter, only a single verse exists on a given chapter, which encloses the entire text of the chapter.
    """
    with open('./XML/{}'.format(filename)) as infile:
        soup = BeautifulSoup(infile, 'xml')
    chapters = soup.find('body').find_all('chapter', recursive=False)
    for chapter in chapters:
        verses = chapter.find_all('verse')
        if len(verses) > 1:
            first_verse = verses[0]
            for verse in verses[1:]:
                first_verse.p.append(u' ')
                first_verse.p.append(verse)
                for p in verse.find_all('p'):
                    p.unwrap()
                verse.unwrap()
    if overwrite:
        outfile_name = './XML/{}'.format(filename)
    else:
        outfile_name = './XML/temp_{}'.format(filename)
    with codecs.open(outfile_name, 'w', 'utf-8') as outfile:
        outfile.write(unicode(soup))


def split_chapters_by_pattern(filename, pattern, offset=0, overwrite=True):
    """
    Given a chapter, split the chapter into verses based on a pattern
    :param str filename: full path of file to edit
    :param unicode pattern: exact pattern on which to split
    :param int offset: Useful to skip redundant strings that the split may create. For example, the first appearance of
    "pattern" may create a redundant first string consisting of nothing but spaces.
    :param overwrite: If True will overwrite original file
    """

    with open(filename) as infile:
        soup = BeautifulSoup(infile, 'xml')
    for chapter in soup.book.body.find_all('chapter', recursive=False):
        p = chapter.verse.p
        chapter_text = re.split(pattern, u''.join([unicode(i) for i in p.children]))
        if len(chapter_text[offset:]) == 0:
            continue
        chapter.clear()

        for v_index, verse in enumerate(chapter_text[offset:]):
            verse = u'<verse num="ch{}-v{}"><p>{}</p></verse>'.format(chapter['num'], v_index+1, verse)
            verse = BeautifulSoup(verse, 'xml').verse
            chapter.append(verse)
    if overwrite:
        outfile_name = filename
    else:
        outfile_name = './XML/test.xml'

    with codecs.open(outfile_name, 'w', 'utf-8') as outfile:
        outfile.write(unicode(soup))


def clean_export(root_tag, filename):
    temp_file = StringIO.StringIO()
    root_tag.export(temp_file, level=1)
    out_text = temp_file.getvalue()
    temp_file.close()
    out_text = out_text.replace(u' xmlns:t="http://www.w3.org/namespace/"', u'')
    out_text = out_text.replace(u't:', u'')
    out_text = re.sub(ur'^\n+', u'\n', out_text)
    out_text = re.sub(ur' +', u' ', out_text)
    out_text = re.sub(ur'\n ', u'\n', out_text)

    with codecs.open(filename, 'w', 'utf-8') as outfile:
        outfile.write(u"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE book SYSTEM "sefaria.dtd">""")
        outfile.write(out_text)


def unmatched_comments(filename, commentator):

    def get_phrase_page(phrase_id):
        return re.search(u'ph-[0-9]{1,2}-([0-9A-Z]{1,3})-[0-9]{1,2}', phrase_id).group(1)

    issues = []
    root = DCXMLsubs.parse(filename, silence=True)
    commentary = root.body.commentaries.get_commentary()[get_commentary_index(root, commentator)]
    for chapter in commentary.get_chapter():
        for phrase in chapter.get_phrase():
            if phrase.subchap == '0':
                issues.append({
                    'page': get_phrase_page(phrase.id),
                    'dh': phrase.dh.get_valueOf_(),
                    'id': phrase.id
                })
    with open(u'{} on {} issues.csv'.format(commentator, root.id), 'w') as outfile:
        writer = csv.DictWriter(outfile, ['id', 'page', 'dh', 'chapter', 'verse'])
        writer.writeheader()
        writer.writerows(issues)

# commentators = [u'כסא רחמים', u'הגהות מהריעב״ץ', u'תומת ישרים']
# for com in commentators:
#     unmatched_comments('XML/tractate-avot_drabi_natan-xml3.xml', com)

def clear_subchaps(filename, commentator, chap_number=None, overwrite=False):
    def condition(chapter_element):
        if chap_number is None:
            return True
        else:
            return int(chapter_element.num) == chap_number

    root = DCXMLsubs.parse(filename, silence=True)
    commentary = root.body.commentaries.get_commentary()[get_commentary_index(root, commentator)]
    for chapter in commentary.get_chapter():
        if condition(chapter):
            for phrase in chapter.get_phrase():
                phrase.subchap = None

    if not overwrite:
        filename = filename.replace('.xml', '_test.xml')
    clean_export(root, filename)


def correct_commentary_chapters(filename, commentator_name, overwrite=False):
    """
    Commentaries that do not have a correct chapter breakup are matched "by page". These commentaries do have have the
    subchaps set in the "ch<n>-v<m>" format once the alignment is complete. This method seeks to correctly place the
    chapter elements, as well as set the phrase "subchap" attribute to a simple integer (in str format).
    :param filename:
    :param commentator_name:
    :param overwrite:
    """
    with open(filename) as infile:
        soup = BeautifulSoup(infile, 'xml')
    commentator = soup.find(lambda x: x.name=='commentary' and x.author.get_text()==commentator_name)
    assert isinstance(commentator, Tag)

    for phrase in commentator.find_all('phrase'):
        match = re.search('ch([0-9]{1,2})-v([0-9]{1,2})', phrase.attrs['subchap'])
        chapter, verse = match.group(1), match.group(2)
        phrase.attrs['subchap'] = verse

        # if this phrase in in the correct chapter, we can move on to the next one
        if phrase.parent['num'] == chapter:
            continue

        # does the correct chapter even exist?
        correct_chapter = commentator.find(lambda x: x.name=='chapter' and x['num']==chapter)

        if correct_chapter is None:
            correct_chapter = soup.new_tag(name='chapter', num=chapter)
            chapters = commentator.find_all('chapter', recursive=False)
            insert_location = bisect.bisect([int(c['num']) for c in chapters], int(chapter))
            if insert_location == len(chapters):
                chapters[-1].insert_after(correct_chapter)
            else:
                chapters[insert_location].insert_before(correct_chapter)

        correct_chapter.append(phrase)

    if not overwrite:
        filename = filename.replace('.xml', '_test.xml')
    with codecs.open(filename, 'w', 'utf-8') as outfile:
        outfile.write(unicode(soup))
