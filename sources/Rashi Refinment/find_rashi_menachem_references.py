# -*- coding: utf-8 -*-

from sefaria.model import *
from sefaria.utils.hebrew import strip_nikkud
import sefaria.tracker as tracker
from sefaria.system.exceptions import DuplicateRecordError

patterns = [
    u"מנחם"
]

books = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"
]
total = 0
for book in books:
    rashi_book = "Rashi on " + book
    i = library.get_index(rashi_book)
    all_rashis = i.all_segment_refs()

    # Loop through all of the Rashis
    for rashi_ref in all_rashis:
        rashi = strip_nikkud(TextChunk(rashi_ref, "he", "On Your Way").text)

        # If it matches the pattern
        for pat in patterns:
            if pat in rashi:
                print u"{}\t{}".format(rashi_ref.normal(), rashi.strip())
                total += 1
                break

print "\nLinks: {}".format(total)
