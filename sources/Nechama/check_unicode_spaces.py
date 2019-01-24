#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db
sheets = db.sheets.find({"group": "גיליונות נחמה"})
count = 0
for sheet in sheets:
    sources = sheet["sources"]
    for i, source in enumerate(sources):
        text = source["text"]["he"] if "text" in source.keys() else source["outsideText"]
        text = text.replace(unichr(160), " ")
        if text.rfind("    ") > 4+text.find("    ") > 0 and len(text) < 200:
            count += 1
            print "{}:{}".format(sheet["id"], i+1)
            print text
            print
            print
print count