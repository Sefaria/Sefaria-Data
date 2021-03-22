import django
django.setup()
from sefaria.model import *
API_KEY = SEFARIA_SERVER = ""


import os
cat = "Meiri"
indices = library.get_indices_by_collective_title(cat)
results = []
start = "Nazir"
found_start = True
for m in indices:
     print(m)
     #cmd = "./run scripts/move_draft_text.py '{}' -d '{}' -k '{}'".format(m, SEFARIA_SERVER, API_KEY)
     #results.append(os.popen(cmd).read())
     # if found_start or start == m:
     #      found_start = True
     # else:
     #      continue
     cmd = "./run scripts/move_draft_text.py '{}' -l '2' -v 'all' -d '{}' -k '{}' --noindex".format(m, SEFARIA_SERVER, API_KEY)
     results.append(os.popen(cmd).read())

