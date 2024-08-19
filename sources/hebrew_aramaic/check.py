import csv
import re
import os
from lxml import etree

prev = ' '
headwords = []
path = 'data'
for file in sorted(os.listdir(path), key=lambda x: int(re.findall('^\d+', x)[0])):
    print(file)
    tree = etree.parse(f'{path}/{file}')
    root = tree.getroot()
    entry_tags = root.findall('.//entry')
    for entry in entry_tags:
        hws = entry.findall('head-word')
        if not hws:
            print('no headword')
            print(etree.tostring(entry, pretty_print=True, encoding='unicode'))
            continue
        hw = entry.findtext('head-word')
        headwords.append({'headword': hw})
        hw = re.sub('[^ א-ת]', '', hw.replace('ײ', 'יי').replace('װ', 'וו'))
        if sorted([prev, hw]) != [prev, hw]:
            headwords[-1]['error'] = '*'
        prev = hw

with open('misorders.csv', 'w') as fp:
    w = csv.DictWriter(fp, fieldnames=['headword', 'error'])
    w.writeheader()
    for r in headwords:
        w.writerow(r)

with open('sefaria_dictionary.dtd') as fp:
    dtd = etree.DTD(fp)
is_valid = dtd.validate(tree)
if is_valid:
    print("XML is valid according to the DTD.")
else:
    print("XML is not valid according to the DTD.")
    print(dtd.error_log.filter_from_errors())

