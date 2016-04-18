# coding=utf-8
from sefaria.model import *
import unicodecsv as csv
import geojson
import re

eras = {
    "Gaonim": "GN",
    "Rishonim": "RI",
    "Achronim": "AH",
    "Contemporary": "CO"
}

def setif(p, attr, field):
    if field:
        setattr(p, attr, field)

garden_key = u"sefaria.custom.responsa"
grdn = Garden().load({"key": garden_key})
if not grdn:
    grdn = Garden({"key": garden_key, "title": u"Responsa Anthology", "heTitle": u"עולם השו״ת"})
    grdn.updateConfig({
        "timeline_scale": "linear"
    })

"""
0 Responsum
1 Author
2 Date
3 Location (Questioner)
4 Location (Respondent)
5 Tags
6 Topic
7 Words (H)
8 Hebrew Source
9 Sefaria ref
10 Notes
11 Words (E)
"""

with open("Responsa translated - Sheet1.csv") as csv_file:
    next(csv_file)

    for l in csv.reader(csv_file, dialect="excel"):
        tags = {"default": [a.title().strip() for a in l[5].split(",")]}
        ref = l[9].replace('http://www.sefaria.org/','').replace('_',' ').replace('.', ' ', 1).replace('.',':')

        print
        print ref

        stop = {
            "type": "inside_source",
            "ref": ref,
            "enVersionTitle": 'Sefaria Responsa Anthology',
            "tags": tags
        }

        grdn.add_stop(stop)

grdn.save()
