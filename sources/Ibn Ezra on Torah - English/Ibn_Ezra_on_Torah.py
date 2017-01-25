# encoding=utf-8

import re
from sefaria.model.text import Ref
from bs4 import BeautifulSoup, Tag
from sefaria.datatype.jagged_array import JaggedArray

"""
filenames: 'IbnEzra_Pentateuch_Vol5.xml', The-Commentary-of-Abraham-ibn-Ezra-on-the-Pentateuch-Vol3.xml

"""


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
        parsed.set_element([loc['chapter']-1, loc['verse']-1], value)
    return parsed.array()

deut = parse('IbnEzra_Pentateuch_Vol5.xml')
torat_emet = Ref("Ibn Ezra on Devarim").text('he', 'Ibn Ezra on Devarim -- Torat Emet').ja().array()
for i, (mine, te) in enumerate(zip(deut, torat_emet)):
    if len(mine) != len(te):
        print 'problem in chapter {}'.format(i+1)
