import django
django.setup()
from sefaria.system.database import db
# change all sheets' owner in a group
sheets = db.sheets.find()
for sheet in sheets:
    sheet["owner"] = 51461
    sheet["status"] = "public"
    sheet["group"] = "Nechama Leibowitz' Source Sheets"
    db.sheets.save(sheet)


