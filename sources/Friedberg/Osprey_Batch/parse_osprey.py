# encoding=utf-8

import sqlite3
from bs4 import BeautifulSoup
from sources.Friedberg.Osprey_Batch import sef_obj
from sefaria.datatype.jagged_array import JaggedTextArray

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
            'he_title': row['he_title'],
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

    def add_segment_from_row(self, row):
        segment = self.clean_segment(row['text'])
        indices = self.get_indices_for_row(row)
        final_index = self.ja.sub_array_length(indices)
        if final_index is None:
            final_index = 0
        indices.append(final_index)
        self.ja.set_element(indices, segment, pad='')

    @staticmethod
    def clean_segment(segment: str) -> str:
        return segment

    @staticmethod
    def get_indices_for_row(row):
        return [row['PerekId']-1, row['HalachaId']-1]


class IntroCommentary(Commentary):

    @staticmethod
    def get_indices_for_row(row):
        return [row['HalachaId']-1]

    @staticmethod
    def book_titles_from_row(row):
        return 'Mishneh Torah, Transmission of the Oral Law', 'משנה תורה, מסירת תורה שבעל פה'


class CommentaryError(Exception):
    pass


def build_commentary_from_row(row):
    if row['HilchotId'] == 1:
        return IntroCommentary.build_from_row(row)
    else:
        return Commentary.build_from_row(row)



cursor = conn.cursor()
cursor.execute('''SELECT stuff.ord, stuff.name, stuff.hdr, u.HilchotId, u.Hilchot, u.PerekId, u.HalachaId, stuff.text FROM links 
    JOIN (
        SELECT b.name, hdr, text, ord, texts.id tid FROM texts JOIN book_info b ON texts.bid = b.id
    ) stuff ON links.text_id = stuff.tid
JOIN units u ON links.unit_id = u.LogicalUnitId
ORDER BY name, ord ASC''')


def iter_cursor(sql_cursor):
    while True:
        value = sql_cursor.fetchone()
        if value is None:
            break
        else:
            yield value


from collections import Counter
classes = Counter()
loc = 0
for item in iter_cursor(cursor):
    loc += 1
    if loc % 5000 == 0:
        print(loc)
    t = f'<root>{item["text"]}</root>'
    soup = BeautifulSoup(t, 'html.parser')
    for s in soup.find_all('span'):
        for c in s.get('class', list()):
            classes[c] += 1
for key, value in classes.items():
    print(key, value)
