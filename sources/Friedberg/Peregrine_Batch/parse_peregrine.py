# encoding=utf-8

import os
import re
import sys
import json
import codecs
import django
django.setup()
import requests
import unicodecsv
from tqdm import tqdm
from sefaria.model import *
from functools import partial
from multiprocessing import Pool
from collections import Counter, defaultdict
from bs4 import BeautifulSoup, NavigableString
from sefaria.datatype.jagged_array import JaggedArray
from sources.functions import add_term, add_category, post_link, post_index, post_text


class DeriveRefFromRow(object):

    def __init__(self):
        self._super_regex = None
        self.replacements = {
            u'עבודת כוכבים': u'עבודה זרה וחוקות הגויים',
            u'תפילה ונשיאת כפים': u'תפילה וברכת כהנים',
            u'יום טוב': u'שביתת יום טוב',
            u'מלוה ולוה': u'מלווה ולווה',
            u'קדוש החדש': u'קידוש החודש',
            u'זכיה ומתנה': u'זכייה ומתנה',
            u'ערכין וחרמין': u'ערכים וחרמין',
            u'מלכים': u'מלכים ומלחמות',
            u'כלי המקדש': u'כלי המקדש והעובדין בו',
            u'סנהדרין': u'סנהדרין והעונשין המסורין להם',
            u'ביאת המקדש': u'ביאת מקדש',
            u'מעשר': u'מעשרות',
            u'תמידין ומוספין': u'תמידים ומוספין',
            u'איסורי מזבח': u'איסורי המזבח',
            u'בכורים': u'ביכורים ושאר מתנות כהונה שבגבולין',
            u'ביכורים': u'ביכורים ושאר מתנות כהונה שבגבולין',
            u'טומאת אוכלין': u'טומאת אוכלים',
            u'שאלה ופקדון': u'שאלה ופיקדון',
            u'גזלה ואבדה': u'גזילה ואבידה',
            u'רוצח ושמירת הנפש': u'רוצח ושמירת נפש',
            u'עבודת כוכבים וחקותיהם': u'עבודה זרה וחוקות הגויים',
            u'שאר אבות הטומאה': u'שאר אבות הטומאות',
            u'עבודת יוה"כ': u'עבודת יום הכפורים',
            u'עבודת יום הכיפורים': u'עבודת יום הכפורים',
            u'לולב': u'שופר וסוכה ולולב',
            u'שופר': u'שופר וסוכה ולולב',
            u'תפלה': u'תפילה וברכת כהנים',
            u'תפילה': u'תפילה וברכת כהנים',
            u'נשיאת כפים': u'תפילה וברכת כהנים',
            u'מגילה': u'מגילה וחנוכה',
            u'חנוכה': u'מגילה וחנוכה',
            u'תפילין': u'תפילין ומזוזה וספר תורה',
            u'ספר תורה': u'תפילין ומזוזה וספר תורה',
            u'תפלין': u'תפילין ומזוזה וספר תורה',
            u'מזוזה': u'תפילין ומזוזה וספר תורה',
            u'מקוואות': u'מקואות',
            u'קידוש החדש': u'קידוש החודש',
        }

    def reprocess_row(self, row_header):
        replacements = sorted(self.replacements.keys(), key=lambda x: len(x), reverse=True)

        return re.sub(u'|'.join(replacements), lambda x: self.replacements[x.group()], row_header)

    def __call__(self, row_header):
        if not self._super_regex:
            title_list = [Ref(t).he_normal() for t in library.get_indexes_in_category(u'Mishneh Torah')]
            title_list = [re.sub(u'\u05de\u05e9\u05e0\u05d4 \u05ea\u05d5\u05e8\u05d4, ', u'', t) for t in
                          title_list]
            title_list = u'|'.join(title_list)
            self._super_regex = re.compile(u'(?P<title>%s) (?:\u05e4\u05e8\u05e7 |\u05e4)'
                                           u'(?P<chap>[\u05d0-\u05ea"]+)\s'
                                           u'(?P<seg>[\u05d0-\u05ea"]+([\s,\-]{1,3}[\u05d0-\u05ea"]+)?)$' % title_list)

        if isinstance(row_header, dict):
            row_header = row_header['hdr']

        regex_result = self._super_regex.search(row_header)
        if not regex_result:
            row_header = self.reprocess_row(row_header)
        regex_result = self._super_regex.search(row_header)
        if not regex_result:
            return None

        chapter = re.sub(u'"', u'', regex_result.group('chap'))
        seg = re.sub(u'"', u'', regex_result.group('seg'))
        seg = re.sub(u'[^\u05d0-\u05ea]+', u'-', seg)
        proper_ref_string = u'(\u05de\u05e9\u05e0\u05d4 \u05ea\u05d5\u05e8\u05d4, {} {} {})'\
            .format(regex_result.group('title'), chapter, seg)
        possible_refs = library.get_refs_in_string(proper_ref_string, lang='he', citing_only=True)
        if len(possible_refs) == 0:
            print "Matched but didn't resolve ref"
            return None
        elif len(possible_refs) > 1:
            print u"Ambiguous Ref: {}".format(row_header)
            print u"Resolved to: {}".format(proper_ref_string)
            raise AssertionError
        else:
            return possible_refs[0]


derive_ref_from_row = DeriveRefFromRow()


u"""
Parsing strategy:
Each index is a depth 3 JA. Use the book id and ref to determine where to place each comment.
I'll use a Counter to keep track of refs. The Rambam ref will give me the super-section and section values, then
the value of that ref in the counter will give me the segment value.

For simplicity, I'll keep the exact value of the Rambam ref as well as the derived ref as a list of tuples this will
be my link list.


For a row:
1) Get index name
2) Get Rambam Ref
3) Compile section level Ref for this comment
4) Obtain segment level index from the comment_tracker
5) Set the element.

Indices:
Each index requires:
- title
- categories
- collective_title
- base_text_title
- schema
- dependence: commentary

The titles come in as "<commentator> on <base-text>". The commentator will be the collective title. We should also have
a lookup table to resolve English title to Hebrew. <base-text> will give the "base_text_title". Can also be use to look
up categories. Categories will be:
[
    "Halakhah",
    "Mishneh Torah",
    "Commentary",
    <commentator>,
    <Rambam-Sefer>
    
]
Call up the index for the base text. The Index.categories[-1] will be the Rambam-Sefer.
"""


class CommentStore(object):

    def __init__(self):
        self.texts = defaultdict(JaggedArray)
        self.comment_tracker = Counter()
        self.links = []
        with open("Friedberg_Texts_Metadata.csv") as fp:
            self.titles = {row['id']: {'en_name': row['en_name'], 'he_name': row['he_name']} for row in
                           unicodecsv.DictReader(fp)}
        self.commentator_mapping = {t['en_name']: t['he_name'] for t in self.titles.values()}

    def resolve_row(self, row_element):
        commentary = self.titles[row_element['bid']]['en_name']
        rambam_ref = derive_ref_from_row(row_element)

        index_title = u'{} on {}'.format(commentary, rambam_ref.book)
        section_level = u'{} {}:{}'.format(index_title, *rambam_ref.sections)

        text_segments = self.format_segment(row_element['text'])
        for segment in text_segments:

            self.comment_tracker[section_level] += 1
            ref_indices = rambam_ref.sections[:] + [self.comment_tracker[section_level]]
            full_ref = u'{} {}:{}:{}'.format(index_title, *ref_indices)

            insertion_indices = [i-1 for i in ref_indices]  # 0 index for ja address
            # check that our section is the correct size
            segments_in_section = self.texts[index_title].sub_array_length(insertion_indices[:-1])
            if segments_in_section is None:
                segments_in_section = 0
            assert segments_in_section == insertion_indices[-1]

            self.texts[index_title].set_element(insertion_indices, segment, pad=u'')
            self.links.append((rambam_ref.normal(), full_ref))

    @staticmethod
    def format_segment(segment_text):
        segment_xml = u'<root>{}</root>'.format(segment_text)
        segment_soup = BeautifulSoup(segment_xml, 'xml')
        segment_root = segment_soup.root

        # clear out multiple classes - we're only interested in the last letter in the class
        for span in segment_root.find_all('span'):
            if span.get('class', u''):
                span['class'] = span['class'][-1]

        # consolidate duplicate tags and unwrap meaningless tags
        for span in segment_root.find_all('span'):
            previous = span.previous_sibling
            if not previous:
                continue

            # make sure all text inside spans end with a space, we'll remove duplicates later
            if span.string:
                span.string.replace_with(NavigableString(u'{} '.format(span.string)))

            if span.get('class', '') == '':
                span.unwrap()

            elif span.name == previous.name and span.get('class') == previous.get('class'):
                previous.append(span)
                span.unwrap()

        # handle footnotes
        marker = segment_root.find('span', attrs={u'class': u'R'})
        note_tag = segment_root.find('span', attrs={u'class': u'N'})
        if marker and note_tag:
            marker.name = u'sup'
            del marker['class']
            note_text = note_tag.text
            note_text = re.sub(u'^{}\s'.format(re.escape(marker.text)), u'', note_text)
            new_note = segment_soup.new_tag(u'i')
            new_note[u'class'] = u'footnote'
            new_note.string = note_text
            marker.insert_after(new_note)
            note_tag.decompose()
        else:
            assert not any([marker, note_tag])

        markup = segment_root.find_all('span', class_=re.compile(u'[BZS]'))
        for b in markup:
            if b['class'] == 'S':
                b.name = 'small'
            elif b['class'] == 'Z':
                b.name = u'quote'
            else:
                b.name = 'b'
            del b['class']

        segment_text = segment_root.decode_contents()
        segment_text = re.sub(u'^\s+|\s+$', u'', segment_text)
        segment_text = re.sub(u'\s{2,}', u' ', segment_text)
        segment_text = re.sub(u'\s*<br/>\s*', u'<br/>', segment_text)
        segment_text = re.sub(u'\s*(<br/>)+$', u'', segment_text)

        # break on quotes which immediately follow a break
        broken_segments = re.split(ur'<br/>(?=<quote>)', segment_text)
        broken_segments = [re.sub(u'quote', u'b', seg) for seg in broken_segments]
        return broken_segments

    def get_index_titles(self):
        return self.texts.keys()

    def get_text_array_for_index(self, index_title):
        if index_title not in self.texts:
            raise KeyError(index_title)
        return self.texts[index_title].array()

    def translate_commentator(self, commentator):
        return self.commentator_mapping[commentator]

    def get_index_for_title(self, title):
        commentator, base_title = re.split(u'\son\s', title, maxsplit=1)
        he_commentator = self.translate_commentator(commentator)
        rambam_index = library.get_index(base_title)
        he_title = u'{} על {}'.format(he_commentator, rambam_index.get_title('he'))
        jnode = JaggedArrayNode()
        jnode.add_primary_titles(title, he_title)
        jnode.add_structure(["Chapter", "Halakhah", "Comment"])
        jnode.validate()
        categories = [
            u"Halakhah",
            u"Mishneh Torah",
            u"Commentary",
            commentator,
            rambam_index.categories[-1]
        ]
        return {
            u'title': title,
            u'categories': categories,
            u'dependence': u'Commentary',
            u'collective_title': commentator,
            u'schema': jnode.serialize(),
            u'base_text_titles': [base_title]
        }

    def get_version_for_title(self, title):
        if title not in self.texts:
            raise KeyError(title)
        return {
            "versionTitle": "Friedberg Edition",
            "versionSource": "https://fjms.genizah.org/",
            "language": "he",
            "text": self.texts[title].array()
        }

    def generate_links(self):
        return [
            {
                'refs': [li[0], li[1]],
                'type': 'commentary',
                'auto': True,
                'generated_by': "Peregrine Parser"
            }
            for li in self.links
        ]


with open("Friedberg_Texts.csv") as fp:
    rows = list(unicodecsv.DictReader(fp))

# with open("Friedberg_Texts_Metadata.csv") as fp:
#     titles = {row['id']: {'en_name': row['en_name'], 'he_name': row['he_name']} for row in unicodecsv.DictReader(fp)}

storage = CommentStore()
for row in rows:
    storage.resolve_row(row)

titles = storage.get_index_titles()


def add_terms_locally(comment_store):
    """
    :param CommentStore comment_store:
    :return:
    """
    for en_name, he_name in comment_store.commentator_mapping.items():
        if not Term().load_by_title(en_name):
            add_term(en_name, he_name, server='http://localhost:8000')


def upload_index(storage_object, title, destination='http://localhost:8000'):
    """
    :param CommentStore storage_object:
    :param title
    :param destination:
    :return:
    """
    index = storage_object.get_index_for_title(title)
    post_index(index, server=destination, weak_network=True)


def upload_version(storage_object, title, destination='http://localhost:8000'):
    version = storage_object.get_version_for_title(title)
    post_text(title, version, index_count="on", server=destination, weak_network=True)


server = 'http://peregrine.sandbox.sefaria.org'
num_processes = 1

add_terms_locally(storage)

partial_upload_index = partial(upload_index, storage, destination=server)
partial_upload_version = partial(upload_version, storage, destination=server)


def ensure_categories(storage_object, destination):
    """
    :param CommentStore storage_object:
    :param destination:
    :return:
    """
    categories = set([tuple(storage_object.get_index_for_title(title)['categories'])
                      for title in storage_object.get_index_titles()])
    for category_list in categories:
        add_category(category_list[-1], category_list, server=destination)


ensure_categories(storage, server)

if num_processes > 1:
    pool = Pool(num_processes)
    pool.map(partial_upload_index, titles)
    pool.map(partial_upload_version, titles)

else:
    regular_output = sys.stdout
    log_file = open('upload_log.log', 'w')
    progress_bar = tqdm(total=len(titles))

    for t in titles:
        sys.stdout = log_file
        partial_upload_index(t)
        partial_upload_version(t)
        sys.stdout = regular_output
        progress_bar.update(1)
    log_file.close()

post_link(storage.generate_links(), server=server, weak_network=True)
with codecs.open('All_Peregrine_Titles.json', 'w', 'utf-8') as fp:
    json.dump(titles, fp)

requests.post(os.getenv('SLACK_URL'), json={'text': 'Peregrine Complete :owl:'})
