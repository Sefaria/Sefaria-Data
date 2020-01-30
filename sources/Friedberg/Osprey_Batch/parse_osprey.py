# encoding=utf-8

import re
import time
import sqlite3
from tqdm import tqdm
from threading import Lock
from bs4 import BeautifulSoup, NavigableString
from sources.Friedberg.Osprey_Batch import sef_obj
from concurrent.futures.thread import ThreadPoolExecutor
from sefaria.datatype.jagged_array import JaggedTextArray
from sources.functions import post_text, post_index, add_category, add_term

conn = sqlite3.connect('osprey.db')
conn.row_factory = sqlite3.Row

"""
All books are depth 3 Jagged Arrays. By joining the links table with texts, book_info and units, we can get a pretty
good breakdown of the data

Irregularities:
HilchotId = 1 goes to "Mishneh Torah, Transmission of the oral law. This is a depth 1 text, and has a PerekId of 0
throughout.
Anything else with a PerekId of 0 should get linked to that book, Chapter 1, Halacha 1

Also of note is HilchotId=2 which relates to מניין המצוות. There's only one comment there, so we can hard code that.
All Hilchot values where HilchotId > 2 can be parsed with the addition of משנה תורה,

We'll want to order the results by book. This way we can store each book in a simple list. Each book has a unique
HilchotId and bid. Finding a new book means we need to add a new book to our list.

Adding text: Use a JaggedTextArray. With the Perek and Halacha we can determine the first two indices of the comment
address. The last index can be determined by calling JaggedArray.sub_array_length(first_two_indices). When this returns
None, the result is 0. We can then set_element with pad=0.

Create a Commentary class. This will have methods to:
* create a new commentary
* check if a row belongs within this commentary
* add new segments 

Text formatting:
R and N represent footnotes. R appears to be a * where N appears to be the comment related to said 8. Having said that,
there are 17 more 'R's than 'N's. We need to verify these assumptions across the corpus.
"""


class Commentary:

    def __init__(self, **kwargs):
        self.commentator = kwargs['en_title']
        self.he_commentator = kwargs['he_title']
        self.book = kwargs['book']
        self.he_book = kwargs['he_book']
        self.book_id = kwargs['bid']
        self.hilchot_id = kwargs['HilchotId']
        self.ja = JaggedTextArray()

    @classmethod
    def build_from_row(cls, row):
        if row['HilchotId'] == 2:
            raise CommentaryError

        en_title, he_title = cls.book_titles_from_row(row)
        init_args = {
            'en_title': row['en_title'],
            'he_title': row['name'],
            'book': en_title,
            'he_book': he_title,
            'bid': row['bid'],
            'HilchotId': row['HilchotId'],
        }
        return cls(**init_args)

    @staticmethod
    def book_titles_from_row(row):
        mishneh_torah = 'משנה תורה'
        full_title = f'{mishneh_torah}, {row["Hilchot"]}'
        en_title = sef_obj.Ref(full_title).normal()
        return en_title, full_title

    def is_part_of_commentary(self, row):
        return (self.book_id, self.hilchot_id) == (row['bid'], row['HilchotId'])

    def add_segment(self, segment: str, indices: tuple) -> None:
        final_index = self.ja.sub_array_length(indices)
        if final_index is None:
            final_index = 0
        indices = indices + (final_index,)
        self.ja.set_element(indices, segment)

    def add_segments_from_row(self, row):
        segments = self.build_segments(row['text'])
        indices = self.get_indices_for_row(row)
        for segment in segments:
            self.add_segment(segment, indices)

    @staticmethod
    def get_ja(title, he_title) -> dict:
        ja = sef_obj.JaggedArrayNode()
        ja.add_primary_titles(title, he_title)
        ja.add_structure(['Chapter', 'Halakhah', 'Comment'])
        ja.validate()
        return ja.serialize()

    def generate_index(self) -> dict:
        title, he_title = f'{self.commentator} on {self.book}', f'{self.he_commentator} על {self.he_book}'

        return {
            'title': title,
            'categories': self.get_category(),
            'dependence': 'Commentary',
            'base_text_titles': [self.book],
            'schema': self.get_ja(title, he_title),
            'collective_title': self.commentator,
            'base_text_mapping': 'many_to_one'
        }

    def build_version(self) -> dict:
        return {
            'versionTitle': 'Friedberg Edition',
            'versionSource': 'https://fjms.genizah.org',
            'language': 'he',
            'text': self.ja.array()
        }

    @staticmethod
    def build_segments(segment: str) -> list:
        segment_xml = '<root>{}</root>'.format(segment)
        segment_soup = BeautifulSoup(segment_xml, 'xml')
        segment_root = segment_soup.root

        # clear out multiple classes - we're only interested in the last letter in the class
        for span in segment_root.find_all('span'):
            klass = span.get('class', '')
            if klass and isinstance(klass, list):
                span['class'] = span['class'][-1]

        # consolidate duplicate tags and unwrap meaningless tags
        for span in segment_root.find_all('span'):
            previous = span.previous_sibling
            if not previous:
                continue

            # make sure all text inside spans end with a space, we'll remove duplicates later
            if span.string:
                span.string.replace_with(NavigableString(' {}'.format(span.string)))

            if span.get('class', '') == '':
                span.unwrap()

            elif span.name == previous.name and span.get('class') == previous.get('class'):
                previous.append(span)
                span.unwrap()

        # handle footnotes
        while True:
            marker = segment_root.find('span', attrs={'class': 'R'})
            note_tag = segment_root.find('span', attrs={'class': 'N'})
            if marker and note_tag:
                marker.name = 'sup'
                del marker['class']
                note_text = note_tag.text
                note_text = re.sub(r'^{}\s'.format(re.escape(marker.text)), '', note_text)
                new_note = segment_soup.new_tag('i')
                new_note['class'] = 'footnote'
                new_note.string = note_text
                marker.insert_after(new_note)
                note_tag.decompose()
            else:
                break

        markup = segment_root.find_all('span', class_=re.compile('[BZS]'))
        for b in markup:
            if b['class'] == 'S':
                b.name = 'small'
            elif b['class'] == 'Z':
                b.name = 'quote'
            else:
                b.name = 'b'
            del b['class']

        segment_text = segment_root.decode_contents()
        segment_text = re.sub(r'^\s+|\s+$', '', segment_text)
        segment_text = re.sub(r'\s{2,}', ' ', segment_text)
        segment_text = re.sub(r'\s*<br/>\s*', '<br/>', segment_text)
        segment_text = re.sub(r'\s*(<br/>)+$', '', segment_text)

        # break on quotes which immediately follow a break
        broken_segments = re.split(r'<br/>(?=<quote>)', segment_text)
        broken_segments = [re.sub(r'quote', 'b', seg) for seg in broken_segments]
        return broken_segments

    @staticmethod
    def get_indices_for_row(row) -> tuple:
        def adjust(value: int):
            return value - 1 if value > 0 else value

        return adjust(row['PerekId']), adjust(row['HalachaId'])

    def get_term_data(self) -> tuple:
        return self.commentator, self.he_commentator

    def get_category(self) -> tuple:
        rambam_index = sef_obj.library.get_index(self.book)
        return (
            'Halakhah',
            'Mishneh Torah',
            'Commentary',
            self.commentator,
            rambam_index.categories[-1]
        )


class IntroCommentary(Commentary):

    @staticmethod
    def get_indices_for_row(row) -> tuple:
        return row['HalachaId']-1,

    @staticmethod
    def book_titles_from_row(row):
        return 'Mishneh Torah, Transmission of the Oral Law', 'משנה תורה, מסירת תורה שבעל פה'

    @staticmethod
    def get_ja(title, he_title) -> dict:
        ja = sef_obj.JaggedArrayNode()
        ja.add_primary_titles(title, he_title)
        ja.add_structure(['Halakhah', 'Comment'])
        ja.validate()
        return ja.serialize()


class CommentaryError(Exception):
    pass


def build_commentary_from_row(row) -> Commentary:
    if row['HilchotId'] == 1:
        return IntroCommentary.build_from_row(row)
    else:
        return Commentary.build_from_row(row)


cursor = conn.cursor()
cursor.execute('''SELECT stuff.ord, stuff.bid, stuff.name, stuff.en_title, stuff.hdr, u.HilchotId, u.Hilchot,
 u.PerekId, u.HalachaId, stuff.text FROM links 
    JOIN (
        SELECT b.name, hdr, text, ord, texts.id tid, b.en_title, bid FROM texts JOIN book_info b ON texts.bid = b.id
    ) stuff ON links.text_id = stuff.tid
JOIN units u ON links.unit_id = u.LogicalUnitId WHERE HilchotId != 2
ORDER BY name, ord ASC''')


def iter_cursor(sql_cursor):
    while True:
        value = sql_cursor.fetchone()
        if value is None:
            break
        else:
            yield value


lock, tracker = Lock(), [0]


def upload_commentary(comm: Commentary):
    ind = comm.generate_index()
    post_index(ind, server=server)
    post_text(ind['title'], comm.build_version(), server=server)
    with lock:
        current_index = tracker[0] + 1
        if current_index % 10 == 0:
            print(current_index)
        if current_index % 25 == 0:
            time.sleep(3)

        tracker[0] = current_index


def print_and_add_category(category):
    add_category(category[-1], list(category), server=server)
    with lock:
        current_index = tracker[0] + 1
        if current_index % 10 == 0:
            print(current_index)
        if current_index % 25 == 0:
            time.sleep(3)
        tracker[0] = current_index


terms, categories = set(), set()
current_commentary, comment_store = None, []
for item in tqdm(iter_cursor(cursor), total=28479):
    if not current_commentary or not current_commentary.is_part_of_commentary(item):
        current_commentary = build_commentary_from_row(item)
        comment_store.append(current_commentary)
        terms.add(current_commentary.get_term_data())
        categories.add(current_commentary.get_category())
    current_commentary.add_segments_from_row(item)

server = 'http://localhost:8000'
# server = 'http://friedberg.sandbox.sefaria.org'
for term in terms:
    add_term(*term, server=server)

print(f'There are {len(categories)} categories')
with ThreadPoolExecutor(10) as executor:
    executor.map(print_and_add_category, categories)

print(f'There are {len(comment_store)} books to upload')
tracker[0] = 0
with ThreadPoolExecutor(max_workers=10) as executor:
    executor.map(upload_commentary, comment_store)


print(len(terms), *terms, sep='\n')
