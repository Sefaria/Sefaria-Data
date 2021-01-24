import django
django.setup()
from sefaria.model import *
import csv
with open("duplicates.csv", 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        set_of_this_link = LinkSet({"$or": [{"refs": row}, {"refs": [row[1], row[0]]}]})
        for i, l in enumerate(set_of_this_link.array()):
            if i == 0:
                pass
            else:
                l.delete()

print("Deleted duplicates")

i = 0
for l in LinkSet():
    i += 1
    if i % 10000 == 0:
        print(i)
    sorted_refs = sorted(l.refs)
    if l.refs != sorted_refs:
        l.refs = sorted_refs
        l.save()

print("Sorted refs on each link")

col, args, kwargs = ('links', ["refs"],{"unique": True})
getattr(active_db, col).create_index(*args, **kwargs)
print("Created unique field on link refs")
