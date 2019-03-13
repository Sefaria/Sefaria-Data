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


def get_sheet_by_id(page_id):
    cursor = MidreshetCursor()
    cursor.execute('select * from Pages where id=?', (page_id,))
    rows = list(cursor.fetchall())
    assert len(rows) == 1
    sheet = convert_row_to_dict(rows[0])

    cursor.execute('select * from PageResources where page_id=?', (sheet['id'],))
    resources = sorted(cursor.fetchall(), key=lambda x: x.display_order)
    resources = [convert_row_to_dict(r) for r in resources]

    for resource in resources:
        cursor.execute('SELECT name, body, exactLocation FROM Resources WHERE id=?', (resource['resource_id'],))
        try:
            actual_resource = convert_row_to_dict(cursor.fetchone())
        except AttributeError:
            actual_resource = {
                'name': '',
                'body': '',
                'exactLocation': ''
            }
        resource.update(actual_resource)
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
        my_file.write(u'exactLocation:\n  {}\n\n'.format(resource['exactLocation']))
        my_file.write(u'display_type: {}'.format(resource['display_type']))
        my_file.write(u'\n\n\n\n')

    my_file.close()


