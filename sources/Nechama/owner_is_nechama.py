import django
django.setup()
from sefaria.system.database import db
# change all sheets' owner in a group
group = "Nechama Leibowitz' Source Sheets"
sheets = db.sheets.find({"group": group})
for sheet in sheets:
    sheet["owner"] = 32044
    db.sheets.save(sheet)