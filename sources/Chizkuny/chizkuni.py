# -*- coding: utf8 -*-

from sefaria.utils.util import count_by_regex as count
from sefaria.utils.util import replace_using_regex as reg_replace
import codecs
import re

'''
Parsing process:
First I I called strip_string (defined below) and removed all instances of '_' that were
all over the place in the original file.

@01 tags were used to mark the beginning of a parsha, perek and pasuk. To identify the beginning of a perek,
I found the common theme @01<perek-number> <pasuk-number>. Using the regular expression @01[א-ת]{1,2}\s[א-ת]{1,2}
I identified the beginning of a perek and replaced those @01 tags with <perek> and added a newline on the previous
line.

Once the פרקים were correctly identified, I could then easily identify @01 tags identifying a new pasuk.
The regular expression I used was '@01[א-ת]{1,2}\.' . Ideally, each pasuk should start on a new line.

A perek and a pasuk should be numbered, and this doesn't necessarily need to be a part of the text. The structure
I'm imposing the following structure:
<perek>
-perek number-
<pasuk>
-pasuk number-
'''


def count_tags(some_file, tag):
    data = codecs.open(some_file, 'r', 'utf-8')
    result = count(data, tag)
    for key, value in result.iteritems():
        print u'{0}: {1}'.format(key, value)

    data.close()


def replace_end(input_string, old, new, counts):
    """
    str.replace(old, new, count) will replace old with new count times, starting from beginning to end.
    This function replaces old with new count times from end to beginning.

    Example:
    replace_end('hello, 'l', 'g', 1)
    > 'helgo'

    :param input_string: Input string
    :param old: substring to be replaced
    :param new: substring with which to replace old
    :param counts: number of replacements to be made
    :return: String with old swapped with new count times end to beginning
    """

    # break input into count strings from end to beginning.
    temp = input_string.rsplit(old, counts)

    return new.join(temp)


def strip_string(to_remove, oldfile, newfile):
    """
    Goes through a file and strips out a single
    :param to_remove: string to be removed
    :param oldfile: original file
    :param newfile: file to save output
    """

    # loop through file
    for line in oldfile:
        line = line.replace(to_remove, '')
        newfile.write(line)


def tag_bold():
    """
    The original chizkuni text contained the tags @02 and @03 which seemed to indicate beginning and end of
    quotes from scripture. There are also some trailing tags (individual cases of @03 for example) who's purpose
    is unclear. The first operation I ran was to replace all cases of @02 <text> @03 with HTML bold tags.
    """

    # open files
    chizkuni_read = codecs.open('test.txt', 'r', 'utf-8')
    chizkuni_write = codecs.open('test_result.txt', 'w', 'utf-8')

    # compile regex
    reg = re.compile(u'@02.*@03')

    # loop through file
    for line in chizkuni_read:

        # get all cases that match regex
        results = reg.findall(line)

        # loop through results. It seems that this part is case dependant and cannot be reused
        for result in results:

            # Make multiple replacements. A temporary variable must be used, as the entire match
            # must be replaced in one shot.
            temp = replace_end(result,u'@02', u'<b>', 1)
            temp = temp.replace(u'@03', u'</b>', 1)

            line = line.replace(result, temp)

        # save line to new file
        chizkuni_write.write(line)

    chizkuni_read.close()
    chizkuni_write.close()


def tag_perek():
    """
    Sort through the ambiguous @01 tags and find the beginning of each perek.
    :param old_file: File to be parsed.
    :param new_file: File to save parsed data.
    :param expression: Regular expression to be used.
    """
    to_parse = codecs.open('chizkuni_strip.txt', 'r', 'utf-8')
    parsed = codecs.open('chizkuni_perek.txt', 'w', 'utf-8')

    for line in to_parse:
        line = reg_replace(u'@01[א-ת]{1,2}\s[א-ת]{1,2}\.', line, u'@01', u'\n<perek>\n')
        parsed.write(line)


def tag_pasuk():
    to_parse = codecs.open('chizkuni_perek.txt', 'r', 'utf-8')
    parsed = codecs.open('chizkuni_perek-pasuk.txt', 'w', 'utf-8')

    for line in to_parse:
        line = reg_replace(u'@01[א-ת]{1,2}\.', line, u'@01', u'\n<pasuk>\n')
        parsed.write(line)

    to_parse.close()
    parsed.close()


def chapter_verse():
    """
    Break the numbers (actually hebrew letters) for chapters and verse off main text so they stand on
    their own lines.
    """

    to_parse = codecs.open('chizkuni_perek-pasuk.txt', 'r', 'utf-8')
    parsed = codecs.open('chizkuni_labeled.txt', 'w', 'utf-8')

    # set flags
    perek, pasuk = False, False

    for line in to_parse:

        if perek:

            # break up line into list of words. First two "words" are chapter, verse numbers
            words = line.split(u' ')

            parsed.write(words[0] + u'\n')
            parsed.write(u'<pasuk>' + u'\n')
            parsed.write(words[1] + u'\n')

            line = ' '.join(words[2:])
            parsed.write(line)

            # reset flag
            perek = False

        elif pasuk:

            # break up line into list of words. First "word" is verse number.
            words = line.split(u' ')
            parsed.write(words[0] + u'\n')

            line = ' '.join(words[1:])
            parsed.write(line)

            # reset flag
            pasuk = False

        elif line == u'<perek>\n':

            parsed.write(line)
            perek = True

        elif line == u'<pasuk>\n':

            parsed.write(line)
            pasuk = True

        else:
            parsed.write(line)

    to_parse.close()
    parsed.close()

chapter_verse()