import re
import csv
import django
django.setup()
from sefaria.model import *
from sefaria.utils.talmud import daf_to_section, section_to_daf
from data_utilities.dibur_hamatchil_matcher import match_ref
from sources.functions import getGematria

ALTS = library.get_index('Zohar TNNNG').alt_structs['Pages']['nodes']

def hebrew_daf_to_section(daf):
    daf, amud = re.findall('^([^ ]*) +ע"([אב])', daf)[0]
    return getGematria(daf) * 2 + getGematria(amud) - 2

def get_ref_from_node(node, page):
    page = hebrew_daf_to_section(page)
    if 'addresses' in node:
        i = node['addresses'].index[page]
    else:
        i = page - daf_to_section(node['startingAddress'])
        for sa in node.get('skipped_addresses', []):
            if sa < page:
                i -= 1
    return node['refs'][i]

def get_wholeref(parasha, page, book):
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
    return dh[0] if dh else ''

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
    for row in rows:
        if any(row[key] for key in ['parasha', 'page', 'book']):
            yield chunk
            chunk = []
        chunk.append(row)

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
            book = ''
        if chunk[0]['page']:
            page = chunk[0]['page']
        if chunk[0]['book']:
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
        new += chunk[:]
    print(len([x for x in new if x['base ref']]))

    nones = []
    for row in new:
        if row['base ref']:
            if len(nones) > 20:
                print(len(nones), nones[0])
            nones = []
        else:
            nones.append(row)

    with open('mikdash links.csv', 'w') as fp:
        w = csv.DictWriter(fp, fieldnames=list(new[0]))
        w.writeheader()
        for row in new:
            w.writerow(row)

if __name__ == '__main__':
    iterate_csv()
