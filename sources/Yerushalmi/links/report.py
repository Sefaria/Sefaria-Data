import django
django.setup()
from sefaria.model import *
import csv

for ind in library.get_indexes_in_category('Yerushalmi'):
    data = []
    for ref in Ref(ind).all_segment_refs():
        links = ref.linkset()
        links = [l for l in links if l.generated_by == 'yerushalmi tables']
        for link in links:
            refs = link.refs
            yer, other = '', ''
            for r in refs:
                if ref in Ref(r).all_segment_refs():
                    yer = r
                else:
                    other = r
            if not (yer and other):
                print(ref, refs)
            data.append({'yerushalmi ref': yer, 'yerushalmi text': Ref(yer).text('he', 'Mechon-Mamre').text,
                         'linked ref': other, 'linked text': Ref(other).text('he').text})
    new = []
    for row in data:
        if row not in new:
            new.append(row)
    data=new
    with open(f'reports/{ind}.csv', 'w', encoding='utf-8', newline='') as fp:
        r = csv.DictWriter(fp, fieldnames=['yerushalmi ref', 'yerushalmi text', 'linked ref', 'linked text'])
        r.writeheader()
        for x in data:
            r.writerow(x)
