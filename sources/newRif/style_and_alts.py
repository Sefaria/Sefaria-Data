import re
import csv
import json
from rif_utils import tags_map, path
from sefaria.model import *

def handle_bolding(string, masechet, address):
    if masechet == 'Bava Kamma': string = string.replace('@77', '@77 ') #problem because of manual work
    start, end = tags_map[masechet]['bold'], tags_map[masechet]['unbold']
    temp = re.sub(start+' *[^<@ ]* *'+end, '', string)
    string = re.sub(start+' *([^<@ ]*) *'+end, r' <b><big>\1</big></b> ', string)
    for unclosed in re.findall(start+' *([^<@ ]*) *', temp):
        string = string.replace(start+unclosed, ' <b><big>'+unclosed+'</big></b> ')
    for unopen in re.findall(' *([^<@ ]*) *'+end, temp):
        string = string.replace(unopen+end, ' <b><big>'+unopen+'</big></b> ')
    if start in string or end in string:
        print('(un)bold tag in', masechet, address)
    return string

def handle_refs_and_notes(string, masechet, address):
    start, end = tags_map['masechet']['tanakh_refs'], tags_map['masechet']['end_tag']
    for ref in re.findall(start+'([^@<])'+end, string):
        try:
            nref = re.sub(r'[\[\]\(\)]', '', ref)
            Ref(nref)
            string = re.sub(start+ref+end, '({})'.format(nref), string)
        except:
            print('problem with ref {} in {} {}'.format(ref, masechet, address))

def delete_trash(string):
    return re.sub(r'@17|@55|\?', '', string)

def handle_alt_tags(data, masechet):
    starts, ends, names, newdata = [], [], [], []
    start = True
    first = True
    for n, row in enumerate(data):
        row['content'] = delete_trash(handle_bolding(row['content'], masechet, row['page.section']))
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
                if '@00פ' in row['content']:
                    row['content'] = ' '.join(row['content'].split()[2:])
                    if 'U' in row['content'] or len(row['content']) < 8: #'U' means unite. short line should be merge with next (probably has nothing)
                        row['content'] = row['content'] + ' ' + data.pop(n+1)['content']
                        newdata.append(row)
                    else:
                        newdata.append(row)
                else: #if not פרק it's tag of new הלכות
                    row['content'] = re.sub('(@00[^@]*)', r'<b><big>\1</big></b>', row['content'])
                    newdata.append(row)
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

def alt_alts(masechet, starts, ends):
    if masechet != 'Menachot':
        alts = Ref(masechet).index.alt_structs
        sub = 'Chapters'
        if masechet == 'Sanhedrin' or masechet == 'Rosh Hashanah':
            alts[sub]['nodes'].pop(1)
        elif masechet == 'Chullin':
            alts[sub]['nodes'].pop(8)
        elif masechet == 'Sukkah':
            alts[sub]['nodes'].pop()
        elif masechet == 'Yoma':
            alts[sub]['nodes'] = [alts[sub]['nodes'][-1]]
        elif masechet == 'Pesachim':
            alts[sub]['nodes'] = alts[sub]['nodes'][:4] + [alts[sub]['nodes'][-1]]
    else:
        alts = Ref('Rif Menachot').index.alt_structs
        sub = 'Hilchot'
    for n ,(start, end) in enumerate(zip(starts, ends)):
        try:
            alts[sub]['nodes'][n]['wholeRef'] = 'Rif {} {}-{}'.format(masechet, start, end)
        except IndexError:
            print('no chapter {} in {}'.format(n+1, masechet))
    return alts

for masechet in tags_map:
    print(masechet)
    with open(path+'/rif_csv/manual/'+masechet+'.csv', encoding='utf-8', newline='') as file:
        data = list(csv.DictReader(file))
        data, starts, ends = handle_alt_tags(data, masechet)
        alts = alt_alts(masechet, starts, ends)
        with open(path+'/alts/{}.json'.format(masechet), 'w') as fp:
            json.dump(alts, fp)
        with open(path+'/rif_csv/styled/'+masechet+'.csv', 'w', encoding='utf-8', newline='') as fp:
            awriter = csv.DictWriter(fp, fieldnames=['page.section', 'content'])
            awriter.writeheader()
            for item in data: awriter.writerow(item)
