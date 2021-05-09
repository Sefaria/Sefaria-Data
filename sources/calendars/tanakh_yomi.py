import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db
import csv
from datetime import datetime
from sefaria.utils.calendars import get_parasha

class TanakhRow(object):
    __slots__ = "date", "refs"

    def __init__(self, date, title, start, end):
        self.date = date
        if title == "Parasha":
            parasha = get_parasha(datetime.strptime(self.date, "%d/%m/%Y"))
            start = Ref(parasha["aliyot"][0]).starting_ref()
            end = Ref(parasha["aliyot"][-1]).ending_ref()
            self.refs = []
            pos = 0
            while start.book != end.book or start.follows(end):
                self.refs.insert(0, end.normal())
                pos -= 1
                end = Ref(parasha["aliyot"][pos-1]).ending_ref()
            first_ref = start.to(end)
            self.refs.insert(0, first_ref.normal())
        else:
            start = Ref(start)
            end = Ref(end)
            self.refs = configure_refs(start, end)



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


rows = []
with open("Tanach_Yomi_Sedarim_Calendar_-_updated.csv") as fp:
    for r in csv.reader(fp):
        try:
            rows.append(TanakhRow(*r))
        except Exception as e:
            break

entries = [
    {
        "date": datetime.strptime(row.date, "%d/%m/%Y"),
        "refs": row.refs
    }
    for row in rows
]
collection = db.tanakh_yomi
db.drop_collection(collection)
for entry in entries:
    collection.insert_one(entry)
collection.create_index("date")