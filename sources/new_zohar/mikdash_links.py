import re
import csv
import django
django.setup()
from sefaria.model import *
from sefaria.utils.talmud import daf_to_section, section_to_daf
from linking_utilities.dibur_hamatchil_matcher import match_ref
from sources.functions import getGematria
from sefaria.system.exceptions import InputError

ALTS = library.get_index('Zohar TNNNG').alt_structs['Pages']['nodes']

def hebrew_daf_to_section(daf):
    daf, amud = re.findall('^([^ ]*) +ע"([אב])', daf)[0]
    return getGematria(daf) * 2 + getGematria(amud) - 2

def get_ref_from_node(node, page):
    page = hebrew_daf_to_section(page)
    if 'addresses' in node:
        i = node['addresses'].index(page)
    else:
        i = page - daf_to_section(node['startingAddress'])
        for sa in node.get('skipped_addresses', []):
            if sa < page:
                i -= 1
    return node['refs'][i]

def get_wholeref(parasha, page, book):
    if parasha == 'שלח':
        parasha = 'שלח לך'
    for vol in ALTS:
        for node in vol['nodes']:
            if node['titles'][1]['text'] == parasha:
                if 'nodes' not in node:
                    return get_ref_from_node(node, page)
                for snode in node['nodes']:
                    if 'titles' in snode and snode['titles'][1]['text'] == book:
                        node = snode
                        return get_ref_from_node(snode, page)
                return get_ref_from_node(node['nodes'][0], page)
    print('not finding', parasha)

def tokenizer(string):
    string = re.sub('<i .*?/i>', '', string)
    string = re.sub('<[^>]*>', '', string)
    string = re.sub('\([^\)]*\)', '', string)
    string = re.sub('\[[^\]]*\]', '', string)
    string = re.sub('[^א-ת"\' ]', '', string)
    return string.split()

def dh_extract_method(com):
    dh = re.findall('@11(.*?)@33', com)
    if dh:
        dh = dh[0]
    else:
        dh = com.split('.')[0]
        dh = ' '.join(dh.split()[:7])
        dh = re.sub('[@\d]', '', dh)
    return dh

def match_refs(parasha, page, book, texts):
    book = book.replace('@00', '')
    if not book:
        book = 'guf'
    elif book == 'ס"ת':
        book = 'סתרי תורה'

    ref = get_wholeref(parasha, page, book)
    matches = match_ref(Ref(ref).text('he', vtitle='Torat Emet'), texts, tokenizer, dh_extract_method=dh_extract_method,
                        place_consecutively=True)['matches']
    return matches

def generate_chunks(rows):
    chunk = []
    old_book = ''
    for row in rows:
        if any(row[key] for key in ['parasha', 'page']) or row['book'] != old_book:
            yield [row for row in chunk if not row['clue']]
            yield [row for row in chunk if row['clue']]
            chunk = []
        chunk.append(row)
        old_book = row['book']
    yield [row for row in chunk if not row['clue']]
    yield [row for row in chunk if row['clue']]

def fillin(data):
    empties = []
    prev = ''
    for r, row in enumerate(data):
        if row['base ref']:
            if type(row['base ref']) == str:
                row['base ref'] = Ref(row['base ref'])
            if empties:
                print(prev, row['base ref'])
                if prev == row['base ref']:
                    for emp in empties:
                        emp['base ref'] = prev
                else:
                    try:
                        ref = Ref(f"{prev}-{row['base ref']}")
                    except InputError:
                        pass
                    else:
                        print(1)
                        texts = [emp['text'] for emp in empties]
                        matches = match_ref(ref.text('he', vtitle='Torat Emet'), texts, tokenizer,
                                            dh_extract_method=dh_extract_method,
                                            place_consecutively=True)['matches']
                        for emp, match in zip(empties, matches):
                            emp['base ref'] = match
                            if emp['base ref']:
                                emp['base ref'] = emp['base ref']
                empties = []
            prev = row['base ref']
        else:
            empties.append(row)
    return data

def iterate_csv():
    with open('mikdash.csv') as fp:
        data = list(csv.DictReader(fp))
    new = []
    parasha, page, book = '', '', ''
    for chunk in generate_chunks(data):
        if not chunk:
            continue
        if chunk[0]['parasha']:
            parasha = chunk[0]['parasha']
        if chunk[0]['page']:
            page = chunk[0]['page']
        book = chunk[0]['book']

        # if parasha != 'בראשית': continue
        # matches = match_refs(parasha, page, book, [row['text'] for row in chunk])


        try:
            matches = match_refs(parasha, page, book, [row['text'] for row in chunk])
        except:
            print('failed', parasha, page, book)
            matches = [None for _ in chunk]
        for row, match in zip(chunk, matches):
            row['base ref'] = match
            if row['base ref']:
                row['base ref'].normal()
        new += chunk[:]
    print(len([x for x in new if x['base ref']]))

    nones = []
    for row in new:
        if row['additional ref']:
            row['base ref'] = row['additional ref']
        if row['base ref']:
            if len(nones) > 20:
                print(len(nones), parasha, book)
            nones = []
        else:
            nones.append(row)
        if row['parasha']:
            parasha = row['parasha']
        if row['book']:
            book = row['book']

    new = fillin(new)
    new = fillin(new)

    print(len([r for r in new if r['base ref']]))

    with open('mikdash links.csv', 'w') as fp:
        w = csv.DictWriter(fp, fieldnames=list(new[0]))
        w.writeheader()
        for row in new:
            w.writerow(row)

if __name__ == '__main__':
    iterate_csv()
