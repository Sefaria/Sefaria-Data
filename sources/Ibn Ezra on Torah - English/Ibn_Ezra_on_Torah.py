# encoding=utf-8

import re
import codecs
from sefaria.model.text import Ref
from bs4 import BeautifulSoup, Tag
from sources.functions import post_text
from data_utilities.util import ja_to_xml
from sefaria.datatype.jagged_array import JaggedArray

"""
filenames: 'IbnEzra_Pentateuch_Vol5.xml', 'The-Commentary-of-Abraham-ibn-Ezra-on-the-Pentateuch-Vol3.xml'

"""
file_data = {
    'Deuteronomy': 'IbnEzra_Pentateuch_Vol5.xml',
    'Leviticus': 'The-Commentary-of-Abraham-ibn-Ezra-on-the-Pentateuch-Vol3.xml'
}

def identify_location(xref):
    """
    Identify chapter, verse of xref. If chapter not listed, set it to None and handle in external function
    :param Tag xref: Element xref.
    :return: {'chapter': int or None, 'verse': int}
    """
    match = re.search(ur'\[(.*?)\]', xref.text)
    assert match is not None
    if re.search(u':', match.group(1)):
        values = match.group(1).split(u':')
        return {'chapter': int(values[0]), 'verse': int(values[1])}
    else:
        return {'chapter': None, 'verse': int(match.group(1))}

def populate_comment_store(filename):
    comment_store = {}

    with open(filename) as infile:
        soup = BeautifulSoup(infile, 'xml')
    # xrefs = soup.find_all(lambda x: True if x.name == 'xref' and 'ftnote' not in [t.name for t in x.parents] else False)
    xrefs = soup.find_all('xref')
    current_chapter = 1
    for xref in xrefs:
        try:
            location = identify_location(xref)
        except AssertionError:
            continue
        if location['chapter'] is None:
            location['chapter'] = current_chapter
        else:
            current_chapter = location['chapter']

        assert comment_store.get(xref.attrs['rid']) is None
        comment_store[xref.attrs['rid']] = location
    return comment_store


def structure_comments(verse):
    def clean_string(value):
        value = value.replace(u'\n', u' ')
        value = value.replace(u'\xb6', u'')
        value = value.replace(u'\u2283', u'')
        value = value.replace(u'\2282', u'')
        value = value.replace(u'\u0259', u'e')
        value = value.replace(u'[ ', u'[')
        value = value.replace(u' ]', u']')
        value = re.sub(u'G ?OD', u'God', value)
        value = re.sub(u' +', u' ', value)
        value = value.rstrip()
        value = value.lstrip()
        return value

    verse = re.sub(u'\[.*?\]', u'', verse, 1)
    soup = BeautifulSoup(u'<root>{}</root>'.format(verse), 'xml')
    # destroy empty b tags
    for element in soup.find_all(lambda x: x.name == 'b' and (x.is_empty_element or x.text.isspace())):
        element.decompose()
    for element in soup.find_all('xref'):
        element.decompose()
    for element in soup.find_all('small'):
        element.unwrap()
    for element in soup.find_all('sup'):
        element.unwrap()

    verse = clean_string(u' '.join(unicode(child) for child in soup.root.children))
    comments, start_index = [], 0
    for match in re.finditer(ur'\. <b>', verse):
        comments.append(verse[start_index:match.start()+1])
        start_index = match.start() + 2
    comments.append(verse[start_index:])
    return comments


def pre_parse(filename, overwrite=False):
    with open(filename) as infile:
        soup = BeautifulSoup(infile, 'xml')

    for li in soup.find_all('li'):
        assert li.parent.name == 'ul'
        li.unwrap()
    for bold in soup.find_all('bold'):
        bold.name = u'b'
    for italic in soup.find_all('italic'):
        italic.name = u'i'

    for chapter in soup.find_all('chapter'):
        footnotes = chapter.find_all('ftnote')

        for footnote in footnotes:
            next_sibling = footnote.next_sibling
            if next_sibling is None:
                break

            while next_sibling.name != 'ftnote':
                footnote.append(next_sibling)
                if isinstance(next_sibling, Tag):
                    next_sibling.unwrap()
                next_sibling = footnote.next_sibling
                if next_sibling is None:
                    break

    if not overwrite:
        filename = filename.replace('.xml', '_copy.xml')
    with codecs.open(filename, 'w', 'utf-8') as outfile:
        outfile.write(unicode(soup))


def parse(filename):
    comment_store = populate_comment_store(filename)
    parsed = JaggedArray([[]])

    with open(filename) as infile:
        soup = BeautifulSoup(infile, 'xml')
    footnotes = soup.find_all('ftnote')
    for footnote in footnotes:
        loc = comment_store.get(footnote.attrs['id'])
        if loc is None:
            continue
        value = u''.join([unicode(child) for child in footnote.children])
        parsed.set_element([loc['chapter']-1, loc['verse']-1], structure_comments(value), pad=[])
    return parsed.array()


def test(book):
    qa_issues = open('Ibn Ezra on {} misalignments.txt'.format(book), 'w')
    levi = parse(file_data[book])
    vtitle = 'Devarim' if book == 'Deuteronomy' else book
    torat_emet = Ref("Ibn Ezra on {}".format(book)).text('he', 'Ibn Ezra on {} -- Torat Emet'.format(vtitle)).ja().array()
    count = 0
    for c_index, (my_chapter, thier_chapter) in enumerate(zip(levi, torat_emet)):
        for v_index, (my_verse, their_verse) in enumerate(zip(my_chapter, thier_chapter)):
            if len(my_verse) != len(their_verse):
                    qa_issues.write('issue found at {}:{}\n'.format(c_index+1, v_index+1))
                    count += 1
        if len(my_chapter) != len(thier_chapter):
            by_length = sorted((my_chapter, thier_chapter), key=lambda x:len(x))
            for i in range(len(by_length[0]), len(by_length[1])):
                qa_issues.write('issue found at {}:{}\n'.format(c_index+1, i+1))
                count += 1
    qa_issues.close()
    print '{} issues found'.format(count)
    ja_to_xml(levi, ['Chapter', 'Verse', 'Comment'])


def post(book):
    title = 'Ibn Ezra on {}'.format(book)
    version = {
        'title': title,
        'versionTitle': 'Ibn Ezra on the Pentateuch; trans. by Jay F. Shachter',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001028367',
        'language': 'en',
        'text': parse(file_data[book])
    }
    post_text(title, version)
