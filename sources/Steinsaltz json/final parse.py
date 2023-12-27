import django
django.setup()
from sefaria.model import *
import bleach
from tqdm import tqdm
books = []
import re
for v in VersionSet({"versionTitle": "The Koren Steinsaltz Tanakh HaMevoar - Hebrew"}).array():
    books.append((library.get_index(v.title), v.versionTitle))
books = books[::-1]
for v in VersionSet({"versionTitle": "The Steinsaltz Tanakh - English"}).array():
    books.append((library.get_index(v.title), v.versionTitle))
for bt in tqdm(books):
    b, v = bt
    # if not b.title == "Steinsaltz on Judges":
    #     continue
    if len(b.all_segment_refs()) < 10:
        b.versionState().refresh()
        assert len(b.all_segment_refs()) > 10
    for r in b.all_segment_refs():
        lang = 'en'
        if "Hebrew" in v:
            lang = 'he'
        orig = text = r.text(lang).text
        both = True
        for c in ['.', ':']:
            c_bool = False
            text_ftnotes = text.split(c)
            for i, l in enumerate(text_ftnotes[1:]):
                text_wout_html = bleach.clean(text_ftnotes[i+1], strip=True, tags=[])
                if len(text_wout_html) > 0 and not text_wout_html.startswith(" "):
                    m = re.findall('^[א-ת]{1}', text_wout_html)
                    if len(m) > 0:
                        text_ftnotes[1+i] = " " + text_ftnotes[i+1]
                        c_bool = True
            both = c_bool and both
            text = f"{c}".join(text_ftnotes)

        for p in ["&lt;footnote.*?&gt;", "&lt;notes.*?&gt;"]:
            for m in re.findall(p, text):
                print(r)
                text = text.replace(m, "")
        if orig != text:
            tc = TextChunk(r, lang=lang, vtitle=v)
            tc.text = text
            tc.save(force_save=True)