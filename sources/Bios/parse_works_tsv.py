# -*- coding: utf-8 -*-

from sefaria.model import *
import csv

"""
0 Primary English Title
1 Author
2 English Description
3 Hebrew Description
4 First Publication / Appearence Year (loazi)
5 Publication Year Margin of Error (+/- years)
6 Place of appearence / publication
7 Era
"""
eras = {
    "Gaonim": "GN",
    "Rishonim": "RI",
    "Achronim": "AH",
    "Tannaim": "T",
    "Amoraim": "A"
}

def _(p, attr, field):
    if field:
        setattr(p, attr, field)

with open("Torah Commentators - Bios - Works.tsv") as tsv:
    next(tsv)
    next(tsv)
    next(tsv)
    for l in csv.reader(tsv, dialect="excel-tab"):
        i = get_index(l[0])
        if not i:
            print "Count not load {}".format(l[0])
            continue
        if i.is_commentary():
            #todo: Do we put this on the version?  Yech.
            continue
        aus = getattr(i, "authors", [])
        for a in l[1].split(","):
            a = a.strip()
            if Person().load({"key": a}) and a not in aus:
                aus.append(a)
        _(i, "authors", aus)
        _(i,"enDesc",l[2])
        _(i,"heDesc",l[3])
        _(i,"pubDate",l[4])
        _(i,"errorMargin",l[5])
        _(i,"placeName",l[6])
        _(i,"era",eras.get(l[7]))
        print "."
        i.save()
