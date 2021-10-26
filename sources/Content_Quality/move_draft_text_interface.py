import django
django.setup()
from sefaria.model import *
indices = []
import time


import os
version = "all"
SEFARIA_SERVER = "https://www.sefaria.org"
results = []
for m in indices:
     print(m)
     cmd = """./run scripts/move_draft_text.py "{}" -s '500' -l '2' -v 'all' -d '{}'""".format(m, SEFARIA_SERVER)
     results.append(os.popen(cmd).read())
     time.sleep(5)

