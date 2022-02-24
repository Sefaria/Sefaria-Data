import django
django.setup()
from sefaria.model import *
import csv
import re
from functools import reduce
import copy
from sources.functions import post_text
import os

RES = {row['from']: row['to'] for row in csv.DictReader(open('res.csv', encoding='utf-8', newline=''))}

def handle_text(text):
    for k, v in RES.items():
        text = re.sub(k, v, text)
    return text

def assign(array, inds, element):
    for i in range(len(inds)):
        to_add = reduce(lambda a, b: [a], inds[i+1:], '')
        try:
            reduce(lambda a, b: a[b], inds[:i+1], array)
        except IndexError:
            sub = reduce(lambda a, b: a[b], inds[:i], array)
            sub += [copy.deepcopy(to_add) for _ in range(1 + inds[i] - len(sub))]
    reduce(lambda a, b: a[b], inds[:-1], array)[inds[-1]] = element
    return array

def text_from_file(file):
    text_array = []
    with open(f'Yerushalmi Fr Footnotes/{file}', encoding='utf-8', newline='') as fp:
        r = csv.DictReader(fp)
        data = list(r)
        first = r.fieldnames[0]
    for row in data:
        text = handle_text(row['Schwab_fr'])
        indexes = [int(x) - 1 for x in row[first].split()[-1].split('-')[0].split(':')]
        try:
            if text_array[indexes[0]][indexes[1]][indexes[2]]:
                text_array[indexes[0]][indexes[1]].append(text)
            else:
                text_array[indexes[0]][indexes[1]][indexes[2]] = text
        except IndexError:
            assign(text_array, indexes, text)
    return text_array

def post(mas, server):
    try:
        file = [f for f in os.listdir('Yerushalmi Fr Footnotes') if mas.replace(" ", "_") in f][0]
    except IndexError:
        print('no file')
        return
    text = text_from_file(file)
    text_version = {
        'versionTitle': 'Le Talmud de Jérusalem, traduit par Moise Schwab, 1878-1890 [fr]',
        'versionSource': "https://www.nli.org.il/he/books/NNL_ALEPH002182155/NLI",
        'language': 'en',
        'text': text
    }
    title = f'Jerusalem Talmud {mas}'
    post_text(title, text_version, server=server, index_count='on')

if __name__ == '__main__':
    server = 'http://localhost:9000'
    #server = 'https://jt4.cauldron.sefaria.org'
    mases = [m.replace('Jerusalem Talmud ', '') for m in library.get_indexes_in_category('Yerushalmi')]
    for mas in mases:
        print(mas)
        post(mas, server)
