import django
django.setup()
from sefaria.model import *
API_KEY = server = ""


import os
cat = "Bavli"
indices = library.get_indices_by_collective_title(cat)
results = []
start = "Nazir"
found_start = False
for m in mishnah:
     #cmd = "./run scripts/move_draft_text.py '{}' -d '{}' -k '{}'".format(i, server, API_KEY)
     #results.append(os.popen(cmd).read())
     if found_start or start==m:
          found_start = True
     else:
          continue
     cmd = "./run scripts/move_draft_text.py '{}' -v 'en|William Davidson Edition - English' -d '{}' -k '{}' --noindex".format(m, server, API_KEY)
     print(cmd) 
     results.append(os.popen(cmd).read())
