from lxml import etree
import csv
from collections import Counter

c = Counter()
with open('entries.csv') as fp:
    data = list(csv.DictReader(fp))

field_name = 'binyan sub tags'
# for row in data:
#     row[field_name] = ''
#     row.pop('pos pos')
#     row.pop('binyan-name pos')
#     xml_string = row['xml'].strip()
#     entry = etree.fromstring(xml_string)
#     for binyan in entry.findall('binyan'):
#         children_names = tuple(child.tag for child in binyan.iterchildren())
#         c[children_names] += 1
#         if children_names not in [('binyan-form', 'binyan-name', 'senses'), ('binyan-name', 'senses'), ('binyan-form', 'senses')]:
#             row[field_name] += f'{children_names}\n'
for row in data:
    row[field_name] = ''
    row.pop('pos pos')
    row.pop('binyan-name pos')
    xml_string = row['xml'].strip()
    entry = etree.fromstring(xml_string)
    children_names = tuple(child.tag for child in entry.iterchildren() if child.tag not in ['head-word', 'pos', 'pgbrk'])
    c[children_names] += 1
    if children_names not in [('binyan-form', 'binyan-name', 'senses'), ('binyan-name', 'senses'), ('binyan-form', 'senses')]:
        row[field_name] += f'{children_names}\n'
    if children_names == ('definition', 'number', 'binyan', 'binyan'):
        print(etree.tostring(entry, encoding="unicode"))
for k, v in sorted(c.items(), key=lambda x: -x[1]):
    print(f'{k}: {v}')

with open('krupnik binyan sub tags report.csv', 'w') as fp:
    w = csv.DictWriter(fp, fieldnames=['xml', field_name])
    w.writeheader()
    for row in data:
        w.writerow(row)

