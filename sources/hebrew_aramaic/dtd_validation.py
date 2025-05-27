from lxml import etree
import re
import os
import django
django.setup()
from report import parse_file
import csv
from collections import Counter

with open('validation.dtd') as fp:
    dtd = etree.DTD(fp)


def original__data_validation():
    path = 'data'
    for file in sorted(os.listdir(path), key=lambda x: int(re.findall('^\d+', x)[0])):
        print(file)
        root = parse_file(file)
        is_valid = dtd.validate(root)
        if is_valid:
            print("XML is valid according to the DTD.")
        else:
            print("XML is not valid according to the DTD.")
            print(dtd.error_log.filter_from_errors())

def csv_validation():
    y, n = 0, 0
    c = Counter()
    with open('entries.csv') as fp:
        data = list(csv.DictReader(fp))
    for row in data:
        xml_string = row['xml'].strip()
        try:
            entry = etree.fromstring(xml_string)
        except Exception as e:
            print(8888, e, xml_string)
            continue
        is_valid = dtd.validate(entry)
        if is_valid:
            y += 1
        else:
            error = str(dtd.error_log.filter_from_errors())
            error = re.findall('(Element .*? content) .*? got (.*)', error)[0]
            error = f'{error[0]} has {error[1]}'
            if error != 'Element binyan content has (binyan-name binyan-form senses)':
                n += 1
                row['problem'] = error
                print(xml_string)
                print(error)
                c[error] += 1
    print(y, n)
    for k in c:
        print(k, c[k])

    with open('krupnik dtd report.csv', 'w') as fp:
        fieldnames = ['id', 'xml', 'problem']
        w = csv.DictWriter(fp, fieldnames=fieldnames)
        w.writeheader()
        for row in data:
            w.writerow({k: row.get(k, '') for k in fieldnames})

csv_validation()

