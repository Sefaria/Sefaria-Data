import csv
import re
import django
django.setup()
from sefaria.utils.hebrew import encode_hebrew_numeral, gematria

with open('Ibn Ezra on Genesis - he - Piotrkow, 1907-1911 (1).csv') as fp:
    ibn_ezra = list(csv.DictReader(fp))
with open('Yahel Ohr - Yahel Ohr.csv') as fp:
    yahel = list(csv.DictReader(fp))
with open('Karnei Ohr - Karnei Ohr.csv') as fp:
    karnei = list(csv.DictReader(fp))

report = []

def check_sequnce(letters, name):
    for j, k in zip(letters, letters[1:]):
        j, k = gematria(j), gematria(k)
        if k != j+1:
            print(f'chapter {i}: {name} {k} comes after {j}')

for i in range(1, 51):
    he_chapter = re.sub('[׳״]', '', encode_hebrew_numeral(i))
    start_index = lambda x: next((i for i, d in enumerate(x) if d['chapter'] == he_chapter), None)
    end_index = lambda x: next((i for i, d in enumerate(x[start_index(x)+1:]) if d['chapter']), len(x)) + start_index(x) + 1
    ibn_chapter = [x['Ibn Ezra on Genesis'] for x in ibn_ezra if x['Index Title'].split()[-1].startswith(f'{i}:')]
    yahel_chapter = [x['text'] for x in yahel[start_index(yahel): end_index(yahel)]]
    karnei_chapter = [x['text'] for x in karnei[start_index(karnei): end_index(karnei)]]
    yahel_tags = [x for t in ibn_chapter for x in re.findall('data-commentator="Yahel Ohr" data-order="([א-ת]+)"', t)]
    karnei_tags = [x for t in ibn_chapter for x in re.findall('data-commentator="Karnei Ohr" data-order="([א-ת]+)"', t)]
    yahel_coms = [re.findall('^\(([א-ת]+)\)', t)[0] for t in yahel_chapter]
    karnei_coms = [re.findall('^\[([א-ת]+)\]', t)[0] for t in karnei_chapter]

    if len(yahel_tags) != len(yahel_coms):
        print(f'chapter {i} has {len(yahel_tags)} yahel tags but {len(yahel_coms)} segments')
    if len(karnei_tags) != len(karnei_coms):
        print(f'chapter {i} has {len(karnei_tags)} karnei tags but {len(karnei_coms)} segments')
    for j, k in zip(yahel_tags, yahel_coms):
        if j!= k:
            print(i, j, k)
    for j, k in zip(karnei_tags, karnei_coms):
        if j!= k:
            print(i, j, k)
    # for letters, name in [(yahel_tags, 'Yahel Ohr tags in Ibn Ezra'), (karnei_tags, 'Karnei Ohr tags in Ibn Ezra'), (yahel_coms, 'Yahel Ohr'), (karnei_coms, 'Karnei Ohr')]:
    #     check_sequnce(letters, name)

with open('report.txt', 'w') as fp:
    fp.write('\n'.join(report))
