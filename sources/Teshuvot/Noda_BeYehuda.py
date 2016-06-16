# encoding=utf-8

from data_utilities import sanity_checks as tests
from data_utilities import util
import re
from sources import functions
import codecs
import os
from sefaria.model import *

filename = 'Noda_BeYehuda.txt'
noda_file = codecs.open(filename, 'r', 'utf-8')


def chapter_in_order(infile, tag, tag_reg, group=0):
    """
    Check that the chapters run in order
    :param infile: input file to examine
    :param tag: Exact form of tag
    :param tag_reg: A regular expression to use to find chapters
    :param group: Capture group for regex if necessary
    :return: A list of lines where order is broken
    """

    # grab all chapter headers and convert to numbers
    tester = tests.TagTester(tag, infile, tag_reg)
    tester.skip_to_next_segment(u'@00')
    all_chapters = []
    while not tester.eof:
        titles = tester.grab_each_header(u'@00', group)
        chap_numbers = [functions.getGematria(txt) for txt in titles]
        all_chapters.append(chap_numbers)

    # check that chapters match index
    for book_num, book in enumerate(all_chapters):
        for index, chapter in enumerate(book):
            if chapter - index != 1:
                print 'error in {} chapter {}'.format(book_num+1, chapter)


def starts_line(tag_list):

    for tag in tag_list:
        checker = tests.TagTester(tag, noda_file)
        if checker.starts_line:
            print u'tag {} is good'.format(tag)

        else:
            print u'tag {} is bad'.format(tag)


def find_important_tags(infile, search_pattern):
    """
    Find all the tags that start lines. All lines begin with a @ character
    :param infile: File to scan
    :param search_pattern: Regular expression pattern
    :return: Dictionary containing all tags and the number of times they appear. A total field counts total
    lines.
    """

    data = {u'total': 0}
    search_reg = re.compile(search_pattern)

    for line_num, line in enumerate(infile):

        match = search_reg.match(line)
        data[u'total'] += 1

        if match:
            if match.group() in data.keys():
                data[match.group()] += 1
            else:
                data[match.group()] = 1

        else:
            print u'bad line at {}'.format(line_num+1)

    return data

"""
Parse outline:

@00 - Start of a new Node
@77 / @88 - These need to be the beginning of a new line
@15 - Numbered section. Should start a new line, but other line breaks appear within text. Can appear on it's
own line - this needs to be handled.
@11 - Seems to be the default for a new segment, is superseded many times by other tags.
@66 - Occasionally starts a new line - does not appear to have any importance on it's own

"""


def join_singlet_tags(infile, infile_name, tag):
    """
    Certain tags may appear on their own line when they need to be inline with the text. This function
    fixes this.
    :param infile: Input file to be edited
    :param infile_name: Path to file to be edited
    :param tag: tag to search for
    :return: The updated file
    """

    infile.seek(0)
    temp_file_name = '{}.tmp'.format(infile_name)
    temp_file = codecs.open(temp_file_name, 'w', 'utf-8')
    replacements = {u'\r': u' ', u'\n': u' '}

    # clean up problematic lines then write them to temp file
    for line in infile:
        if re.match(tag, line) and len(line.split()) == 1:
            line = util.multiple_replace(line, replacements)
            line = re.sub(u' +', u' ', line)
        temp_file.write(line)

    infile.close(), temp_file.close()
    os.remove(infile_name)
    os.rename(temp_file_name, infile_name)

    return codecs.open(infile_name, 'r', 'utf-8')


noda_file.close()
os.remove('errors.html')
