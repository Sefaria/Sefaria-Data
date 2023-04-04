import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db
import csv
from datetime import datetime
from sefaria.utils.calendars import get_parasha
from sefaria.utils.hebrew import *
from sefaria.system.exceptions import BookNameError

class TanyaRow(object):
    __slots__ = "date", "ref", "displayValue", "heDisplayValue"

    def __init__(self, date, title, start):
        self.date = date
        self.start = start

entries = []
with open("../chabad/daily_study_tanya_calendar_-_data_-_daily_study_tanya_calendar_-_data.csv", 'r') as fp:
    for r in list(csv.reader(fp))[1:]:
        if "".join(r).strip() == "":
            continue
        date, heb, eng, ref = r
        try:
            entry = {
                "date": datetime.strptime(date, "%m/%d/%Y"),
                "ref": ref,
                "displayValue": eng,
                "heDisplayValue": heb
            }
            entries.append(entry)
        except Exception as e:
            print(e)
            print(r)
            break

collection = db.tanya_yomi
db.drop_collection(collection)
for entry in entries:
    collection.insert_one(entry)
collection.create_index("date")