# -*- coding: utf-8 -*-
import django
django.setup()

import pymongo
import geojson
from sefaria.system.database import db
from sefaria.model import *
import unicodecsv as csv


"""
0 Category
1 Desc - En
2 Desc - He
"""

def _(p, attr, field):
    if field:
        setattr(p, attr, field)

with open("Torah Commentators - Bios - Categories.tsv") as tsv:
    next(tsv)
    for l in csv.reader(tsv, dialect="excel-tab"):
        path = l[0].split(",")
        c = Category().load({"path": path})
        c.enDesc = l[1].strip()
        c.heDesc = l[2].strip()
        c.save()
