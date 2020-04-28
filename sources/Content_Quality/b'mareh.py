import django
django.setup()
from sefaria.model import *
vs = VersionSet({"title": {"$regex": "^B'Mareh"}})
vs.delete()
