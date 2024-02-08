import csv
import re
import os
import django
django.setup()
from sefaria.model import *

def check_file(filename):
    report = []
    prev = ''
    with open(filename, encoding='utf-8', newline='') as fp:
        data = list(csv.DictReader(fp))
        for i, row in enumerate(data):
            row['base text ref'] = row['base text ref'].replace('JTmock', 'Jerusalem Talmud')
            if not row['base text ref']:
                row['problem'] = 'no ref'
                row['prev found match'] = data[i-1]['base text ref']
                try:
                    row['next found match'] = data[i+1]['base text ref']
                except IndexError:
                    pass
                row['index'] = i
                report.append(row)
            start_tag = re.findall(r'^(?:@\d\d|\d|\$|~|&)', row['comment'])
            if not start_tag:
                continue
            if row['comment'].count(start_tag[0]) > 1 or row['comment'].count('. @') > 1:
                row['problem'] = 'suspect for two comments'
                row['index'] = i
                report.append(row)
            if row['base text ref'] and prev:
                if Ref(prev).follows(Ref(row['base text ref'])):
                    print(row)
            if row['base text ref']:
                prev = row['base text ref']
    return report

if __name__ == '__main__':
    report = []
    path = 'csvs/Chatam Sofer'
    for file in os.listdir(path):
        if file[0].islower():
            continue
        report += check_file(f'{path}/{file}')

    with open(f'{path}/report.csv', 'w', newline='') as fp:
        w = csv.DictWriter(fp, fieldnames=['masechet', 'commentary', 'perek', 'halakha', 'page', 'comment', 'dh',
                                           'base text ref', 'base text', 'problem', 'prev found match', 'next found match', 'index'])
        w.writeheader()
        for row in report:
            w.writerow(row)
