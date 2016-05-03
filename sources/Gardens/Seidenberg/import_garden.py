# coding=utf-8
from sefaria.model import *
import unicodecsv as csv
import geojson
import re



reflist = []
placed_ref_list = []
vtitle = 'Rabbi Dr. David Mevorach Seidenberg, from "Kabbalah and Ecology"'
with open("Kabbalah & Ecology Sources - ecology.tsv") as tsvfile:
    """
    0 Ref
    1 Resolved (yes/no)
    2 Pages
    3 Hebrew Available
    4 Other English Available
    5 Text Placed
    6 Notes
    7 Adjusted Ref
    """
    next(tsvfile)
    for l in csv.reader(tsvfile, dialect="excel-tab"):
        if l[7]:
            placed_ref_list.append(Ref(l[7]))
        elif l[5] == "yes":
            if not TextChunk(Ref(l[0]), "en", vtitle).is_empty():
                placed_ref_list.append(Ref(l[0]))
            else:
                reflist.append(Ref(l[0]))
        elif l[6]:  # note and not placed, assuming not a good source
            continue
        elif l[1] == "yes":
            reflist.append(Ref(l[0]))
    reflist = list(set(reflist) - set(placed_ref_list))
    print len(reflist)
    print len(placed_ref_list)

garden_key = u"sefaria.custom.ecology"
grdn = Garden().load({"key": garden_key})
if grdn:
    grdn.delete()

grdn = Garden({"key": garden_key,
               "title": u"Kabbalah & Ecology",
               "heTitle": u"קבלה ואקולוגיה"})
grdn.updateFilter("translation", {"en": "Translation", "he": u"תרגום", "logic": "OR"})
grdn.updateConfig({"filter_order": ["translation","default"]})
grdn.import_ref_list(reflist, defaults={'tags': {"translation": ["Cited in K&E"]}})
grdn.import_ref_list(placed_ref_list, defaults={
        'tags': {"translation": ["Translated in K&E"]},
        'enVersionTitle': vtitle,
        'enSubtitle': 'Translation by Rabbi Dr. David Mevorach Seidenberg, from "Kabbalah and Ecology"'
})
grdn.save()
