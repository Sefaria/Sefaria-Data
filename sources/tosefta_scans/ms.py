import csv
from os.path import expanduser
with open(f'{expanduser("~")}/Downloads/aggregation.csv', newline='', encoding='utf-8') as fp:
    data = csv.DictReader(fp)
    fieldnames = data.fieldnames
    with open('mss.csv', 'w', newline='', encoding='utf-8') as fp:
        w = csv.DictWriter(fp, fieldnames=fieldnames)
        w.writeheader()
        for row in data:
            if row['book type'] == 'תוספתא':
                w.writerow(row)
