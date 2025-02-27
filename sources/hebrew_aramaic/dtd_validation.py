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
        for row in csv.DictReader(fp):
            xml_string = row['xml'].strip()
            entry = etree.fromstring(xml_string)
            is_valid = dtd.validate(entry)
            if is_valid:
                y += 1
            else:
                n += 1
                error = str(dtd.error_log.filter_from_errors())
                print(xml_string)
                print(error)
                c[error] += 1
    print(y, n)
    print(c)

csv_validation()


