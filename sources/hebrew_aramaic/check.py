import csv
import re

from lxml import etree

tree = etree.parse('01-Alef.xml')
root = tree.getroot()
entry_tags = root.findall('.//entry')
prev = ' '
headwords = []
for entry in entry_tags:
    hws = entry.findall('head-word')
    if not hws:
        print(etree.tostring(entry, pretty_print=True, encoding='unicode'))
    hw = entry.findtext('head-word')
    headwords.append({'headword': hw})
    hw = re.sub('[^ א-ת]', '', hw)
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

