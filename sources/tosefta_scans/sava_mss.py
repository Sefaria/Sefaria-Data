import json
import django
django.setup()
from sefaria.model.manuscript import Manuscript, ManuscriptPage
from sefaria.system.exceptions import DuplicateRecordError
from pymongo.errors import DuplicateKeyError

with open('mss.json') as fp:
    data = json.load(fp)
for ms in data:
    ms = Manuscript(ms)
    try:
        ms.save()
    except (DuplicateKeyError, DuplicateRecordError):
        pass

with open('msp.json') as fp:
    data = json.load(fp)
for ms in data:
    ms = ManuscriptPage(ms)
    try:
        ms.save()
    except (DuplicateKeyError, DuplicateRecordError):
        pass
