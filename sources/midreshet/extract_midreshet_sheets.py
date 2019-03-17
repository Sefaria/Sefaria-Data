# encoding=utf-8
from __future__ import print_function

import json
import codecs
import bleach
import pyodbc
from data_utilities.util import Singleton


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
Source with an exactLocation can get sourePrefix = u'מקור', otherwise sourcePrefix = u'דיון'
"""

# my_cursor = MidreshetCursor()
# my_cursor.execute('SELECT DISTINCT typeTerms FROM ResourcesRelativeTerms')
# term_types = [r.typeTerms for r in my_cursor.fetchall()]
# for term_type in term_types:
#     print(term_type)
#     my_cursor.execute('SELECT TOP 3 * FROM ResourcesRelativeTerms WHERE typeTerms=?', (term_type,))
#     resource_ids = [r.resourceId for r in my_cursor.fetchall()]
#     for resource in resource_ids:
#         my_cursor.execute('SELECT page_id FROM PageResources WHERE resource_id=?', (resource,))
#         try:
#             page_id = my_cursor.fetchone().page_id
#         except AttributeError:
#             continue
#         my_cursor.execute('SELECT * FROM Pages WHERE id=?', (page_id,))
#         result = my_cursor.fetchone()
#         print(result.name)
#         print(result.description)
#         print('\n')


sheet_indices = [7, 14, 17, 49, 7387]
for s in sheet_indices:
    export_sheet_to_file(s)
