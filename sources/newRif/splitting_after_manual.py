import csv
from rif_utils import netlen2, path

with open('fixed.csv', encoding='utf-8', newline='') as fp:
    data = [row for row in csv.DictReader(fp)]

o150 = 0
o200 = 0
o300 = 0
o0 = 0
for row in data:
    if row['masechet'].strip() != '':
        try:
            newdata
            page = 'X'.join(page).replace('U', ' ').replace('\n', '').replace('XX', 'X').split('X')
            for n, sec in enumerate(page):
                newdata.append({'page.section': f'{npage}:{n+1}', 'content': sec})
            with open(f'{path}/rif_csv/manual/{masechet}.csv', 'w', encoding='utf-8', newline='') as fp:
                awriter = csv.DictWriter(fp, fieldnames=['page.section', 'content'])
                awriter.writeheader()
                for item in newdata: awriter.writerow(item)
        except NameError:
            pass
        masechet = row['masechet'].replace('\n', '')
        npage = ''
        page = []
        newdata = []

    elif row['page.section'].strip() != '':
        if page != []:
            page = 'X'.join(page).replace('U', ' ').replace('\n', '').replace('XX', 'X').split('X')
            for n, sec in enumerate(page):
                newdata.append({'page.section': f'{npage}:{n+1}', 'content': sec})
                if netlen2(sec, masechet) > 150: o150 += 1
                if netlen2(sec, masechet) > 200: o200 += 1
                if netlen2(sec, masechet) > 300: o300 += 1
                o0+=1
            page = []
        npage = row['page.section'].replace('\n', '')

    if row['content'] != 'content':
        page.append(row['content'])

page = 'X'.join(page).replace('U', ' ').replace('\n', '').replace('XX', 'X').split('X')
for n, sec in enumerate(page):
    newdata.append({'page.section': f'{npage}:{n+1}', 'content': sec})
page = []
with open(f'{path}/rif_csv/manual/{masechet}.csv', 'w', encoding='utf-8', newline='') as fp:
    awriter = csv.DictWriter(fp, fieldnames=['page.section', 'content'])
    awriter.writeheader()
    for item in newdata: awriter.writerow(item)

print(o0, o150, o200, o300)
