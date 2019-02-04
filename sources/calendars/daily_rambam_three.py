# encoding=utf-8

import csv
import sys
from datetime import datetime

import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db


class RambamRow(object):
    __slots__ = "date", "start", "end"

    def __init__(self, date, start, end):
        self.date = date
        self.start = "Mishneh Torah, {}".format(start)
        self.end = "Mishneh Torah, {}".format(end)


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


with open("Daily_Rambam_schedule_3_chapters.csv") as fp:
    rows = [RambamRow(*r) for r in csv.reader(fp)]

problems = 0
for row in rows:
    if not Ref.is_ref(row.start):
        problems += 1
    if not Ref.is_ref(row.end):
        problems += 1

if problems:
    print "Unable to resolve refs"
    sys.exit(0)

entries = [
    {
        "date": datetime.strptime(row.date, "%m/%d/%Y"),
        "refs": configure_refs(Ref(row.start), Ref(row.end))
    }
    for row in rows
]

rambam_collection = db.daily_rambam_three
db.drop_collection(rambam_collection)
for entry in entries:
    rambam_collection.insert_one(entry)
rambam_collection.ensure_index("date")
