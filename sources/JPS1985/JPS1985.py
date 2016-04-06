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
import re
import codecs


def process_verses(chap_string, expression):
    """
    Take an entire chapters as a string and break up into verses.

    :param chap_string: All verses in a chapter combined as one string. Should not contain newline characters.
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

    return verses


def write_to_file(books, output_file):
    for book in books:
        output_file.write(book+u'\n')
        for number, chapter in enumerate(books[book]):
            output_file.write(str(number+1)+u'\n')
            for verse in chapter:
                output_file.write(verse+u'\n')


# declare variables
Books, Chapters, Verses = {}, [], []
previous_line = u''
book_name = u''
errors = []

# regular expressions
chapter_reg = re.compile(u'\d{1,3}\s')
verse_reg = re.compile(u'\d{1,3}[a-z,A-Z]')
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
    footnotes = footnote_reg.findall(line)
    for case in footnotes:
        line = line.replace(case, u'')

    # check if line is beginning of new chapter
    new_chap = chapter_reg.match(line)
    if new_chap:

        # get chapter num
        chap_number = int(new_chap.group())
        if chap_number == 1:

            # save previous book
            if book_name != u'':
                Chapters.append((process_verses(u''.join(Verses), verse_reg)))
                Books[book_name] = Chapters
                Chapters = []
                Verses = []

            book_name = previous_line

        else:
            Verses.append(previous_line)
            Chapters.append(process_verses(u''.join(Verses), verse_reg))
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
