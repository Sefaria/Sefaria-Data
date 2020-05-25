import csv
import django
django.setup()
from sefaria.model import *
print("Deleting...")
delete = True
with open("links_to_delete.csv") as f:
    for n, row in enumerate(csv.reader(f)):
        if n == 0: #headers
            continue
        if n % 100 == 0:
            print(n)
        link = Link().load({"$and": [{"refs": row[0]}, {"refs": row[1]}]})
        if link:
            link.delete()
print("\nCreating...\n")
already_existing = 0
total = 0
with open("links_to_create.csv") as f:
    for n, row in enumerate(csv.reader(f)):
        link = {"refs": [row[0], row[1]], "generated_by": "redisambiguator", "type": "Commentary", "auto": True}
        curr_link = Link().load({"$and": [{"refs": row[0]}, {"refs": row[1]}]})
        assert curr_link is None
        if link:
            already_existing += 1
        else:
            Link(link).save()
        total += 1
print(already_existing)
print(total)