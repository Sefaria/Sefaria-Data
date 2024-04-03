import django
django.setup()
from sefaria.model import *
from tqdm import tqdm
with_base_text_mapping = IndexSet({"base_text_mapping": {"$exists": True}})
for x in tqdm(with_base_text_mapping):
    if hasattr(x, "base_text_titles"):
        if len(x.base_text_titles) == 1 and x.categories[0] == "Tanakh":
            x.versionState().refresh()
    else:
        print(f"DOESNT HAVE BASE TEXT TITLES: {x}")