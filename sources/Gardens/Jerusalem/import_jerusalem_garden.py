# coding=utf-8
from sefaria.model import *
from sefaria.system.exceptions import InputError
import unicodecsv as csv

"""
0	Source Reference (Hebrew)
1	Source Reference (English)
2	Names of Jerusalem
3	Geography
4	Time Referenced
5	Intellectual Orientation
6	Characters
7	Keywords
8	Document #
9	Document Title
10	Order
11	Hebrew in Sefaria?
12	Other English in Sefaria?
13	Text Placed?
14	Reference as it appears in Sefaria
15	Hebrew
16	English
17	Shoshana's Notes
18	Text Notes
19  Work Title
"""

books = {}
with open("Jerusalem Anthology - Bibliographic Data.tsv") as tsv:
    next(tsv)
    for l in csv.reader(tsv, dialect="excel-tab"):
        books[l[0]] = {
            "year": int(l[1]),
            "margin": int(l[2] or 0),
            "place": l[3]
        }

garden_key = u"sefaria.custom.jerusalem"
grdn = Garden().load({"key": garden_key})
if grdn:
    grdn.delete()
grdn = Garden({
    "key": garden_key,
    "title": u"Jerusalem",
    "heTitle": u"ירושלים",
    "subtitle": u"Curated and translated by <a href='/profile/michael-feuer'>Rabbi Mike Feuer</a>",
    "heSubtitle": u""
})
grdn.updateConfig({
    "timeline_scale": "linear"
})
grdn.updateFilter("NamesOfJerusalem", {"en": "Names of Jerusalem", "he": u"שמות ירושלים", "logic": "AND", "position": "TOP"})
grdn.updateFilter("Geography", {"en": "Geography", "he": u"מקום", "logic": "AND", "position": "TOP"})
grdn.updateFilter("TimeReferenced", {"en": "Time Referenced", "he": u"זמן", "logic": "AND", "position": "TOP"})
grdn.updateFilter("Characters", {"en": "Characters", "he": u"דמויות", "logic": "AND", "position": "TOP"})
grdn.updateFilter("default", {"logic": "AND", "position": "TOP"})

with open("Jerusalem Anthology - Sheet1.tsv") as tsv:
    next(tsv)
    next(tsv)
    for l in csv.reader(tsv, dialect="excel-tab"):
        tags = {
            "default": [a.title().strip() for a in l[7].split(",") if a],
            "NamesOfJerusalem": [a.title().strip() for a in l[2].split(",") if a],
            "Geography": [a.title().strip() for a in l[3].split(",") if a],
            "TimeReferenced": [a.title().strip() for a in l[4].split(",") if a],
            "Characters": [a.title().strip() for a in l[6].split(",") if a]
        }
        try:
            ref = Ref(l[14])

            if u"Tanakh" in ref.index.categories:
                en = TextChunk(ref, "en").ja().flatten_to_string()
            else:
                en = TextChunk(ref, "en", "Rabbi Mike Feuer, Jerusalem Anthology").ja().flatten_to_string()
            if not en:
                print "Empty! {}".format(ref.normal())
                continue

            stop = {
                "type": "inside_source",
                "ref": ref.normal(),
                "tags": tags,
                "title": ref.normal(),
                "heTitle": ref.he_normal()
            }
            if u"Tanakh" not in ref.index.categories:
                stop["enVersionTitle"] = "Rabbi Mike Feuer, Jerusalem Anthology"

        except (InputError, AttributeError) as e:
            if l[13] != "no":
                print u"Placed Ref Failed - {} - {}".format(l[14], l[1])

            stop = {
                "type": "outside_source",
                'title': l[1],
                'heTitle': l[0],
                'heText': l[15],
                'enText': l[16],
                "tags": tags,
            }
            if l[19]:
                book = books[l[19]]
                print u"Referencing {}".format(l[19])
                stop["placeKey"] = book["place"]
                stop["start"] = book["year"] - book["margin"]
                stop["end"] = book["year"] + book["margin"]
                stop["startIsApprox"] = book["margin"] != 0
                stop["endIsApprox"] = book["margin"] != 0

        grdn.add_stop(stop)

grdn.save()
