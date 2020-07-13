import re
import csv
from rif_utils import tags_map, path

def handle_bolding(string, masechet, address):
    start, end = tags_map['masechet']['bold'], tags_map['masechet']['unbold']
    temp = re.sub(start+' *[^<@ ]* *'+end, '', string)
    string = re.sub(start+' *([^<@ ]*) *'+end, ' <b>\1</b> ', string)
    for unclosed in re.findall(start+' *([^<@ ]*) *', temp):
        string = string.replace(start+unclosed, ' <b>'+unclosed+'</b> ')
    for unopen in re.findall(' *([^<@ ]*) *'+end, temp):
        string = string.replace(unclosed+end, ' <b>'+unopen+'</b> ')
    if start in string or end in string:
        print('(un)bold tag in', masechet, address)
    return string

def handle_refs_and_notes(string, masechet, address):
    start, end = tags_map['masechet']['tanakh_refs'], tags_map['masechet']['end_tag']
    for ref in re.findall(start+'([^@<])'+end, string):
        try:
            Ref(ref)
            string = re.sub(start+'([^@<])'+end, '(\1)')
        except:
            pass
    if any(tag in string for tag in [start, end, tags_map['masechet']['notes'], tags_map['masechet']['end_tag']]):
        print('reg tags in', masechet, address)

def delete_trash(string):
    string = string.replace('@17', '')

def check_alts(data, masechet):
    starts, ends, names = [], [], []
    start = True
    first = True
    for n, row in enumerate(data):
        if '@99' in row['content']:
            ends.append(row['page.section'])
            row['content'] = row['content'].replace('@99', '')
            if len(row['content']) > 25: print('hadran too long', masechet, row['page.section'])
            start = True
        elif '@00' in row['content'] or start:
            starts.append(row['page.section'])
            if not start and data[n-1]['page.section'] not in ends:
                ends.append(data[n-1]['page.section'])
                print('no @99 in', masechet, data[n-1]['page.section'])
                if len(data[n-1]['page.section']) > 25: print('hadran too long', masechet, data[n-1]['page.section'])
            if '@00' in row['content']:
                row['content'] = row['content'].replace('@00', '')
                if len(row['content']) > 18: print('chapter beginning too long', masechet, row['page.section'])
                names.append(row['content'])
            else:
                print('no @00 in chapter beginning', masechet, row['page.section'])
                names.append('')
            start = False
        first = False

for masechet in tags_map:
    with open(path+'/rif_csv/rif_'+masechet+'.csv', encoding='utf-8', newline='') as file:
        data = list(csv.DictReader(file))
