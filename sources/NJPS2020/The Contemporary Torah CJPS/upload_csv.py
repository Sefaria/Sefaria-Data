import django
django.setup()
from sefaria.model import *
import csv
vtitle = "The Contemporary Torah, Jewish Publication Society, 2006"
with open("cjps issues.csv", 'r') as f:
    lines = list(csv.reader(f))[1:]
    for ref, comm in lines:
        tc = TextChunk(Ref(ref), vtitle=vtitle, lang='en')
        assert tc.text != comm
        tc.text = comm.strip()
        tc.save(force_save=True)
