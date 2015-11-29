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

def _(p, attr, field):
    if field:
        setattr(p, attr, field)

garden_key = u"sefaria.custom.maggid"
grdn = Garden().load({"key": garden_key})
if not grdn:
    grdn = Garden({"key": garden_key, "title": u"Tracing the Maggid", "heTitle": u"חצי צורות של המגיד"})


with open("Bibliographic Data - Sefaria Maggid Project - Places.tsv") as tsv:
    next(tsv)
    next(tsv)
    for l in csv.reader(tsv, dialect="excel-tab"):
        if not l[0]:
            continue
        key = l[0]
        if Place().load({"key": key}):
            continue
        p = Place()
        p.key = key
        p.name_group.add_title(l[0], "en", primary=True, replace_primary=True)
        if l[1]:
            p.name_group.add_title(l[1], "he", primary=True, replace_primary=True)

        if l[2]:
            latlon = []
            try:
                latlon = [float(_) for _ in l[2].split(",")]
            except Exception as e:
                if l[2] != "#ERROR!":
                    print "Failed to parse geo: {}. \n{}".format(l[2], e)
                continue
            if len(latlon) != 2:
                continue
            p.point_location(latlon[1], latlon[0])
        if l[3]:
            p.area_location(geojson.loads(l[3]))

        if l[2] or l[3]:
            p.save()

# Keeping these local for the time being
people = {}
with open("Bibliographic Data - Sefaria Maggid Project - People.tsv") as tsv:
    next(tsv)
    next(tsv)
    next(tsv)
    for l in csv.reader(tsv, dialect="excel-tab"):
        key = l[0].encode('ascii', errors='ignore')
        if not key:
            continue
        p = Person().load({"key": key}) or Person()
        p.key = key
        p.name_group.add_title(l[0], "en", primary=True, replace_primary=True)
        p.name_group.add_title(l[2], "he", primary=True, replace_primary=True)
        for x in l[1].split(","):
            p.name_group.add_title(x, "en")
        for x in l[3].split(","):
            p.name_group.add_title(x, "he")
        if len(l[4]) > 0:
            if "c" in l[4]:
                p.birthYearIsApprox = True
            else:
                p.birthYearIsApprox = False
            m = re.search(r"\d+", l[4])
            if m:
                p.birthYear = m.group(0)
        if len(l[6]) > 0:
            if "c" in l[6]:
                p.deathYearIsApprox = True
            else:
                p.deathYearIsApprox = False
            m = re.search(r"\d+", l[6])
            if m:
                p.deathYear = m.group(0)
        _(p, "birthPlace", l[5])
        _(p, "deathPlace", l[7])
        _(p, "era", eras.get(l[8]))
        _(p, "enBio", l[9])
        _(p, "heBio", l[10])
        _(p, "enWikiLink", l[11])
        _(p, "heWikiLink", l[12])
        _(p, "jeLink", l[13])
        _(p, "sex", l[23])
        people[p.key] = p

books = {}
with open("Bibliographic Data - Sefaria Maggid Project - Works.tsv") as tsv:
    next(tsv)
    next(tsv)
    next(tsv)
    for l in csv.reader(tsv, dialect="excel-tab"):
        if not l[0]:
            continue

        book = {
            "authors": [],
            "title": l[0],
            "heTitle": l[2],
            "compDate": l[8],
            "errorMargin": l[9],
            "compPlace": l[10], #composition place
            "pubDate": l[11],
            "pubPlace": l[12], # publication place
            "era": eras.get(l[13]),
            }
        for a in l[4].split(","):
            a = a.strip()
            if people.get(a):
                book["authors"].append(a)

        books[l[0]] = book

with open("Bibliographic Data - Sefaria Maggid Project - Versions.csv") as csvfile:
    """
    0 Title
    1 Version Name
    2 Version Source
    3 Ref
    4 Text
    5 Attributed
    6 Dynasty
    """
    next(csvfile)
    next(csvfile)
    next(csvfile)
    for l in csv.reader(csvfile, dialect="excel"):
        if not l[0]:
            continue
        book = books[l[0]]
        if len(book["authors"]):
            author = people[book["authors"][0]]
        else:
            author = {}

        placekey = book["compPlace"] or book["pubPlace"] or getattr(author, "deathPlace", "") or getattr(author, "birthPlace", "")
        if not placekey or not place.Place().load({"key": placekey}):
            placekey = ""

        stopdata = {
            "type": "outside_source",
            "placeKey": placekey,
            'title': book["title"],
            'heTitle': book["heTitle"],
            'heText': l[4],
            'enSubtitle': u"{} / {}".format(l[1], l[3]) if l[1] else l[3],
            'heSubtitle': u"{} / {}".format(l[1], l[3]) if l[1] else l[3],
            'tags': {
                "default": [],
                "Attribution": [l[5]],
                "Dynasty": [l[6]]
            }
        }
        if author:
            stopdata["authorsEn"] = author.primary_name("en")
            stopdata["authorsHe"] = author.primary_name("he")

        if book.get("compDate"):
            comp = int(book.get("compDate"))   # doesn't handle the 'c' here
            err = int(book.get("errorMargin", 0))
            stopdata["start"] = comp - err
            stopdata["end"] = comp + err
            stopdata["startIsApprox"] = err != 0
            stopdata["endIsApprox"] = err != 0
        elif author and getattr(author, "birthYear", None) and getattr(author, "deathYear", None):
            stopdata["start"] = int(author.birthYear)
            stopdata["end"] = int(author.deathYear)
            stopdata["startIsApprox"] = author.birthYearIsApprox
            stopdata["endIsApprox"] = author.deathYearIsApprox
        elif author and getattr(author, "deathYear", None):
            stopdata["start"] = int(author.deathYear)
            stopdata["end"] = int(author.deathYear) - 40
            stopdata["startIsApprox"] = True
            stopdata["endIsApprox"] = author.deathYearIsApprox
        elif book.get("pubDate"):
            stopdata["start"] = int(book.get("pubDate"))
            stopdata["end"] = int(book.get("pubDate"))
            stopdata["startIsApprox"] = True
            stopdata["endIsApprox"] = True
        elif author and author.mostAccurateTimePeriod():
            tp = author.mostAccurateTimePeriod()
            stopdata["start"] = tp.start
            stopdata["end"] = tp.end
            stopdata["startIsApprox"] = tp.startIsApprox
            stopdata["endIsApprox"] = tp.endIsApprox

        """
            'enText',
            'tags',  # dictionary of lists
            'indexTitle',
            'timePeriodEn',
            'timePeriodHe'
        """

        grdn.add_stop(stopdata)

grdn.save()
