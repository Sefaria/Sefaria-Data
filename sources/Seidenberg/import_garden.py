# coding=utf-8
from sefaria.model import *
import unicodecsv as csv
import geojson
import re


reflist = []

with open("ecology.csv") as csvfile:
    """
    0 Ref
    1 Resolved (yes/no)
    2 Pages
    3 Hebrew Available
    4 Other English Available
    5 Text Placed
    """
    next(csvfile)
    for l in csv.reader(csvfile, dialect="excel"):
        if l[1] == "yes":
            reflist.append(Ref(l[0]))
    print len(reflist)


garden_key = u"sefaria.custom.ecology"
grdn = Garden().load({"key": garden_key})
if not grdn:
    grdn = Garden({"key": garden_key, "title": u"Kabbalah & Ecology", "heTitle": u"קבלה ואקולוגיה"})

grdn.import_ref_list(reflist)
grdn.save()
