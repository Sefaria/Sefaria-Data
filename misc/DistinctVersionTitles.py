import unicodecsv as csv
from collections import defaultdict
from sefaria.model import *

counter = defaultdict(int)

for v in VersionSet():
    try:
        counter[v.versionTitle] += 1
    except Exception as e:
        print u"Failed: {}: {}".format(v.title, e)

with open("versionTitles.csv", "w") as csvout:
    csvout = csv.writer(csvout)
    for s in sorted(counter.items(), key=lambda a: -a[1]):
        csvout.writerow(s)