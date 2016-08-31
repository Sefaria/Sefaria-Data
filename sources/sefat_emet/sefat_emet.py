# encoding=utf-8
import re
import os
import codecs
from collections import Counter
from data_utilities import util
from sefaria.model import *


def filenames():
    """
    Get the filenames for sefat emet source files
    """
    file_header =  'sefat_emet_on_{}.txt'
    for book in library.get_indexes_in_category('Torah'):
        yield file_header.format(book)


def untagged_lines():
    """
    Looks for lines without tags
    :return:
    """
    file_header = 'sefat_emet_on_{}.txt'
    for book in library.get_indexes_in_category('Torah'):
        good = True

        with codecs.open(file_header.format(book), 'r', 'utf-8') as infile:
            for line_num, line in enumerate(infile):

                if not re.match(u'@[0-9]{2}', line):
                    print '\nbad line at: {} line {}'.format(book, line_num)
                    print line
                    good = False

        if good:
            print '{} is okay'.format(book)


def tag_counter(filename, line_start=False):
    """
    Count the number of tags in the documents
    :param filename: Name of the file to examine
    :param line_start: If True, will only count tags that begin a line
    :return: Counter dictionary
    """

    pattern = re.compile(u'@[0-9]{2}')

    with codecs.open(filename, 'r', 'utf-8') as infile:
        if line_start:
            return Counter([pattern.match(line).group() for line in infile])

        else:
            return Counter([match for line in infile for match in pattern.findall(line)])


def analyze_files():
    for filename in filenames():
        print '\n{}'.format(filename)
        print 'all tags:'
        c = tag_counter(filename)
        for key in c.keys():
            print u'{}: {}'.format(key, c[key])

        print '\nLine start only'
        c = tag_counter(filename, line_start=True)
        for key in c.keys():
            print u'{}: {}'.format(key, c[key])


def combine_lines():

    file_name = 'sefat_emet_on_Leviticus.txt'
    with codecs.open(file_name, 'r', 'utf-8') as infile:
        old_file = infile.readlines()

    previous_line = None
    new_file = codecs.open('tmp.txt', 'w', 'utf-8')

    for line in old_file:
        if previous_line is not None:
            if re.match(u'@22', previous_line) and re.match(u'@44', line):
                previous_line = previous_line.replace(u'\n', u' ')
            new_file.write(previous_line)

        previous_line = line
    else:
        new_file.write(previous_line)

    new_file.close()
    os.rename('tmp.txt', file_name)


def isolate_years(line):
    """
    Helper function to be passed to util.restructure_file().
    Restructure source files so the years appear on a line before the @22 tag.
    """

    match = re.match(u'@22.*(@44\[[\u05d0-\u05ea" -]+]).*', line)
    if match:
        year = match.group(1)
        line = line.replace(year, u'')
        line = u'{}\n{}'.format(year, line)

    return line
