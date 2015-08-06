# -*- coding: utf-8 -*-

from sefaria.model import *
import csv

with open("Torah Commentators - Bios - Works.tsv") as tsv:
    next(tsv)
    next(tsv)
    next(tsv)
    for line in csv.reader(tsv, dialect="excel-tab"):
