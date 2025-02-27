import csv
import re
from lxml import etree

def handle_hw(hw):
    return re.sub('[\.,]', '', hw).strip()


with open('entries.csv') as fp:
    data = list(csv.DictReader(fp))
with open('xrefs.csv') as fp:
    xrefs = {x['from_id']: x for x in csv.DictReader(fp)}
with open('krupnik xref report.csv') as fp:
    wrong_xrefs = {row['xml']: row['xref']  for row in csv.DictReader(fp) if 'rid does not exist:' in row['xref']}
wrong_xrefs = {etree.fromstring(x).get('id'): wrong_xrefs[x].split()[-1] for x in wrong_xrefs}

for row in data:
    xml = etree.fromstring(row['xml'])
    _id = xml.get('id')
    if _id in xrefs:
        if _id in wrong_xrefs:
            xref = xml.xpath(f".//xref[@rid='{wrong_xrefs[_id]}']")[0]
            xref.attrib['rid'] = xrefs[_id]['to_id'].strip()
            continue
        potential_xrefs = xml.xpath(".//xref[not(@rid)]")
        found = False
        for xref in potential_xrefs:
            if not xref.get('rid') and handle_hw(xref.text) == handle_hw(xrefs[_id]['hw']):
                xref.set('rid', xrefs[_id]['to_id'].strip())
                found = True
                break
            if not found and len(potential_xrefs) == 1:
                xref = potential_xrefs[0]
                xref.set('rid', xrefs[_id]['to_id'].strip())
                found = True
            if not found:
                print(f'not found for {_id}', handle_hw(xref.text), handle_hw(xrefs[_id]['hw']))
        row['xml'] = etree.tostring(xml, encoding="unicode")

with open('newnew.csv', 'w') as fp:
    w = csv.DictWriter(fp, fieldnames=['xml'])
    w.writeheader()
    for row in data:
        w.writerow({'xml': row['xml']})

