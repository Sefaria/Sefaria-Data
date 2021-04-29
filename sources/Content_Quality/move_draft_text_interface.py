import django
django.setup()
from sefaria.model import *
API_KEY = SEFARIA_SERVER = ""


import os
cat = "Tanakh"
indices = library.get_indexes_in_category(cat)
results = []
start = "Nazir"
found_start = True
version = "en:Tanakh: The Holy Scriptures, published by JPS -- updated"
for m in indices:
     print(m)
     # if found_start or start == m:
     #      found_start = True
     # else:
     #      continue
     cmd = "./run scripts/move_draft_text.py '{}' -l '2' -v '{}' -d '{}' -k '{}' --noindex".format(m, version, SEFARIA_SERVER, API_KEY)
     results.append(os.popen(cmd).read())

