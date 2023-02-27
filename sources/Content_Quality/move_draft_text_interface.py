import django
django.setup()
from sefaria.model import *

import time
import os

version = "all"
results = []
indices = []


# Change the following according to your specific needs
SEFARIA_SERVER = "https://www.sefaria.org"
api_key = ""

# Specify which indices you need, and which version.
indices = library.get_indexes_in_category("Mishneh Torah")
vtitle = "Mishneh Torah, trans. by Eliyahu Touger. Jerusalem, Moznaim Pub. c1986-c2007"


for m in indices:
     print(m)
     cmd = f"./run scripts/move_draft_text.py '{m}' --noindex -v 'en:{vtitle}' -k '{api_key}' -d '{SEFARIA_SERVER}'"
     results.append(os.popen(cmd).read())
     time.sleep(5)
