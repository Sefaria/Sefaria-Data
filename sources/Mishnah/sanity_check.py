# -*- coding: utf-8 -*-
import pdb
import os
import sys
import re
import codecs
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.insert(0, '../Match/')
from data_utilities.util import *
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from sources.functions import *
import glob
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from data_utilities.sanity_checks import TagTester
from sefaria.model import *

tractates = library.get_indexes_in_category('Mishnah')


def check_mishna_order():
    #checked Mishnayot for Pereks being in order and within each perek each comment is in order
    #checked Boaz for Pereks being in order but DID NOT check that each comment within each perek is in order

    count=0
    for file in glob.glob(u"*.txt"):
     file = file.replace(u"\u200f", u"")
     if file.split(" ")[0] == u"יכין":
        count += 1
        in_order_caller(file, reg_exp_tag=u'@00\u05E4(?:"|\u05E8\u05E7 )?([\u05D0-\u05EA]{1}"?[\u05D0-\u05EA]?)')


def files_exist():
    """
    Looks through the directory to ensure all files that should be there do exist. It will also take care
    of naming conventions - i.e. it will mark a file as missing if it's named in an unpredictable manner.
    """

    # get a list of all tractates
    tractates = library.get_indexes_in_category('Mishnah')
    missing = codecs.open('missing_tractates.txt', 'w', 'utf-8')

    for tractate in tractates:
        ref = Ref(tractate)
        name = ref.he_book()
        terms = [u'משניות', u'יכין', u'בועז']

        for term in terms:
            file_name = u'{}.txt'.format(name.replace(u'משנה', term))
            if not os.path.isfile(file_name):
                missing.write(u'{}\n'.format(file_name))

    missing.close()


def compare_tags_to_comments(main_tag, commentary_tag, output):
    """
    Check that their the number of comments in a commentary match the number of tags in the main text.
    Outputs errors to a file. main_tag and commentary_tag should have members added called segment_tag
    which indicate the beginning of a new segment (chapter, verse, etc.).

    :param main_tag: A TagTester object associated with the main text
    :param commentary_tag: TagTester associated with the commentary.
    :param output: output file for results.
    """

    text_tags = main_tag.count_tags_by_segment(main_tag.segment_tag)
    comment_tags = commentary_tag.count_tags_by_segment(commentary_tag.segment_tag)

    perfect = True

    if len(text_tags) != len(comment_tags):
        output.write(u'Major alignment mismatch between {} and {}\n'.format(main_tag.name, commentary_tag.name))
        return

    for index, appearances in enumerate(text_tags):
        if appearances != comment_tags[index]:
            output.write(u'Tag mismatch {} and {} segment {}\n'.format(main_tag.name,
                                                                       commentary_tag.name, index+1))
            output.write(u'Found {} tags in Mishna; {} tags in Yachin\n'.format(appearances,
                                                                                comment_tags[index]))
            perfect = False
    if perfect:
        output.write(u'Perfect alignment {} and {}\n'.format(main_tag.name, commentary_tag.name))


def compare_mishna_to_yachin(tractate_list):

    for tractate in tractate_list:
        r = Ref(tractate)
        name = r.he_book()
        m_name = name.replace(u'משנה', u'משניות')
        y_name = name.replace(u'משנה', u'יכין')
        output = codecs.open('tag_match_up.txt', 'a', 'utf-8')
        try:
            m_file = codecs.open(u'{}.txt'.format(m_name), 'r', 'utf-8')
            y_file = codecs.open(u'{}.txt'.format(y_name), 'r', 'utf-8')
        except IOError:
            output.write(u'missing file {}\n'.format(name))
            continue

        m_tag = TagTester(u'@44', m_file, name=m_name)
        y_tag = TagTester(u'@11', y_file, name=y_name)

        seg_tag = u'@00(?:פרק |פ)([א-ת,"]{1,3})'
        m_tag.segment_tag = seg_tag
        y_tag.segment_tag = seg_tag

        compare_tags_to_comments(m_tag, y_tag, output)

        m_file.close()
        y_file.close()
        output.close()


def get_perakim(type, tag, tag_reg):
    """
    :param type: identifies if this is Mishnah, yachin or boaz
    :param tag: the tag to identify the start of a new perek
    :param tag_reg: regular expression for the tag
    :return: a dictionary, keys are the tractate, values are a list of perakim
    """

    # get a list of all tractates
    tractates = library.get_indexes_in_category('Mishnah')
    results = {}

    for tractate in tractates:
        ref = Ref(tractate)
        name = ref.he_book()
        name = name.replace(u'משנה', type)
        file_name = u'{}.txt'.format(name)

        # if file doesn't exist, skip
        if not os.path.isfile(file_name):
            continue

        text_file = codecs.open(file_name, 'r', 'utf-8')

        data_tag = TagTester(tag, text_file, tag_reg, name)
        results[name] = data_tag.grab_by_section()

        text_file.close()


def get_tags_by_perek(srika_tag, segment_regex, capture_group=0):
    """
    Create an array of arrays, with outer arrays corresponding to chapters and inner arrays containing the
    captures of srika_tag in order.
    :param srika_tag: A TagTester object
    :param segment_regex: used to find the beginning of each segment
    :return: 2D array
    """

    # set tag file to the beginning of the first segment
    srika_tag.file.seek(0)
    srika_tag.eof = False
    srika_tag.skip_to_next_segment(segment_regex)
    captures_by_segment = []

    while True:
        captures_by_segment.append(srika_tag.grab_each_header(segment_regex, capture_group))

        if srika_tag.eof:
            break

    return captures_by_segment


def he_tags_in_order(captures, seg_name, output_file):
    """
    Checks if tags properly increment by 1.
    :param captures: An array of captures to be analyzed by function
    :param seg_name: Name of segment. Will be displayed in the output_file/
    :param output_file: File to output results
    :return: True if tags in order, False otherwise.
    """

    if len(captures) == 0:
        output_file.write(u'{} has no tags\n'.format(seg_name))
        return True

    previous = getGematria(captures[0].replace(u'"', u''))
    correct = True

    for index, current in enumerate(captures):

        # do nothing for first index
        if index == 0:
            previous = getGematria(current.replace(u'"', u''))
            continue

        else:
            current = getGematria(current.replace(u'"', u''))
            if current - previous != 1:
                output_file.write(u'{} קופץ מ-{} ל-{}\n'.format(seg_name, previous, current))
                correct = False
            previous = current
    return correct


def reasonable_increment(captures, seg_name, output_file):
    """
    Checks that tags increment correctly, but allows for reuse of previous tags
    :param captures: An array of captures to be analyzed by function
    :param seg_name: Name of segment. Will be displayed in the output_file/
    :param output_file: File to output results
    :return: True if tags in order, False otherwise.
    """

    if len(captures) == 0:
        output_file.write(u'{} has no tags\n'.format(seg_name))
        return True

    tag_values = he_array_to_int(captures)
    max_tag, correct = 0, True

    for value in tag_values:
        if value > max_tag:
            if value - max_tag != 1:
                output_file.write(u'{} קופץ מ-{} ל-{}\n'.format(seg_name, max_tag, value))
                correct = False
            max_tag = value

    return correct


def skipped_comments(captures, seg_name, output_file):
    """
    Looks for tags that were skipped, yet allows for a single misnumbered tag. Two misnumbered tags in a row
    will fail. For example 1,2,3,4,8,6 will pass, but 1,2,3,4,6,7 will fail (as 6 is still expected in the final
    position).

    :param captures: An array of captures to be analyzed by function
    :param seg_name: Name of segment. Will be displayed in the output_file/
    :param output_file: File to output results
    :return: True no skips were found, False otherwise.
    """

    if len(captures) == 0:
        output_file.write(u'{} has no tags\n'.format(seg_name))
        return True

    tag_values = he_array_to_int(captures)

    expected, correct = 1, True

    for index, value in enumerate(tag_values):
        if correct:
            if value != expected:
                correct = False
            else:
                correct = True
        else:
            if value == expected:
                correct = True
            else:
                if index > 1:
                    output_file.write(u'{} קופץ מ-{} ל-{}\n'.format(
                        seg_name, tag_values[index-2], tag_values[index-1]))
                else:
                    output_file.write(u'{} מתחיל מ-{}\n'.format(seg_name, tag_values[0]))
                return False
        expected += 1
    else:
        return True


def check_tags_on_category(category, tag, tag_regex, check_function):
    """
    Check that all the tags in category run in order
    :param category: משניות, יכין or whatever is needed to identify the files
    """

    output = codecs.open(u'{}_tags.txt'.format(category), 'w', 'utf-8')
    seg_reg = u'@00(?:פרק |פ)([א-ת,"]{1,3})'

    for tractate in tractates:
        ref = Ref(tractate)
        name = ref.he_book()
        name = name.replace(u'משנה', category)
        try:
            in_file = codecs.open(u'{}.txt'.format(name), 'r', 'utf-8')
        except IOError:
            output.write(u'{}.txt does not exist\n'.format(name))
            continue

        # create TagTester object for each file
        tag_object = TagTester(tag, in_file, tag_regex, name)

        # get tags in array
        whole_book = get_tags_by_perek(tag_object, seg_reg, 1)
        perfect = True

        for index, perek in enumerate(whole_book):
            message = u'{} פרק {}'.format(name, index+1)
            if not check_function(perek, message, output):
                perfect = False

        if perfect:
            output.write(u'{}-אין בעיות\n'.format(name))

    output.close()


def check_chapters(category, chap_reg):

    output = codecs.open('chapters.txt', 'w', 'utf-8')

    for tractate in tractates:
        ref = Ref(tractate)
        name = ref.he_book()
        name = name.replace(u'משנה', category)
        try:
            in_file = codecs.open(u'{}.txt'.format(name), 'r', 'utf-8')
        except IOError:
            output.write(u'{}.txt does not exist\n'.format(name))
            continue

        chap_tag = TagTester(u'@00', in_file, chap_reg, name)
        chapters = get_tags_by_perek(chap_tag, chap_tag.reg, capture_group=1)

        if len(chapters) != len(ref.all_subrefs()):
            output.write(u'Chapter mismatch {}\n'.format(tractate))

    output.close()


def tag_starts_line(tag, category):
    """
    Make sure a tag always begins a new line
    :param tag: regular expression with which to find tag
    :param category: Identifier for the files (i.e משניות, יכין etc.)
    """

    for tractate in tractates:
        ref = Ref(tractate)
        name = ref.he_book()
        name = name.replace(u'משנה', category)
        try:
            in_file = codecs.open(u'{}.txt'.format(name), 'r', 'utf-8')
        except IOError:
            print u'cannot find {}'.format(name)
            continue

        # instantiate TagTester
        tester = TagTester(tag, in_file)
        if tester.does_start_line():
            print u'{} is okay!'.format(name)
        else:
            print u'problem with {}'.format(name)


check_tags_on_category(u'משניות', u'@22', u'@22([א-ת,"]{1,3})', he_tags_in_order)
check_tags_on_category(u'יכין', u'@11', u'@11([א-ת,"]{1,3})', he_tags_in_order)
compare_mishna_to_yachin(library.get_indexes_in_category('Mishnah'))
check_chapters(u'משניות', u'@00(?:פרק |פ)([א-ת,"]{1,3})')
