# encoding=utf-8
import re
import os
import codecs
from collections import Counter, OrderedDict
from parsing_utilities import util
from sefaria.utils.hebrew import hebrew_term
from urllib2 import HTTPError, URLError
from sources import functions
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


def get_parsha_dict():
    """
    Terms map English parsha names to Hebrew. We need to build a dictionary that will do the reverse.
    :return: Dictionary
    """

    # We have some special cases that can't be looked up in mongo
    parashot = {u'לחנוכה': 'For Chanuka',
                u'פרשת שקלים': 'Parashat Shekalim',
                u'פרשת זכור': 'Parashat Zachor',
                u'לפורים': 'For Purim',
                u'פרשת פרה': 'Parashat Parah',
                u'פרשת החודש': 'Parashat HaChodesh',
                u'לשבת הגדול': 'For Shabbat HaGadol',
                u'פסח': 'Passover',
                u'שבועות': 'Shavuot',
                u'לחודש אלול': 'For the Month of Elul',
                u'ראש השנה': 'Rosh HaShanah',
                u'שבת תשובה': 'Shabbat Shuva',
                u'ליום כיפור': 'For the Day of Atonement',
                u'לסוכות': 'Sukkot'}
    terms = TermSet({"scheme": "Parasha"})

    for term in terms.array():
        contents = term.contents()
        he_name = contents['titles'][-1]['text']
        parashot[he_name] = contents['name']

    return parashot


def node_names():
    """
    Assemble a collection of names to use on each node.
    :return: OrderedDict of keys 'parasha' to values <year>
    """
    year_reg = re.compile(u'@44\[([\u05d0-\u05ea" -]+)]')
    parsha_reg = re.compile(u'@88([\u05d0-\u05ea ].+?) ?$')
    books = OrderedDict()
    book_names = library.get_indexes_in_category('Torah')

    for number, filename in enumerate(filenames()):
        parsha, years = None, []
        names = OrderedDict()
        with codecs.open(filename, 'r', 'utf-8') as source:
            for line in source:
                new_parsha, year = parsha_reg.match(line), year_reg.match(line)

                if new_parsha:
                    if parsha is None: # First case, no years were found yet
                        parsha = new_parsha.group(1)
                    else:
                        names[parsha] = years
                        parsha = new_parsha.group(1)
                        years = []

                elif year:
                    years.append(year.group(1))

                else:
                    continue
            else:
                names[parsha] = years
        books[book_names[number]] = names
    return books


def get_civil_year(year_line, book):
    """
    JN are named by year. The he_title can be lifted directly from the text, this function converts them to English
    equivalent. The conversion is not exact, as an exact mapping of Parsha - Date is not available at this time.
    Therefore, each book will get a "typical" Hebrew data which is used to extract the standard civil date. This may
    contain several errors, which will be corrected down the road.
    :param year_line: A line of text from which year data is extracted. May contain multiple years (i.e. תרל"ז-תרל"ח)
    :param book: What book is this taken from (i.e. Genesis, Exodus etc.).
    :return: civil year(s)
    """

    typical_dates = {
        'Genesis': [7, 1],
        'Exodus': [10, 20],
        'Leviticus': [1, 1],
        'Numbers': [3, 20],
        'Deuteronomy': [5, 1]
    }

    he_years = [util.getGematria(match)+5000 for match in re.findall(u'[\u05d0-\u05ea"]{4,5}', year_line)]
    en_years = [str(year) for year in he_years]

    return '; '.join(en_years)


def sefat_parse_helper(lines):

    parsed, current = [], None
    for line in lines:
        line = re.sub(u' +', u' ', line)
        line = line.replace(u'\n', u'')
        line = line.rstrip(u' ')
        line = line.replace(u'@22', u'')

        if re.search(ur'@44\[.*]', line):
            if current is not None:
                parsed.append(current)
            current = [re.sub(ur'@44\[(.*)]', ur'\1', line)]

        else:
            if line == u'':
                continue
            else:
                current.append(line)
    else:
        parsed.append(current)
    return parsed


def parse():
    book_names = library.get_indexes_in_category('Torah')
    names = node_names()
    parsed = {}
    for book_name, filename in zip(book_names, filenames()):
        with codecs.open(filename, 'r', 'utf-8') as infile:
            current = util.file_to_ja(2, infile, [u'@88'], sefat_parse_helper).array()
            parsed[book_name] = util.clean_jagged_array(current, [u'@[0-9]{2}', u'\?'])
    for book in book_names:
        parashot = names[book].keys()
        parsed[book] = util.simple_to_complex(parashot, parsed[book])

    return parsed


def fix_hebrew_years(to_fix):
    if re.search(u'-', to_fix):
        to_fix = to_fix.replace(u'-', u' ; ')
        to_fix = re.sub(u' +', u' ', to_fix)
        to_fix = to_fix.replace(u' ;', u';')
        return to_fix
    else:
        return to_fix


def construct_index():
    names = node_names()
    en_parasha = get_parsha_dict()

    root = SchemaNode()
    root.add_title('Sefat Emet', 'en', primary=True)
    root.add_title(u'שפת אמת', 'he', primary=True)
    root.key = 'Sefat Emet'

    for book in names.keys():
        book_node = SchemaNode()
        book_node.add_title(book, 'en', primary=True)
        book_node.add_title(hebrew_term(book), 'he', primary=True)
        book_node.key = book

        for parasha in names[book].keys():
            parsha_node = JaggedArrayNode()
            p_names = [p.contents()['name'] for p in TermSet({'scheme': "Parasha"})]
            if en_parasha[parasha] in p_names:
                parsha_node.add_shared_term(en_parasha[parasha])
                parsha_node.key = en_parasha[parasha]
            else:
                parsha_node.add_primary_titles(en_parasha[parasha], parasha)
            parsha_node.add_structure(['Section', 'Comment'])
            book_node.append(parsha_node)
        root.append(book_node)
    root.validate()

    index = {
        'title': 'Sefat Emet',
        'categories': ['Chasidut'],
        'schema': root.serialize()
    }
    return index


def upload():
    functions.post_index(construct_index())
    parsed = parse()
    names = node_names()
    en_parasha_names = get_parsha_dict()
    for book in names.keys():
        for parasha in names[book].keys():
            current_text = {
                'versionTitle': 'Sefat emet, Piotrków, 1905-1908',
                'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001186213',
                'language': 'he',
                'text': parsed[book][parasha]
            }
            en_parasha = en_parasha_names[parasha]
            url = 'Sefat Emet, {}, {}'.format(book, en_parasha)
            print url
            functions.post_text(url, current_text, weak_network=True)

upload()