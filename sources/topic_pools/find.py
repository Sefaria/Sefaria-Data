import csv
import django
django.setup()
from sefaria.helper.topic import generate_all_topic_links_from_sheets

fieldnames = []
sheet_source_links, sheet_related_links, sheet_topic_links = generate_all_topic_links_from_sheets()
for l in sheet_source_links + sheet_related_links + sheet_topic_links:
    for key in l:
        if key not in fieldnames:
            fieldnames.append(key)

with open('topics.csv', 'w') as fp:
    w = csv.DictWriter(fp, fieldnames=fieldnames)
    w.writeheader()
    for l in sheet_source_links + sheet_related_links + sheet_topic_links:
        w.writerow(l)
