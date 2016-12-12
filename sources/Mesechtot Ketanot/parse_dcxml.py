import DCXMLsubs
import os
import re
import unicodecsv as csv
from data_utilities.util import ja_to_xml


class Collection:

    def __init__(self):
        self.file_map = self.get_file_mapping()
        self.commentarySchemas = {}
        self.versionList = []
        self.linkSet = []

    @staticmethod
    def get_file_mapping():
        with open('file_to_index_map.csv') as infile:
            lines = infile.readlines()
        reader = csv.DictReader(lines)
        return [row for row in reader]


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
