# encoding=utf-8
import re
import csv
import codecs
from data_utilities.sanity_checks import TagTester
from data_utilities import util
from sources.Match.match_new import Match
from sources import functions
from sefaria.model import *

filename = 'Minchat_Chinuch.txt'
m_pattern = u'@30מצוה ([\u05d0-\u05ea"]{1,5})'
comment_pattern = u'@44\(([\u05d0-\u05ea]{1,2})\)'

"""
מקרא:

@44 קישור ואות לינוך.
@66מצב אות רגיל.
@55 ציטוט מודש.
@88 סוגרים.
@30 מצוה.
@29 סוף מצוה.

"""


def check_chapters():
    with codecs.open('Minchat_Chinuch.txt', 'r', 'utf-8') as chinuch:
        test = TagTester(u'@30', chinuch, u'@30מצוה ([\u05d0-\u05ea"]{1,5})')

        index = 1

        for header in test.grab_each_header(capture_group=1):

            header = header.replace(u'"', u'')
            count = util.getGematria(header)

            if count != index:
                print util.numToHeb(index)
                index = count
            index += 1


def check_segments():

    segments = []

    infile = codecs.open(filename, 'r', 'utf-8')

    headers = TagTester(u'@30', infile, u'@30מצוה ([\u05d0-\u05ea"]{1,5})').grab_each_header()
    tester = TagTester(u'@44', infile, u'@44\(([\u05d0-\u05ea]{1,2})\)')

    while not tester.eof:

        segments.append(tester.grab_each_header(u'@30מצוה ([\u05d0-\u05ea"]{1,5})', 1))

    infile.close()

    for sec_number, section in enumerate(segments):

        index = 1

        for title in section:

            title = title.replace(u'"', u'')
            count = util.getGematria(title)

            if count != index:

                print headers[sec_number-1]
                print util.numToHeb(index)
                index = count
            index += 1


def tag_position(text, pattern, position):
    """
    Given a line of text, check if the given pattern can be found at the word of specified position
    :param text: text to be examined
    :param pattern: pattern to search for
    :param position: Word number pattern is expected to appear
    :return: True of False
    """

    expression = re.compile(pattern)

    words = text.split()

    if expression.search(words[position]):
        return True
    else:
        return False


def analyze_lines(pattern, condition, *args):
    """
    Outputs a list of lines that contain pattern but don't satisfy condition
    :param pattern: Pattern to identify lines of interest
    :param condition: Condition lines are expected to fulfill
    :return: List of dictionaries with line numbers and text where lines don't meet condition
    """

    expression = re.compile(pattern)
    bad_lines = []
    count = 0

    with codecs.open(filename, 'r', 'utf-8') as thefile:

        for line_num, line in enumerate(thefile):

            if expression.search(line):
                if not condition(line, *args):
                    data = {
                        'line number': line_num,
                        'text': line
                    }
                    count += 1
                    bad_lines.append(data)
    print '{} bad lines'.format(count)

    return bad_lines


def grab_dh(text, start_tag, end_tag):
    """
    for a given string grab the text that rests between start_tag and end_tag
    :param text:
    :param start_tag:
    :param end_tag:
    :return: the text identified as the dh. Will return None if one cannot be identified.
    """

    start_reg = re.compile(start_tag)
    end_reg = re.compile(end_tag)

    start = start_reg.search(text)
    if not start:
        return None

    end = end_reg.search(text[start.end():])
    if not end:
        return None

    # add the text that goes from the end of the start tag to the beginning of the end tag
    return text[start.end():end.start()+start.end()]


def grab_all_dh(comment_tag, start_tag, end_tag):
    """
    Grabs all dh in a file
    :param comment_tag:
    :param start_tag:
    :param end_tag:
    :return: Dictionary with the text and line_number fields
    """

    data = []
    comment_reg = re.compile(comment_tag)

    with codecs.open(filename, 'r', 'utf-8') as infile:

        for index, line in enumerate(infile):

            if comment_reg.search(line):
                dh = grab_dh(line, start_tag, end_tag)

                if dh:
                    data.append({'text': dh, 'line_number': index+1})

                else:
                    print 'bad line at {}'.format(index+1)

    return data


def nothing(something):
    return something


def add_line_breaks(text, pattern):
    """
    Align the file so that tags for a new comment take up their own line
    """

    expression = re.compile(pattern)

    if expression.match(text):

        words = text.split(u' ')
        words[0] += u'\n'
        return words[0] + u' '.join(words[1:])

    else:
        return text


def find_links(current_text, parent_text, dh_finder, *args):
    """

    :param current_text: Text being parsed. Must have keys "name" and "text"
    :param parent_text: Parent text text should be linked to. Must have keys "name" and "text"
    :param dh_finder:  function to find dh in text
    :return: List of links
    """

    matcher = Match(guess=True)
    links = []

    for chapter_num, chapter in enumerate(current_text['text']):

        if chapter:
            dh_list = [dh_finder(seif[0], *args) for seif in chapter if dh_finder(seif[0], *args)]
            matches = matcher.match_list(dh_list, parent_text['text'][chapter_num])
            links.append(build_links(parent_text['name'], current_text['name'], chapter_num+1, matches))

    return [linker for sublist in links for linker in sublist]


def build_links(parent_name, current_name, chapter, match_list):
    """

    :param parent_name: Name of parent text
    :param current_name: Name of text being parsed
    :param chapter: chapter number being analyzed
    :param match_list: data returned from calling Match.match_list()
    :return: List of links
    """

    links = []

    for match in match_list.keys():
        if len(match_list[match]) == 1:
            if match_list[match][0] > 0:

                parent = u'{}.{}.{}'.format(parent_name, chapter, match_list[match][0])
                child = u'{}.{}.{}.1'.format(current_name, chapter, match)

                new_link = {
                    'refs': [parent, child],
                    'type': 'commentary2',
                    'auto': False,
                    'generated_by': 'Minchat Chinukh parse script',
                }
                links.append(new_link)
            else:
                continue
        else:
            continue

    return links


def get_data(filename):

    with codecs.open(filename, 'r', 'utf-8') as data_file:

        data = []
        data_reader = csv.reader(data_file, delimiter=',')

        for row in data_reader:

            data.append({
                'Parsha': row[0],
                'ref': row[1]
            })

    return data


def construct_alt_struct(data_file, name):

    struct = {'nodes': []}

    for title in get_data(data_file):

        node = {
            'depth': 0,
            'sharedTitle': title['Parsha'],
            'nodeType': 'ArrayMapNode',
            'wholeRef': 'Minchat Chinukh.{}'.format(title['ref']),
            'includeSections': True
        }

        struct['nodes'].append(node)

    return {name: struct}


def construct_index(alt_struct=None):

    schema = JaggedArrayNode()
    schema.add_title(u'Minchat Chinukh', 'en', primary=True)
    schema.add_title(u'מנחת חינוך', 'he', primary=True)
    schema.key = u'Minchat Chinukh'
    schema.depth = 3
    schema.addressTypes = ['Integer', 'Integer', 'Integer']
    schema.sectionNames = ['Mitzvah', 'Seif', 'Paragraph']
    schema.validate()

    index = {
        'title': "Minchat Chinukh",
        'categories': ['Halakhah'],
        'schema': schema.serialize()
    }

    if alt_struct:
        index['alt_structs'] = alt_struct

    return index


def produce_parsed_data(filename):

    with codecs.open(filename, 'r', 'utf-8') as datafile:
        parsed = util.file_to_ja([[[]]], datafile, (m_pattern, comment_pattern), nothing)

        datafile.seek(0)

        names = util.grab_section_names(m_pattern, datafile, 1)
        names = [int(util.getGematria(name)) for name in names]

    comp_text = util.simple_to_complex(names, parsed.array())
    parsed = util.convert_dict_to_array(comp_text)

    return parsed


minchat = {'name': 'Minchat Chinukh', 'text': produce_parsed_data(filename)}
sefer = {'name': 'Sefer HaChinukh', 'text': Ref('Sefer HaChinukh').text('he').text}

chinukh_links = find_links(minchat, sefer, grab_dh, u'@55', u'@66')

with codecs.open('links.txt', 'w', 'utf-8') as outfile:
    for each_link in chinukh_links:
        outfile.write(u'{}\n'.format(each_link['refs']))

alt = construct_alt_struct('Chinukh_by_Parsha.csv', u'Parsha')

cleaned = util.clean_jagged_array(minchat['text'], [m_pattern, comment_pattern, u'@[0-9]{2}',
                                  u'\n', u'\r'])
with codecs.open('parsed.txt', 'w', 'utf-8') as outfile:
    util.jagged_array_to_file(outfile, cleaned, [u'Mitzva', u'Seif', u'Paragraph'])

full_text = {
    'versionTitle': 'Minchat Chinuch, Piotrków, 1902',
    'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001175092',
    'language': 'he',
    'text': cleaned
}

index = construct_index(alt)
functions.post_index(index)
functions.post_text('Minchat Chinukh', full_text)
functions.post_link(chinukh_links)