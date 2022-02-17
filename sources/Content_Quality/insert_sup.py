import django
django.setup()
from sefaria.model import *
from bs4 import BeautifulSoup
for v in VersionSet({"versionTitle": "The Contemporary Torah, Jewish Publication Society, 2006"}):
    vtitle = v.versionTitle
    title = v.title
    if title == "Exodus":
        continue
    segments = library.get_index(title).all_segment_refs()
    for r in segments:
        tc = TextChunk(r, lang='en', vtitle=vtitle)
        soup = BeautifulSoup(tc.text)
        i_tags = soup.find_all("i", {"class": "footnote"})
        print(len(i_tags))
        for i in i_tags:
            orig = str(i)
            if "sup" not in orig:
                assert orig in tc.text
                new = orig.replace('<i class="footnote">', '<sup>*</sup><i class="footnote">')
                print(new)
                assert "</i>" == orig[-4:]
                tc.text = tc.text.replace(orig, new)
                tc.save()
