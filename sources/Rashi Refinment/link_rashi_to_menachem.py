# -*- coding: utf-8 -*-

import unicodecsv as csv

from sefaria.model import *
import sefaria.tracker as tracker
from sefaria.system.exceptions import DuplicateRecordError

total = 0

with open("Rashi-Menachem - Links.tsv") as tsv:
    next(tsv)
    for l in csv.reader(tsv, dialect="excel-tab"):
        if not l[2]:
            continue
        refs = [Ref(l[0]).normal(), Ref(l[2]).normal()]

        d = {
            "refs": refs,
            "type": "reference",
            "auto": True,
            "generated_by": "Rashi - Menachem Linker"
        }
        try:
            tracker.add(28, Link, d)
            print u"{}\t{}".format(*refs)
            total += 1
        except DuplicateRecordError:
            print u"Link already exists for {}-{}".format(*refs)


print "\nLinks: {}".format(total)
