import csv
import re

with open('entries.csv') as fp:
    data = list(csv.DictReader(fp))

for row in data:
    if not row['result']:
        continue

    if row['result'] == 'n':
        continue
    elif row['result'] == 'y':
        replace_by = re.findall('xref: ([AE].*?),', row['xref'])[0]
    else:
        replace_by = row['result']
    if not re.search('^(?:ADD|E)\d+[a-cu]?$', replace_by):
        print(row['id'], replace_by)
    replace_by = f'<xref rid="{replace_by}">'

    if 'rid does not exist' in row['xref']:
        rid = row['xref'].split(': ')[1]
        to_replace = f'<xref rid="{rid}">'
    else:
        to_replace = '<xref>'

    row['xml'] = row['xml'].replace(to_replace, replace_by)

with open('xrefs.csv', 'w') as fp:
    w = csv.DictWriter(fp, row.keys())
    w.writeheader()
    for row in data:
        w.writerow(row)
