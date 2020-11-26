import django
django.setup()
from sefaria.model import *
API_KEY = SEFARIA_SERVER = ""


import os
cat = "Rashash"
indices = library.get_indices_by_collective_title(cat)
results = []
start = "Nazir"
found_start = True
for m in indices:
     print(m)
     cmd = "./run scripts/move_draft_text.py '{}' -d '{}' -l 'all' --noindex -k '{}'".format(m, SEFARIA_SERVER, API_KEY)
     results.append(os.popen(cmd).read())
     if found_start or start == m:
          found_start = True
     else:
          continue
     #cmd = "./run scripts/move_draft_text.py '{}' -v 'all' -d '{}' -k '{}' --noindex".format(m, SEFARIA_SERVER, API_KEY)
