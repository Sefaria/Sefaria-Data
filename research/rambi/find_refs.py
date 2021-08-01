import django, csv, json, re, roman
django.setup()
from sefaria.model import *
from collections import defaultdict
from tqdm import tqdm
from bs4 import BeautifulSoup
from glob import glob
from sefaria.system.database import db
from pymongo import ReplaceOne, UpdateOne


RAMBI_ROOT = "/home/nss/sefaria/datasets/rambi/export-08-05-2021"

def get_list_from_soup(soup, name, attrs, neg_codes=None, pos_codes=None, text_regex=None, output='list'):
    out = []
    list_of_lists = soup.find_all(name, attrs)
    for list_el in list_of_lists:
        inner_list = {'titles': []} if output == 'list-of-dicts' else []
        lang = None
        for el in list_el.find_all('subfield'):
            if el.get('code') == '9': lang = el.text
            if neg_codes is not None and el.get('code') in neg_codes: continue
            if pos_codes is not None and el.get('code') not in pos_codes: continue
            if text_regex is not None and not re.search(text_regex, el.text): continue
            if output == 'list-of-dicts':
                inner_list['titles'] += [el.text]
            else:
                inner_list += [el.text]
        if output == 'list-of-dicts':
            inner_list['lang'] = lang
            out += [inner_list]
        else:
            out += inner_list
    return out

def parse_record_soup(record_soup, fname):
    record = {
        'titles': get_list_from_soup(record_soup, 'datafield', {'tag': '245'}),
        'alt_titles': get_list_from_soup(record_soup, 'datafield', {'tag': '246'}),
        'topics': get_list_from_soup(record_soup, 'datafield', {'tag': '650'}, {'8', '2', '9'}, output='list-of-dicts'),
        'other_topics': get_list_from_soup(record_soup, 'datafield', {'tag': '630'}, {'8', '2', '9'}, output='list-of-dicts'),
        'langs':  get_list_from_soup(record_soup, 'datafield', {'tag': '041'}),
        'links':  get_list_from_soup(record_soup, 'datafield', {'tag': '856'}, text_regex=r'^http'),
        'people': get_list_from_soup(record_soup, 'datafield', {'tag': '100', 'ind1': '0'}, {'8', '2', '9'}, output='list-of-dicts'),
        'bibliography': get_list_from_soup(record_soup, 'datafield', {'tag': '773'}, {'w'}),
        'authors': get_list_from_soup(record_soup, 'datafield', {'tag': '100', 'ind1': '1'}, {'8', '2', '9'}, output='list-of-dicts'),
        'filename': fname,
    }
    # remove empty lists
    items = list(record.items())
    for k, v in items:
        if isinstance(v, list) and len(v) == 0:
            del record[k]
    record['id'] = record_soup.find('controlfield', {'tag': '001'}).text
    return record

def parse_records_in_file(fname):
    records = []
    with open(fname, 'r') as fin:
        data = fin.read()
        soup = BeautifulSoup(data, 'xml')
        for record_soup in soup.find_all('record'):
            records += [parse_record_soup(record_soup, fname)]
    db.rambi.bulk_write([
        ReplaceOne({"id": record['id']}, record, upsert=True) for record in records
    ])

def parse_all():
    for fname in tqdm(glob(RAMBI_ROOT + '/*.xml')):
        parse_records_in_file(fname)

def is_roman_numerals(s):
    roman_num_reg = r'[IVXLCDM]+'
    return re.search(fr'^{roman_num_reg}(\-{roman_num_reg})?$', s) is not None

def from_roman_range(s):
    roman_sections = s.split('-')
    assert len(roman_sections) <= 2
    return '-'.join([str(roman.fromRoman(rsec)) for rsec in roman_sections])

def normalize_book(s):
    m = re.search(r'^(.+), (1st|2nd)$', s)
    if m is not None:
        num = 'I' if m.group(2) == '1st' else 'II'
        return f'{num} {m.group(1)}'
    s = s.replace(' (Apocryphal book)', '')
    return s

def find_refs_in_record(record):
    orefs = []
    num_bad = 0
    for topic in record.get('other_topics', []):
        for ititle, title in enumerate(topic['titles']):
            if is_roman_numerals(title) and ititle > 0:
                if topic['titles'][0] in {'New Testament.', 'Ethiopic Book of Enoch', 'Apocalypse of Ezra.', 'Syriac Apocalypse of Baruch'}: continue
                book = normalize_book(topic['titles'][ititle-1])
                tref = f"{book} {from_roman_range(title)}"
                try:
                    oref = Ref(tref)
                    orefs += [oref]
                except:
                    num_bad += 1
                    print("BAD", tref, record['id'])
    for title in record.get('titles', []) + record.get('alt_titles', []):
        try:
            temp_orefs = library.get_refs_in_string(title, citing_only=True)
            orefs += temp_orefs        
        except:
            continue

    # remove more general refs
    orefs.sort(key=lambda r: r.order_id())
    most_specific_orefs = []
    for ioref, oref in enumerate(orefs):
        assert isinstance(oref, Ref)
        if ioref < (len(orefs) - 1) and oref.contains(orefs[ioref+1]): continue
        most_specific_orefs += [oref]
    return most_specific_orefs, num_bad        

def find_all_refs():
    num_good = 0
    num_bad = 0
    total = db.rambi.count_documents({})
    updates = []
    for record in tqdm(db.rambi.find({}), total=total):
        temp_orefs, temp_num_bad = find_refs_in_record(record)
        updates += [UpdateOne({"id": record['id']}, {"$set": {"refs": [temp_oref.normal() for temp_oref in temp_orefs]}})]
        num_bad += temp_num_bad
        num_good += len(temp_orefs)
    db.rambi.bulk_write(updates)
    print(num_good, num_bad)
if __name__ == "__main__":
    # parse_all()
    find_all_refs()

"""
seg2ref = {}
ref2segs = {}
for seg, refs in seg2ref:
    find pairs of refs that have ids in common
"""