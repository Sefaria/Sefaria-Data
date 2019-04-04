# -*- coding: utf-8 -*-

import django
django.setup()
from sefaria.system.database import db

# change all sheets' owner in a group
sheets = db.sheets.find({"tags": "Bilingual"})
for sheet in sheets:
    # sheet["owner"] = 51461
    sheet["status"] = "public"
    sheet["group"] = u"גיליונות נחמה"
    del sheet["_id"]
    db.sheets.insert_one(sheet)