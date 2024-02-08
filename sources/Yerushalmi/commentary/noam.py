import django
django.setup()
from sefaria.model import *
import re
from linking_utilities.dibur_hamatchil_matcher import match_ref
import csv

Y,N=0,0
LINKS = []

def yield_by_conditions(rows, get_start_value, to_yield):
    bunch = []
    start_value = get_start_value(rows[0])
    for row in rows:
        if to_yield(row, start_value) and bunch:
            yield bunch
            bunch = []
            start_value = get_start_value(row)
        bunch.append(row)
    if bunch:
        yield bunch

def get_masechet(row):
    return ' '.join(row['ref'].split(',')[-1].split()[:-1]).replace('Maaserot', 'Maasrot').replace('Meggilah', 'Megillah')

def get_perek_halakha(row):
    return ':'.join(row['ref'].split()[-1].split(':')[:-1])

def make_links(rows):
    def dh_extract_method(comment):
        dh = comment.split('.')[0]
        dh = re.sub('\([^)]*\)', '', dh)
        dh = re.sub('<b>(?:שם|עוד|ירושלמי|מתניתין|דף)[^>]*</b>', '', dh)
        dh = re.sub('</?b>', '', dh).strip()
        dh = re.sub('^שם', '', dh).strip()
        dh = re.sub('^בירושלמי', '', dh).strip()
        dh = re.sub("^בירו'", '', dh).strip()
        dh = re.sub('^מתניתין', '', dh).strip()
        dh = re.sub("^מתני'", '', dh).strip()
        dh = re.sub('^בירושלמי', '', dh).strip()
        return ' '.join(dh.split()[:7])

    global Y, N, LINKS
    masechet = get_masechet(rows[0])
    perek_halakha = get_perek_halakha(rows[0])
    comments_to_match = [r['text'] for r in rows if r['new DH'] == '#']
    base_ref = f'Jerusalem Talmud {masechet} {perek_halakha}'
    if not Ref(base_ref).text('he').text:
        print(base_ref)
        return
    matches = match_ref(Ref(base_ref).text('he', 'Venice Edition'), comments_to_match, lambda x: re.sub('[^\'" א-ת]', '', x).split(),
                        dh_extract_method=dh_extract_method)['matches']
    for bunch, match in zip(yield_by_conditions(rows, lambda _: None, lambda x, _: x['new DH'] == '#'), matches):
        if match:
            first_ref = f'Noam Yerushalmi on {masechet} {bunch[0]["ref"].split()[-1]}'
            if len(bunch) == 1:
                ref = first_ref
            else:
                ref = f'{first_ref}-{bunch[-1]["ref"].split(":")[-1]}'
            Y += 1
            LINKS.append({
                'refs': [match, ref],
                'type': 'commentary',
                'auto': True,
                'generated_by': 'noam yerushalmi parser'
            })
            bunch[0]['base text ref'] = match
        else:
            match = match_ref(Ref(base_ref).text('he', 'Mechon-Mamre'), [bunch[0]['text']],
                                lambda x: re.sub('[^\'" א-ת]', '', x).split(),
                                dh_extract_method=dh_extract_method)['matches'][0]
            if match:
                Y += 1
                bunch[0]['mamre text ref'] = match
            else:
                match = match_ref(Ref(base_ref).text('he', 'The Jerusalem Talmud, edition by Heinrich W. Guggenheimer. Berlin, De Gruyter, 1999-2015'),
                                  [bunch[0]['text']],
                                  lambda x: re.sub('[^\'" א-ת]', '', x).split(),
                                  dh_extract_method=dh_extract_method)['matches'][0]
                if match:
                    Y += 1
                    bunch[0]['guggenheimer text ref'] = match
                else:
                    N += 1
                    print(dh_extract_method(bunch[0]['text']))

def parse_masechet(rows):
    text = []
    for bunch in yield_by_conditions(rows, get_perek_halakha, lambda x, y: get_perek_halakha(x) != y):
        make_links(bunch)
        perek, halakha = get_perek_halakha(bunch[0]).split(':')
        for _ in range(int(perek) - len(text)):
            text.append([])
        for _ in range(int(halakha) - len(text[-1])):
            text[-1].append([])
        text[-1][-1] += [row['text'] for row in bunch]

if __name__ == '__main__':
    with open('Noam Yerushalmi.csv') as fp:
        r = csv.DictReader(fp)
        fieldnames = r.fieldnames
        rows = list(r)
    for bunch in yield_by_conditions(rows, get_masechet, lambda x, y: get_masechet(x) != y):
        mas = get_masechet(bunch[0])
        print(mas)
        parse_masechet(bunch)
    print(Y,N)

    with open('Noam Yerushalmi with links.csv', 'w') as fp:
        w = csv.DictWriter(fp, fieldnames=fieldnames+['base text ref', 'mamre text ref', 'guggenheimer text ref'])
        w.writeheader()
        for row in rows:
            w.writerow(row)


