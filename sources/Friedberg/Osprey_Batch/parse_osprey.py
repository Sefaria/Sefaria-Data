# encoding=utf-8

import sqlite3
from . import sef_obj

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
"""

cursor = conn.cursor()
cursor.execute('''SELECT stuff.ord, stuff.name, stuff.hdr, u.HilchotId, u.PerekId, u.HalachaId, stuff.text FROM links 
    JOIN (
        SELECT b.name, hdr, text, ord, texts.id tid FROM texts JOIN book_info b ON texts.bid = b.id
    ) stuff ON links.text_id = stuff.tid
JOIN units u ON links.unit_id = u.LogicalUnitId
ORDER BY name, ord ASC''')
