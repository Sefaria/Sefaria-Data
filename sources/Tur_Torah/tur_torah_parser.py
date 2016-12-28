# encoding=utf-8

import codecs
import re
from data_utilities.util import ja_to_xml, multiple_replace, traverse_ja , file_to_ja_g
from sources.functions import post_text, post_index, post_link
from sefaria.model import *
from sefaria.datatype.jagged_array import JaggedArray

def parse_he(filename):
    replace_dict = {u'@(11|44|99)':u'<b>',u'@(33|55)' : u'</b>', ur'@22\(([\u05d0-\u05ea]{1,3})\)':u'',
                    ur'@22': u''}
    def cleaner(my_text):
        new = []
        for line in my_text:
            line = multiple_replace(line,replace_dict,using_regex=True)
            new.append(line)

        return ''.join(new) # join is reduces it to depth 2 without comments so it is like the en, return new for depth 3.

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
        if starting and not re.search(u'@01', line) and not line.isspace():
            cleaned.append(line)

    tt_ja = file_to_ja_g(4, cleaned, regs, cleaner, gimatria = True, group_name = 'gim', grab_all=[False,False,True]).array()
    Pentateuch = ['Genesis','Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']
    parsed_texts = dict({book:ja for book, ja in zip(Pentateuch,tt_ja)})

    for book,ja in zip(Pentateuch,tt_ja):
        ja_to_xml(ja, ['perek', 'pasuk', 'comment'], 'tur_{}.xml'.format(book))
    return parsed_texts

def parse_en(filename, parsed_he = False):
    with codecs.open(filename, 'r', 'utf-8') as fp:
        lines = fp.readlines()
    ja = JaggedArray([[[]]])
    temp = []
    indices = [-1]*2
    for line in lines:
        dh = re.match(u'(\s*[0-9]{1,2}),([0-9]{1,2})-?[0-9]*\.', line)
        if dh:
            temp = ' '.join(temp)
            ja.set_element(indices, temp, [])
            temp = [line]
            indices = [int(dh.group(1))-1, int(dh.group(2))-1]
        if not line.isspace():
            temp.append(line)

    ja_to_xml(ja.array(), ['perek', 'pasuk'], '{}.xml'.format(filename))
    return ja


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

def boolean_ja(ja):
    bool = JaggedArray([[]])
    if not isinstance(ja,list):
        ja = ja.array()
    for dh in traverse_ja(ja):
        if dh['data']:
            bool.set_element(dh['indices'][:2], True, pad=False)
            #testing where there is more then one comment on a pasuk (in the he)
            if len(dh['indices']) > 2 and dh['indices'][2] > 0:
                print dh['indices']
        else:
            bool.set_element(dh['indices'][:2], False, pad=False)
    print bool.array()
    return bool.array()


if __name__ == "__main__":
    p_he = parse_he('tur_he.txt')
    pentateuch = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']
    # testing to find where the he vs en differ
    for book in pentateuch:
        p_en = parse_en('en_tur_{}.txt'.format(book.lower()))
        print book
        b_he = boolean_ja(p_en)
        b_en = boolean_ja(p_he['{}'.format(book)])
        i = 0
        for he, en in zip(b_he, b_en):
            i += 1
            if len(he) != len(en):
                print book, i

    # tt_schema()
    # tt_index()
    # tt_text_post(parsed)

