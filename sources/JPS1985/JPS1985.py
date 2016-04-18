# coding=utf-8
"""
url for original files:
https://drive.google.com/drive/u/1/folders/0BwEntTcxGmMANFdVSGdJRS1hYzQ

Stripped out all footnotes. Footnote markers are in rectangular brackets.

Parsha names are all in caps - use str.upper to find them.

Book names are not clearly marked. A previous line can be indicated as a book name by the chapter number
resetting to 1.

Chapter numbers are listed as <digit><space>. Verse numbers are connected to words.

On every line called, call str.replace as follows:
% --when it follows a letter means that there should be a dot under that letter
@ --stands for "s" with a dot underneath. - only appears in footnotes

A first run should strip out all footnote markers. Later on, a script should be run to map footnotes to
Book, chapter, verse.

The information declaring the beginning of a new chapter always appears in the next line. Because of this, each
line is processed, then saved as previous_line. Decisions about what to do with this line can then be made based
on the next line in the text.

Copyright JPS
"""

from sources import functions
import regex as re
import codecs
from sefaria.model import *
import sys


def process_verses(chap_string, expression):
    """
    Take an entire chapters as a string and break up into verses. The new chapter index (number followed by
    a space) must be stripped out.

    :param chap_string: All verses in a chapter combined as one string.
    :param expression: A compiled regular expression with which to find new verses.
    :return: A list of strings (jagged array), with each verse as a separate string.
    """

    # find all new verses with the regular expression
    matches = expression.finditer(chap_string)

    # save start position of first verse and initiate list of verses
    try:
        start = next(matches)
    except StopIteration:
        return [chap_string]
    verses = []

    # loop through matches until StopIteration is raised at the last verse
    while True:
        try:
            end = next(matches)
            verses.append(chap_string[start.end()-1:end.start()])
            start = end

        except StopIteration:
            verses.append(chap_string[start.end()-1:])
            break

    # error correction - look for numbers in each verse and compare to verse number
    # This will differentiate between incorrectly formatted verses numbers and other numbers in the text.
    corrected_verses = []
    for index, verse in enumerate(verses):
        nums = re.finditer(u'\d{1,3} ', verse)
        good = True

        for num in nums:
            if int(num.group()) - index == 2:

                # add first verse
                corrected_verses.append(verse[:num.start()])

                # edit second verse
                second = verse[num.start():]
                second = second.replace(num.group(), num.group()[:len(num.group())])
                corrected_verses.append(second)
                good = False
                break

        if good:
            corrected_verses.append(verse)

    # strip out the * marker used to help differentiate numbers and verses
    for index, verse in enumerate(corrected_verses):
        corrected_verses[index] = verse.replace(u'*', u'')

    return corrected_verses


def chapter_correct(chapter):
    """
    Check a chapter to ensure the number of verses match the verse numbers included in a chapter

    :param chapter: a list of strings representing all verses in chapter
    :return: True if no errors are found, false otherwise.
    """


def write_to_file(books, output_file):
    for book in books:
        output_file.write(book+u'\n')
        for number, chapter in enumerate(books[book]):
            output_file.write(u'\tchapter {0}:'.format(number+1)+u'\n')
            for verse_number, verse in enumerate(chapter):
                output_file.write(u'\t\t'+str(verse_number+1)+verse+u'\n')


def check_verses(verse_list, data, error_list):
    """
    Go through the verses of a chapter and make sure the verse numbers match the number of verses

    :param verse_list: All verses in a chapter, arranged as a list
    :param data: Book name and chapter number, in a tuple
    :param error_list: A list of errors to log an error if found
    :return: True if no errors are found, False otherwise
    """

    for index, verse in enumerate(verse_list):

        try:
            verse_num = int(re.match(u'\d{1,3}', verse).group())

            if verse_num != index + 1:
                error_list.append(data)
                return False

        except AttributeError:
            error_list.append(data)
            return False

    return True


def upload_all(things_to_upload, upload=True):
    """

    :param things_to_upload: A dictionary where the keys are the refs, values are the texts
    :param upload: set this to false and the function will do nothing
    """

    if not upload:
        return

    # make JSON object of book
    for ref in things_to_upload.keys():
        book = {
            "versionTitle": "JPS 1985 English Translation",
            "versionSource": "Copyright JPS publishing",
            "language": "en",
            "text": things_to_upload[ref]
        }
        print ref
        functions.post_text(ref, book)


def set_flags(books, upload=True):

    if not upload:
        return

    for book in books.keys():

        # make JSON object for version
        version = {
            "ref": book,
            "lang": "en",
            "vtitle": "JPS 1985 English Translation"
        }

        # set flags
        flags = {
            "priority": 2,
            "status": 'locked'
        }
        print book
        functions.post_flags(version, flags)


def parse():

    # declare variables
    Books, Chapters, Verses = {}, [], []
    previous_line = u''
    book_name = u''
    errors = []

    # regular expressions
    chapter_reg = re.compile(u'\d{1,3}\s')
    verse_reg = re.compile(u'\d{1,3}[a-zA-Z\-"“\[‘(—]')
    footnote_reg = re.compile(u'\[[a-z]\]')

    input_file = codecs.open('JPSTanakhMaster.txt', 'r', 'utf-8')

    # define replacement dictionary
    replacements = {
            u'H%': u'\u1e24',
            u'h%': u'\u1e25',
            u'\n': u'',
            u'\r': u'',
    }

    # loop through file
    for line in input_file:

        # if this line is a parsha name - do nothing
        if line == line.upper():
            continue

        # make necessary replacements and strip footnotes
        line = functions.multiple_replace(line, replacements)
        '''footnotes = footnote_reg.findall(line)
        for case in footnotes:
            line = line.replace(case, u'')'''

        # check if line is beginning of new chapter
        new_chap = chapter_reg.match(line)
        if new_chap:

            # get chapter num
            chap_number = int(new_chap.group())
            if chap_number == 1:

                # save previous book
                if book_name != u'':
                    Chapters.append((process_verses(u''.join(Verses), verse_reg)))
                    check_verses(Chapters[len(Chapters)-1], (book_name.replace(u'\r', u';'), len(Chapters)), errors)
                    Books[book_name] = Chapters
                    Chapters = []
                    Verses = []

                book_name = previous_line

            else:
                Verses.append(previous_line)
                Chapters.append(process_verses(u''.join(Verses), verse_reg))
                check_verses(Chapters[len(Chapters) - 1], (book_name.replace(u'\r', u';'), chap_number - 1), errors)
                Verses = []

            # check that chapters are incrementing correctly
            if chap_number - len(Chapters) != 1:
                errors.append((book_name.replace(u'\r', u';'), chap_number-1))
                Chapters.append([u'error'])

            # copy line into previous_line placeholder, excluding the chapter number itself

            # if chapter number is 1, this is a new book
            previous_line = line[new_chap.end():]

        else:

            # Add previous line to verses, and save current line
            Verses.append(previous_line)
            previous_line = line

    # add last book
    Chapters.append((process_verses(u''.join(Verses), verse_reg)))
    check_verses(Chapters[len(Chapters) - 1], (book_name.replace(u'\r', u';'), len(Chapters)), errors)
    Books[book_name] = Chapters

    input_file.close()
    out = codecs.open('output.txt', 'w', 'utf-8')
    write_to_file(Books, out)
    out.close()

    # write errors
    out = codecs.open('errors.txt', 'w', 'utf-8')
    for error in errors:
        out.write('Book: {0} Chapter: {1}\n'.format(*error))
    out.close()
    print len(errors)

    return Books


def count_foot(books, regexes):
    """
    loop through books and count number of times regex appears

    :param books: dictionary containing entire jps 1985 translation
    :param regexes: list of regular expressions to compare
    :return: number of appearances of the regular expression
    """

    all_books = library.get_indexes_in_category('Tanach')
    total = 0

    # define replacement dictionary
    replacements = {
        u'\n': u'',
        u'\r': u'',
        u'\n\r': u'',
    }

    # loop through books, and combine each chapter into one string
    for book in all_books:
        for num, chapter in enumerate(books[book]):

            # make chapter into single string (to account for footnotes spanning multiple lines and verses)
            text = []
            for verse in chapter:
                text.append(functions.multiple_replace(verse, replacements))

            text = ' '.join(text)
            counts = []
            for reg in regexes:
                counts.append(len(re.findall(reg, text)))

            cannon = counts[0]
            for index, count in enumerate(counts):
                if count != cannon:
                    print '{}: {}; {}'.format(book, num+1, index)
                    total += 1
                    break

    return total


def align_footnotes(books):
    """
    The footnotes need to be structured by book and chapter. Each footnote may refer to multiple verses.

    :param books: Dictionary, containing the entire JPS 1985 translation
    return: Dictionary, with books as keys and chapters as values. Each chapter is a list of dictionaries,
    with the key "footnote" set to the footnote and the key "links" being a list of verses where the
    footnote appears.
    """

    jps_footnotes = {}

    # define replacement dictionary
    replacements = {
        u'@': u'\u1e63',
        u'h%': u'\u1e25',
        u'H%': u'\u1e24',
        u'\n': u'',
        u'\r': u'',
        u'\n\r': u'',
    }

    # get list of book in tanach
    all_books = library.get_indexes_in_category('Tanach')

    # open footnote document and retrieve first footnote
    input_file = codecs.open('JPS1985_footnotes.txt', 'r', 'utf-8')
    note = {'footnote': functions.multiple_replace(input_file.readline(), replacements)}

    # iterate through Tanach
    for book in all_books:

        # set dictionary to with keys set to chapter numbers
        footnote_chaps = {}

        for chap_num, chapter in enumerate(books[book]):

            # set flag to indicate if any footnote markers have been found
            found_note = False

            # declare array to hold all note in chapter
            chap_notes = []

            # repeatedly loop through chapter, searching for cases where footnote appears
            while True:

                # account for the case where a footnote is tagged "aa"
                if note['footnote'].find(u'aa') == 0:
                    tag = u'aa'
                else:
                    tag = note['footnote'][0]

                found = []
                for verse_num, verse in enumerate(chapter):
                    if verse.find(u'[{}]'.format(tag)) != -1:
                        found.append(verse_num+1)
                        found_note = True
                    note['links'] = found

                # if footnote markers were found, get the next footnote
                if found_note:
                    chap_notes.append(note)
                    note = {'footnote': functions.multiple_replace(input_file.readline(), replacements)}

                    if note['footnote'] == u'':
                        footnote_chaps[chap_num] = chap_notes
                        break

                # if footnote begins with "a", this is a new chapter
                try:
                    if note['footnote'][0] == u'a' and note['footnote'][1] != u'a':
                        footnote_chaps[chap_num] = chap_notes
                        break

                except IndexError:
                    print 'error'
                    print note['footnote']
                    print u'{}, chapter {}'.format(book, chap_num+1)
                    input_file.close()
                    sys.exit(1)

        jps_footnotes[book] = functions.convertDictToArray(footnote_chaps)

    input_file.close()
    return jps_footnotes

test = codecs.open('test.txt', 'w', 'utf-8')
jps = parse()
footnotes = align_footnotes(jps)
books = library.get_indexes_in_category('Tanach')
for book in books:
    test.write(u'{}:\n'.format(book))
    for index, chapter in enumerate(footnotes[book]):
        if chapter != []:
            test.write(u'  chapter {}:\n'.format(index+1))
            for note in chapter:
                test.write(u'    {}\n'.format(note['footnote']))
                test.write(u'    links:{}\n'.format(note['links']))

test.close()
