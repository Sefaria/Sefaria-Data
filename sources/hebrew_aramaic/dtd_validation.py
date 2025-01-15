from lxml import etree
import re
import os
import django
django.setup()
from report import parse_file

path = 'data'
with open('validation.dtd') as fp:
    dtd = etree.DTD(fp)
for file in sorted(os.listdir(path), key=lambda x: int(re.findall('^\d+', x)[0])):
    print(file)
    root = parse_file(file)
    is_valid = dtd.validate(root)
    if is_valid:
        print("XML is valid according to the DTD.")
    else:
        print("XML is not valid according to the DTD.")
        print(dtd.error_log.filter_from_errors())

