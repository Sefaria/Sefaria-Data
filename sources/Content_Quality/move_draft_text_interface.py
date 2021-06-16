import django
django.setup()
from sefaria.model import *


import os
indices = """Bereshit Rabbah
Shemot Rabbah
Vayikra Rabbah
Bamidbar Rabbah
Devarim Rabbah
Shir HaShirim Rabbah
Ruth Rabbah
Esther Rabbah
Kohelet Rabbah
Eichah Rabbah""".splitlines()
version = "all"
SEFARIA_SERVER = "https://www.sefaria.org"
results = []
for m in indices:
     print(m)
     # if found_start or start == m:
     #      found_start = True
     # else:
     #      continue
     cmd = "./run scripts/move_draft_text.py '{}' -d '{}'".format(m, SEFARIA_SERVER)
     results.append(os.popen(cmd).read())

