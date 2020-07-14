import re
import csv
import json
from rif_utils import tags_map, path
from sefaria.model import *

def handle_bolding(string, masechet, address):
    start, end = tags_map['masechet']['bold'], tags_map['masechet']['unbold']
    temp = re.sub(start+' *[^<@ ]* *'+end, '', string)
    string = re.sub(start+' *([^<@ ]*) *'+end, ' <b><big>\1</b></big> ', string)
    for unclosed in re.findall(start+' *([^<@ ]*) *', temp):
        string = string.replace(start+unclosed, ' <b><big>'+unclosed+'</b></big> ')
    for unopen in re.findall(' *([^<@ ]*) *'+end, temp):
        string = string.replace(unclosed+end, ' <b><big>'+unopen+'</b></bg> ')
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

def handle_alt_tags(data, masechet):
    starts, ends, names, newdata = [], [], [], []
    start = True
    first = True
    for n, row in enumerate(data):
        if '@99' in row['content']:
            ends.append(row['page.section'])
            row['content'] = row['content'].replace('@99', '')
            newdata.append(row)
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
                if len(row['content']) > 18:
                    print('chapter beginning too long', masechet, row['page.section'])
                    newdata.append(row) #not when short - we dont want the title in the text
            else:
                print('no @00 in chapter beginning', masechet, row['page.section'])
                newdata.append(row)
            start = False
        else:
            newdata.append(row)
        first = False
    gemara_chapters = len(Ref(masechet).index.alt_structs['Chapters']['nodes'])
    if len(starts) != gemara_chapters:
        print(gemara_chapters, 'chapters in gemara and', len(starts), 'in rif in masechet', masechet)
    return newdata, starts, ends

def make_alts(masechet, starts, ends):
    if masechet != 'Menachot':
        alts = Ref(masechet).index.alt_structs
        sub = 'Chapters'
        if masechet == 'Sanhedrin' or masechet == 'Rosh Hashanah':
            alts[sub]['nodes'].pop(1)
        elif masechet == 'Chullin':
            alts[sub]['nodes'].pop(8)
        elif masechet == 'Yoma':
            alts[sub]['nodes'] = [alts[sub]['nodes'][-1]]
        elif masechet == 'Pesachim':
            alts[sub]['nodes'] = alts[sub]['nodes'][:4] + [alts[sub]['nodes'][-1]]
    else:
        alts = Ref('Rif Menachot').index.alt_structs
        sub = 'Hilchot'
    for n ,(start, end) in enumerate(zip(starts, ends)):
        alts[sub]['nodes'][n]['wholeRef'] = '{} {}-{}'.format(masechet, start, end)
    return alts

for masechet in tags_map:
    with open(path+'/rif_csv/rif_'+masechet+'.csv', encoding='utf-8', newline='') as file:
        data = list(csv.DictReader(file))
        data, starts, ends = handle_alt_tags(data, masechet)
        alts = make_alts(masechet, starts, ends)
        with open(path+'/alt_structs/{}.json'.format(masechet), 'w') as fp:
            json.dump(alts, fp)
