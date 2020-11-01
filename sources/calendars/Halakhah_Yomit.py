# encoding=utf-8

import sys
import csv
from datetime import datetime

import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db

if len(sys.argv) < 2:
    print("Please add data filename as first cmd-line argument")
    sys.exit(1)

filename = sys.argv[1]

with open(filename) as fp:
    rows = list(csv.DictReader(fp))


def fix_ref(doc_row):
    original = doc_row["Ref"]
    doc_row["Ref"] = doc_row["Ref"].replace("OC", "Shulchan Arukh, Orach Chayim")
    doc_row["Ref"] = doc_row["Ref"].replace("Kitzur", "Kitzur Shulchan Aruch")
    if not Ref.is_ref(doc_row["Ref"]):
        print(f'{original} -> {doc_row["Ref"]} not recognized as a Ref')
    return doc_row


rows = [fix_ref(row) for row in rows]

db_entries = [
    {
        "date": datetime.strptime(row["Date"], "%m/%d/%Y"),
        "ref": Ref(row["Ref"]).normal()
    }
    for row in rows
]
hy = db.halakhah_yomit
# db.drop_collection(hy)
for e in db_entries:
    hy.replace_one({'date': e['date']}, e, upsert=True)
hy.create_index("date")
