# encoding=utf-8

import re
import unicodecsv
from datetime import datetime

import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db


with open("DafAWeek.csv") as fp:
    rows = list(unicodecsv.DictReader(fp))

entries = []
for row_num, row in enumerate(rows, 2):
    if Ref.is_ref(row["Daf"]):
        temp_ref = Ref(row["Daf"]).normal()
        row["Daf"] = re.sub(u'[ab]$', u'', temp_ref)
    entries.append({
        "date": datetime.strptime(row["Secular Date"], "%m/%d/%Y"),
        "daf": row["Daf"]
    })

daf_weekly = db.daf_weekly
db.drop_collection(daf_weekly)
for entry in entries:
    daf_weekly.insert_one(entry)
daf_weekly.ensure_index("date")
