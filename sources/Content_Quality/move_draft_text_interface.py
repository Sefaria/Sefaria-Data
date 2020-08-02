import django
django.setup()
from sefaria.model import *
API_KEY = server = ""


import os
cat = "Gur Aryeh"
indices = library.get_indices_by_collective_title(cat)
results = []
for i in indices:
     #cmd = "./run scripts/move_draft_text.py '{}' -d '{}' -k '{}'".format(i, server, API_KEY)
     #results.append(os.popen(cmd).read())
     cmd = "./run scripts/move_draft_text.py '{}' -d '{}' -k '{}' --noindex -l '2'".format(i, server, API_KEY)
     print(cmd) 
     results.append(os.popen(cmd).read())
