# encoding=utf-8

import codecs
import re
from data_utilities.util import ja_to_xml, multiple_replace, traverse_ja, file_to_ja_g
from data_utilities.sanity_checks import TagTester
from sources.functions import post_text, post_index, post_link
from sefaria.model import *
from sefaria.datatype.jagged_array import JaggedArray
import json

def parse_he(filename):
    """
    :returns a dictionary, key: name of book, value: JaggadArray obj of the ja for the book
    """
    replace_dict = {u'@(11|44|99)': u'<b>', u'@(33|55)': u'</b>', ur'@22\(([\u05d0-\u05ea]{1,3})\)': u'',
                    ur'@(22|77)': u''}
    def cleaner(my_text):
        new = []
        for line in my_text:
            line = multiple_replace(line,replace_dict,using_regex=True)
            new.append(line)

        return new

    regs = [ur'@00(?P<gim>)',ur'@02(?P<gim>[\u05d0-\u05ea]{1,3})', ur'@22\((?P<gim>[\u05d0-\u05ea]{1,3})\)']  # ,ur'@77'
    with codecs.open(filename, 'r', 'utf-8') as fp:
        lines = fp.readlines()
    starting = None
    # check if we got to the end of the legend and change to started
    # clean all lines of Parasha start with @01
    cleaned = []
    dh_list = []
    for line_num, line in enumerate(lines):
        if line == u'\n':
            starting = line_num + 1
        if starting and not re.search(u'@01', line) and not line.isspace():
            dh_recognize = re.compile(ur'@11(.*?)@33')
            if dh_recognize.search(line):
                dh_list.append(dh_recognize.search(line).group(1))
            line = re.sub(dh_recognize, ur'#<b>\1</b>', line)
            line = re.split(ur'#',line)
            if isinstance(line, basestring):
                cleaned.append(line)
            else:
                cleaned.extend(line)

    tt_ja = file_to_ja_g(4, cleaned, regs, cleaner, gimatria = True, group_name = 'gim', grab_all=[False, False, False]).array()
    Pentateuch = ['Genesis','Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']
    parsed_texts = dict({book:ja for book, ja in zip(Pentateuch,tt_ja)})

    for book,ja in zip(Pentateuch,tt_ja):
        ja_to_xml(ja, ['perek', 'pasuk', 'comment'], 'tur_{}.xml'.format(book))

    # for str in  dh_list:
    #     print str
    return parsed_texts


def parse_en(filename):
    with codecs.open(filename, 'r', 'utf-8') as fp:
        lines = fp.readlines()
    ja = JaggedArray([[[[]]]])
    placing = u'(\s*[0-9]{1,2}),([0-9]{1,2})-?[0-9]*\.'  # the regex to find the indexing on Monk
    # q1, q2 = ur'“', ur'”' # Rabbi Monk uses these to enclose translation of a pasuk
    # dh_reg = ur'([\u05d0 - \u05ea]*), *({}.*?{})'.format(q1, q2)
    replace_dict = {placing: u'', u'@': ''}
    temp = []
    indices = [0]*3
    for line in lines:
        pasuk_dh = re.match(placing, line)
        reg_dh = re.search(ur'@([\u05d0-\u05ea|\\s]*)',line) #  reg_dh = re.search(ur'([\u05d0-\u05ea]+, *“.*?”)',line)
        line = multiple_replace(line, replace_dict, using_regex=True)
        if pasuk_dh or reg_dh:
            temp = ' '.join(temp)
            ja.set_element(indices, temp, [])
            temp = []
            if pasuk_dh:
                indices = [int(pasuk_dh.group(1))-1, int(pasuk_dh.group(2))-1, indices[2]]
                indices[2] = 0
            elif reg_dh:
                indices[2] += 1
        if not line.isspace() and not re.match(ur' *Parshat *(\S+) *(\S+)? *', line):  # don't put into array names of Parasha or empty lines
            temp.append(line)

    ja_to_xml(ja.array(), ['perek', 'pasuk', 'comment'], '{}.xml'.format(re.match('(.*)\.',filename).group(1)))
    return ja


def parse_all_en():
    en_texts = {}
    pentateuch = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']
    for book in pentateuch:
        parsed_book = parse_en('en_tur_{}.txt'.format(book.lower()))
        en_texts[book] = parsed_book
    return en_texts


def tt_schema():
    record_root = SchemaNode()
    record_root.add_title('Tur HaAroch', 'en', True)
    record_root.add_title(u'הטור הארוך', 'he', True)
    record_root.key = 'Tur HaAroch'
    # introduction ja node
    intro_node = JaggedArrayNode()
    intro_node.depth = 1
    intro_node.add_primary_titles(u'Introduction', u'הקדמה')
    intro_node.add_structure(['Paragraph'])
    record_root.append(intro_node)
    # book nodes
    Pentateuch = library.get_indexes_in_category('Torah')
    Chumshai = [u'בראשית',u'שמות',u'ויקרא',u'במדבר',u'דברים']
    #loop on the Pentateuch to create 5 the ja nodes
    for i in range(5):
        book_node = JaggedArrayNode()
        book_node.add_primary_titles('{}'.format(Pentateuch[i]),u'{}'.format(Chumshai[i]),True)
        book_node.add_structure(['Chapter', 'Verse', 'Comment'])
        book_node.toc_zoom = 2
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


def intro_text_post():
    version_dict = {
        'versionTitle': 'Perush al ha-Torah, Hanover, 1838',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001935796',
        'language': 'he',
        'text': [u'צריך להקליד את ההקדמה'] # note: if ever coming back to this script
    }
    post_text('Tur HaAroch, Introduction', version_dict)


def en_tt_text_post(en_text):
    for key in en_text.keys():
        version_dict = {
            'versionTitle': 'Tur on the Torah, trans. Eliyahu Munk',
            'versionSource': 'http://www.urimpublications.com/Merchant2/merchant.mv?Screen=PROD&Store_Code=UP&Product_Code=TUR&Category_Code=bde',
            'language': 'en',
            'text': en_text[key].array()
        }
        post_text('Tur HaAroch, {}'.format(key), version_dict)


def links(text_dict):
    links = []
    for book in text_dict.keys():
        for dh in traverse_ja(text_dict[book]):
            perek = (dh['indices'][0] + 1)
            pasuk = (dh['indices'][1] + 1)
            comment = (dh['indices'][2] + 1)
            link = (
                {
                    "refs": [
                        'Tur HaAroch, {} {}:{}:{}'.format(book, perek, pasuk, comment),
                        '{} {}:{}'.format(book,perek, pasuk),
                    ],
                    "type": "commentary",
                    "auto": True,
                    "generated_by": "tur_torah_parser"
                })
            # append to links list
            links.append(link)
    return links

# the same as links just works book by book really could merge both functions together. but didn't want to change code.
# def relinks(ja_book):
#     links = []
#     for dh in traverse_ja(ja_book):
#             perek = (dh['indices'][0] + 1)
#             pasuk = (dh['indices'][1] + 1)
#             comment = (dh['indices'][2] + 1)
#             link = (
#                 {
#                     "refs": [
#                         'Tur HaAroch, {} {}:{}:{}'.format(book, perek, pasuk, comment),
#                         '{} {}:{}'.format(book,perek, pasuk),
#                     ],
#                     "type": "commentary",
#                     "auto": True,
#                     "generated_by": "tur_torah_parser"
#                 })
#             # append to links list
#             links.append(link)
#     return links

def test_accercy(tag, filename):
    with codecs.open(filename, 'r', 'utf-8') as fp:
        tag_tester = TagTester(tag, fp)
        appearences = tag_tester.appearances
        print appearences


def test_boolean_ja(book, ja1, ja2):
    ja1set = set()
    for i,x in enumerate(ja1):
        for j,y in enumerate(x):
            for k,z in enumerate(y):
                ja1set.add((i+1,j+1,k+1))
    ja2set = set()
    for i,x in enumerate(ja2):
        for j,y in enumerate(x):
            for k,z in enumerate(y):
                ja2set.add((i+1,j+1,k+1))


    missing = ja1set.symmetric_difference(ja2set)
    miss_list = list(missing)
    miss_list.sort()
    print len(miss_list)
    for x in miss_list:
        print '{}.{}.{}.{}'.format(book, x[0], x[1], x[2])


if __name__ == "__main__":
    # parse
    parsed_he = parse_he('tur_he.txt')
    # parsed_en = parse_all_en()
    # # index
    # tt_index()
    # # post
    # intro_text_post()
    # tt_text_post(parsed_he)
    # en_tt_text_post(parsed_en)
    # link
    # links = links(parsed_he)
    # post_link(links)

    # these files were coppied from Draft back to here.

    # with open('Tur HaAroch - en - merged.json') as pt:
    #     tur_en = json.load(pt)
    #
    # with open('Tur HaAroch - he - merged.json') as pt:
    #     tur_he = json.load(pt)
    #
    # for book in ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']:
    #     print book
    #     ja_he = tur_he['text'][book]
    #     ja_en = tur_en['text'][book]
    #     # test_boolean_ja('Tur HaAroch, {}'.format(book),ja_he, ja_en)
    #     book_link = relinks(ja_he)
    #     post_link(book_link)
    #     print book, book_link