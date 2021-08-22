import django
django.setup()
from sefaria.model import *
import time


import os
version = "all"
SEFARIA_SERVER = "https://www.sefaria.org"
results = []
indices = """Man of the Earth
Let Us Welcome the Shemitah
Zikaron leYom HaRishon
Al Kapot HaMan'ul; Homilies for the Days of Awe
Talmud Series; Shemitah
Badei HaAron; Sheviit""".splitlines()
indices = [indices[3]]
for m in indices:
     print(m)
     cmd = """./run scripts/move_draft_text.py "{}" -v 'all' -l '2' -d '{}'""".format(m, SEFARIA_SERVER)
     results.append(os.popen(cmd).read())
     time.sleep(5)

