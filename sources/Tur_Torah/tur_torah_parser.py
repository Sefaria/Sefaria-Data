# encoding=utf-8

import codecs
import re
from data_utilities.util import ja_to_xml, multiple_replace, traverse_ja , file_to_ja_g
from sources.functions import post_text, post_index, post_link
from sefaria.model import *
from sefaria.datatype.jagged_array import JaggedArray

def parse_he(filename):
    replace_dict = {u'@(11|44|99)':u'<b>',u'@(33|55)' : u'</b>', ur'@22\(([\u05d0-\u05ea]{1,3})\)':u''}
    def cleaner(my_text):
        new = []
        for line in my_text:
            line = multiple_replace(line,replace_dict,using_regex=True)
            new.append(line)
        return new

    regs = [ur'@00(?P<gim>)',ur'@02(?P<gim>[\u05d0-\u05ea]{1,3})', ur'@22\((?P<gim>[\u05d0-\u05ea]{1,3})\)']
    with codecs.open(filename, 'r', 'utf-8') as fp:
        lines = fp.readlines()
    starting = None
    # check if we got to the end of the legend and change to started
    # clean all lines of Parasha start with @01
    cleaned = []
    for line_num, line in enumerate(lines):
        if line == u'\n':
            starting = line_num + 1
        if starting and not re.search(u'@01', line):
            cleaned.append(line)

    tt_ja = file_to_ja_g(4, cleaned, regs, cleaner, gimatria = True, group_name = 'gim', grab_all=[False,False,True]).array()
    Pentateuch = ['Genesis','Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']
    parsed_texts = dict({book:ja for book, ja in zip(Pentateuch,tt_ja)})

    for book,ja in zip(Pentateuch,tt_ja):
        ja_to_xml(ja,['Book','perek','pasuk','comment'], 'tur_{}.xml'.format(book))

    return parsed_texts

def parse_en(filename, parsed_he):
    with codecs.open(filename, 'r', 'utf-8') as fp:
        lines = fp.readlines()
    ja = JaggedArray([[[]]])
    for line in lines:
        dh = re.search(u'(\d),(\d\d)\.', line)
        if dh:
            indices = [int(dh.group(1)), int(dh.group(2))]
            ja.set_element(indices, line, [])


def tt_schema():
    record_root = SchemaNode()
    record_root.add_title('Tur HaAroch', 'en', True)
    record_root.add_title(u'הטור הארוך', 'he', True)
    record_root.key = 'Tur HaAroch'

    Pentateuch = ['Genesis','Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']
    Chumshai = [u'בראשית',u'שמות',u'ויקרא',u'במדבר',u'דברים']
    #loop on the Pentateuch to create 5 ja nodes
    for i in range(5):
        book_node = JaggedArrayNode()
        book_node.add_primary_titles('{}'.format(Pentateuch[i]),u'{}'.format(Chumshai[i]),True)
        book_node.add_structure(['Chapter', 'Verse', 'Comment'])
        record_root.append(book_node)

    record_root.validate()

    return record_root


def tt_index():
    index_dict = {
        'title': 'Tur HaAroch',
        'categories': ['Commentary2', 'Tanakh', 'Tur HaAroch'],
        'schema': tt_schema().serialize()  # This line converts the schema into json
    }
    post_index(index_dict)


def tt_text_post(text_dict):
    for key in text_dict.keys():
        version_dict = {
            'versionTitle': 'Perush al ha-Torah, Hanover, 1838',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001935796',
            'language': 'he',
            'text': text_dict[key]
        }
        post_text('Tur HaAroch, {}'.format(key), version_dict)


if __name__ == "__main__":
    parsed = parse_he('tur_he.txt')
    parse_en('tur_en.txt',parsed)
    # tt_schema()
    # tt_index()
    # tt_text_post(parsed)