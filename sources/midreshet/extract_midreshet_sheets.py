# encoding=utf-8
from __future__ import print_function

import re
import os
import sys
import time
import random
import signal
import regex
import json
from tqdm import tqdm
import codecs
import pymongo
import bleach
import pyodbc
import requests
import unicodecsv
from functools import partial
from itertools import groupby
from collections import namedtuple, Counter, defaultdict
from multiprocessing import Pool
from sources.functions import post_sheet
from sources.local_settings import API_KEY
from data_utilities.util import Singleton, getGematria, split_list
from research.source_sheet_disambiguator.main import refine_ref_by_text

import django
django.setup()
from sefaria.model import *
from sefaria.s3 import HostedFile
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


class NGramCatcher(object):
    """
    Use a mapping of length: counter
    One method collects grams of length n
    Another runs the previous method on a series of integers
    Add an method for catching words
    """
    def __init__(self):
        self.gram_lengths = defaultdict(Counter)

    def find_n_grams(self, n, input_string):
        pattern = u'.{%s}' % n
        self.gram_lengths[n].update(regex.findall(pattern, input_string, overlapped=True))

    def find_series_of_grams(self, n_list, input_string):
        for n in n_list:
            self.find_n_grams(n, input_string)

    def retrieve_most_common(self, gram_length, num_to_retrieve):
        return self.gram_lengths[gram_length].most_common(num_to_retrieve)


class WordSequenceCatcher(NGramCatcher):
    def find_n_grams(self, n, input_string):
        words = input_string.split()
        self.gram_lengths[n].update([u' '.join(words[i:i+n]) for i in range(len(words) - n + 1)])


class SefariaTermsAndTitles(object):
    def __init__(self):
        self.titles_and_terms_counter = Counter()
        self.terms_to_refs_map = defaultdict(set)
        # all_terms = [term_title for term in TermSet() for term_title in term.get_titles('he')]
        # everything = sorted(library.citing_title_list('he') + all_terms, key=lambda x: len(x), reverse=True)
        everything = [re.escape(s) for s in sorted(library.full_title_list('he'), key=lambda x: len(x), reverse=True)]
        prefixes = u'משהוכלב'
        pattern = u'(?:^|\s)(?:[{}])?(?P<title>{})(?=\s|$)'.format(prefixes, u'|'.join(everything))
        self.regex = re.compile(pattern)

    def find_titles_and_terms(self, input_string):
        titles = [m.group('title') for m in self.regex.finditer(input_string)]
        self.titles_and_terms_counter.update(titles)
        for t in titles:
            self.terms_to_refs_map[t].add(input_string)


def convert_row_to_dict(table_row):
    columns = [i[0] for i in table_row.cursor_description]
    return {column: getattr(table_row, column) for column in columns}


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


def cache_to_mongo(mongo_client, ref_builder):
    def wrapper(resource_id, exact_location, resource_text, replace=False):
        yonis_data = mongo_client.yonis_data
        saved_ref = yonis_data.RefSources.find_one({'resource_id': resource_id})

        if saved_ref and not replace:
            return saved_ref['SefariaRef']

        else:
            derived_ref = get_ref_for_resource(ref_builder, resource_id, exact_location, resource_text)
            yonis_data.RefSources.update_one({'resource_id': resource_id},
                                             {'$set': {'SefariaRef': derived_ref}}, upsert=True)
            return derived_ref
    return wrapper


def get_ref_for_resource(ref_builder, resource_id, exact_location, resource_text):
    if exact_location is None:
        return None

    resource_text = bleach_clean(resource_text)
    cursor = MidreshetCursor()
    cursor.execute('SELECT SefariaRef FROM RefMap WHERE id = ?', (resource_id,))
    result = cursor.fetchone()

    if result.SefariaRef:
        sefaria_ref = Ref(result.SefariaRef)
        if sefaria_ref.is_talmud() or not sefaria_ref.is_segment_level():
            try:
                refined_ref = refine_ref_by_text(sefaria_ref, u'', resource_text)
            except InputError:
                return sefaria_ref.normal()
            if refined_ref:
                return refined_ref.normal()
        return sefaria_ref.normal()

    possible_refs = library.get_refs_in_string(u'({})'.format(exact_location), 'he', citing_only=True)
    if len(possible_refs) == 1:
        constructed_ref = ref_builder.build_difficult_ref(exact_location, possible_refs[0])
        try:
            refined_ref = refine_ref_by_text(constructed_ref, u'', resource_text)
        except InputError:
            return constructed_ref.normal()
        if refined_ref:
            return refined_ref.normal()
        else:
            return constructed_ref.normal()

    else:
        return None


builder = RefBuilder()
my_mongo_client = pymongo.MongoClient()
get_ref_for_resource_p = cache_to_mongo(my_mongo_client, builder)
SheetWrapper = namedtuple('SheetWrapper', ('page_id', 'sheet_json'))


class ImageAdapter(object):
    """
    Adapts an image from the format used in midreshet to that which is used on Sefaria.
    """
    def __init__(self):
        self.image_collection = pymongo.MongoClient().yois_data.images

    def adapt_image(self, name, filename, image_bytestring, image_type):
        image_data = self.image_collection.find_one({'name': name})
        if image_data:
            return image_data['image_url']

        else:
            filename = filename.split(u'\\')[-1]
            with open(filename, 'wb') as fp:
                fp.write(image_bytestring)

            hosted_file = HostedFile(filename, image_type)
            file_url = hosted_file.upload()
            self.image_collection.insert_one({'name': name, 'image_url': file_url})
            os.remove(filename)
            return file_url


class GroupManager(object):
    def __init__(self, server):
        self.server = server
        self.group_cache = {}
        self.mongo_client = pymongo.MongoClient()

    def get_and_register_group_for_sheet(self, sheet_id):
        """
        Query data for group in SQL database
        Lookup group in cache
        if not in cache:
            lookup group and add to cache
        add sheet to group in cache
        :param sheet_id:
        :return: name of group
        """
        cursor = MidreshetCursor()
        cursor.execute('SELECT F.name AS filename, F.data, S.name AS name, S.body AS body, F.type, S.logoId '
                       'FROM Pages P '
                       'INNER JOIN Seminary S ON P.seminary_id = S.id '
                       'JOIN Files F ON S.logoId = F.id '
                       'WHERE P.id = ?', (sheet_id,))
        result = cursor.fetchone()
        if result is None:
            return self.default_group()
        group_name = result.name

        if group_name not in self.group_cache:
            self.cache_group_from_server(group_name)

        if self.group_cache[group_name]['need_to_add']:
            self.add_new_group(convert_row_to_dict(result))

        self.group_cache[group_name]['num_sheets'] += 1

        return group_name

    def change_server(self, server):
        self.server = server
        self.group_cache.clear()

    def cache_group_from_server(self, group_name):
        """
        Lookup group
        For each group, track:
            need_to_add
            num_sheets
            public
        :param group_name:
        :return:
        """
        while True:
            raw_response = requests.get(u'{}/api/groups/{}'.format(self.server, group_name))
            if raw_response.status_code == 200:
                break
            elif raw_response.status_code == 502:
                print("Got 502. will try again")
                time.sleep(30)
            else:
                print("Got bad status code. Exiting")
                sys.exit(1)

        response = raw_response.json()
        if 'error' in response:
            self.group_cache[group_name] = {
                'need_to_add': True,
                'num_sheets': 0,
                'public': False
            }
        else:
            self.group_cache[group_name] = {
                'need_to_add': False,
                'num_sheets': len(response['sheets']),
                'public': response.get('listed', False)
            }

    def add_new_group(self, group_data):
        image_collection = self.mongo_client.yonis_data.images
        image_data = image_collection.find_one({'name': group_data['name']})
        if image_data:
            file_url = image_data['image_url']

        else:
            filename = group_data['filename'].split(u'\\')[-1]
            with open(filename, 'wb') as fp:
                fp.write(group_data['data'])

            hosted_file = HostedFile(filename, group_data['type'])
            file_url = hosted_file.upload()
            image_collection.insert_one({'name': group_data['name'], 'image_url': file_url})
            os.remove(filename)

        group_json = {
            'name': group_data['name'],
            'description': bleach_clean(group_data['body']),
            'headerUrl': file_url,
            'imageUrl': file_url,
            'new': True
        }
        post_body = {'apikey': API_KEY, 'json': json.dumps(group_json)}
        post_url = u'{}/api/groups/{}'.format(self.server, group_data['name'])

        response = requests.post(post_url, data=post_body)
        if response.ok:
            self.group_cache[group_data['name']]['need_to_add'] = False

        return

    def make_group_public(self, group_name):
        if self.group_cache[group_name]['num_sheets'] < 3 or self.group_cache[group_name]['public']:
            return

        url = u'{}/api/groups/{}'.format(self.server, group_name)
        post_body = {'apikey': API_KEY, 'json': json.dumps({'name': group_name, 'listed': True})}
        response = requests.post(url, data=post_body)
        response = response.json()

        if 'error' in response:
            print(group_name, response['error'])
        else:
            self.group_cache[group_name]['public'] = True

    def publicize_groups(self):
        for group_name in self.group_cache.keys():
            if self.group_cache[group_name]['num_sheets'] >= 3 and not self.group_cache[group_name]['public']:
                self.make_group_public(group_name)

    def default_group(self):
        group_name = u'מדרשת'
        if group_name not in self.group_cache:
            self.cache_group_from_server(group_name)

        if self.group_cache[group_name]['need_to_add']:
            with open('midreshet_logo.jpg') as fp:
                logo_data = fp.read()

            self.add_new_group({
                'filename': 'midreshet_logo2.jpg',
                'data': logo_data,
                'name': u'מדרשת',
                'body': '',
                'type': 'image/pjpeg',
                'logoId': None
            })

        self.group_cache[group_name]['num_sheets'] += 1
        return group_name


class MidreshetGroupManager(GroupManager):

    def get_and_register_group_for_sheet(self, sheet_id):
        return self.default_group()


class SheetRelation(object):
    def __init__(self, sheet_id, sheet_name):
        self.sheet_id = sheet_id
        self.sheet_name = sheet_name
        self._children = []
        self._parent = None

    def set_parent(self, parent_sheet):
        self._parent = parent_sheet

    def add_child(self, child_relation):
        self._children.append(child_relation)

    def get_children(self):
        return self._children[:]

    def get_branch(self, sheet_list=None):
        if sheet_list is None:
            sheet_list = []

        sheet_list.append(self)
        for child in self.get_children():
            child.get_branch(sheet_list)
        return sheet_list

    def get_names_from_branch(self):
        return [sheet.sheet_name for sheet in self.get_branch()]

    def render(self, nesting_level=0):
        nesting_color = {
            0: 'white',
            1: 'aqua',
            2: 'green',
            3: 'yellow',
            4: 'red',
            5: 'orange',
            6: 'GoldenRod'
        }
        background_color = nesting_color[nesting_level]
        nesting_level += 1
        children = u''.join(child.render(nesting_level) for child in self._children)

        return u'<dl style="background-color: {};"><dt>id</dt><dd>{}</dd><dt>name</dt><dd>{}</dd><dt>children</dt><dd>{}</dd></dl>'.\
            format(background_color, self.sheet_id, self.sheet_name, children)


class NullSheetRelation(SheetRelation):
    def __init__(self):
        super(NullSheetRelation, self).__init__(0, None)
        self._parent = None

    def set_parent(self, parent_sheet):
        return


class SheetManager(object):
    def __init__(self):
        self._store = {
            0: NullSheetRelation()
        }

    def set_sheet_relation(self, parent_id, child_id):
        try:
            parent = self.get_sheet(parent_id)
        except KeyError:
            parent = self.get_sheet(0)

        child = self.get_sheet(child_id)
        parent.add_child(child)
        child.set_parent(parent)

    def create_sheet(self, sheet_id, sheet_name, parent_id):
        new_sheet_relation = SheetRelation(sheet_id, sheet_name)
        self._store[sheet_id] = new_sheet_relation
        self.set_sheet_relation(parent_id, sheet_id)

    def get_sheet(self, sheet_id):
        return self._store[sheet_id]

    def get_root_sheets(self):
        return self.get_sheet(0).get_children()


def get_sheet_by_id(page_id, rebuild_cache=False):
    cursor = MidreshetCursor()
    cursor.execute('select * from Pages where id=?', (page_id,))
    rows = list(cursor.fetchall())
    assert len(rows) == 1
    sheet = convert_row_to_dict(rows[0])

    cursor.execute('SELECT name, body, exactLocation, resource_id, display_type, minorType, copyright, copyrightLink '
                   'FROM PageResources JOIN Resources '
                   'ON PageResources.resource_id = Resources.id '
                   'WHERE PageResources.page_id=? '
                   'ORDER BY PageResources.display_order', (page_id,))
    resources = [convert_row_to_dict(r) for r in cursor.fetchall()]

    for resource in resources:
        resource['terms'] = get_terms_for_resource(resource['resource_id'], page_id)
        resource['dictionary'] = get_dicts_for_resource(resource['resource_id'])
        if resource['exactLocation']:
            resource['SefariaRef'] = get_ref_for_resource_p(resource['resource_id'], resource['exactLocation'],
                                                            resource['body'], replace=rebuild_cache)
    sheet['resources'] = resources

    cursor.execute('SELECT tag '
                   'FROM PageTags P JOIN Tags T ON P.tag_id = T.id '
                   'WHERE P.page_id=?', (page_id,))
    sheet['tags'] = [t.tag for t in cursor.fetchall()]

    cursor.execute('SELECT first_name, last_name FROM Users WHERE id=?', (sheet['userId'],))
    result = cursor.fetchone()
    if result:
        sheet['username'] = u'{} {}'.format(result.first_name, result.last_name)
    else:
        sheet['username'] = u'אתר מדרשת'

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


def format_terms(term_list):
    term_list.sort(key=lambda x: x['typeTerms'])
    terms_by_type = {k: list(g) for k, g in groupby(term_list, key=lambda x: u'הסברים' if x['typeTerms'] == 0 else u'מושגים')}
    formatted_terms = []
    for term_type in sorted(terms_by_type.keys()):
        term_text_list = []

        for term_item in terms_by_type[term_type]:
            term_name = u' '.join(term_item['name'].split())
            if term_name:
                term_text_list.append(u'{} - {}'.format(term_name, term_item['body']))
            else:
                term_text_list.append(term_item['body'])

        formatted_terms.append(u'<i>{}</i><ul style="margin: 1px;"><li>{}</li></ul>'.
                               format(term_type, u'</li><li>'.join(term_text_list)))
    return u'<br>'.join(formatted_terms)


def format_dictionaries(word_list):
    """Consider making this into descriptive lists in the future."""
    entries = [u'{} - {}'.format(word['name'], word['body']) for word in word_list]
    return u'<i>{}</i><ul><li>{}</li></ul>'.format(u'מילים', u'</li><li>'.join(entries))


def wrap_verse_markers(text_to_wrap):
    """
    Tanakh segments typically have vowels. We'll identify verse markers by a series of Hebrew characters that have
    no vowel markers. As a sanity check, we'll make sure that a significant portion of the text contain vowel marks.
    :param text_to_wrap:
    :return:
    """
    def wrap(word_to_wrap):
        match = re.match(ur'^\(?([\u05d0-\u05ea]+)\)?$', word_to_wrap)
        if match:
            return u'<small>({})</small>'.format(match.group(1))
        else:
            return word_to_wrap

    all_he = len(re.findall(ur'[\u0591-\u05f4]', text_to_wrap))
    just_chars = len(re.findall(ur'[\u05d0-\u05ea]', text_to_wrap))
    try:
        marks_to_chars_ratio = float(all_he - just_chars) / float(all_he)
    except ZeroDivisionError:
        marks_to_chars_ratio = 0.0

    if marks_to_chars_ratio < 0.3:  # this ratio is a guess, but the cases I checked were over 0.4
        return text_to_wrap

    as_words = [wrap(word) for word in text_to_wrap.split()]
    return u' '.join(as_words)


def create_sheet_json(page_id, group_manager):
    raw_sheet = get_sheet_by_id(page_id)
    sheet = {
        'title': raw_sheet['name'],
        'status': 'public',
        'tags': raw_sheet['tags'],
        'options': {
            'language': 'hebrew',
            'numbered': False,
        },
        'sources': [],
        'attribution': raw_sheet['username']
    }

    for resource in raw_sheet['resources']:
        source = {
            # 'outsideText': bleach.clean(resource['body'], strip=True, tags=[], attributes={}),
            'options': {}
        }
        if resource['exactLocation']:
            sefaria_ref = resource.get('SefariaRef', None)

            if sefaria_ref:
                source['ref'] = sefaria_ref
                source['text'] = {'he': bleach.clean(resource['body'], tags=['ul', 'li'], attributes={}, strip=True),
                                  'en': ''}

                oref = Ref(sefaria_ref)
                if 'Tanakh' in oref.index.categories and not oref.is_commentary():
                    source['text']['he'] = wrap_verse_markers(source['text']['he'])

                # source['options']['sourcePrefix'] = u'מקור'
                source['options']['PrependRefWithHe'] = resource['exactLocation']

            else:
                source['outsideText'] = u'<span style="color: #999">{}</span><br>{}'.format(
                    resource['exactLocation'],
                    bleach.clean(resource['body'], tags=['ul', 'li'], attributes={}, strip=True))

        else:
            cleaned_text = bleach.clean(resource['body'], tags=['ul', 'li'], attributes={}, strip=True)
            if not cleaned_text:
                continue

            if resource['minorType'] == 2:  # this is a secondary title
                source['outsideText'] = u'<span style="font-size: 24px; ' \
                                        u'text-decoration:underline;' \
                                        u' text-decoration-color:grey;">{}</span>'.format(cleaned_text)
            else:
                source['outsideText'] = u'<span style="text-decoration:underline; text-decoration-color:grey">{}</span>' \
                                    u'<br>{}'.format(u'דיון', cleaned_text)

        if resource['copyright']:
            resource_attribution = u'כל הזכויות שמורות ל'
            resource_attribution = u'{}{}'.format(resource_attribution, resource['copyright'])
            copyright_link = re.sub(ur'/$', u'', resource['copyrightLink'])
            resource_attribution = u'<small><span style="color: #999">{}</span><br><a href={}>{}</a></small>'.format(
                resource_attribution, resource['copyrightLink'], copyright_link
            )
            if 'outsideText' in source:
                source['outsideText'] = u'{}<br>{}'.format(source['outsideText'], resource_attribution)
            else:
                source['text']['he'] = u'{}<br>{}'.format(source['text']['he'], resource_attribution)

        if resource['terms']:
            if 'outsideText' in source:
                source['outsideText'] = u'{}<br><br>{}'.format(source['outsideText'], format_terms(resource['terms']))
            else:
                source['text']['he'] = u'{}<br><br>{}'.format(source['text']['he'], format_terms(resource['terms']))

        if resource['dictionary']:
            if 'outsideText' in source:
                source['outsideText'] = u'{}<br><br>{}'.format(source['outsideText'], format_dictionaries(resource['dictionary']))
            else:
                source['text']['he'] = u'{}<br><br>{}'.format(source['text']['he'], format_dictionaries(resource['dictionary']))

        sheet['sources'].append(source)
        sheet['group'] = group_manager.get_and_register_group_for_sheet(page_id)
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
    if not sheet_json['sources']:
        return
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


def bulk_sheet_post(wrapped_sheet_list, server='http://localhost:8000'):
    """
    Posts a list of pre-generated sheets. We can't maintain a single mongo client across forks, so when multiprocessing
    it is necessary to split our list of sheets into chunks. We instantiate one client for each chunk, then work on all
    the chunks in parallel
    :param wrapped_sheet_list: NamedTuple, keys: page_id, sheet_json
    :param server: server to post to
    :return:
    """
    client = pymongo.MongoClient()
    server_map = client.yonis_data.server_map

    for wrapped_sheet in wrapped_sheet_list:
        page_id, sheet_json = wrapped_sheet.page_id, wrapped_sheet.sheet_json
        if not sheet_json['sources']:
            continue
        server_map_data = server_map.find_one({'pageId': page_id, 'server': server})

        if server_map_data:
            # check that sheet really exists
            response = requests.get('{}/api/sheets/{}'.format(server, server_map_data['serverIndex'])).json()

            if 'error' in response or response['title'] != sheet_json['title']:
                response = post_sheet(sheet_json, server=server)
                server_map.find_one_and_update({'pageId': page_id, 'server': server},
                                               {'$set': {'serverIndex': response['id']}})
            else:
                sheet_json['id'] = response['id']
                post_sheet(sheet_json, server=server)

        else:
            response = post_sheet(sheet_json, server=server)
            server_map.insert_one({'pageId': page_id, 'server': server, 'serverIndex': response['id']})
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


def bleach_clean(some_text):
    return bleach.clean(some_text, tags=[], attributes={}, strip=True)


def sheet_poster(server, wrapped_sheet_list):
    return bulk_sheet_post(wrapped_sheet_list, server)


def try_refs_by_id(id_list):
    """
    Now pull out all ids associated with a specific term. Get the associated full strings, and run library.get_refs_in_string
    :param id_list:
    :return:
    """
    cursor = MidreshetCursor()
    cursor.execute('SELECT MidreshetRef FROM RefMap WHERE id IN ({})'.format(', '.join([str(i) for i in id_list])))
    for result_row in cursor.fetchall():
        possible_refs = library.get_refs_in_string(u'({})'.format(result_row.MidreshetRef), lang='he', citing_only=True)
        print(result_row.MidreshetRef, *possible_refs, sep=u'\n', end=u'\n\n')


def rematch_ref(ref_id):
    cursor = MidreshetCursor()
    cursor.execute('SELECT id, exactLocation, body FROM Resources WHERE id = ?', (ref_id,))
    result = cursor.fetchone()
    return get_ref_for_resource_p(result.id, result.exactLocation, bleach_clean(result.body), replace=True)


def get_url_for_sheet_id(sheet_id, server, server_map=None):
    if not server_map:
        server_map = pymongo.MongoClient().yonis_data.server_map

    sheet_server_data = server_map.find_one({'pageId': sheet_id, 'server': server})
    return u'{}/sheets/{}'.format(server, sheet_server_data['serverIndex'])


multiple_group_servers = {
    'http://midreshetgroups.sandbox.sefaria.org'
}

single_group_servers = {
    'http://midreshet.sandbox.sefaria.org',
    'http://localhost:8000'
}

# destination_server = 'http://localhost:8000'
destination_server = 'http://midreshet.sandbox.sefaria.org'
if destination_server in multiple_group_servers:
    group_handler = GroupManager(destination_server)
else:
    group_handler = MidreshetGroupManager(destination_server)

p_sheet_poster = partial(sheet_poster, destination_server)
my_cursor = MidreshetCursor()
# my_cursor.execute('SELECT id, body, exactLocation FROM Resources WHERE exactLocation IS NOT NULL')
# to_examine = []
# for table_row in tqdm(my_cursor.fetchall()):
#     if not get_ref_for_resource_p(table_row.id, table_row.exactLocation, table_row.body):
#         to_examine.append({
#             'id': table_row.id,
#             'Original Ref': table_row.exactLocation
#         })
# print(len(to_examine))
# with open('unparsed_refs.csv', 'w') as fp:
#     writer = unicodecsv.DictWriter(fp, fieldnames=['id', 'Original Ref'])
#     writer.writeheader()
#     writer.writerows(to_examine)

relation_manager = SheetManager()
my_cursor.execute('SELECT id, name, parent_id FROM Pages')
for sheet_data in my_cursor.fetchall():
    relation_manager.create_sheet(sheet_data.id, sheet_data.name, sheet_data.parent_id)

root_sheets = relation_manager.get_root_sheets()
print("root sheets:", len(root_sheets))

multiple_title_ids = []
for sheet_relation in root_sheets:
    names = sheet_relation.get_names_from_branch()
    if len(set(names)) > 1:
        multiple_title_ids.append(sheet_relation)
print("multiple title branches:", len(multiple_title_ids))
rendered_relations = [sheet_relation.render() for sheet_relation in multiple_title_ids]

with codecs.open('multiple_title_id_sheets.html', 'w', 'utf-8') as fp:
    fp.write(u''.join(rendered_relations))

# my_cursor.execute('SELECT id FROM Pages WHERE parent_id = 0')
my_wrapped_sheet_list = [SheetWrapper(m.sheet_id, create_sheet_json(m.sheet_id, group_handler))
                         for m in tqdm(root_sheets)]
print('finished creating sheets')
num_processes = 29
sheet_chunks = list(split_list(my_wrapped_sheet_list, num_processes))
pool = Pool(num_processes)
pool.map(p_sheet_poster, sheet_chunks)
group_handler.publicize_groups()

qa_sheets = random.sample([ws for ws in my_wrapped_sheet_list if ws.sheet_json['sources']], 60)
qa_rows = [
    {
        'Sefaria URL': get_url_for_sheet_id(qa_sheet.page_id, destination_server),
        'Midreshet URL': 'https://midreshet.org.il/PageView.aspx?id={}'.format(qa_sheet.page_id),
        'Comments': ''
    }
    for qa_sheet in qa_sheets
]
with open('Midreshet QA.csv', 'w') as fp:
    writer = unicodecsv.DictWriter(fp, ['Sefaria URL', 'Midreshet URL', 'Comments'])
    writer.writeheader()
    writer.writerows(qa_rows)

# my_cursor = MidreshetCursor()
# my_cursor.execute('SELECT id, MidreshetRef FROM RefMap WHERE SefariaRef IS NULL')
# ref_sources_mongo = my_mongo_client.yonis_data.RefSources
# valid_ids = [q['resource_id'] for q in ref_sources_mongo.find({"SefariaRef": {"$eq": None}})]
# valid_id_set = set(valid_ids)
# q_rows = my_cursor.fetchall()
# all_sources = [q.MidreshetRef for q in q_rows if q.id in valid_id_set]
# valid_ids = [q.id for q in q_rows if q.id in valid_id_set]
# del q_rows
# id_map = {}
# sf = SefariaTermsAndTitles()
# print('sources and ids match?', len(all_sources) == len(valid_ids))


# catcher, word_catcher = NGramCatcher(), WordSequenceCatcher()
# gram_lengths, sequence_lengths = range(12, 30), range(1, 8)
#
# for each_source, source_id in zip(all_sources, valid_ids):
#     simplified = re.sub(u'[^\u05d0-\u05ea ]', u'', each_source)
#     sf.find_titles_and_terms(simplified)
#     id_map[simplified] = source_id
#     # catcher.find_series_of_grams(gram_lengths, simplified)
#     word_catcher.find_series_of_grams(sequence_lengths, simplified)
#
# for length in sequence_lengths:
#     print('')
#     print('words of length {}'.format(length))
#     common = word_catcher.retrieve_most_common(length, 40)
#     for c in common:
#         print(u'{}: {}'.format(*c))

# for length in gram_lengths:
#     print('')
#     print('length {}'.format(length))
#     common = catcher.retrieve_most_common(length, 20)
#     for c in common:
#         print(u'{}: {}'.format(*c))

# print('\n\n\n')
# print(len(sf.titles_and_terms_counter.keys()))
# for foo, bar in sf.titles_and_terms_counter.most_common(30):
#     print(foo, bar)
#
#
# def handler(signum, frame):
#     print("No input, exiting")
#     sys.exit(0)
#
#
# signal.signal(signal.SIGALRM, handler)
# while True:
#     signal.alarm(600)
#     lookup_term = unicode(raw_input(u"Type 'exit' to end program\n").decode('utf-8'))
#     signal.alarm(0)
#     if lookup_term == u'exit':
#         break
#     elif lookup_term == u'reprint':
#         for foo, bar in sf.titles_and_terms_counter.most_common(50):
#             print(foo, bar)
#     else:
#         interesting_ids = [id_map[thing] for thing in sf.terms_to_refs_map[lookup_term]]
#         try_refs_by_id(interesting_ids)


# for possible_ref in sf.terms_to_refs_map[u'תהלים']:
#     interesting_id = id_map[possible_ref]
#     print(interesting_id, possible_ref)
#     new_ref = rematch_ref(interesting_id)
#     if new_ref:
#         print(new_ref)
#     else:
#         print('Found Nothing')


