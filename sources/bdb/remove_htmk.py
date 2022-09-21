import csv
import json
import re

tags = {}
i = 1
with open('problems2.csv', newline='', encoding='utf-8') as fp:
    data = list(csv.DictReader(fp))

for row in data:
    for tag in re.findall('((?:<[^>]*?>)+)', row['text']):
        if len(tag) > 4 and 'sup>' not in tag:
            row['text'] = re.sub(re.escape(tag), f'#{i}#', row['text'], 1)
            tags[i] = tag
            i += 1

with open('html tags new.json', 'w') as fp:
    json.dump(tags, fp)

with open('problems wo html new.csv', 'w', newline='', encoding='utf-8') as fp:
    w = csv.DictWriter(fp,
                       fieldnames=['id', 'text', 'al hatorah text', 'al hatorah link', 'biblehub text', 'biblehub link',
                                   'problems'])
    w.writeheader()
    for p in data:
        w.writerow(p)
print(i)
