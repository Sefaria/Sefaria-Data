
from datetime import datetime
import unicodecsv as csv

from sefaria.model import *
from sefaria.sheets import save_sheet, add_ref_to_sheet, add_source_to_sheet


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
"""
uid = 15872  # Mike Feuer
live = True

sheets = []
current_doc_number = None
current_sheet = None

with open("Jerusalem Anthology - Sheet1.tsv") as tsv:
    next(tsv)
    next(tsv)
    for l in csv.reader(tsv, dialect="excel-tab"):
        if l[8] != current_doc_number:
            current_doc_number = l[8]
            if current_sheet and live:
                sheets.append(save_sheet(current_sheet, uid))

            current_sheet = {
                "title": "Jerusalem Anthology - {}".format(l[9]),
                "sources": [],
                "status": "public",
                "options": {"numbered": 0, "divineNames": "noSub"},
                "generatedBy": "Sefaria Jerusalem Anthology",
                "promptedToPublish": datetime.now().isoformat(),
            }
        try:
            ref = Ref(l[14])
            if u"Tanach" in ref.index.categories:
                en = TextChunk(ref, "en").ja().flatten_to_string()
            else:
                en = TextChunk(ref, "en", "Rabbi Mike Feuer, Jerusalem Anthology").ja().flatten_to_string()
            if not en:
                print "Empty! {}".format(ref.normal())
                continue
            source = {
                "ref": ref.normal(),
                "heRef": ref.he_normal(),
                "text": {
                    "en": en,
                    "he": TextChunk(ref, "he").ja().flatten_to_string()
                }
            }
            current_sheet["sources"].append(source)
        except Exception as e:
            if l[13] != "no":

                print u"Placed Ref Failed - {} - {}".format(l[14], l[1])
            source = {
                "outsideBiText": {
                    "he": u"<b>{}</b>\n{}".format(l[0], l[15]),
                    "en": u"<b>{}</b>\n{}".format(l[1], l[16])
                }
            }
            current_sheet["sources"].append(source)

index_sheet = {
    "title": "Jerusalem Anthology",
    "sources": [{"comment": u"\n".join(["<p><a href='{}'>{}</a></p>".format("/sheets/{}".format(s["id"]), s["title"].replace("Jerusalem Anthology - ", "")) for s in sheets])}],
    "status": "public",
    "options": {"numbered": 0, "divineNames": "noSub"},
    "generatedBy": "Sefaria Jerusalem Anthology",
    "promptedToPublish": datetime.now().isoformat(),
}
if live:
    save_sheet(index_sheet, uid)