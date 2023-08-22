import csv
import django
django.setup()
from sefaria.model import *
from sources.functions import post_index

def make_alts(data):
    vol = 0
    start = ''
    refs = [[]]
    spages = []
    for row in data:
        newvol = row['Index Title'].count('I')

        if not newvol:
            continue
        if newvol != vol:
            spages.append(row['page'].split(':')[-1][:-1])
        if row['page']:
            if start:
                if row['with'].split(row['page'])[0].strip():
                    end = row['Index Title']
                ref = f'{start.replace("Zohar", "Zohar TNNNG").replace("For ", "")}-{end.split()[-1]}'
                Ref(ref)
                refs[-1].append(ref)
                if newvol != vol:
                    start = ''
                    refs.append([])
            start = row['Index Title']
        end = row['Index Title']

        vol = newvol

    nodes = []
    for i, ref in enumerate(refs):
        nodes.append({
            'nodeType': 'ArrayMapNode',
            'depth': 1,
            'wholeRef': f'Zohar TNNNG, Addenda, Volume {"I"*(i+1)}',
            'addressTypes': ['Talmud'],
            'sectionNames': ['Daf'],
            'refs': refs[i],
            'startingAddress': spages[i],
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
        })
    # for node in nodes:
    #     print(node)
    return nodes

if __name__ == '__main__':
    with open('/home/yishai/Downloads/Zohar - he - Sulam - New.csv') as fp:
        data = list(csv.DictReader(fp))
    nodes = make_alts(data)
    server = 'http://localhost:9000'
    index = post_index({'title': 'Zohar TNNNG'}, method='GET', server=server)
    for node in index['alt_structs']['Daf']['nodes']:
        node['nodes'].append(nodes.pop(0))
    # print(index['alt_structs']['Daf'])
    post_index(index, server=server)
