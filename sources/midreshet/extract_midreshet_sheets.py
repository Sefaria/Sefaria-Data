# encoding=utf-8
from __future__ import print_function

import re
import json
from tqdm import tqdm
import codecs
import bleach
import pyodbc
import requests
from sources.functions import post_sheet
from data_utilities.util import Singleton, getGematria
from research.source_sheet_disambiguator.main import refine_ref_by_text

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


def disambiguate_simple_tanakh_ref(raw_ref, book_name):
    # strip all non-hebrew characters, except the dash (maybe the em-dash?)
    clean_ref = re.sub(u'[^\u05d0-\u05ea\s\-\u2013]', u'', raw_ref)
    clean_ref = u' '.join(clean_ref.split())

    # he_book_title = Ref(book_name).he_book()
    he_book_title = u'|'.join(Ref(book_name).index.all_titles('he'))
    perek = u'פרק'
    prefix = u'ספר|מגילת'

    # ^(<book-name>) <perek> (<1-3 letters>) <pasuk(im)> (<chars>-?<chars>?)
    pattern = ur'(?:(?:%s) )?(%s)(?: %s)? ([\u05d0-\u05ea]{1,3}) \u05e4\u05e1\u05d5\u05e7(?:\u05d9\u05dd)? ([\u05d0-\u05ea]{1,3}(-[\u05d0-\u05ea]{1,3})?)' % (prefix, he_book_title, perek)
    match = re.search(pattern, clean_ref)
    if match is None:
        return None
    else:
        sefaria_ref = u'{} {} {}'.format(match.group(1), match.group(2), match.group(3))
        try:
            return Ref(sefaria_ref)
        except InputError:
            print(u'Could not create Ref:')
            print(sefaria_ref)
            return None


def get_he_talmud_titles(en_tractate):
    alts = {
        u'Niddah': [u'נידה'],
    }

    standard_title = Ref(en_tractate).he_book()
    all_titles = [standard_title] + alts.get(en_tractate, [])
    return u'|'.join(all_titles)


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

    # if re.search(u'רשי', cleaned_ref):
    #     return None

    # he_book_title = Ref(expected_book).he_book()
    he_book_title = get_he_talmud_titles(expected_book)
    # masechet_pattern = u'{} (?:{} )?(?P<book>{})'.format(u'תלמוד ה?בבלי', u'מסכת', he_book_title)
    masechet_pattern = u'(?:{} )?(?P<book>{})'.format(u'מסכת', he_book_title)

    start_daf_pattern = u'(?:%s )?(?P<start_daf>[\u05d0-\u05ea]{1,3})' % (u'דף',)
    end_daf_pattern = start_daf_pattern.replace(u'start_daf', u'end_daf')

    start_amud_pattern = u'(?:%s)?(?P<start_ammud>[\u05d0-\u05d1])(?! (?:%s|%s))' % (u'עמוד |ע', u'דף', u'עמוד')
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

    return Ref(raw_ref)


class RefBuilder(object):

    def __init__(self):
        self._category_maps = {
            u'משנה': u'Mishnah',
            u'תוספתא': u'Tosefta',
            u'ירושלמי': u'Jerusalem Talmud',
        }
        self._commentary_maps = {}

    def redirect_category(self, raw_ref, base_ref):

        def redirected_sections(new_book, sections):
            book_node = Ref(new_book).index_node
            return u':'.join([book_node.address_class(i).toStr('en', section) for i, section in enumerate(sections)])

        if base_ref.book == u'Pirkei Avot':  # special case
            return base_ref

        if base_ref.is_talmud():
            base_book = base_ref.book
        elif base_ref.primary_category == u'Mishnah':
            base_book = re.sub(u'Mishnah ', u'', base_ref.book)
        else:
            return base_ref

        cat_regex = re.compile(u'|'.join(self._category_maps.keys()))
        category_match = cat_regex.search(raw_ref)

        if not category_match:
            return base_ref

        ref_prefix = self._category_maps[category_match.group()]
        book_title = u"{} {}".format(ref_prefix, base_book)
        try:
            new_ref = Ref(u"{} {}".format(book_title, redirected_sections(book_title, base_ref.sections)))
        except InputError:
            return base_ref
        if base_ref.is_range():
            range_end = Ref(u"{} {}".format(book_title, redirected_sections(book_title, base_ref.toSections)))
            new_ref = new_ref.to(range_end)
        return new_ref

    def _get_commentary_map_for_book(self, book_title):
        if book_title in self._category_maps:
            return self._category_maps[book_title]

        def get_hebrew_commentator(commentator_index):
            if hasattr(commentator_index, 'collective_title'):
                return library.get_term(commentator_index.collective_title).get_primary_title('he')
            else:
                return commentator_index.get_title('he')

        dependent_books = library.get_dependant_indices(book_title, full_records=True)
        he_commentators = [get_hebrew_commentator(book) for book in dependent_books]
        commentary_titles = [book.title for book in dependent_books]
        mapping = dict(zip(he_commentators, commentary_titles))

        self._commentary_maps[book_title] = mapping
        return mapping

    def apply_commentator(self, raw_ref, base_ref):
        """
        :param raw_ref:
        :param Ref base_ref:
        :return:
        """
        commentary_map = self._get_commentary_map_for_book(base_ref.book)
        if not commentary_map:  # Book has no commentaries
            return base_ref

        commentator_regex = re.compile(u'|'.join(commentary_map.keys()))
        commentator_match = commentator_regex.search(raw_ref)

        if not commentator_match:
            return base_ref

        commentator_book = commentary_map[commentator_match.group()]
        commentator_index = library.get_index(commentator_book)

        if commentator_index.is_complex():
            # get first leaf that contains our book name
            leaves = commentator_index.nodes.get_leaf_nodes()
            for leaf in leaves:
                if re.search(leaf.get_primary_title('en'), base_ref.book):
                    commentator_book = leaf.full_title('en')
                    break
            else:
                return base_ref

        commentator_ref = Ref(u"{} {}".format(commentator_book, u':'.join(base_ref.normal_sections())))
        if base_ref.is_range():
            range_end = Ref(u"{} {}".format(commentator_book, u':'.join(base_ref.normal_toSections())))
            commentator_ref = commentator_ref.to(range_end)

        return commentator_ref

    @staticmethod
    def refine_ref(raw_ref, base_ref):
        """
        :param raw_ref:
        :param Ref base_ref:
        :return:
        """
        fixed_ref = None

        if base_ref.is_talmud():
            fixed_ref = disambiguate_simple_talmud_ref(raw_ref, base_ref.book)
        elif u'Tanakh' in base_ref.index.categories:
            if base_ref.is_dependant():
                fixed_ref = disambiguate_simple_tanakh_ref(raw_ref, base_ref.index.base_text_titles[0])
            else:
                fixed_ref = disambiguate_simple_tanakh_ref(raw_ref, base_ref.book)

        if fixed_ref is None:
            return base_ref
        else:
            return fixed_ref

    def build_difficult_ref(self, raw_ref, suspected_base_ref):
        refined_ref = self.refine_ref(raw_ref, suspected_base_ref)
        refined_ref = self.redirect_category(raw_ref, refined_ref)
        return self.apply_commentator(raw_ref, refined_ref)


builder = RefBuilder()
cu = MidreshetCursor()
cu.execute("SELECT RefMap.id, MidreshetRef, Book, body FROM RefMap JOIN Resources ON RefMap.id = Resources.id WHERE RefMap.SefariaRef IS NULL")
easy, weird = [], []

for q in cu.fetchall():
    possible_refs = library.get_refs_in_string(u'({})'.format(q.MidreshetRef), 'he', citing_only=True)
    if len(possible_refs) == 1:
        better_ref = builder.build_difficult_ref(q.MidreshetRef, possible_refs[0])
        easy.append((possible_refs[0], q, better_ref))
    elif len(possible_refs) > 1:
        weird.append(q)

print(len(easy))
print(len(weird))
# for e in easy[100:200]:
#     print(e[0].normal())
#     print(e[1].MidreshetRef)
#     print(builder.build_difficult_ref(e[1].MidreshetRef, e[0]))
#     print('')

# for q in weird:
#     print(q.MidreshetRef)


def bleach_clean(some_text):
    return bleach.clean(some_text, tags=[], attributes={}, strip=True)

import unicodecsv
rows = []
for e in tqdm(easy):
    my_row = {
        'id': e[1].id,
        'MidreshetRef': e[1].MidreshetRef,
        'full_text': bleach_clean(e[1].body),
        'Sefaria Ref': e[0].normal(),
        "Yoni's attempt": e[2],
    }
    try:
        my_row['Disambiguated'] = refine_ref_by_text(e[2], '', bleach_clean(e[1].body))
    except InputError:
        my_row['Disambiguated'] = e[2]
    rows.append(my_row)

with open('Ref_Report.csv', 'w') as fp:
    writer = unicodecsv.DictWriter(fp, ['id', 'MidreshetRef', 'Sefaria Ref', "Yoni's attempt", "Disambiguated", 'full_text'])
    writer.writeheader()
    writer.writerows(rows)


# blork = RefBuilder()
# blip = u'רש"י על התלמוד הבבלי, בבא בתרא דף ז, עמוד ב'
# bloop = Ref(u'Bava Batra 7a')
# porg = blork.build_difficult_ref(blip, bloop)
# print(porg.normal())


# cu.executemany("UPDATE RefMap SET Category = 'Mishnah' WHERE id = ?", mishnah)
# build_thingy = RefBuilder()
# my_cursor = MidreshetCursor()
# my_id_list = [111, 124, 543]
# for thing in my_id_list:
#     my_cursor.execute('SELECT exactLocation, body FROM Resources WHERE id = ?', (thing,))
#     q_row = my_cursor.fetchone()
#     basic_ref = library.get_refs_in_string(u'({})'.format(q_row.exactLocation), 'he', citing_only=True)[0]
#     better_ref = build_thingy.build_difficult_ref(q_row.exactLocation, basic_ref)
#     even_better = refine_ref_by_text(better_ref, '', bleach.clean(q_row.body, tags=[], attributes={}, strip=True))
#
#     print(q_row.exactLocation)
#     print(basic_ref.normal())
#     print(better_ref.normal())
#     print(even_better.normal())
#     print(u'')
