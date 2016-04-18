# -*- coding: utf8 -*-
from sefaria.model import *
from sefaria.utils.util import count_by_regex as count
from sefaria.utils.util import replace_using_regex as reg_replace
from sefaria.utils.hebrew import decode_hebrew_numeral, hebrew_term
from sources.functions import convertDictToArray, removeAllStrings, post_index, post_text, post_link
from sources.local_setting import *
import codecs
import re

'''
Parsing process:
First I called strip_string (defined below) and removed all instances of '_' that were
all over the place in the original file. Performed by function strip_string()

@01 tags were used to mark the beginning of a parsha, perek and pasuk. To identify the beginning of a perek,
I found the common theme @01<perek-number> <pasuk-number>. Using the regular expression @01[א-ת]{1,2}\s[א-ת]{1,2}
I identified the beginning of a perek and replaced those @01 tags with <perek> and added a newline on the previous
line. Performed by tag_perek()

Once the פרקים were correctly identified, I could then easily identify @01 tags identifying a new pasuk.
The regular expression I used was '@01[א-ת]{1,2}\.' . Ideally, each pasuk should start on a new line.
Performed by tag_pasuk()

A perek and a pasuk should be numbered, and this doesn't necessarily need to be a part of the text. The structure
I'm imposing the following structure:
<perek>
-perek number-
<pasuk>
-pasuk number-

Quotes from the Torah were printed in bold in the original text. @02 tags represent the beginning of a
bold segment, and the @03 represents the return to non bold text. Unfortunately, this format left several
"floating" tags, where an @02 tag may not be followed by an @03 tag, or @03 tags with no preceding @02 tags.
Trying to catch the format @02<text>@03 is difficult using regular expressions, and therefore I outlined the
algorithm described in tag_bold() to catch only those quotes that begin and end with tags. Performed by
tag_bold().

The beginning of a parsha is designated by the tag @01פרשת . Went through file and replaced @01פרשה
with <parsha>. Performed by tag_parsha

 I manually labeled books (Genesis, Exodus...).
 I then stripped all remaining tags with strip_tags().

 The Chizkuni commentator must be deleted in addition to each reference

 Chizkuni will be uploaded as a single book, not a commentary. Therefore, each comment must be
 individually linked. To do this, a the book will be saved as a level four jagged array,
 with the levels being Book, Chapter, Verse, comments. Using this structure, linking should be
 trivial.

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


def combine_pasuk(preparsed, combined):
    """
    Combine each pasuk into one long string

    """

    # set flag to ensure text is from commentary and is not meta-data. Declare storage variable.
    is_pasuk = False
    pasuk = []

    for line in preparsed:

        if is_pasuk:

            # if end of pasuk has been reached, combine and write to file
            if line.find(u'<pasuk>') == 0:
                combined.write(u''.join(pasuk).replace(u'  ', u' ') + u'\n')

                # write pasuk tag and pasuk number
                combined.write(line + preparsed.readline())
                pasuk = []

            elif line.find(u'<perek>') == 0:
                is_pasuk = False

                combined.write(u''.join(pasuk).replace(u'  ', u' ') + u'\n')
                pasuk = []

                combined.write(line)

            else:

                # remove new line tags
                line = line.replace(u'\n', u' ')
                pasuk.append(line)

        else:

            if line.find(u'<pasuk>') == 0:
                is_pasuk = True

                # write pasuk tag and pasuk number
                combined.write(line + preparsed.readline())

            else:
                combined.write(line)

    # write last line
    combined.write(u''.join(pasuk).replace(u'  ', u' ') + u'\n')


def tag_bold():
    """
    * Loop through file. Combine every pasuk into one long string.
    *
    * In each pasuk, replace every @02 with \n@02 and every @03 with @03\n.
    *
    * If and only if a line begins and ends with the correct tag, replace tags with HTML bold.
    *
    * Otherwise, remove tags.
    """

    # combine each pasuk
    preparsed = codecs.open('chizkuni_labeled.txt', 'r', 'utf-8')
    parsed = codecs.open('chizkuni_combined.txt', 'w', 'utf-8')

    combine_pasuk(preparsed, parsed)

    preparsed.close()
    parsed.close()

    # make all @02 start a line, @03 end a line
    preparsed = codecs.open('chizkuni_combined.txt', 'r', 'utf-8')
    parsed = codecs.open('chizkuni_split.txt', 'w', 'utf-8')

    for line in preparsed:
        line = line.replace(u'@02', u'\n@02')
        line = line.replace(u'@03', u'@03\n')
        parsed.write(line)

    preparsed.close()
    parsed.close()


    # on line that begin and end with tags, replace tags with HTML
    preparsed = codecs.open('chizkuni_split.txt', 'r', 'utf-8')
    parsed = codecs.open('chizkuni_bold.txt', 'w', 'utf-8')

    reg = re.compile(u'@02.*@03')

    for line in preparsed:
        found = reg.search(line)

        if found:
            line = line.replace(u'@02', u'<b>')
            line = line.replace(u'@03', u'</b>')

        else:
            line = line.replace(u'@02', u'')
            line = line.replace(u'@03', u'')

        parsed.write(line)

    preparsed.close()
    parsed.close()

    # recombine each pasuk
    preparsed = codecs.open('chizkuni_bold.txt', 'r', 'utf-8')
    parsed = codecs.open('chizkuni_combined.txt', 'w', 'utf-8')

    combine_pasuk(preparsed, parsed)

    preparsed.close()
    parsed.close()


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
        line = line.replace(u'_', u'')
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


def tag_parsha():
    """
    Put each parsha tag on a separate line
    """

    to_parse = codecs.open('chizkuni_combined.txt', 'r', 'utf-8')
    parsed = codecs.open('chizkuni_parsha.txt', 'w', 'utf-8')

    for line in to_parse:
        line = line.replace(u'@01פרשת', u'\n<parsha>')

        parsed.write(line)

    to_parse.close()
    parsed.close()


def strip_tags():
    """
    Strip all remaining tags.
    """

    to_parse = codecs.open('chizkuni_parsha.txt', 'r', 'utf-8')
    parsed = codecs.open('chizkuni_no-tags.txt', 'w', 'utf-8')

    for line in to_parse:
        found = re.search(u'@[\d]{1,4}', line)

        if found:
            line = line.replace(found.group(), u'')

        parsed.write(line)

    to_parse.close()
    parsed.close()


def process_verse(text):
    """

    :return A list of strings. Each string represents a single comment
    """
    # strip out newline tags
    text = removeAllStrings([u'\n', u'\r'], text)
    comments = []

    # break up comments in verse by searching for quotes following periods
    new_comments = re.finditer(u'\. <b>', text)
    start = 0

    while True:
        try:
            end = next(new_comments).start()
            comments.append(text[start:end])
            start = end+2

        except StopIteration:
            comments.append(text[start:])
            break

    return comments


def parse_text():
    """
    Takes the result of strip_tags() and parses into a level four data structure for easy upload

    :return: Dictionary of books, depth 4.
    """

    # initiate data structure and variables
    full_text, chapters, verses, raw_text = {}, {}, {}, u''
    current_book, current_chapter, current_verse = u'', u'', u''

    to_parse = codecs.open('chizkuni_no-tags.txt', 'r', 'utf-8')

    for line in to_parse:

        # if new book add book to full_text.
        if line.find(u'<book>') != -1:

            # if this is the first book, do nothing
            if current_book != u'':

                # set up book and add it to full_text
                verses[current_verse] = process_verse(raw_text)
                chapters[current_chapter] = convertDictToArray(verses)
                full_text[current_book] = convertDictToArray(chapters)

                # reset verses and chapters
                chapters, verses, raw_text = {}, {} ,u''
                current_chapter, current_verse = u'', u''

            # save the next book as current_book
            current_book = removeAllStrings([u'\n', u'\r', u' '], to_parse.readline())

        # if new chapter, add verses to previous chapter
        elif line.find(u'<perek>') != -1:

            # if first chapter, set current chapter but do nothing else
            if current_chapter != u'':

                verses[current_verse] = process_verse(raw_text)
                chapters[current_chapter] = convertDictToArray(verses)
                verses, raw_text = {}, u''

            # get next chapter number
            current_chapter = removeAllStrings([u'.', u'\n'], to_parse.readline())
            current_chapter = decode_hebrew_numeral(current_chapter)
            current_verse = u''

        # if new verse, process raw text and add to verses
        elif line.find(u'<pasuk>') != -1:

            # add previous verse if not first verse
            if current_verse != u'':
                verses[current_verse] = process_verse(raw_text)
                raw_text = u''

            # get next verse number
            current_verse = removeAllStrings([u'.', u'\n'], to_parse.readline())
            current_verse = decode_hebrew_numeral(current_verse)

        # don't include parsha tags
        elif line.find(u'<parsha>') != -1:
            continue

        else:

            # add to raw text
            raw_text += line

    # add final book
    verses[current_verse] = process_verse(raw_text)
    chapters[current_chapter] = convertDictToArray(verses)
    full_text[current_book] = convertDictToArray(chapters)

    to_parse.close()
    return full_text


def print_struct_to_file(struct):

    output = codecs.open('test.txt', 'w', 'utf-8')
    books = [u'Genesis', u'Exodus', u'Leviticus', u'Numbers']
    print struct.keys()

    for book in books:
        output.write(u'<book>\n{}\n'.format(book))

        for index, chapter in enumerate(struct[book]):
            output.write(u'<chapter>\n{}\n'.format(index+1))

            for num, verse in enumerate(chapter):
                output.write(u'<verse>\n{}\n'.format(num+1))

                for comment in verse:
                    output.write(u'<comment>\n{}\n'.format(comment))

    output.close()


def upload_index(full_text, upload=False):
    """
    :param full_text: Data structure from parse_text()
    :param upload: set to True, otherwise function will do nothing
    """

    if not upload:
        return

    books = [u'Genesis', u'Exodus', u'Leviticus', u'Numbers', u'Deuteronomy']

    # create index record
    record = SchemaNode()
    record.add_title('Chizkuni', 'en', primary=True,)
    record.add_title(u'חזקוני', 'he', primary=True)
    record.key = 'Chizkuni'

    # add nodes
    for book in books:
        node = JaggedArrayNode()
        node.add_title(book, 'en', primary=True)
        node.add_title(hebrew_term(book), 'he', primary=True)
        node.key = book
        node.depth = 3
        node.addressTypes = ['Integer', 'Integer', 'Integer']
        node.sectionNames = ['Chapter', 'Verse', 'Comment']
        record.append(node)
    record.validate()

    index = {
        "title": "Chizkuni",
        "categories": ["Commentary2", "Tanach", "Chizkuni"],
        "schema": record.serialize()
    }
    post_index(index)


def upload_text(full_text, upload=False):
    """
    :param full_text: Data structure from parse_text()
    :param upload: set to True, otherwise function will do nothing
    """

    if not upload:
        return

    # make JSON object of book
    for ref in full_text.keys():
        book = {
            "versionTitle": "Chizkuni",
            "versionSource": "Chizkuni",
            "language": "he",
            "text": full_text[ref]
        }
        print ref
        post_text('Chizkuni,_{}'.format(ref), book)


def add_links(full_text, upload=False):
    """
    :param full_text: Data structure from parse_text()
    :param upload: set to True, otherwise function will do nothing
    """

    if not upload:
        return

    for book in full_text.keys():
        for chap_index, chapter in enumerate(full_text[book]):
            for verse_index, verse in enumerate(chapter):
                for comment in xrange(len(verse)):

                    post_link({
                        'refs':[
                            '{}.{}.{}'.format(book, chap_index+1, verse_index+1),
                            'Chizkuni,_{}.{}.{}.{}'.format(book, chap_index+1, verse_index+1, comment+1)
                        ],
                        'type': 'commentary',
                        'auto': True,
                        'generated_by': 'Chizkuni linker'
                    })

tag_perek()
tag_pasuk()
chapter_verse()
tag_bold()
tag_parsha()
strip_tags()
chizkuni = parse_text()
print_struct_to_file(chizkuni)
upload_index(chizkuni, True)
upload_text(chizkuni, True)
add_links(chizkuni, True)
