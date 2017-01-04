# encoding=utf-8

import DCXMLsubs
import os
import re
import bleach
import bisect
import codecs
import unicodecsv as csv
from data_utilities.util import ja_to_xml
from data_utilities.dibur_hamatchil_matcher import match_text
from sources.functions import post_text, post_index, post_link


class Collection:

    def __init__(self):
        self.file_map = self.get_file_mapping()
        self.commentarySchemas = {}
        self.versionList = []
        self.linkSet = []
        self.base_indices = []

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
                if self.commentarySchemas.get(author) is None:
                    self.commentarySchemas[author] = commentary.build_node()
                self.commentarySchemas[author].append(root.commentary_ja_node(en_title, he_title))

                version = self.get_version_skeleton()
                if commentaries.is_linked_commentary(commentary):
                    version['text'] = commentary.parse_linked()
                else:
                    version['text'] = commentary.parse_unlinked()

                ref = '{}, {}'.format(DCXMLsubs.commentatorNames[author], en_title)
                self.versionList.append({'ref': ref, 'version': version})
            self.linkSet.extend(root.get_stored_links(en_title))

    def parse_collection(self, include_commentaries=True, skip_exceptions=False):
        """
        Parse entire collection
        :param include_commentaries: Set to False to skip all commentaries
        :param handle_exceptions: Used only for debugging and development, if set to True, will push through all
        exceptions and upload those files on which exceptions were not raised
        :return:
        """
        for mapping in self.file_map:
            assert isinstance(mapping, dict)
            try:
                self.parse_file(mapping['filename'], mapping['en_title'], mapping['he_title'], include_commentaries)
            except Exception as e:
                print 'Problem found in {}'.format(mapping['filename'])
                if skip_exceptions:
                    raise e

    @staticmethod
    def get_version_skeleton():
        return {
            'versionTitle': 'Talmud Bavli, Vilna 1883 ed.',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957',
            'language': 'he',
        }

    def post(self):
        for index in self.base_indices:
            post_index(index, weak_network=True)
        for he_author in self.commentarySchemas.keys():
            en_author = DCXMLsubs.commentatorNames[he_author]
            index = {
                'title': en_author,
                'categories': ['Commentary2', 'Masechtot Ketanot', en_author],
                'schema': self.commentarySchemas[he_author].serialize()
            }
            post_index(index)
        for version in self.versionList:
            post_text(version['ref'], version['version'], index_count='on', weak_network=True)
        post_link(self.linkSet)


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
    assert len(base_text) == len(commentary.get_chapter())
    counter = 1
    for base_chapter, comment_chapter in zip(base_text, commentary.get_chapter()):
        print 'fixing chapter {}'.format(counter)
        book_text = [bleach.clean(segment, tags=[], strip=True) for segment in base_chapter]
        seg_indices = first_word_indices(book_text)
        word_list = u' '.join(book_text).split()
        dh_list = [p.dh.get_valueOf_() for p in comment_chapter.get_phrase()]
        matches = match_text(word_list, dh_list, dh_extract_method=cleaner, place_all=False)
        locations.append([bisect.bisect_right(seg_indices, match[0]) if match[0] >= 0 else match[0] for match in matches['matches']])
        counter += 1
    commentary.set_verses(locations)
    commentary.correct_phrase_verses()

    if overwrite:
        outfile = filename
    else:
        outfile = '{}_fixed'.format(filename)
    with codecs.open('XML/{}.xml'.format(outfile), 'w', 'utf-8') as out:
        root.export(out, level=1)


# root = DCXMLsubs.parse('XML/tractate-avot_drabi_natan-xml2.xml', silence=True)
# for i in root.chapter_page_map():
#     print 'chapter {}: first: {} last: {}'.format(i['num'], i['first'], i['last'])
# for phrase in root.body.commentaries.get_commentary()[2].get_phrase():
#     if DCXMLsubs.commentStore.get(phrase.id) is None:
#         print phrase.id

