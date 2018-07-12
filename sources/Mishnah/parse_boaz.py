# -*- coding: utf-8 -*-
from data_utilities import util
import codecs
import re
from sources import functions
from sefaria.model import *
import json

"""
Parsing strategy: Use @00 and @22 for structure in the auto-parser.

Two places have a repeated numbered comment (i.e. a and a*). I think dropping to depth 3 is silly, I'll add a line
break instead. I've marked these cases with the @23 tag.

I've skipped the text labeled as פירוש הקצר in בועז שבת, as I'm not sure this is actually a part of Boaz. This is
tagged with @10.

There is section called פתח האוהל in בועז אוהלות. This is styled as a run-on segment. These get an @23 tag which add a
line break.
"""

strip_list = [u'@22\([\u05d0-\u05ea]{1,2}\)', u'@[0-9]{2}']


def get_file_names():

    he = [Ref(book).he_book() for book in library.get_indexes_in_category('Mishnah')[:-5]]
    boaz_file_names = [u'{}.txt'.format(name.replace(u'משנה', u'בועז')) for name in he]
    return boaz_file_names


def files_with_tag(tag):
    files = []
    for filename in get_file_names():
        with codecs.open(filename, 'r', 'utf-8') as boaz_file:
            for line in boaz_file:
                if re.search(tag, line):
                    files.append(filename)
                    break
    print 'found {} files with tag {}'.format(len(files), tag)
    for thing in files:
        print thing


def find_strange_stuff():
    weird_chars = []
    for filename in get_file_names():
        with codecs.open(filename, 'r', 'utf-8') as boaz_file:
            for line in boaz_file:
                weird_chars.append(re.findall(u'[^\u05d0-\u05ea \.0-9\(\):@\[\"]', line))
    weird_chars = [thing for char_list in weird_chars for thing in char_list]
    return set(weird_chars)


def unclear_lines(expected_tags):

    problems = 0
    for book in get_file_names():
        with codecs.open(book, 'r', 'utf-8') as data:
            for linenum, line in enumerate(data):
                if not any(re.match(pattern, line) for pattern in expected_tags):
                    print u'{}: {}'.format(book, linenum)
                    print line
                    problems += 1
    print '{} issues found'.format(problems)


def structure_boaz(chapter):

    new_comment = re.compile(u'@22')
    break_tag = re.compile(u'@23')
    skip_tag = re.compile(u'@99')
    parsed = []

    for line in chapter:
        line = util.multiple_replace(line, {u'\n': u'', u'\r': u''})

        if new_comment.match(line):
            parsed.append(line)

        elif break_tag.match(line):
            line = line.replace(break_tag.pattern, u'<br>')
            parsed[-1] += line

        elif skip_tag.match(line) or line == u'':
            continue

        else:
            parsed[-1] += u' {}'.format(line)

    return parsed


def align_boaz_chapters(source_file, simple_array):
    """
    Boaz does not guarantee text for every chapter. Using the util library, this method will pad the parsed text with
     empty sections as necessary to accurately represent the data.
    :param source_file: File from which to derive chapter numbers
    :param simple_array: A "naive" parse of the data structured as a nested list.
    :return: Nested array, with proper padding to account for empty chapters.
    """

    # grab each chapter number from the source file
    chapters = [util.getGematria(n) for n in util.grab_section_names(u'@00פרק ([\u05d0-\u05ea]{1,2})', source_file, 1)]
    as_dict = util.simple_to_complex(chapters, simple_array)
    return util.convert_dict_to_array(as_dict)


def build_index(mishna_name):

    jnode = JaggedArrayNode()
    jnode.add_title('Boaz on {}'.format(mishna_name), 'en', True)
    jnode.add_title(u'בועז על {}'.format(Ref(mishna_name).he_book()), 'he', True)
    jnode.key = 'Boaz on {}'.format(mishna_name)
    jnode.depth = 2
    jnode.addressTypes = ['Integer', 'Integer']
    jnode.sectionNames = ['Chapter', 'comment']
    jnode.validate()

    index = {
        'title': 'Boaz on {}'.format(mishna_name),
        'categories': ['Commentary2', 'Mishnah', 'Boaz'],
        'schema': jnode.serialize()
    }
    functions.post_index(index)


def parse_and_post(filename, index_key):

    with codecs.open(filename, 'r', 'utf-8') as source_file:
        data = util.file_to_ja([[]], source_file, [u'@00'], structure_boaz)
        data = util.clean_jagged_array(data.array(), strip_list)
        source_file.seek(0)
        data = align_boaz_chapters(source_file, data)

    text_version = {
        'versionTitle': u'Mishnah, ed. Romm, Vilna 1913',
        'versionSource': 'http://http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001741739',
        'language': 'he',
        'text': data
    }
    functions.post_text(index_key, text_version)

for number, filename in enumerate(get_file_names()):
    mishna = library.get_indexes_in_category('Mishnah')[number]
    boaz = 'Boaz on {}'.format(mishna)
    print boaz
    build_index(mishna)
    parse_and_post(filename, boaz)

with open('boaz_links.json') as links:
    functions.post_link(json.load(links))
