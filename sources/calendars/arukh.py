import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db
import csv
from datetime import datetime

class ArukhRow(object):
    __slots__ = "date", "start", "end"

    def __init__(self, date, start):
        self.date = date
        self.start = start.replace("%2C_", ", ").replace("_", " ").replace("OYoreh", "Yoreh")


def configure_refs(r1, r2):
    """
    :param Ref r1:
    :param Ref r2:
    :return:
    """
    if r1.book == r2.book:
        return [r1.to(r2).normal()]

    next_chap = book_end = r1
    while next_chap:
        book_end = next_chap
        next_chap = next_chap.next_section_ref()

    prev_chap = book_start = r2
    while prev_chap:
        book_start = prev_chap
        prev_chap = prev_chap.prev_section_ref()

    return [r1.to(book_end).normal(), book_start.to(r2).normal()]


with open("AhS_Yomi_Calendar_-_Sefaria_(1).csv.csv") as fp:
    rows = [ArukhRow(*r) for r in csv.reader(fp)]

problems = 0
for row in rows:
    if not Ref.is_ref(row.start):
        problems += 1

entries = [
    {
        "date": datetime.strptime(row.date, "%m/%d/%Y"),
        "refs": Ref(row.start).normal()
    }
    for row in rows
]

collection = db.arukh_hashulchan
db.drop_collection(collection)
for entry in entries:
    collection.insert_one(entry)
collection.create_index("date")
