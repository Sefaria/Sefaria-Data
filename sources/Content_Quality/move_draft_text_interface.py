import django
django.setup()
from sefaria.model import *
indices = []
import time


import os
version = "all"
SEFARIA_SERVER = "https://jmc.cauldron.sefaria.org"
results = []
indices = ["Connecticut Ratification Debates", "Delaware Ratification Debates"]
for m in indices:
     print(m)
     cmd = """./run scripts/move_draft_text.py "{}" -k '{}' -d '{}'""".format(m,  API_KEY, SEFARIA_SERVER)
     results.append(os.popen(cmd).read())
     time.sleep(1)

