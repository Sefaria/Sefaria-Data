import csv
import re
import django
django.setup()
from sefaria.model import *
# from sources.functions import post_index
from sefaria.utils.hebrew import gematria

def make_alts(data):
    start = re.findall('{\d:(\d+[ab])}', data[0]['text'])[0]
    nodes = []
    for r, row in enumerate(data):
        if re.search('^{\d:(\d+[ab])}', row['text']):
            start = re.findall('^{\d:(\d+[ab])}', row['text'])[0]
        if (re.search('^{\d:(\d+[ab])}', row['text']) or row['siman']) and nodes:
            nodes[-1]['refs'][-1] = Ref(f"{nodes[-1]['refs'][-1]}-{data[r-1]['ref']}").normal()
        elif re.search('{\d:(\d+[ab])}', row['text']) and nodes:
            nodes[-1]['refs'][-1] = Ref(f"{nodes[-1]['refs'][-1]}-{row['ref']}").normal()
        if row['siman']:
            if nodes:
                nodes[-1]['wholeRef'] = Ref(f"{nodes[-1]['wholeRef']}-{data[r-1]['ref']}").normal()
            nodes.append({
                'nodeType': 'ArrayMapNode',
                'depth': 1,
                'wholeRef': row['ref'],
                'addressTypes': ['Talmud'],
                'sectionNames': ['Daf'],
                'refs': [row['ref']],
                'startingAddress': start,
                'titles': [{
                    'primary': True,
                    'lang': "en",
                    'text': f"Siman {gematria(row['siman'].split()[-1])}"
                    },
                    {
                    'primary': True,
                    'lang': "he",
                    'text': row['siman']
                }]})
        elif re.search('{\d:(\d+[ab])}', row['text']) and nodes:
            nodes[-1]['refs'].append(row['ref'])
            start = re.findall('{\d:(\d+[ab])}', row['text'])[-1]
    nodes[-1]['refs'][-1] = Ref(f"{nodes[-1]['refs'][-1]}-{row['ref']}").normal()
    nodes[-1]['wholeRef'] = Ref(f"{nodes[-1]['wholeRef']}-{row['ref']}").normal()
    return {'nodes': nodes,
            'titles': [{
                'primary': True,
                'lang': "en",
                'text': "Addenda"
            },
                {
                    'primary': True,
                    'lang': "he",
                    'text': "תוספות"
                }]
        }

if __name__ == '__main__':
    with open('addenda_pages.csv') as fp:
        data = list(csv.DictReader(fp))
    vols = [[] for _ in range(3)]
    for r, row in enumerate(data):
        if r > 0:
            if row['siman'] and row['ref'].split()[-1].split(':')[0] == data[r-1]['ref'].split()[-1].split(':')[0]:
                print(row['ref'])
        row['text'] = ' '.join(row['text'].split())
        vols[row['ref'].count('I')-1].append(row)
        tc = Ref(row['ref']).text('he', 'Sulam')
        tc.text = re.sub('{\d:(\d+[ab])} ?', r'<i data-overlay="Vilna Pages" data-value="\1"></i>', row['text'])
        # tc.save()
    # server = 'http://localhost:9000'
    # # server = 'https://zohar.cauldron.sefaria.org'
    # index = post_index({'title': 'Zohar TNNNG'}, method='GET', server=server)
    # for node in index['alt_structs']['Daf']['nodes']:
    #     node['nodes'].append(make_alts(vols.pop(0)))
    # post_index(index, server=server)

