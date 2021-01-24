import django
django.setup()
from sefaria.model import *
import csv
already_found = []
with open("duplicates.csv", 'w') as f:
    writer = csv.writer(f)
    i = 0
    for l in LinkSet():
        i += 1
        if i % 10000 == 0:
            print(i)
        set_of_this_link = LinkSet({"$or": [{"refs": l.refs}, {"refs": [l.refs[1], l.refs[0]]}]})
        if set_of_this_link.count() > 1:
            refs = sorted(l.refs)
            if refs not in already_found:
                print(refs)
                writer.writerow([refs])
                already_found.append(refs)