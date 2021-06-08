import django
django.setup()
from sources.functions import *

indxs = library.get_indexes_in_category("Bavli")
for i in indxs:
    for v in i.versionSet():
        if v.language == "en" and v.versionTitle.startswith('"Talmud Bavli'):
            print(v.versionTitle)
