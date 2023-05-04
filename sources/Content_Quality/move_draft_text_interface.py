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
api_key = "kAEw7OKw5IjZIG4lFbrYxpSdu78Jsza67HgR0gRBOdg"

# Specify which indices you need, and which version.
indices = ["Torah Ohr", "Likkutei Torah"]
vtitle = "all"
lang = "he"


for m in indices:
     print(m)
     cmd = f"./run scripts/move_draft_text.py '{m}' --noindex -v '{lang}:{vtitle}' -k '{api_key}' -d '{SEFARIA_SERVER}'"
     results.append(os.popen(cmd).read())
     time.sleep(5)
