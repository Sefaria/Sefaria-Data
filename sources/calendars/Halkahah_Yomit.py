# encoding=utf-8

import re
import unicodecsv
from datetime import datetime

import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db

with open("Halakhah_Yomit.csv") as fp:
    rows = list(unicodecsv.DictReader(fp))


def fix_ref(doc_row):
    doc_row["Ref"] = doc_row["Ref"].replace("OC", "Shulchan Arukh, Orach Chayim")
    doc_row["Ref"] = doc_row["Ref"].replace("Kitzur", "Kitzur Shulchan Aruch")


map(fix_ref, rows)

db_entries = [
    {
        "date": datetime.strptime(row["Date"], "%m/%d/%Y"),
        "ref": Ref(row["Ref"]).normal()
    }
    for row in rows
]
hy = db.halkhah_yomit
db.drop_collection(hy)
for e in db_entries:
    hy.insert_one(e)
hy.ensure_index("date")
