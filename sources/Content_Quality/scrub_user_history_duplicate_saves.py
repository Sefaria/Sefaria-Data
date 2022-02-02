import django
django.setup()
from collections import defaultdict
from sefaria.model import *


uhs = UserHistorySet({"saved": True})
uh_by_user = defaultdict(list)
for uh in uhs:
    if uh.ref in uh_by_user[uh.uid]:
        print(f"Deleting... {uh.uid}'s {uh.ref}")
        uh.delete()
    else:
        uh_by_user[uh.uid].append(uh.ref)

# versions = ["The contemporary Torah, a gender-sensitive adaptation of the JPS translation. Jewish Publication Society, 2006",
#             "The Five Books of Moses, by Everett Fox", "The Koren Jerusalem Bible", "Metsudah Chumash, Metsudah Publications, 2009",
#             "Tanakh: The Holy Scriptures, published by JPS", "The Rashi chumash by Rabbi Shraga Silverstein",
#             "The Holy Scriptures: A New Translation (JPS 1917)"]
# for i in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
#     for num_v, v in enumerate(versions):
#         vset = VersionSet({"title": i, "versionTitle": v})
#         assert vset.count() == 1
#         for actual_v in vset:
#             actual_v.priority = len(versions) - num_v
#             print(f"{v} for {i} => {actual_v.priority}")
#             #actual_v.save()
