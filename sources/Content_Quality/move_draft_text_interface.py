import django
django.setup()
from sefaria.model import *


import os
indices = library.get_indices_by_collective_title("Lechem Mishneh")
version = "all"
SEFARIA_SERVER = "https://www.sefaria.org"
results = []
for m in indices:
     print(m)
     cmd = "./run scripts/move_draft_text.py '{}' -d '{}'".format(m, SEFARIA_SERVER)
     results.append(os.popen(cmd).read())

