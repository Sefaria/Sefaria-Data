# -*- coding: utf-8 -*-
import sys
import os
import codecs
from sefaria.datatype import jagged_array
from collections import Counter
from urllib2 import URLError
import json
from parsing_utilities.util import jagged_array_to_file as j_to_file, getGematria
from parsing_utilities.sanity_checks import *
from sources import functions
from sefaria.model import *


def file_to_ja(structure, infile, expressions, cleaner, grab_all=False):
    """
    Designed to be the first stage of a reusable parsing tool. Adds lines of text to the Jagged
    Array in the desired structure (Chapter, verse, etc.)
    :param structure: A nested list one level lower than the final result. Example: for a depth 2
    text, structure should be [[]].
    :param infile: Text file to read from
    :param expressions: A list of regular expressions with which to identify segment (chapter) level. Do
    not include an expression with which to break up the actual text.
    :param cleaner: A function that takes a list of strings and returns an array with the text broken up
    correctly. Should also break up and remove unnecessary tagging data.
    :param grab_all: If set to true, will grab the lines indicating new sections.
    :return: A jagged_array with the text properly structured.
    """

    # instantiate ja
    ja = jagged_array.JaggedArray(structure)

    if structure == []:
        depth = 1
    else:
        depth = ja.get_depth()

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

            if reg.search(line):
                # check that we've hit the first chapter and verse
                if indices.count(-1) == 0:
                    ja.set_element(indices, cleaner(temp))
                    temp = []

                    if grab_all:
                        temp.append(line)

                # increment index that's been hit, reset all subsequent indices
                indices[i] += 1
                indices[i+1:] = [0 for x in indices[i+1:]]
                break

        else:
            if indices.count(-1) == 0:
                temp.append(line)
    else:
        ja.set_element(indices, cleaner(temp))

    return ja


def get_file_names(category):
    """
    Get a list of all the file names for specified category
    :param category: משניות, יכין, בועז
    :return: List of all filenames in specified category
    """

    tractates = library.get_indexes_in_category('Mishnah')
    file_names = []

    for book in tractates:

        he_name = Ref(book).he_book()
        he_name = he_name.replace(u'משנה', category)
        file_names.append(u'{}.txt'.format(he_name))

    return file_names


def do_nothing(text_array):
    return text_array


def simple_align(text):

    clean = []

    for line in text:
        line = line.replace(u'\n', u'')
        line = line.replace(u'\r', u'')

        if line != u'':
            clean.append(line)

    return clean


def boaz_align(text):

    clean = []
    reg = re.compile(u'@22')

    for line in text:
        line = line.replace(u'\n', u'')
        line = line.replace(u'\r', u'')

        if reg.match(line):
            clean.append(line)
        else:
            clean[-1] += line

    return clean


def align_comments(text_array):
    # strip out unnecessary lines
    remove = re.compile(u'@99')
    for index, line in enumerate(text_array):
        if remove.search(line):
            del text_array[index]

    section_name, result, tmp = '', {}, []
    t = u''.join(text_array)
    t = t.replace(u'\n', u'')
    t = t.replace(u'\r', u'')
    t = t.split(u' ')
    for word in t:
        search = re.search(u'@11([\u05d0-\u05ea"]){1,4}\*?\)', word)
        if search:
            section_name = getGematria(search.group(1).replace(u'"', u''))
            if section_name in result.keys():
                result[section_name].append(u'\n')
        if section_name not in result.keys():
            result[section_name] = []

        result[section_name].append(re.sub(u'@[0-9]{2}', u'', word))

    return result


def simple_to_complex(segment_names, jagged_text_array):
    """
    Given a simple text and the names of each section, convert a simple text into a complex one.
    :param segment_names: A list of names for each section
    :param jagged_text_array: A parsed jagged array to be converted from a simple to a complex text
    :return: Dictionary representing the complex text structure
    """

    # Ensure there are the correct number of segment names
    if len(segment_names) != len(jagged_text_array):
        raise IndexError('Length of segment_names does not match length of jaggedArray')

    complex_text = {}

    for index, name in enumerate(segment_names):
        complex_text[name] = jagged_text_array[index]

    return complex_text


def grab_intro(infile, stop_tag, cleaner=None):
    """
    An introduction lies outside the regular chapter verse structure of the text. Use this function to grab the
    intro
    :param infile: input file to read from.
    :param stop_tag: When this pattern is recognized, the function will return
    :param cleaner: A function that takes a list of strings and returns a list of strings
    :return: List of string(s).
    """

    stop_tag = re.compile(stop_tag)

    result = []

    for line in infile:

        if stop_tag.search(line):
            if cleaner:
                return cleaner(result)
            else:
                return result
        else:
            result.append(line)

    else:
        infile.close()
        raise EOFError('Hit the end of the file')


def grab_section_names(section_expression, input_file, group_number=0):
    """
    Grab the names of the sections that need to be converted into a complex text
    :param section_expression: An expression that can be compiled into a regex that will find
     the corresponding sections
    :param input_file: File from which to grab the results
    :param group_number: If needed, supply the capture group that will return the correct name.
    :return: List of strings.
    """

    section_reg = re.compile(section_expression)
    names = []

    for line in input_file:

        found_match = section_reg.search(line)
        if found_match:
            names.append(found_match.group(group_number))

    return names


def find_boaz_in_yachin(yachin_struct, boaz_struct, comment_tag):
    """
    Check that yachin has all the links to boaz. First take a parsed boaz, check how many comments are in a given
    chapter, then see if the corresponding yachin structure has tags that can be linked to said boaz.
    :param yachin_struct: A roughly parsed ja-like structure of Yachin - depth 2
    :param boaz_struct: Same as above, but for boaz.
    :param comment_tag: syntax for regular expression with which to find tags in Yachin
    :return: Dictionary 'chapter': diff (int representing the difference in comments between commentaries)
    """

    comment_reg = re.compile(comment_tag)
    diffs = []

    # loop through boaz
    for index, section in enumerate(boaz_struct):

        try:
            # count number of comments in chapter of boaz
            num_comments = len(section)

            # grab Yachin chapter
            y_chapter = u' '.join(yachin_struct[index])

            # number of boaz references in Yachin chapter
            b_comments_in_y = len(comment_reg.findall(y_chapter))

            diffs.append(b_comments_in_y - num_comments)

        except IndexError:

            diffs.append(-999)

    return diffs


def parse_boaz(input_file):

    expression = u'@00(?:\u05e4\u05e8\u05e7 |\u05e4")([\u05d0-\u05ea"]{1,3})'

    simple_parse = file_to_ja([[]], input_file, [expression], boaz_align)

    # reset file
    input_file.seek(0)

    headers = [functions.getGematria(x) for x in grab_section_names(expression, input_file, 1)]

    comp_parse = simple_to_complex(headers, simple_parse.array())

    full_parse = functions.convertDictToArray(comp_parse)

    return full_parse


def yachin_boaz_diffs(output_file):
    """
    Simple parse of Yachin and Boaz, run find_boaz_in_yachin, then print diffs if necessary
    """

    tractates = library.get_indexes_in_category('Mishnah')
    count = 0

    for book in tractates:

        he_name = Ref(book).he_book()


        try:
            yachin_file = codecs.open(u'{}.txt'.format(he_name.replace(u'משנה', u'יכין')), 'r', 'utf-8')
            boaz_file = codecs.open(u'{}.txt'.format(he_name.replace(u'משנה', u'בועז')), 'r', 'utf-8')
        except IOError:
            continue

        y_jarray = file_to_ja([[]], yachin_file, [u'@00(?:\u05e4\u05e8\u05e7 |\u05e4)([\u05d0-\u05ea"]{1,3})'],
                              simple_align, True)
        b_array = parse_boaz(boaz_file)

        diffs = find_boaz_in_yachin(y_jarray.array(), b_array, u'@22')

        yachin_file.close()
        boaz_file.close()

        for index, value in enumerate(diffs):

            if value > 0:
                count += 1
                output_file.write(u'{}: {} extra comment(s) found in {} chapter {}\n'
                                  .format(count, abs(value), book.replace(u'Mishnah', u'Yachin'), index + 1))

            elif value < 0 and value != -999:
                count += 1
                output_file.write(u'{}: {} extra comment(s) found in {} chapter {}\n'
                                  .format(count, abs(value), book.replace(u'Mishnah', u'Boaz'), index + 1))

            elif value == -999:
                count += 1
                output_file.write(u'{} strange issue at {} chapter {}\n'.format(count, book, index+1))


def double_tags():

    chap_reg = u'@00(?:\u05e4\u05e8\u05e7 |\u05e4")([\u05d0-\u05ea"]{1,3})'
    boaz_reg = u'@44\([\u05d0-\u05ea"]{1,3}'

    for text_file in get_file_names(u'משניות'):

        input_file = codecs.open(text_file, 'r', 'utf-8')

        double_tags = find_double_tags(chap_reg, boaz_reg, input_file)

        if double_tags:

            print u'{}: {}'.format(text_file, double_tags)


def yachin_builder(text_list):
    """
    Takes a raw list of yachin comments in a chapter and parses them into the correct structure.
    Does not remove links and other garbage that might exist in the text.
    :param text_list: A list of strings
    :return: Nested list of strings (unicode)

    tags and their meaning:
    @42 - This is an introduction. Saved as the first segment in a section.
    @11 - New comment
    @11 with * - needs to be appended to the end of a section
    @53 - Requires <br> tag
    @99 - skip line completely

    """

    chapter = []

    # set up regexes for each line type
    new_comment = re.compile(u'@11[\u05d0-\u05ea"]{1,3}\)')
    skip_line = re.compile(u'@99')
    intro, has_intro = re.compile(u'@42'), False
    star_comment = re.compile(u'@11[\u05d0-\u05ea"]{1,3}\*?\)')
    line_break = re.compile(u'@53')

    for line in text_list:

        # clean up line
        line = line.replace(u'\n', u'')
        line = line.replace(u'\r', u'')
        line = line.replace(u'\ufeff', u'')
        line = line.replace(u'!', u'')
        line = line.replace(u' @22', u'@22')
        line = line.rstrip()
        if line == u'':
            continue

        if skip_line.match(line):
            continue

        elif intro.match(line):
            chapter.append([line])
            has_intro = True

        elif new_comment.search(line):
            # if an intro exists, add comment immediately afterwords
            if has_intro:
                chapter[-1].append(line)
                has_intro = False
            else:
                chapter.append([line])

        elif star_comment.search(line):
            chapter[-1].append(line)

        # Replace @53 tags with <br>, then add to last string in structure
        elif line_break.search(line):
            line = re.sub(line_break, u'<br>', line)
            chapter[-1][-1] += line

        else:
            print 'bad line'
            print line
            raise RuntimeError

    return chapter


def find_reg_in_file(input_file, pattern):
    """
    Prints line numbers where pattern matches text
    :param pattern: Pattern to compile regex
    """

    regex = re.compile(pattern)

    count = 0

    for line_num, line in enumerate(input_file):

        count += 1
        if regex.search(line):
            print '{} '.format(line_num+1),

    print 'Total lines: {}'.format(count)


def find_unclear_lines(input_file, pattern_list):
    """
    Print out line numbers that can't be identified by any regex
    :param pattern_list: list of regular expression patterns
    """

    expression_list = [re.compile(pattern) for pattern in pattern_list]

    for line_num, line in enumerate(input_file):

        line = line.replace(u'\n', u'')
        line = line.replace(u'\r', u'')
        line = line.replace(u'\ufeff', u'')
        line = line.rstrip()
        if line == u'':
            continue

        if not any(expression.search(line) for expression in expression_list):
            print '{}: '.format(line_num+1), line


def tags_to_strip():
    """
    :return: List of tags to remove from parsed structure
    """
    return [u'@00(?:\u05e4\u05e8\u05e7 |\u05e4")([\u05d0-\u05ea"]{1,3})', u'@11[\u05d0-\u05ea"]{1,3}\*?\)',
            u'@22\([\u05d0-\u05ea]{1,2}\)', u'@[0-9]{2}']

# [u'@00(?:\u05e4\u05e8\u05e7 |\u05e4")([\u05d0-\u05ea"]{1,3})',
#  u'@11[\u05d0-\u05ea"]{1,3}\*?\)', u'@99', u'@42', u'@53']


def combine_lines_in_file(file_name, pattern, skip_pattern):
    """
    Look for lines that BEGIN with a specific pattern, and make them a continuation of the previous
    line
    :param file_name: name of the file to be fixed
    :param pattern: regex pattern to identify lines that need to be fixed
    :param skip_pattern: regex pattern that if found line should not be ignored
    """

    expression = re.compile(pattern)
    skip_expression = re.compile(skip_pattern)
    old_file = codecs.open(file_name, 'r', 'utf-8')
    new_file = codecs.open(u'{}.tmp'.format(file_name), 'w', 'utf-8')
    previous_line = u''

    for line in old_file:

        if expression.match(line) and not skip_expression.search(line):

            # remove line breaks from previous line
            previous_line = previous_line.replace(u'\n', u' ')
            previous_line = previous_line.replace(u'\r', u' ')
            previous_line = re.sub(u' +', u' ', previous_line)

        if previous_line:
            new_file.write(previous_line)

        previous_line = line

    else:
        new_file.write(previous_line)

    old_file.close()
    new_file.close()
    os.remove(file_name)
    os.rename(u'{}.tmp'.format(file_name), file_name)


def check_chapter_intro():

    new_chap = re.compile(u'@00(?:\u05e4\u05e8\u05e7 |\u05e4")([\u05d0-\u05ea"]{1,3})')
    intro = re.compile(u'@42')
    issues = []

    for file_name in get_file_names(u'יכין'):
        with codecs.open(file_name, 'r', 'utf-8') as current_file:
            found_intro = False
            for line_num, line in enumerate(current_file):

                if intro.search(line):
                    found_intro = True
                    continue

                elif new_chap.search(line) and found_intro:
                    issues.append(u'{}: {}\n'.format(file_name, line_num))
                    found_intro = False

                else:
                    found_intro = False

    if len(issues) == 0:
        print 'no issues found'
    else:
        for issue in issues:
            print issue


def parse_files():

    results = {}

    chap_expression = [u'@00(?:\u05e4\u05e8\u05e7 |\u05e4")([\u05d0-\u05ea"]{1,3})']

    tractates = library.get_indexes_in_category('Mishnah')
    print tractates

    for tractate in tractates:

        en_name = u'Yachin on ' + tractate
        he_name = Ref(tractate).he_book().replace(u'משנה', u'יכין')
        filename = u'{}.txt'.format(he_name)
        print en_name

        with codecs.open(filename, 'r', 'utf-8') as datafile:
            results[en_name] = {
                'en': en_name,
                'he': he_name,
                'data': util.file_to_ja([[]], datafile, chap_expression, yachin_builder)
            }
    return results


def parse_mishna(input_file, perek_tag, mishna_tag, skip_tag):
    """
    The Mishna parsing was done before the reusable parser was written (Yachin was the first project
    to use it). This is the function as it appears in the mishna parser. It was decided to forgo DRY
    to maintain reverse compatibility for the sake of linking in this case.
    :param input_file: File to parse
    :param perek_tag: Used to identify the start of a new perek.
    :param mishna_tag: Identify next mishna.
    :return: A 2D jaggedArray to match Sefaria's format. Rough, will require more processing.
    """

    chapters, mishnayot, current = [], [], []
    found_first_chapter = False

    for line in input_file:

        # look for skip_tag
        if re.search(skip_tag, line):
            continue

        # look for tags
        new_chapter, new_mishna = re.search(perek_tag, line), re.search(mishna_tag, line)

        # make sure perek and mishna don't appear on the same line
        if new_chapter and new_mishna:
            print 'Mishna starts on same line as chapter\n'
            print '{}\n\n'.format(new_chapter.group())
            input_file.close()
            sys.exit(1)

        # found chapter tag.
        if new_chapter:
            if found_first_chapter:
                if current != []:
                    mishnayot.append(u' '.join(current).lstrip())
                    current = []
                chapters.append(mishnayot)
                mishnayot = []
            else:
                found_first_chapter = True
            continue

        if found_first_chapter:
            if new_mishna:
                if current != []:
                    mishnayot.append(u' '.join(current).lstrip())
                current = [util.multiple_replace(line, {u'\n': u'', u'\r': u'', new_mishna.group(): u''})]

            else:
                current.append(util.multiple_replace(line, {u'\n': u'', }))
            # add next line

    else:
        mishnayot.append(u''.join(current).lstrip())
        chapters.append(mishnayot)

    return chapters


def collect_links(tractate):
    """
    Link creator for Yachin. Links from Mishnah to Yachin are depicted in the Mishna. Tags are removed
    from the uploaded Mishna, so the files are re-parsed, and the link data is extracted
    :param tractate: tractate to which links are to be built
    :return: A list of link objects, ready for upload
    """
    links = []
    y_counter = Counter([])

    filename = Ref(tractate).he_book().replace(u'משנה', u'משניות') + u'.txt'
    with codecs.open(filename, 'r', 'utf-8') as datafile:
        parsed_mishna = parse_mishna(datafile, u'@00(?:\u05e4\u05e8\u05e7 |\u05e4)([\u05d0-\u05ea"]{1,3})',
                                     u'@22[\u05d0-\u05ea]{1,2}', u'@99')
    comment_reg = re.compile(u'(?:[).\d])(?:[ \d@]*)([\u05d0-\u05ea"\' ]*?)(?:[ \d@]*)@44([\u05d0-\u05ea]{1,3})')

    for line in util.traverse_ja(parsed_mishna):
        for match in comment_reg.finditer(util.multiple_replace(line['data'], {u'!': u'', u'@33': u''})):
            m_ref = u'{}.{}.{}'.format(tractate, line['indices'][0]+1, line['indices'][1]+1)
            y_ref = u'{}.{}.{}'.format(u'Yachin on ' + tractate, line['indices'][0]+1,
                                       util.getGematria(match.group(2)))
            y_counter.update([y_ref])
            if y_counter[y_ref] != 1:
                continue

            links.append({
                'refs': [m_ref, y_ref],
                'type': 'commentary',
                'auto': False,
                'generated_by': 'Yachin Parse Script',
                'text': match.group(1)
            })

    return links


def build_links(ref_list):

    # flatten links to depth 1 list
    references = [ref for ref_array in ref_list for ref in ref_array]

    return references


def upload(data, post_index=True):

    # create index
    schema = JaggedArrayNode()
    schema.add_title(data['en'], 'en', True)
    schema.add_title(data['he'], 'he', True)
    schema.key = data['en']
    schema.depth = 3
    schema.addressTypes = ['Integer', 'Integer', 'Integer']
    schema.sectionNames = ['Chapter', 'Seif', 'Comment']
    schema.validate()

    index = {
        'title': data['en'],
        'categories': ['Commentary2', 'Mishnah', 'Yachin'],
        'schema': schema.serialize()
    }
    if post_index:
        functions.post_index(index)

    # clean and upload text
    upload_text = util.clean_jagged_array(data['data'].array(), tags_to_strip())
    text_version = {
        'versionTitle': u'Mishnah, ed. Romm, Vilna 1913',
        'versionSource': 'http://http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001741739',
        'language': 'he',
        'text': upload_text
    }
    functions.post_text(data['en'], text_version)


def add_dh_to_text(link_dict, parsed_files):

    # grab appropriate ref in the link object
    try:
        ref = filter(lambda x: re.search('Yachin on', x), link_dict['refs'])[0]
    except IndexError:
        raise IndexError('could not find Yachin in either link')

    # parse out the tractate name and indexes
    book_name = ref[:ref.index('.')]
    index_string = ref[ref.index('.')+1:]
    indexes = [int(i)-1 for i in index_string.split('.')]
    del index_string

    our_text = parsed_files[book_name]
    temp = None
    for i in indexes:
        try:
            if temp is None:
                temp = our_text['data'].array()[i]
            else:
                temp = temp[i]
        except IndexError:
            break
    else:
        temp[0] = u'<b>{}</b><br>'.format(link_dict['text']) + temp[0]

    del link_dict['text']


def post_index_text_links():
    tracs = library.get_indexes_in_category('Mishnah')
    parsed = parse_files()
    link_refs = [collect_links(tractate) for tractate in tracs]
    full_links = build_links(link_refs)
    for linker in full_links:
        add_dh_to_text(linker, parsed)
    for num, data in enumerate(sorted(parsed.keys())):
        print num+1, data
        for attempt in range(3):
            try:
                upload(parsed[data], True)
            except URLError:
                print 'handling weak network'
            else:
                break
        else:
            raise URLError
        # util.ja_to_xml(parsed[data]['data'].array(), ['chapter', 'comment', 'line'])
        # break
    functions.post_link(full_links)

    os.remove('errors.html')


def grab_boaz_links():
    """
    Extract links from Yachin and save as a json file
    :return:
    """
    comment_reg = re.compile(u'@22\(([\u05d0-\u05ea]{1,3})\)')
    links = []

    yachin_data = parse_files()
    for book in yachin_data:
        for line in util.traverse_ja(yachin_data[book]['data'].array()):
            indices = line['indices']
            for match in comment_reg.finditer(line['data']):
                y_ref = u'{}.{}.{}.{}'.format(yachin_data[book]['en'], indices[0]+1, indices[1]+1, indices[2]+1)
                b_ref = u'{}.{}.{}'.format(yachin_data[book]['en'].replace('Yachin', 'Boaz'), indices[0]+1,
                                           util.getGematria(match.group(1)))
                links.append({
                    'refs': (y_ref, b_ref),
                    'type': 'commentary',
                    'auto': False,
                    'generated_by': 'Yachin Parse Script'
                })

    with open('boaz_links.json', 'w') as json_output:
        data = json.dumps(links)
        json_output.write(data)

post_index_text_links()