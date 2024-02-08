import csv
import os
import django
django.setup()
from sefaria.model import *

ZEROS = []

def check_sequence(data):
    ref = ''
    for row in data:
        row['problem'] = ''
        if ref and row['base text ref'] and Ref(ref).follows(Ref(row['base text ref'])) and row['base text ref'][-2:] != ':1':
            row['problem'] += 'sequence problem'
        if '22גמ' in row['comment'] and ref[-2:] != ':1':
            row['problem'] += 'mishna not in segment 1'
        if row['base text ref']:
            ref = row['base text ref']
    return data

def check_density(data):
    words = 0
    comments = 0
    dens = {}
    num_of_comm = []
    subrefs = Ref(Ref(data[0]['base text ref']).book).all_segment_refs()
    for ref in subrefs:
        ref_words = len(ref.text('he', 'Mechon-Mamre').text.split())
        ref_coms = len([row for row in data if row['base text ref'] == ref.normal()])
        if not ref_words:
            if ref_coms:
                print('empty ref', ref.normal())
            continue
        if not ref_coms:
            global ZEROS
            ZEROS.append((ref.normal(), ref_words))
        dens[ref.normal()] = (ref_coms, ref_words)
        words += ref_words
        comments += ref_coms
        num_of_comm.append(ref_coms)
        if num_of_comm[-4:] == [0, 0, 0, 0]:
            print('4 segments without comments, ends by', ref.normal())

def jt(data):
    for row in data:
        row['base text ref'] = row['base text ref'].replace('JTmock', 'Jerusalem Talmud')
    return data

if __name__ == '__main__':
    comm = 'Ammudei Yerushalayim Tinyana'
    path = f'csvs/{comm}'
    all = []
    for file in os.listdir(path):
        if file[0] == '.' or file == 'report.csv': continue
        if comm in file:
            continue
        print(file)
        data = list(csv.DictReader(open(f'{path}/{file}', encoding='utf-8', newline='')))
        data = jt(data)
        data = check_sequence(data)
        all += data
        #check_density(data)
    with open(f'{path}/{comm}.csv', 'w', encoding='utf-8', newline='') as fp:
        w = csv.DictWriter(fp, fieldnames=['masechet', 'commentary', 'perek', 'halakha', 'page', 'comment', 'dh',
                                           'base text ref', 'base text', 'problem'])
        w.writeheader()
        for row in all:
            w.writerow(row)

    ZEROS.sort(key = lambda x: x[1])
    '''for x in ZEROS[-30:]:
        print(x[0])'''
