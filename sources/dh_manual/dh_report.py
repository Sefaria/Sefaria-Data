import csv
import django
django.setup()
from sefaria.model import *

def make_report(path, fname):
    inds = IndexSet({'categories': {'$all': path}})
    report = []
    for ind in inds:
        segs = 0
        links = 0
        for seg in ind.all_segment_refs():
            segs += 1
            linkset = seg.linkset()
            if linkset and any(l.type in ['Commentary', 'commentary'] for l in linkset):
                links += 1
        report.append({'title': ind.title,
                       'segments': segs,
                       'linked': links,
                       'rate': links/segs})
    with open(f'{fname}.csv', 'w', newline='') as fp:
        w = csv.DictWriter(fp, fieldnames=['title', 'segments', 'linked', 'rate'])
        w.writeheader()
        for r in report:
            w.writerow(r)

if __name__ == '__main__':
    make_report(['Talmud','Bavli','Rishonim on Talmud','Ritva'], 'Ritva')
