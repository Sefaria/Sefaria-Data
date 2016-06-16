# encoding=utf-8

from data_utilities import sanity_checks as tests
from data_utilities import util
from sources import functions
import codecs
import os
from sefaria.model import *

noda_file = codecs.open('Noda_BeYehuda.txt', 'r', 'utf-8')


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


noda_file.close()
os.remove('errors.html')
