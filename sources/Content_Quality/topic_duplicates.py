import django
django.setup()
import csv
from sefaria.model import *
from collections import defaultdict
he_titles = defaultdict(list)
en_titles = defaultdict(list)
for t in TopicSet():
    for title in t.get_titles('en'):
        if title != "" and t.slug not in en_titles[title]:
            en_titles[title].append(t.slug)
    for title in t.get_titles('he'):
        if title != "" and t.slug not in he_titles[title]:
            he_titles[title].append(t.slug)

c = 0
for l in [en_titles, he_titles]:
    c += 1
    for k in list(l.keys()):
        if len(l[k]) == 1:
            l.pop(k)
    with open(f"report part {c}.csv", 'w') as f:
        writer = csv.writer(f)
        for k in l:
            arr = [k]
            for o in l[k]:
                disambig = [x for x in Topic.init(o).title_group.titles if 'disambiguation' in x]
                if len(disambig) == 0:
                    arr.append(f"https://www.sefaria.org/topics/{o}")
            if len(arr) > 2:
                writer.writerow(arr)
# perhaps report could have columns for disambiguation after each URL