# encoding=utf-8

import codecs
import re
from parsing_utilities.util import ja_to_xml, multiple_replace, traverse_ja , file_to_ja, getGematria
from sources.functions import post_text, post_index, post_link
from sefaria.model import *
from sefaria.datatype.jagged_array import JaggedArray

def file_to_ja_g(depth, infile, expressions, cleaner,grab_all=False):
    """
    Designed to be the first stage of a reusable parsing tool. Adds lines of text to the Jagged
    Array in the desired structure (Chapter, verse, etc.)
    This function is a modulation of the origanal file_to_ja because it deals with gimatria letters
    so to place the correct chapters and segments in the currect places according to the hebrew letter numbering.
    Ofcourse it also puts in the padding where needed. (_g stands for Gimatria.
    :param depth: depth of the JaggedArray.
    :param infile: Text file to read from
    :param expressions: A list of regular expressions with which to identify section (chapter) level. Do
    not include an expression with which to break up the segment levels.
    :param cleaner: A function that takes a list of strings and returns an array with the text parsed
    correctly. Should also break up and remove unnecessary tagging data.
    :param grab_all: If set to true, will grab the lines indicating new sections.
    :return: A jagged_array with the text properly structured.
    """

    # instantiate ja
    # structure = reduce(lambda x,y: [x], range(depth-1), [])
    # ja = JaggedArray(structure)
    ja = JaggedArray([])
    # ensure there is a regex for every level except the lowest
    if depth - len(expressions) != 1:
        raise AttributeError('Not enough data to parse. Need {} expressions, '
                             'received {}'.format(depth-1, len(expressions)))

    # compile regexes, instantiate index list
    regexes, indices = [re.compile(ex) for ex in expressions], [-1]*len(expressions)
    temp = []

    # loop through file
    for line in infile:

        # check for matches to the regexes
        for i, reg in enumerate(regexes):
            found = reg.search(line)
            if found:
                # check that we've hit the first chapter and verse
                if indices.count(-1) == 0:
                    ja.set_element(indices, cleaner(temp), [])
                    temp = []

                    if grab_all:
                        temp.append(line)
                gimt = getGematria(found.group('gim'))
                if gimt != 0:
                    indices[i] = gimt - 1
                else:
                    indices[i] += 1
                indices[i+1:] = [-1 if x >= 0 else x for x in indices[i+1:]]
                break

        else:
            if indices.count(-1) == 0:
                temp.append(line)
    else:
        ja.set_element(indices, cleaner(temp), [])

    return ja

def parse_general(filename):

    def cleaner(my_text):
        return my_text

    regs = [u'@22 ?(\u05e4\u05e8\u05e7)? ?(?P<gim>[\u05d0-\u05ea]{1,3})', u'\{(?P<gim>[\u05d0-\u05ea]{1,3})\}']
    with codecs.open(filename, 'r', 'utf-8') as infile:
        bs_ja = file_to_ja_g(3, infile, regs, cleaner).array()
        print(bs_ja)
        ja_to_xml(bs_ja,['perek','pasuk','comment'], '{}xml'.format(re.search(u'.*\.',filename).group()))
        return bs_ja

def parse_all():
    ja_bershit = parse_general('bs_genesis.txt')
    ja_shemot = parse_general('bs_exodus.txt')
    ja_vikra = parse_general('bs_leviticus.txt')
    ja_bamidbar_1 = parse_general('bs_numbers1.txt')
    ja_bamidbar_2 = parse_general('bs_numbers2.txt')
    ja_devarim_1 = parse_general('bs_deuteronomy1.txt')
    ja_devarim_2 = parse_general('bs_deuteronomy2.txt')
    parsed_text = {'Genesis ': ja_bershit,
                   'Exodus ': ja_shemot,
                   'Leviticus ' : ja_vikra,
                   'Numbers part 1': ja_bamidbar_1,
                   'Numbers part 2': ja_bamidbar_2,
                   'Deuteronomy part 1': ja_devarim_1,
                   'Deuteronomy part 2': ja_devarim_2,
                   }
    return parsed_text

def bs_schema():
    record_root = SchemaNode()
    record_root.add_title('Bekhor Shor', 'en', True)
    record_root.add_title(u'בכור שור', 'he', True)
    record_root.key = 'Bekhor Shor'

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

def bs_index():
    index_dict = {
        'title': 'Bekhor Shor',
        'categories': ['Commentary2', 'Tanakh', 'Bekhor Shor'],
        'schema': bs_schema().serialize()  # This line converts the schema into json
    }
    post_index(index_dict)

def bs_text_post(text_dict):
        v_genesis = {
            'versionTitle': 'Bekhor Shor, Leipzig, 1856',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001931068',
            'language': 'he',
            'text': text_dict['Genesis ']
        }
        post_text('Bekhor Shor, Genesis', v_genesis)

        v_exodus = {
            'versionTitle': 'Bekhor Shor, Leipzig, 1856',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001931068',
            'language': 'he',
            'text': text_dict['Exodus ']
        }
        post_text('Bekhor Shor, Exodus', v_exodus)

        v_leviticus = {
            'versionTitle': 'Bekhor Shor, HaTzofeh LeHokhmat Yisrael VIII, Budapest, 1924',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002062192',
            'language': 'he',
            'text': text_dict['Leviticus ']
        }
        post_text('Bekhor Shor, Leviticus', v_leviticus)

        v_numbers1 = {
            'versionTitle': 'Bekhor Shor, Breslau, 1900',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001933451',
            'language': 'he',
            'text': text_dict['Numbers part 1']
        }
        post_text('Bekhor Shor, Numbers', v_numbers1)

        v_numbers2 = {
            'versionTitle': 'Bekhor Shor, HaTzofeh LeHokhmat Yisrael VIII, Budapest, 1928',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001933437',
            'language': 'he',
            'text': text_dict['Numbers part 2']
        }
        post_text('Bekhor Shor, Numbers', v_numbers2)

        v_deuteronomy1 = {
            'versionTitle': 'Bekhor Shor, Breslau, 1914',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002062194',
            'language': 'he',
            'text': text_dict['Deuteronomy part 1']
        }
        post_text('Bekhor Shor, Deuteronomy', v_deuteronomy1)

        v_deuteronomy2 = {
            'versionTitle': 'Bekhor Shor, Breslau, 1890',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002206252',
            'language': 'he',
            'text': text_dict['Deuteronomy part 2']
        }
        post_text('Bekhor Shor, Deuteronomy', v_deuteronomy2)


def link_bs(text_dict):
    links = []
    for text in text_dict.keys():
        book = re.match(u'(.*?)\s', text).group().strip()
        for dh in traverse_ja(text_dict[text]):
            perek = (dh['indices'][0] + 1)
            pasuk = (dh['indices'][1] + 1)
            comment = (dh['indices'][2]+1)
            link = (
                {
                    "refs": [
                        'Bekhor Shor, {} {}:{}:{}'.format(book, perek, pasuk, comment),
                        '{} {}:{}'.format(book,perek, pasuk),
                    ],
                    "type": "commentary",
                    "auto": True,
                    "generated_by": "bekhor_shor_parser"
                })
            # append to links list
            links.append(link)
    return links