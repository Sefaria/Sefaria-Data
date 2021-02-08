from sources.functions import *
import time
with open("Ohr Chadash/New Footnotes.csv", 'r') as f:
    text = {}
    for row in csv.reader(f):
        if row[0].startswith("Footnotes"):
            ref = Ref(row[0]).section_ref().normal()
            if ref not in text:
                text[ref] = []
            text[ref].append(row[1])


starting = False
start = "10:1"
for ref in text:
    if start in ref:
        starting = True
    if not starting:
        continue
    send_text = {
        "language": "he",
        "versionTitle": "Ohr Chadash, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2014",
        "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH004713598/NLI",
        "text": text[ref]
    }
    post_text(ref, send_text, server="https://www.sefaria.org")
    time.sleep(35)