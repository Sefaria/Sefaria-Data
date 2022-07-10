import django
django.setup()
from sefaria.sheets import get_sheet
from sefaria.system.database import db
from sefaria.model import *

ids = Collection().load({'slug':'חק-לישראל'}).sheets
owner = 153800
for i in ids:
    sheet = get_sheet(i)
    sheet['owner'] = owner
    sheet.pop('_id')
    db.sheets.find_one_and_replace({"id": sheet["id"]}, sheet)
