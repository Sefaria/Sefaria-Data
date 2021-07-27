import csv
import django
django.setup()
from sefaria.model import *
links = 0
nones = 0
rows = []
with open("manual_or_engineer_incorrectly_linked.csv", 'r') as f:
	for row in csv.reader(f):
		rows.append(row)

with open("structural_problems.csv", 'r') as f:
	for row in csv.reader(f):
		rows.append(row)

for row in rows:
	link = Link().load({"$and": [{"refs": row[0]}, {"refs": row[1]}]})
	if link is None:
		nones += 1
	else:
		links += 1
		link.delete()

print("{} links already deleted before script ran.  Script deleted {} links.".format(nones, links))

