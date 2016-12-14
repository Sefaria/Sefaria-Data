import DCXMLsubs
import os
import re
import unicodecsv as csv
from data_utilities.util import ja_to_xml
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

    def parse_file(self, filename, en_title, he_title):

        root = DCXMLsubs.parse('XML/{}'.format(filename), silence=True)
        version = self.get_version_skeleton()
        version['text'] = root.getBaseTextArray()
        self.versionList.append({'ref': en_title, 'version': version})
        self.base_indices.append(root.get_base_index(en_title, he_title))
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

    def parse_collection(self):
        for mapping in self.file_map:
            assert isinstance(mapping, dict)
            self.parse_file(mapping['filename'], mapping['en_title'], mapping['he_title'])

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
