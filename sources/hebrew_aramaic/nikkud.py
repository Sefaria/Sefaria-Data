import csv
import os
import re
from lxml import etree
import django
django.setup()
from report import parse_file

real_poses = ['שם מקום', 'נ׳', 'מה״ש', 'שם איש', 'ז׳', 'פ״י', 'נ״ר', 'נ', 'זו״נ', 'מה״ק', 'מה״ח',
              'ז׳ שם איש', 'שה״מ', 'תה״פ׳', 'ז׳ שם מקום', 'פ״ע', 'ת׳', 'שס איש', 'ז״ר', 'מה״י', 'ת׳ ותה״פ',
              'כנ׳', 'פ׳י', 'תה״פ', 'פעו״י', 'מה״ג', 'מה״ג ומה״י', 'פיו״ע', 'מה״ג ומה״ח', ]
fix_yud = ['ני', 'תי', 'זי', ]
add_space = ['ת׳נ׳', 'מה״גז״ר', 'ז׳נ׳', ]
other = ['פעז״י', 'ז״', 'ג׳', 'פע״וי', 'פ״ו', 'נ״', ]
poses = real_poses + fix_yud + add_space + other
pos_reg = f'(?:{"|".join(poses)})'
nikkud_reg = '[\u05b0-\u05bc\u05c1\u05c2\u05c7]'
start_reg = '.{75,} '

path = 'data'
report = []
dots_report = []
for file in sorted(os.listdir(path), key=lambda x: int(re.findall('^\d+', x)[0])):
    # if file != '02-Beth.xml': continue
    print(file)
    root = parse_file(file)
    entries = root.findall('.//entry')
    for entry in entries:
        string = etree.tostring(entry, pretty_print=True, encoding='utf-8').decode()
        string = re.sub('<[^>]*>', ' ', string).replace('\n', ' ')
        match = re.search(rf'{start_reg}([^ ]*{nikkud_reg}[^ ]* {pos_reg}\b)', string)
        if match:
            report.append({'entry': etree.tostring(entry, pretty_print=True, encoding='utf-8').decode(), 'suspected string': match.group(1)})
        first_words = [s.split()[0] for s in string.split('.')[1:] if s.strip()]
        for w in first_words:
            match = re.search(nikkud_reg, w)
            if match:
                dots_report.append({'entry': etree.tostring(entry, pretty_print=True, encoding='utf-8').decode(),
                               'suspected string': w})
                break

with open('nikkud in notes report.csv', 'w') as fp:
    w = csv.DictWriter(fp, fieldnames=['entry', 'suspected string'])
    w.writeheader()
    for entry in report:
        w.writerow(entry)
with open('nikkud after dot.csv', 'w') as fp:
    w = csv.DictWriter(fp, fieldnames=['entry', 'suspected string'])
    w.writeheader()
    for entry in dots_report:
        w.writerow(entry)
print(len(report))


