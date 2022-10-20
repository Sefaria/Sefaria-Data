from sources.functions import *
from bs4 import BeautifulSoup

vtitle = "The Contemporary Torah, Jewish Publication Society, 2006"

refs = library.get_index("Genesis").all_segment_refs()
import re
for ref in refs:
    tc = TextChunk(ref, lang='en', vtitle=vtitle)
    soup = BeautifulSoup(tc.text)
    m = re.findall("<sup>.{1}</sup><sup>.{1}</sup>", tc.text)
    changed = len(m) > 0
    for x in m:
        tc.text = tc.text.replace(x, "<sup>*</sup>", 1)
    send_text = {
        "language": "en", "versionTitle": vtitle, "text": tc.text, "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH002529489/NLI"
    }
    if changed:
        places[ref.normal()] = tc.text
        #tc.save()
