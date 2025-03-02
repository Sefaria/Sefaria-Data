import csv
import re

from parse_csv import Entry

with open('entries.csv') as fp:
    orig_data = list(csv.DictReader(fp))
entries = []
for row in orig_data:
    entry = Entry(row['xml'])
    entries.append(entry)

with open('addenda.csv') as fp:
    added_data = list(csv.DictReader(fp))
addenda = []
for row in added_data:
    entry = Entry(row['xml'])
    addenda.append(entry)

def get_addendum_row_and_hw():
    try:
        row, entry = added_data.pop(0), addenda.pop(0)
    except IndexError:
        return None, None
    return row, entry.headword['word']

def comes_before(hw1, hw2):
    return re.sub('[^ א-ת]', '', hw1) < re.sub('[^ א-ת]', '', hw2)

def should_pop(added_hw, i):
    if all(comes_before(added_hw, entries[j].headword['word']) for j in range(i, i+3)):
        return True

added_row, added_hw = get_addendum_row_and_hw()
unined_data = []
for i in range(len(entries)):
    row = orig_data[i]
    while added_hw and should_pop(added_hw, i):
        unined_data.append(added_row)
        added_row, added_hw = get_addendum_row_and_hw()
    unined_data.append(row)

if added_data or added_hw:
    print('boo')

with open('new.csv', 'w') as fp:
    w = csv.DictWriter(fp, fieldnames=['xml'])
    w.writeheader()
    for row in unined_data:
        w.writerow({'xml': row['xml']})
