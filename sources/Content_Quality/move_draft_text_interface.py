import django
django.setup()
from sefaria.model import *
from sources.local_settings import API_KEY, SEFARIA_SERVER

import time
import os

version = "all"
results = []
indices = []


# Change the following according to your specific needs
sefaria_server = SEFARIA_SERVER
api_key = API_KEY

# Specify which indices you need, and which version.
indices = ["Torah Ohr", "Likkutei Torah"]
vtitle = "all"
lang = "he"


for m in indices:
     print(m)
     cmd = f"./run scripts/move_draft_text.py '{m}' --noindex -v '{lang}:{vtitle}' -k '{api_key}' -d '{sefaria_server}'"
     results.append(os.popen(cmd).read())
     time.sleep(5)
