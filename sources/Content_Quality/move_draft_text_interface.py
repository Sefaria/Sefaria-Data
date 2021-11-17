import django
django.setup()
from sefaria.model import *
indices = []
import time


import os
version = "all"
SEFARIA_SERVER = "https://www.sefaria.org"
results = []
indices = library.get_indexes_in_category("Tanakh")
vtitle = "La Bible, Traduction Nouvelle, Samuel Cahen, 1831 [fr]"
for m in indices:
     print(m)
     cmd = """./run scripts/move_draft_text.py "{}" --noindex -v 'he:{}' -d '{}'""".format(m, vtitle, SEFARIA_SERVER)
     results.append(os.popen(cmd).read())
     time.sleep(5)

