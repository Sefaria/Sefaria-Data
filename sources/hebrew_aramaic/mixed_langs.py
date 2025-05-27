import csv
from lxml import etree
import re

def get_relevant_text(element):
    text = element.text or ''
    for child in element:
        if child.tag in ['italic', 'bold']:
            text += child.text or ''
        text += child.tail or ''
    return text

def has_mixed_langs(string):
    if re.search('[א-ת].*[a-zA-Z]', string) :
        return True

with open('entries.csv') as fp:
    data = list(csv.DictReader(fp))
for r, row in enumerate(data):
    try:
        tree = etree.fromstring(row['xml'])
    except etree.XMLSyntaxError as e:
        print(r, e)
    else:
        mixed = []
        for element in tree.iter():
            text = get_relevant_text(element)
            if has_mixed_langs(text):
                mixed.append(etree.tostring(element, encoding="unicode"))
        row['elements with latin after hebrew'] = mixed or ''

with open(f'krupnik mixed langs report.csv', 'w') as fp:
    fieldnames = ['xml', 'elements with latin after hebrew']
    w = csv.DictWriter(fp, fieldnames=fieldnames)
    w.writeheader()
    for row in data:
        row = {k: row.get(k, '') for k in fieldnames}
        w.writerow(row)
