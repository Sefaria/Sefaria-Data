# encoding=utf-8
from __future__ import print_function

import re
import json
import codecs
import bleach
import pyodbc
import requests
from data_utilities.util import Singleton, getGematria
from sources.functions import post_sheet

import django
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import InputError


class MidreshetCursor(object):
    __metaclass__ = Singleton

    def __init__(self):
        try:
            with open('login_details.json') as fp:
                login_details = json.load(fp)
        except IOError as e:
            print("Please save your username and password as json in file login_details.json")
            raise e

        username = login_details['username']
        password = login_details['password']
        server = 'localhost'
        database = 'BeitMidrash'
        connect_string = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password
        cnxn = pyodbc.connect(connect_string)
        self.cursor = cnxn.cursor()

    def __getattr__(self, item):
        return getattr(self.cursor, item)


def convert_row_to_dict(table_row):
    columns = [i[0] for i in table_row.cursor_description]
    return {column: getattr(table_row, column) for column in columns}


def get_terms_for_resource(resource_id, page_id):
    cursor = MidreshetCursor()
    cursor.execute('SELECT typeTerms, name, body, termId '
                   'FROM ResourcesTermsOnPage '
                   'JOIN Terms ON ResourcesTermsOnPage.termId = Terms.Id '
                   'WHERE ResourcesTermsOnPage.resourceId=? AND ResourcesTermsOnPage.pageId=?', (resource_id, page_id))
    return [convert_row_to_dict(r) for r in cursor.fetchall()]


def get_dicts_for_resource(resource_id):
    cursor = MidreshetCursor()
    cursor.execute('SELECT name, body '
                  'FROM ResourcesTranslations JOIN Dictionary '
                  'ON ResourcesTranslations.dicId = Dictionary.id '
                  'WHERE ResourcesTranslations.resourceId=? AND ResourcesTranslations.isOnPage=?', (resource_id, 1))
    return [convert_row_to_dict(r) for r in cursor.fetchall()]


def get_sheet_by_id(page_id):
    cursor = MidreshetCursor()
    cursor.execute('select * from Pages where id=?', (page_id,))
    rows = list(cursor.fetchall())
    assert len(rows) == 1
    sheet = convert_row_to_dict(rows[0])

    cursor.execute('SELECT name, body, exactLocation, resource_id, display_type '
                   'FROM PageResources JOIN Resources '
                   'ON PageResources.resource_id = Resources.id '
                   'WHERE PageResources.page_id=? '
                   'ORDER BY PageResources.display_order', (page_id,))
    resources = [convert_row_to_dict(r) for r in cursor.fetchall()]

    for resource in resources:
        resource['terms'] = get_terms_for_resource(resource['resource_id'], page_id)
        resource['dictionary'] = get_dicts_for_resource(resource['resource_id'])
    sheet['resources'] = resources
    return sheet


def export_sheet_to_file(sheet_id):
    sheet = get_sheet_by_id(sheet_id)
    my_file = codecs.open('sheet_{}.txt'.format(sheet_id), 'w', 'utf-8')
    my_file.write(u'{}\n\n'.format(sheet['name']))
    my_file.write(u'{}\n\n'.format(sheet['description']))

    for resource in sheet['resources']:
        my_file.write(u'name:\n  {}\n\n'.format(resource['name']))
        my_file.write(u'{}\n\n'.format(bleach.clean(resource['body'], strip=True, tags=[], attributes={})))
        for term in resource['terms']:
            my_file.write(u'typeTerms: {}; Id: {}\n{} - {}\n'.format(term['typeTerms'], term['termId'], term['name'].rstrip(), term['body']))
        for dict_entry in resource['dictionary']:
            my_file.write(u'{} - {}\n'.format(dict_entry['name'], dict_entry['body']))
        my_file.write(u'exactLocation:\n  {}\n\n'.format(resource['exactLocation']))
        my_file.write(u'display_type: {}'.format(resource['display_type']))
        my_file.write(u'\n\n\n\n')

    my_file.close()


u"""
מושגים / הסברים:
For each Resource, look up it's id in ResourceRelativeTerms.resourceId and get it's termId. Look up the term in Terms.
ResourceRelativeTerms.typeTerms defines the type of term (מושגים / הסברים).

# todo - figure out what the other types of typeTerms are
type 1,2,3 - מושגים
type 0 - הסברים
Seems not to have a name
For now, best to mark the TermType. Then, once sheets are fully compiled we can compare with the original site.

מילים:
Use ResourcesTranslations. For each Resource, look up it's id in ResourcesTranslations.resourceId. Then get it's dicId
and look that up in Dictionary


For now set all resources as outsideText. Use PrependRefWithHe for the exactLocation.
Source with an exactLocation can get sourcePrefix = u'מקור', otherwise sourcePrefix = u'דיון'
"""


def create_sheet_json(page_id):
    raw_sheet = get_sheet_by_id(page_id)
    sheet = {
        'title': raw_sheet['name'],
        'status': 'public',
        'tags': ['foo', 'bar', 'spam', 'eggs'],
        'options': {
            'language': 'hebrew',
            'numbered': False,
        },
        'sources': []
    }

    for resource in raw_sheet['resources']:
        source = {
            'outsideText': bleach.clean(resource['body'], strip=True, tags=[], attributes={}),
            'options': {}
        }
        if resource['exactLocation']:
            source['options']['sourcePrefix'] = u'מקור'
            source['options']['PrependRefWithHe'] = resource['exactLocation']
        else:
            source['options']['sourcePrefix'] = u'דיון'
        sheet['sources'].append(source)
    return sheet


def post_sheet_to_server(page_id, server):
    """
    Look up the id of a sheet on the server we're about to post to. If this is the first time the sheet has been posted,
    save the id so the sheet can be edited later.
    :param page_id:
    :param server:
    :return:
    """
    sheet_json = create_sheet_json(page_id)
    cursor = MidreshetCursor()
    cursor.execute('SELECT serverIndex FROM ServerMap WHERE pageId=? AND server=?', (page_id, server))
    result = cursor.fetchone()

    if result:
        # check that sheet really exists
        response = requests.get('{}/api/sheets/{}'.format(server, result.serverIndex)).json()

        if 'error' in response:  # update sql database
            print("Updating serverMap")
            response = post_sheet(sheet_json, server=server)
            cursor.execute('UPDATE ServerMap SET serverIndex = ? WHERE pageId=? AND server=?', (response['id'], page_id, server))
            cursor.commit()
        else:
            print("Editing sheet {}".format(result.serverIndex))
            sheet_json['id'] = result.serverIndex
            post_sheet(sheet_json, server=server)
            return
    else:
        print("Creating new sheet")
        response = post_sheet(sheet_json, server=server)
        sheet_id = response['id']
        cursor.execute('INSERT INTO ServerMap (pageId, server, serverIndex) VALUES (?, ?, ?)', (page_id, server, sheet_id))
        cursor.commit()
    return


# sheet_indices = [7, 14, 17, 49, 7387]
# for s in sheet_indices:
#     export_sheet_to_file(s)
# s = 'http://localhost:8000'
# post_sheet_to_server(7, s)
# post_sheet_to_server(14, s)
# post_sheet_to_server(14, s)


def find_books_and_categories():
    zero, single, multiple = [], [], []
    my_cursor = MidreshetCursor()
    my_cursor.execute('SELECT id, MidreshetRef FROM RefMap WHERE Book IS NULL')
    rows = my_cursor.fetchall()
    for row in rows:
        books = library.get_titles_in_string(row.MidreshetRef, 'he', True)
        if len(books) == 1:
            book_index = library.get_index(books[0])
            book_title = book_index.title
            book_category = book_index.get_primary_category()
            single.append((book_title, book_category, row.id))
        elif len(books) > 1:
            multiple.append((row.id,))
        else:
            zero.append(row)

    print('zero: {}; single: {}; multiple: {}; total: {}'.format(len(zero), len(single), len(multiple), len(rows)))

    my_cursor.executemany('UPDATE RefMap SET Book = ?, Category = ? WHERE id = ?', single)
    my_cursor.executemany("UPDATE RefMap SET Comment='Multiple' WHERE id = ?", multiple)
    my_cursor.commit()


def disambiguate_simple_tanakh_ref(map_row):
    # strip all non-hebrew characters, except the dash (maybe the em-dash?)
    clean_ref = re.sub(u'[^\u05d0-\u05ea\s\-\u2013]', u'', map_row.MidreshetRef)
    clean_ref = u' '.join(clean_ref.split())

    he_book_title = Ref(map_row.Book).he_book()
    perek = u'פרק'
    prefix = u'ספר|מגילת'

    # ^(<book-name>) <perek> (<1-3 letters>) <pasuk(im)> (<chars>-?<chars>?)
    pattern = ur'^(?:(?:%s) )?(%s) %s ([\u05d0-\u05ea]{1,3}) \u05e4\u05e1\u05d5\u05e7(?:\u05d9\u05dd)? ([\u05d0-\u05ea]{1,3}(-[\u05d0-\u05ea]{1,3})?)' % (prefix, he_book_title, perek)
    match = re.search(pattern, clean_ref)
    if match is None:
        return None
    else:
        sefaria_ref = u'{} {} {}'.format(match.group(1), match.group(2), match.group(3))
        try:
            return Ref(sefaria_ref).normal()
        except InputError:
            print(u'Could not create Ref at id = {}'.format(map_row.id))
            print(sefaria_ref)
            return None


def disambiguate_simple_talmud_ref(midreshet_ref, expected_book):
    u"""
    <Talmud Bavli> Masechet? <Masechet pattern> <Daf Pattern> <Amud Pattern>
    if range (presence of dash):
        add amud pattern
        if that fails, try daf pattern followed by amud pattern
    """
    def translate_ammud(daf_letter):
        if daf_letter == u'א':
            return u'a'
        elif daf_letter == u'ב':
            return u'b'
        else:
            raise AssertionError('Daf must be Aleph or Bet')

    cleaned_ref = re.sub(u'\u2013', u'-', midreshet_ref)
    cleaned_ref = re.sub(u'[^\u05d0-\u05ea\s\-]', u'', cleaned_ref)
    cleaned_ref = re.sub(u'\s*-\s*', u' - ', cleaned_ref)
    cleaned_ref = u' '.join(cleaned_ref.split())

    # todo write a function that can give a title with alternate spellings
    he_book_title = Ref(expected_book).he_book()
    masechet_pattern = u'{} (?:{} )?(?P<book>{})'.format(u'תלמוד בבלי', u'מסכת', he_book_title)

    start_daf_pattern = u'(?:%s )?(?P<start_daf>[\u05d0-\u05ea]{1,3})' % (u'דף',)
    end_daf_pattern = start_daf_pattern.replace(u'start_daf', u'end_daf')

    start_amud_pattern = u'(?:%s )?(?P<start_ammud>[\u05d0-\u05d1])(?! (?:%s|%s))' % (u'עמוד', u'דף', u'עמוד')
    end_amud_pattern = start_amud_pattern.replace(u'start_ammud', u'end_ammud')

    base_pattern = u'{} {} {}(?=\s|$)'.format(masechet_pattern, start_daf_pattern, start_amud_pattern)
    is_range = bool(re.search(u'{} -'.format(base_pattern), cleaned_ref))

    if is_range:
        pattern = u'{} - {}'.format(base_pattern, end_amud_pattern)
        match = re.search(pattern, cleaned_ref)

        if match:
            raw_ref = u'{} {}{}-{}{}'.format(
                expected_book, getGematria(match.group('start_daf')), translate_ammud(match.group('start_ammud')),
                getGematria(match.group('start_daf')), translate_ammud(match.group('end_ammud'))
            )

        else:
            pattern = u'{} - {} {}'.format(base_pattern, end_daf_pattern, end_amud_pattern)
            match = re.search(pattern, cleaned_ref)
            if not match:
                return
            raw_ref = u'{} {}{}-{}{}'.format(
                expected_book, getGematria(match.group('start_daf')), translate_ammud(match.group('start_ammud')),
                getGematria(match.group('end_daf')), translate_ammud(match.group('end_ammud'))
            )

    else:
        match = re.search(base_pattern, cleaned_ref)
        if not match:
            return
        raw_ref = u'{} {}{}'.format(
            expected_book, getGematria(match.group('start_daf')), translate_ammud(match.group('start_ammud')))

    return Ref(raw_ref).normal()


cu = MidreshetCursor()
# cu.execute("SELECT id, MidreshetRef, Book FROM RefMap WHERE Category = 'Tanakh' AND SefariaRef IS NULL")
# things = [(disambiguate_simple_tanakh_ref(q), q.id) for q in cu.fetchall()]
# cu.executemany("UPDATE RefMap SET SefariaRef = ? WHERE id = ?", things)
cu.execute("SELECT id, MidreshetRef, Book FROM RefMap WHERE Category = 'Talmud' AND SefariaRef IS NULL")
# for q in cu.fetchall():
#     m_ref = re.sub(u'\([^()]+\)', u'', q.MidreshetRef)
#     m_ref = u' '.join(m_ref.split())
#     ref_list = library.get_refs_in_string(u'({})'.format(m_ref), 'he', True)
#     if ref_list:
#         print(q.MidreshetRef)
#         print(ref_list[0].normal())
#     if q.id > 1000:
#         break
# cu.commit()
results, misses = [], []
q_rows = cu.fetchall()
for q in q_rows:
    try:
        t_ref = disambiguate_simple_talmud_ref(q.MidreshetRef, q.Book)
    except InputError:
        t_ref = None

    if t_ref:
        results.append((q.MidreshetRef, t_ref))
    else:
        misses.append(q.MidreshetRef)

print(len(q_rows))
print(len(results))
for q in results[:50]:
    print(q[0])
    print(q[1])
    print('')

print('Misses:')
for q in misses[:50]:
    print(q)
# foobar = disambiguate_simple_talmud_ref(u'תלמוד בבלי, מסכת שבת, דף לג עמוד ב – דף לד עמוד א (מתורגם)', 'Shabbat')
# print(foobar)


