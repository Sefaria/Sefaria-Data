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
# from urllib import parse as urlparse
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from functools import partial
from itertools import groupby
from collections import namedtuple, Counter, defaultdict
from multiprocessing import Pool
from sources.functions import post_sheet
from sources.local_settings import API_KEY
from data_utilities.util import Singleton, getGematria, split_list, numToHeb
from research.source_sheet_disambiguator.main import refine_ref_by_text

import django
django.setup()
from sefaria.model import *
from sefaria.s3 import HostedFile
from sefaria.system.exceptions import InputError
from sefaria.datatype.jagged_array import JaggedTextArray

LOGIN_PATH=os.environ.get('LOGIN_PATH', 'login_details.json')
if not os.path.exists(LOGIN_PATH):
    print('path to login details does not exist - exiting')
    sys.exit(1)


class MidreshetCursor(object):
    __metaclass__ = Singleton

    def __init__(self):
        try:
            with open(LOGIN_PATH) as fp:
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

    def fetch_iter(self):
        while True:
            item = self.cursor.fetchone()
            if item:
                yield item
            else:
                break
        raise StopIteration

    def __getattr__(self, item):
        return getattr(self.cursor, item)

    def __iter__(self):
        return self.cursor


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
        pattern = '.{%s}' % n
        self.gram_lengths[n].update(regex.findall(pattern, input_string, overlapped=True))

    def find_series_of_grams(self, n_list, input_string):
        for n in n_list:
            self.find_n_grams(n, input_string)

    def retrieve_most_common(self, gram_length, num_to_retrieve):
        return self.gram_lengths[gram_length].most_common(num_to_retrieve)


class WordSequenceCatcher(NGramCatcher):
    def find_n_grams(self, n, input_string):
        words = input_string.split()
        self.gram_lengths[n].update([' '.join(words[i:i+n]) for i in range(len(words) - n + 1)])


class SefariaTermsAndTitles(object):
    def __init__(self):
        self.titles_and_terms_counter = Counter()
        self.terms_to_refs_map = defaultdict(set)
        # all_terms = [term_title for term in TermSet() for term_title in term.get_titles('he')]
        # everything = sorted(library.citing_title_list('he') + all_terms, key=lambda x: len(x), reverse=True)
        everything = [re.escape(s) for s in sorted(library.full_title_list('he'), key=lambda x: len(x), reverse=True)]
        prefixes = 'משהוכלב'
        pattern = '(?:^|\s)(?:[{}])?(?P<title>{})(?=\s|$)'.format(prefixes, '|'.join(everything))
        self.regex = re.compile(pattern)

    def find_titles_and_terms(self, input_string):
        titles = [m.group('title') for m in self.regex.finditer(input_string)]
        self.titles_and_terms_counter.update(titles)
        for t in titles:
            self.terms_to_refs_map[t].add(input_string)


class Series(object):

    def __init__(self, series_id, series_name, destination):
        self.id = series_id
        self.name = series_name
        self._destination = destination
        self._sheet_list = self._get_sheet_list()

    def _get_sheet_list(self):
        my_cursor.execute('SELECT id, page_num FROM Pages WHERE series_id=? ORDER BY page_num', (self.id,))
        sheet_urls = []
        for page in my_cursor:
            try:
                url = get_url_for_sheet_id(page.id, self._destination, my_mongo_client.yonis_data.server_map)
            except TypeError:
                url = ''
            sheet_urls.append(url)

        return sheet_urls

    def get_sheets(self):
        for sheet in self._sheet_list:
            yield sheet


def get_series_mapping(destination):
    my_cursor.execute('SELECT * FROM Series')
    return {c.id: Series(c.id, c.name, destination) for c in my_cursor.fetchall()}


def parse_expansion(expansion):
    if not expansion or expansion.isspace():
        return

    # expansion is already made up of html elements - drop as is (more or less)
    if re.search(r'[<>]', expansion):
        soup = BeautifulSoup(expansion, 'xml')
        if not soup.string or soup.string.isspace():
            return
        return expansion.replace('http://', 'https://')
    else:
        matches = re.finditer(r'(?P<url>[^{}]*){{DATA}}(?P<text>[^{}]*){{ITEM}}', expansion)
        link_list = ['<a href={}>{}</a>'.format(match.group('url'), match.group('text')) for match in matches
                     if urlparse(match.group('url')).hostname]  # filter out `http://` without any actual url

        return '<br>'.join(map(lambda x: x.replace('http://', 'https://'), link_list))


def convert_row_to_dict(table_row):
    columns = [i[0] for i in table_row.cursor_description]
    return {column: getattr(table_row, column) for column in columns}


def disambiguate_simple_tanakh_ref(raw_ref, book_name):
    # strip all non-hebrew characters, except the dash (maybe the em-dash?)
    clean_ref = re.sub('[^\u05d0-\u05ea\s\-\u2013]', '', raw_ref)
    clean_ref = ' '.join(clean_ref.split())

    # he_book_title = Ref(book_name).he_book()
    he_book_title = '|'.join(Ref(book_name).index.all_titles('he'))
    perek = 'פרק'
    prefix = 'ספר|מגילת'

    # ^(<book-name>) <perek> (<1-3 letters>) <pasuk(im)> (<chars>-?<chars>?)
    pattern = r'(?:(?:%s) )?(%s)(?: %s)? ([\u05d0-\u05ea]{1,3}) \u05e4\u05e1\u05d5\u05e7(?:\u05d9\u05dd)? ([\u05d0-\u05ea]{1,3}(-[\u05d0-\u05ea]{1,3})?)' % (prefix, he_book_title, perek)
    match = re.search(pattern, clean_ref)
    if match is None:
        return None
    else:
        sefaria_ref = '{} {} {}'.format(match.group(1), match.group(2), match.group(3))
        try:
            return Ref(sefaria_ref)
        except InputError:
            print('Could not create Ref:')
            print(sefaria_ref)
            return None


def get_he_talmud_titles(en_tractate):
    alts = {
        'Niddah': ['נידה'],
    }

    standard_title = Ref(en_tractate).he_book()
    all_titles = [standard_title] + alts.get(en_tractate, [])
    return '|'.join(all_titles)


def disambiguate_simple_talmud_ref(midreshet_ref, expected_book):
    """
    <Talmud Bavli> Masechet? <Masechet pattern> <Daf Pattern> <Amud Pattern>
    if range (presence of dash):
        add amud pattern
        if that fails, try daf pattern followed by amud pattern
    """
    def translate_ammud(daf_letter):
        if daf_letter == 'א':
            return 'a'
        elif daf_letter == 'ב':
            return 'b'
        else:
            raise AssertionError('Daf must be Aleph or Bet')

    cleaned_ref = re.sub('\u2013', '-', midreshet_ref)
    cleaned_ref = re.sub('[^\u05d0-\u05ea\s\-]', '', cleaned_ref)
    cleaned_ref = re.sub('\s*-\s*', ' - ', cleaned_ref)
    cleaned_ref = ' '.join(cleaned_ref.split())

    # if re.search('רשי', cleaned_ref):
    #     return None

    # he_book_title = Ref(expected_book).he_book()
    he_book_title = get_he_talmud_titles(expected_book)
    # masechet_pattern = '{} (?:{} )?(?P<book>{})'.format('תלמוד ה?בבלי', 'מסכת', he_book_title)
    masechet_pattern = '(?:{} )?(?P<book>{})'.format('מסכת', he_book_title)

    start_daf_pattern = '(?:%s )?(?P<start_daf>[\u05d0-\u05ea]{1,3})' % ('דף',)
    end_daf_pattern = start_daf_pattern.replace('start_daf', 'end_daf')

    start_amud_pattern = '(?:%s)?(?P<start_ammud>[\u05d0-\u05d1])(?! (?:%s|%s))' % ('עמוד |ע', 'דף', 'עמוד')
    end_amud_pattern = start_amud_pattern.replace('start_ammud', 'end_ammud')

    base_pattern = '{} {} {}(?=\s|$)'.format(masechet_pattern, start_daf_pattern, start_amud_pattern)
    is_range = bool(re.search('{} -'.format(base_pattern), cleaned_ref))

    if is_range:
        pattern = '{} - {}'.format(base_pattern, end_amud_pattern)
        match = re.search(pattern, cleaned_ref)

        if match:
            raw_ref = '{} {}{}-{}{}'.format(
                expected_book, getGematria(match.group('start_daf')), translate_ammud(match.group('start_ammud')),
                getGematria(match.group('start_daf')), translate_ammud(match.group('end_ammud'))
            )

        else:
            pattern = '{} - {} {}'.format(base_pattern, end_daf_pattern, end_amud_pattern)
            match = re.search(pattern, cleaned_ref)
            if not match:
                return
            raw_ref = '{} {}{}-{}{}'.format(
                expected_book, getGematria(match.group('start_daf')), translate_ammud(match.group('start_ammud')),
                getGematria(match.group('end_daf')), translate_ammud(match.group('end_ammud'))
            )

    else:
        match = re.search(base_pattern, cleaned_ref)
        if not match:
            return
        raw_ref = '{} {}{}'.format(
            expected_book, getGematria(match.group('start_daf')), translate_ammud(match.group('start_ammud')))

    return Ref(raw_ref)


class RefBuilder(object):

    def __init__(self):
        self._category_maps = {
            'משנה': 'Mishnah',
            'תוספתא': 'Tosefta',
            'ירושלמי': 'Jerusalem Talmud',
        }
        self._commentary_maps = {}

    def redirect_category(self, raw_ref, base_ref):

        def redirected_sections(new_book, sections):
            book_node = Ref(new_book).index_node
            return ':'.join([book_node.address_class(i).toStr('en', section) for i, section in enumerate(sections)])

        if base_ref.book == 'Pirkei Avot':  # special case
            return base_ref

        if base_ref.is_talmud():
            base_book = base_ref.book
        elif base_ref.primary_category == 'Mishnah':
            base_book = re.sub('Mishnah ', '', base_ref.book)
        else:
            return base_ref

        cat_regex = re.compile('|'.join(self._category_maps.keys()))
        category_match = cat_regex.search(raw_ref)

        if not category_match:
            return base_ref

        ref_prefix = self._category_maps[category_match.group()]
        book_title = "{} {}".format(ref_prefix, base_book)
        try:
            new_ref = Ref("{} {}".format(book_title, redirected_sections(book_title, base_ref.sections)))
        except InputError:
            return base_ref
        if base_ref.is_range():
            range_end = Ref("{} {}".format(book_title, redirected_sections(book_title, base_ref.toSections)))
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

        commentator_regex = re.compile('|'.join(commentary_map.keys()))
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

        commentator_ref = Ref("{} {}".format(commentator_book, ':'.join(base_ref.normal_sections())))
        if base_ref.is_range():
            range_end = Ref("{} {}".format(commentator_book, ':'.join(base_ref.normal_toSections())))
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
        elif 'Tanakh' in base_ref.index.categories:
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
    my_cursor.execute('SELECT typeTerms, name, body, termId '
                      'FROM ResourcesTermsOnPage '
                      'JOIN Terms ON ResourcesTermsOnPage.termId = Terms.Id '
                      'WHERE ResourcesTermsOnPage.resourceId=? AND ResourcesTermsOnPage.pageId=?', (resource_id, page_id))
    return [convert_row_to_dict(r) for r in my_cursor.fetchall()]


def get_dicts_for_resource(resource_id):
    my_cursor.execute('SELECT name, body '
                      'FROM ResourcesTranslations JOIN Dictionary '
                      'ON ResourcesTranslations.dicId = Dictionary.id '
                      'WHERE ResourcesTranslations.resourceId=? AND ResourcesTranslations.isOnPage=?', (resource_id, 1))
    return [convert_row_to_dict(r) for r in my_cursor.fetchall()]


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


'''
Steps:
1) Get a function that does the lookup. Function should take server, page_id
2) Get a temp fix for the sheet ids. For now, create a special collection with a single document. This document can have a "next_id" field. Get and increment as an atomic operation.
3) Dump the RefSources collection from yonis_data
4) Get some example sheets. We'll probably want to save their json and re-upload them so we can make a comparison. re-uploading might not be necessary, but we'll definitely want to save the json.
5) Drop the collection RefSources
6) For now, if the method "refined_ref_by_text" doesn't return something useful, return None
7) Perform visual analysis of the sheets.
8) Repeat steps 6 & 7 as needed.
'''


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
                refined_ref = refine_ref_by_text(sefaria_ref, '', resource_text)
            except InputError:
                return sefaria_ref.normal()
            if refined_ref:
                return refined_ref.normal()
        return sefaria_ref.normal()

    possible_refs = library.get_refs_in_string('({})'.format(exact_location), 'he', citing_only=True)
    if len(possible_refs) == 1:
        constructed_ref = ref_builder.build_difficult_ref(exact_location, possible_refs[0])
        try:
            refined_ref = refine_ref_by_text(constructed_ref, '', resource_text)
        except InputError:
            return constructed_ref.normal()
        if refined_ref:
            return refined_ref.normal()
        # else:
        #     return constructed_ref.normal()

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
        self.image_collection = pymongo.MongoClient().yonis_data.images

    def adapt_image(self, name, filename, image_bytestring, image_type):
        image_data = self.image_collection.find_one({'name': name})
        if image_data:
            return image_data['image_url']

        else:
            filename = filename.split('\\')[-1]
            extension = filename[-3:].lower()
            filename = re.sub(r'.{3}$', extension, filename)
            with open(filename, 'wb') as fp:
                fp.write(image_bytestring)

            hosted_file = HostedFile(filename, image_type)
            file_url = hosted_file.upload()
            self.image_collection.insert_one({'name': name, 'image_url': file_url})
            os.remove(filename)
            return file_url


def load_seminary_images():
    adapter = ImageAdapter()
    adapter.image_collection = pymongo.MongoClient().yonis_data.seminary_images
    cursor = MidreshetCursor()
    cursor.execute('SELECT S.name, F.name as filename, F.data, F.type FROM Seminary S '
                   'LEFT JOIN Files F ON S.logoId = F.id')
    image_urls = {}
    for row in cursor:
        assert row.name not in image_urls
        if row.filename:
            url = adapter.adapt_image(row.name, row.filename, row.data, row.type)
            image_urls[row.name] = url
        else:
            image_urls[row.name] = None

    return image_urls


SEMINARY_IMAGE_URL_MAPPING = load_seminary_images()


class GroupManager(object):
    def __init__(self, server):
        self.server = server
        self.group_cache = {}
        self.image_adapter = ImageAdapter()

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
            raw_response = requests.get('{}/api/groups/{}'.format(self.server, group_name))
            if raw_response.status_code == 200:
                break
            elif raw_response.status_code == 502:
                print("Got 502. will try again")
                time.sleep(3)
            else:
                print("Got bad status code. Exiting")
                with codecs.open('errors.html', 'w', 'utf-8') as fp:
                    fp.write(raw_response.text)
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
        # image_collection = self.mongo_client.yonis_data.images
        # image_data = image_collection.find_one({'name': group_data['name']})
        # if image_data:
        #     file_url = image_data['image_url']
        #
        # else:
        #     filename = group_data['filename'].split('\\')[-1]
        #     with open(filename, 'wb') as fp:
        #         fp.write(group_data['data'])
        #
        #     hosted_file = HostedFile(filename, group_data['type'])
        #     file_url = hosted_file.upload()
        #     image_collection.insert_one({'name': group_data['name'], 'image_url': file_url})
        #     os.remove(filename)

        file_url = self.image_adapter.adapt_image(group_data['name'], group_data['filename'],
                                                  group_data['data'], group_data['type'])
        group_json = {
            'name': group_data['name'],
            'description': bleach_clean(group_data['body']),
            'headerUrl': file_url,
            'imageUrl': file_url,
            'new': True
        }
        post_body = {'apikey': API_KEY, 'json': json.dumps(group_json)}
        post_url = '{}/api/groups/{}'.format(self.server, group_data['name'])

        response = requests.post(post_url, data=post_body)
        if response.ok:
            self.group_cache[group_data['name']]['need_to_add'] = False

        return

    def post_pinned_tags(self, group_name):
        if not self.group_cache[group_name].get('pinnedTags'):
            self.group_cache[group_name]['pinnedTags'] = []
        self.group_cache[group_name]['pinnedTags'] = list(set(self.group_cache[group_name]['pinnedTags']))
        self.group_cache[group_name]['pinnedTags'].sort(key=lambda x: re.sub(r'[^\u05d0-\u05ea]', '', x))

        url = '{}/api/groups/{}'.format(self.server, group_name)
        post_body = {'apikey': API_KEY, 'json': json.dumps({'name': group_name,
                                                            'pinnedTags': self.group_cache[group_name]['pinnedTags']})}
        response = requests.post(url, data=post_body)
        response = response.json()

        if 'error' in response:
            print(group_name, response['error'])

    def add_pinned_tag_to_group(self, group_name, pinned_tag):
        if not self.group_cache[group_name].get('pinnedTags'):
            self.group_cache[group_name]['pinnedTags'] = []

        self.group_cache[group_name]['pinnedTags'].append(pinned_tag)

    def make_group_public(self, group_name):
        if self.group_cache[group_name]['num_sheets'] < 3 or self.group_cache[group_name]['public']:
            return

        url = '{}/api/groups/{}'.format(self.server, group_name)
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

    def default_group(self, draft=False):
        if draft:
            group_name = 'מדרשת טיוטה'
        else:
            group_name = 'מדרשת'
        if group_name not in self.group_cache:
            self.cache_group_from_server(group_name)

        if self.group_cache[group_name]['need_to_add']:
            with open('midreshet_logo.jpg', 'rb') as fp:
                logo_data = fp.read()

            self.add_new_group({
                'filename': 'midreshet_logo2.jpg',
                'data': logo_data,
                'name': group_name,
                'body': '',
                'type': 'image/pjpeg',
                'logoId': None
            })

        self.group_cache[group_name]['num_sheets'] += 1
        return group_name


class MidreshetGroupManager(GroupManager):

    def get_and_register_group_for_sheet(self, sheet_id):
        cursor = MidreshetCursor()
        cursor.execute('SELECT status FROM Pages WHERE Pages.id=?', (sheet_id, ))

        try:
            status = int(cursor.fetchone().status)
        except (TypeError, ValueError):
            status = 0

        if status in {3, 4}:
            return self.default_group()
        else:
            return self.default_group(draft=True)


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
        children = ''.join(child.render(nesting_level) for child in self._children)

        return '<dl style="background-color: {};"><dt>id</dt><dd>{}</dd><dt>name</dt><dd>{}</dd><dt>children</dt><dd>{}</dd></dl>'.\
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
    cursor.execute("select * from Pages "
                   "left join ("
                   "    select name se_name, id se_id from Seminary) se "
                   "ON Pages.seminary_id = se_id "
                   "where id=?", (page_id,))
    rows = list(cursor.fetchall())
    assert len(rows) == 1
    sheet = convert_row_to_dict(rows[0])

    cursor.execute('SELECT id, name, body, exactLocation, resource_id, display_type, minorType, copyright, copyrightLink, fullResourceLink, attachId '
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
    cursor.execute('SELECT Seminary.name, Seminary.url, Seminary.body FROM Pages JOIN Seminary ON Pages.seminary_id = Seminary.id WHERE Pages.id=?',
                   (page_id,))
    result = cursor.fetchone()
    if result and result.name and result.name != '-':
        sheet['tags'].append(result.name)
        sheet['seminary'] = result.name
        if result.url:
            sheet['seminary_data'] = '<a href="{}">לאתר {}</a>'.format(result.url, result.name)
        elif result.name == 'מעגל טוב':
            sheet['seminary_data'] = result.body
        else:
            sheet['seminary_data'] = None
        if SEMINARY_IMAGE_URL_MAPPING[result.name]:
            sheet['seminary_image'] = SEMINARY_IMAGE_URL_MAPPING[result.name]

    if not sheet['tags']:
        sheet['tags'].append('Untagged')

    cursor.execute('SELECT first_name, last_name FROM Users WHERE id=?', (sheet['userId'],))
    result = cursor.fetchone()
    if result:
        sheet['username'] = '{} {}'.format(result.first_name, result.last_name)
    else:
        sheet['username'] = 'אתר מדרשת'

    return sheet


def export_sheet_to_file(sheet_id):
    sheet = get_sheet_by_id(sheet_id)
    my_file = codecs.open('sheet_{}.txt'.format(sheet_id), 'w', 'utf-8')
    my_file.write('{}\n\n'.format(sheet['name']))
    my_file.write('{}\n\n'.format(sheet['description']))

    for resource in sheet['resources']:
        my_file.write('name:\n  {}\n\n'.format(resource['name']))
        my_file.write('{}\n\n'.format(bleach.clean(resource['body'], strip=True, tags=[], attributes={})))
        for term in resource['terms']:
            my_file.write('typeTerms: {}; Id: {}\n{} - {}\n'.format(term['typeTerms'], term['termId'], term['name'].rstrip(), term['body']))
        for dict_entry in resource['dictionary']:
            my_file.write('{} - {}\n'.format(dict_entry['name'], dict_entry['body']))
        my_file.write('exactLocation:\n  {}\n\n'.format(resource['exactLocation']))
        my_file.write('display_type: {}'.format(resource['display_type']))
        my_file.write('\n\n\n\n')

    my_file.close()


"""
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
Source with an exactLocation can get sourcePrefix = 'מקור', otherwise sourcePrefix = 'דיון'
"""


def format_terms(term_list):
    term_list.sort(key=lambda x: x['typeTerms'])
    terms_by_type = {k: list(g) for k, g in groupby(term_list, key=lambda x: 'הסברים' if x['typeTerms'] == 0 else 'מושגים')}
    formatted_terms = []
    for term_type in sorted(terms_by_type.keys()):
        term_text_list = []

        for term_item in terms_by_type[term_type]:
            term_name = ' '.join(term_item['name'].split())
            if term_name:
                term_text_list.append('{} - {}'.format(term_name, format_source_text(term_item['body'])))
            else:
                term_text_list.append(format_source_text(term_item['body']))

        formatted_terms.append('<i>{}</i><ul style="margin: 1px;"><li>{}</li></ul>'.
                               format('<span style="color: #999">{}</span>'.format(term_type),
                                      '</li><li>'.join(term_text_list)))
    return '<small>{}</small>'.format('<br>'.join(formatted_terms))


def format_dictionaries(word_list):
    """Consider making this into descriptive lists in the future."""
    entries = ['{} - {}'.format(word['name'], format_source_text(word['body'])) for word in word_list]
    return '<small><i>{}</i><ul><li>{}</li></ul></small>'.format('<span style="color: #999">{}</span><br>'
                                                                  .format('מילים'), '</li><li>'.join(entries))


class VerseMarkWrapper(object):
    """
    Tanakh segments typically have vowels. We'll identify verse markers by a series of Hebrew characters that have
    no vowel markers. As a sanity check, we'll make sure that a significant portion of the text contain vowel marks.

    We'll also calculate the exact Gematria presentations of the values 1-199.
    """
    def __init__(self):
        gematrias = sorted([numToHeb(num) for num in range(1, 200)], key=lambda x: len(x), reverse=True)
        self.verse_pattern = '|'.join(gematrias)

    def wrap(self, word_to_wrap):
        # match = re.match(r'^({})$'.format(self.verse_pattern), word_to_wrap)
        # if match:
        #     return '<small>({})</small>'.format(match.group(1))
        # else:
        #     return word_to_wrap
        return re.sub(r'(^|>)({})($|<)(?!br)'.format(self.verse_pattern),
                      r'\g<1><small>(\g<2>)</small>\g<3>', word_to_wrap)

    def __call__(self, text_to_wrap):
        all_he = len(re.findall(r'[\u0591-\u05f4]', text_to_wrap))
        just_chars = len(re.findall(r'[\u05d0-\u05ea]', text_to_wrap))
        try:
            marks_to_chars_ratio = float(all_he - just_chars) / float(all_he)
        except ZeroDivisionError:
            marks_to_chars_ratio = 0.0

        if marks_to_chars_ratio < 0.3:  # this ratio is a guess, but the cases I checked were over 0.4
            return text_to_wrap

        as_words = [self.wrap(word) for word in text_to_wrap.split()]
        return ' '.join(as_words)


wrap_verse_markers = VerseMarkWrapper()
# def wrap_verse_markers(text_to_wrap):
#     """
#     Tanakh segments typically have vowels. We'll identify verse markers by a series of Hebrew characters that have
#     no vowel markers. As a sanity check, we'll make sure that a significant portion of the text contain vowel marks.
#     :param text_to_wrap:
#     :return:
#     """
#     def wrap(word_to_wrap):
#         match = re.match(r'^\(?([\u05d0-\u05ea]+)\)?$', word_to_wrap)
#         if match:
#             return '<small>({})</small>'.format(match.group(1))
#         else:
#             return word_to_wrap
#
#     all_he = len(re.findall(r'[\u0591-\u05f4]', text_to_wrap))
#     just_chars = len(re.findall(r'[\u05d0-\u05ea]', text_to_wrap))
#     try:
#         marks_to_chars_ratio = float(all_he - just_chars) / float(all_he)
#     except ZeroDivisionError:
#         marks_to_chars_ratio = 0.0
#
#     if marks_to_chars_ratio < 0.3:  # this ratio is a guess, but the cases I checked were over 0.4
#         return text_to_wrap
#
#     as_words = [wrap(word) for word in text_to_wrap.split()]
#     return ' '.join(as_words)


def format_source_text(source_text):
    def not_double(html_tag):
        before = getattr(html_tag.previous, 'name', 'thingamabob') == html_tag.name
        after = getattr(html_tag.next, 'name', 'thingamabob') == html_tag.name
        return not before and not after

    tag_map = {
        'B': 'strong',
        'STRONG': 'strong',
        'b': 'strong',
        'BR': 'br',
        'A': 'a'
    }
    if not source_text:
        source_text = ''
    source_text = re.sub('&nbsp;', ' ', source_text)
    soup = BeautifulSoup('<root>{}</root>'.format(source_text), 'xml')
    for tag in soup.root.find_all(True):
        if tag.name in tag_map:
            tag.name = tag_map[tag.name]

        tag_style = tag.get('style', '')
        if re.search('font-weight: ?bold|text-decoration: ?underline', tag_style):
            tag.name = 'strong'

        # if tag.name == 'br' and not_double(tag):
        #     tag.insert_before(soup.new_tag('br'))
    for tag in soup.root.find_all(['p', 'div']):
        next_tag = getattr(tag.next, 'name', '')

        # if tag.name == 'div' and next_tag in {'div', 'p', 'br'}:
        #     continue  # <div> tags should only have one <br> after them, no need for <br> before <p>

        tag.insert_after(soup.new_tag('br'))
        if tag.name == 'p':  # add a double tag after <p> tags
            tag.insert_after(soup.new_tag('br'))

    for ul in soup.root.find_all('ul'):
        for br in ul.find_all('br'):
            br.unwrap()

    source_text = str(soup.root)
    source_text = re.sub(r'http(?!s):', 'https:', source_text)
    bad_chars = [
        '\x83',
        '\uf0a7',
        '\u202d',
        '\u202c',
        '\uf0b7',
        '\u200b',
        '\u200f',
        '\uf0d8',
        '\u202a',
        '\u200e',
        '\uf0a9',
        '\u202e',
        '\u200d',
        '\u202b'
    ]
    source_text = re.sub('|'.join(bad_chars), ' ', source_text)
    source_text = ' '.join(source_text.split())
    source_text = bleach.clean(
        source_text,
        tags=['ul', 'li', 'strong', 'i', 'br', 'a', 'big', 'table', 'tbody', 'thead', 'tr', 'td'],
        attributes={'a': ['href']},
        strip=True
    )
    source_text = re.sub(r'\s+<br>\s*', '<br> ', source_text)
    return re.sub(r'(<br>)+\s*$', '', source_text)


def final_source_clean(final_source_text):
    final_source_text = re.sub(r'(<br>\s*)+<ul>', '<ul>', final_source_text)
    final_source_text = re.sub(r'</ul>\s*(<br>\s*)+', '</ul>', final_source_text)
    final_source_text = re.sub(r'(<br>\s*){3,}', '<br><br>', final_source_text)
    final_source_text = re.sub(r'^\s*<br>|<br>\s*$', '', final_source_text)

    return final_source_text


class AddImage(object):
    def __init__(self):
        self.image_adapter = ImageAdapter()
        self.cursor = MidreshetCursor()

    def __call__(self, image_id, name):
        image_data = self.cursor.execute('SELECT name, data, type FROM Files WHERE id=?', (image_id,)).fetchone()
        if not image_data:
            return None
        image_url = self.image_adapter.adapt_image(name, image_data.name, image_data.data, image_data.type)
        return image_url


add_image = AddImage()


def get_iframe_url(text_with_iframe):
    soup = BeautifulSoup('<root>{}</root>'.format(text_with_iframe), 'xml')
    iframe = soup.iframe
    return iframe['src']


def create_sheet_json(page_id, group_manager, series_map):
    raw_sheet = get_sheet_by_id(page_id)
    sheet = {
        'title': raw_sheet['name'],
        'status': 'public' if raw_sheet['status'] in [3, 4] else 'unlisted',
        'tags': raw_sheet['tags'],
        'options': {
            'language': 'hebrew',
            'numbered': False,
        },
        'sources': [],
        'attribution': raw_sheet['username']
    }

    sheet['sources'].append(
        {
            'options': {},
            'outsideText': '<strong>{}: {} / {}</strong>'.format('הדף מאת', raw_sheet['author'], raw_sheet['se_name'])
            if (raw_sheet['se_name'] and raw_sheet['se_name'] != '-') else
            '<strong>{}: {}</strong>'.format('הדף מאת', raw_sheet['author'])
        }
    )

    sheet['sources'].append({
        'options': {},
        'outsideText': '{}'.format(raw_sheet['description'])
    })

    for resource in raw_sheet['resources']:
        source = {
            # 'outsideText': bleach.clean(resource['body'], strip=True, tags=[], attributes={}),
            'options': {}
        }

        resource_title = re.sub(r'^\s+$', '', resource['name'])
        resource_body = resource['body'] if resource['body'] else ''
        if re.search('<iframe', resource_body):
            is_video, video_url = True, get_iframe_url(resource_body)
        else:
            is_video, video_url = False, ''

        if resource_title:
            if resource_body:
                resource_body = '<strong>{}</strong><br>{}'.format(resource_title, resource_body)
            else:
                resource_body = '<strong>{}</strong>'.format(resource_title)

        if resource['exactLocation']:
            sefaria_ref = resource.get('SefariaRef', None)

            if sefaria_ref:
                oref = Ref(sefaria_ref)

                en_text = oref.text('en').text

                source['ref'] = sefaria_ref
                source['text'] = {'he': format_source_text(resource_body),
                                  'en': JaggedTextArray(en_text).flatten_to_string()}
                source['heRef'] = oref.he_normal()

                if 'Tanakh' in oref.index.categories and not oref.is_commentary():
                    source['text']['he'] = wrap_verse_markers(source['text']['he'])

                # source['options']['sourcePrefix'] = 'מקור'
                # source['options']['PrependRefWithHe'] = resource['exactLocation']

            else:
                source['outsideText'] = '<span style="color: #999">{}</span><br>{}'.format(
                    resource['exactLocation'],
                    format_source_text(resource_body)
                )

        else:
            cleaned_text = format_source_text(resource_body)
            if not cleaned_text:
                continue

            if resource['minorType'] == 2:  # this is a secondary title
                # source['outsideText'] = '<span style="font-size: 24px; ' \
                #                         'text-decoration:underline;' \
                #                         ' text-decoration-color:grey;">{}</span>'.format(cleaned_text)
                source['outsideText'] = '<strong><big>{}</big></strong>'.format(cleaned_text)
            else:
                diyun = '<span style="text-decoration:underline; color: #999">{}</span>'.format('דיון')

                if re.match('^<ul>', cleaned_text):
                    source['outsideText'] = '{}{}'.format(diyun, cleaned_text)
                else:
                    source['outsideText'] = '{}<br>{}'.format(diyun, cleaned_text)
                # source['outsideText'] = '<span style="text-decoration:underline; text-decoration-color:grey">{}</span>' \
                #                     '<br>{}'.format('דיון', cleaned_text)

        truncated_copyright = re.sub(r'https?://', '', resource['copyrightLink'] if resource['copyrightLink'] else '')
        if resource['copyright'] or truncated_copyright:
            resource_attribution = 'כל הזכויות שמורות ל'
            resource_attribution = '{}{}'.format(resource_attribution, resource.get('copyright', ''))

            if not truncated_copyright:
                if resource['fullResourceLink']:
                    copyright_link = resource['fullResourceLink']
                else:
                    copyright_link = ''
            else:
                copyright_link = resource['copyrightLink']

            copyright_link = re.sub(r'^(https?://)+', 'https://', copyright_link)
            # if not re.match(r'^https://', copyright_link):
            #     copyright_link = 'https://{}'.format(copyright_link)
            copyright_link = re.sub(r'/$', '', copyright_link)
            copyright_link = ' '.join(copyright_link.split())
            parsed = urlparse(copyright_link)
            shortened_link = parsed.netloc
            if copyright_link and not shortened_link:
                shortened_link = parsed.path

            resource_attribution = '<small><span style="color: #999">\u00a9 {}</span><br><a href={}>{}</a></small>'.format(
                resource_attribution, copyright_link, shortened_link
            )
            if 'outsideText' in source:
                source['outsideText'] = '{}<br>{}'.format(source['outsideText'], resource_attribution)
            else:
                source['text']['he'] = '{}<br>{}'.format(source['text']['he'], resource_attribution)

        elif resource['fullResourceLink']:  # some sources have a source link but no copyright
            full_source_link = re.sub(r'^(https?://)+', 'https://', resource['fullResourceLink'])
            full_source_link = '<a href="{}">{}</a>'.format(full_source_link, 'למקור השלם')
            if 'outsideText' in source:
                source['outsideText'] = '{}<br>{}'.format(source['outsideText'], full_source_link)
            else:
                source['text']['he'] = '{}<br>{}'.format(source['text']['he'], full_source_link)

        if resource['terms']:
            if 'outsideText' in source:
                source['outsideText'] = '{}<br><br>{}'.format(source['outsideText'], format_terms(resource['terms']))
            else:
                source['text']['he'] = '{}<br><br>{}'.format(source['text']['he'], format_terms(resource['terms']))

        if resource['dictionary']:
            if 'outsideText' in source:
                source['outsideText'] = '{}<br><br>{}'.format(source['outsideText'], format_dictionaries(resource['dictionary']))
            else:
                source['text']['he'] = '{}<br><br>{}'.format(source['text']['he'], format_dictionaries(resource['dictionary']))

        if resource['attachId'] > 0 or is_video:
            if is_video:
                media_url = video_url
            else:
                media_url = add_image(resource['attachId'], resource['name'])
            if media_url:
                source['media'] = media_url
                if 'outsideText' in source:
                    source['caption'] = {
                        'he': source['outsideText'],
                        'en': ''
                    }
                    del source['outsideText']
                else:
                    source['caption'] = {
                        'he': source['text']['he'],
                        'en': ''
                    }
                    # del source['text']

        # final source cleanup
        if 'outsideText' in source:
            source['outsideText'] = final_source_clean(source['outsideText'])
        elif 'caption' in source:
            source['caption']['he'] = final_source_clean(source['caption']['he'])
        else:
            source['text']['he'] = final_source_clean(source['text']['he'])

        sheet['sources'].append(source)

    # add link to organization website
    if raw_sheet.get('seminary_data', None):
        sheet['sources'].append({
            'outsideText': final_source_clean(raw_sheet['seminary_data'])
        })
        if raw_sheet.get('seminary_image'):
            sheet['sources'].append({
                'media': raw_sheet['seminary_image']
            })

    # add external links for further reading
    external = parse_expansion(raw_sheet['bgAndExpansion'])
    if external:
        sheet['sources'].append({
            'outsideText': final_source_clean('<small>{}:<br>{}</small>'.format('קישורים לרקע והרחבה', external))
        })

    # add instructor sheet link if one exists:
    instructor_sheet = my_mongo_client.yonis_data.instructor_sheets.find_one({'pageId': page_id})
    if instructor_sheet:
        sheet['sources'].append({
            'outsideText': '<small>{}<br><a href={}>{}</a></small>'.format(
                'דף הנחיות למנחה:', instructor_sheet['url'], instructor_sheet['name'])
        })

    # handle sheet series
    if raw_sheet['series_id'] in series_map:
        series = series_map[raw_sheet['series_id']]
        assert isinstance(series, Series)
        url_list = []
        for i, s in enumerate(series.get_sheets(), 1):
            if i == raw_sheet['page_num']:
                continue
            else:
                url_list.append('<a href={}>{}</a>'.format(s, i))
        text_part = 'דף מספר {} בסדרה {}, דפים נוספים בסדרה:'.format(raw_sheet['page_num'], series.name)
        sheet['sources'].append({
            'outsideText': '<small>{}<br>{}</small>'.format(text_part, ' '.join(url_list))
        })

    sheet['group'] = group_manager.get_and_register_group_for_sheet(page_id)
    if raw_sheet.get('seminary'):
        group_manager.add_pinned_tag_to_group(sheet['group'], raw_sheet['seminary'])
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
                response = post_sheet(sheet_json, server=server, weak_network=True)
                server_map.find_one_and_update({'pageId': page_id, 'server': server},
                                               {'$set': {'serverIndex': response['id']}})
            else:
                sheet_json['id'] = response['id']
                post_sheet(sheet_json, server=server, weak_network=True)

        else:
            response = ''
            while not isinstance(response, dict):
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
        possible_refs = library.get_refs_in_string('({})'.format(result_row.MidreshetRef), lang='he', citing_only=True)
        print(result_row.MidreshetRef, *possible_refs, sep='\n', end='\n\n')


def rematch_ref(ref_id):
    cursor = MidreshetCursor()
    cursor.execute('SELECT id, exactLocation, body FROM Resources WHERE id = ?', (ref_id,))
    result = cursor.fetchone()
    return get_ref_for_resource_p(result.id, result.exactLocation, bleach_clean(result.body), replace=True)


def get_url_for_sheet_id(sheet_id, server, server_map=None):
    if not server_map:
        server_map = pymongo.MongoClient().yonis_data.server_map

    sheet_server_data = server_map.find_one({'pageId': sheet_id, 'server': server})
    return '{}/sheets/{}'.format(server, sheet_server_data['serverIndex'])


if __name__ == '__main__':
    multiple_group_servers = {
        'http://midreshetgroups.sandbox.sefaria.org'
    }

    single_group_servers = {
        'http://midreshet.sandbox.sefaria.org',
        'http://localhost:8000',
        'https://www.sefaria.org'
    }

    # destination_server = 'http://localhost:8000'
    # destination_server = 'http://midreshet.sandbox.sefaria.org'
    destination_server = 'https://www.sefaria.org'
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
    series_mapping = get_series_mapping(destination_server)
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
        fp.write(''.join(rendered_relations))

    # my_cursor.execute('SELECT id FROM Pages WHERE parent_id = 0')
    # from sefaria.profiling import prof
    # import sys
    # create_sheet_json(root_sheets[0].sheet_id, group_handler, series_mapping)
    # prof('create_sheet_json(root_sheets[1].sheet_id, group_handler, series_mapping)')
    # sys.exit(0)
    my_wrapped_sheet_list = [SheetWrapper(m.sheet_id, create_sheet_json(m.sheet_id, group_handler, series_mapping))
                             for m in tqdm(root_sheets)]
    print('finished creating sheets')
    num_processes = 20
    sheet_chunks = list(split_list(my_wrapped_sheet_list, num_processes))
    # pool = Pool(num_processes)
    # pool.map(p_sheet_poster, sheet_chunks)
    # map(p_sheet_poster, sheet_chunks)
    from concurrent.futures.thread import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=num_processes) as executor:
        executor.map(p_sheet_poster, sheet_chunks)
    # map(p_sheet_poster, sheet_chunks)
    print('done')
    group_handler.make_group_public('מדרשת')
    group_handler.post_pinned_tags('מדרשת')
    group_handler.post_pinned_tags('מדרשת טיוטה')


    # qa_sheets = random.sample([ws for ws in my_wrapped_sheet_list if ws.sheet_json['sources']], 60)
    # qa_rows = [
    #     {
    #         'Sefaria URL': get_url_for_sheet_id(qa_sheet.page_id, destination_server),
    #         'Midreshet URL': 'https://midreshet.org.il/PageView.aspx?id={}'.format(qa_sheet.page_id),
    #         'Comments': ''
    #     }
    #     for qa_sheet in qa_sheets
    # ]
    # with open('Midreshet QA.csv', 'w') as fp:
    #     writer = unicodecsv.DictWriter(fp, ['Sefaria URL', 'Midreshet URL', 'Comments'])
    #     writer.writeheader()
    #     writer.writerows(qa_rows)

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
    #     simplified = re.sub('[^\u05d0-\u05ea ]', '', each_source)
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
    #         print('{}: {}'.format(*c))

    # for length in gram_lengths:
    #     print('')
    #     print('length {}'.format(length))
    #     common = catcher.retrieve_most_common(length, 20)
    #     for c in common:
    #         print('{}: {}'.format(*c))

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
    #     lookup_term = unicode(raw_input("Type 'exit' to end program\n").decode('utf-8'))
    #     signal.alarm(0)
    #     if lookup_term == 'exit':
    #         break
    #     elif lookup_term == 'reprint':
    #         for foo, bar in sf.titles_and_terms_counter.most_common(50):
    #             print(foo, bar)
    #     else:
    #         interesting_ids = [id_map[thing] for thing in sf.terms_to_refs_map[lookup_term]]
    #         try_refs_by_id(interesting_ids)


    # for possible_ref in sf.terms_to_refs_map['תהלים']:
    #     interesting_id = id_map[possible_ref]
    #     print(interesting_id, possible_ref)
    #     new_ref = rematch_ref(interesting_id)
    #     if new_ref:
    #         print(new_ref)
    #     else:
    #         print('Found Nothing')
    requests.post(os.environ['SLACK_URL'], json={'text': 'upload complete'})


