import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db
sheets = db.sheets.find({"group": "גיליונות נחמה"})
found_table = []
for sheet in sheets:
    sources = sheet["sources"]
    id = sheet["id"]
    for source_n, source in enumerate(sources):
        if source["node"]:
            text = source["outsideText"] if "outsideText" in source.keys() else source["text"]["he"]
            if "<table" in text and len(text.split()) > 10:
                found_table.append("{}:{}".format(id, source_n+1))

