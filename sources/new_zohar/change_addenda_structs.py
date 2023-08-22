import django
django.setup()
from sefaria.model import *
import csv
from sefaria.utils.hebrew import gematria
from sources.functions import post_index

mapping = {}
with open('addenda_pages.csv') as fp:
    data = list(csv.DictReader(fp))
for row in data:
    if row['siman']:
        siman = gematria(row['siman']) - 160
    seg = row['ref'].split(':')[1]
    mapping[row['ref']] = f'{siman}:{seg}'

def get_new_raw_ref(ref):
    refs = Ref(ref).all_segment_refs()
    first = refs[0].normal().replace(', Volume', ', For Volume').replace(' TNNNG', '')
    last = refs[-1].normal().replace(', Volume', ', For Volume').replace(' TNNNG', '')
    return f'{" ".join(ref.split()[:-1])} {mapping[first]}-{mapping[last]}'.replace(' For', '').replace('Zohar,', 'Zohar TNNNG,')

# index = post_index({'title': 'Zohar TNNNG'}, 'https://zohar.cauldron.sefaria.org', 'GET')
# daf = [n['nodes'][-1] for n in post_index({'title': 'Zohar TNNNG'}, 'http://localhost:9000', 'GET')['alt_structs']['Daf']['nodes']]
# for v, vol in enumerate(daf):
#     snode = index['schema']['nodes'][-1]['nodes'][v]
#     snode['sectionNames'][0] = 'Siman'
#     snode['index_offsets_by_depth']['2'] = []
#     for node in vol['nodes']:
#         snode['index_offsets_by_depth']['2'].append(int(node['wholeRef'].split('-')[0].split(':')[1])-1)
#         node['wholeRef'] = get_new_raw_ref(node['wholeRef'])
#         node['refs'] = [get_new_raw_ref(ref) for ref in node['refs']]
#     index['alt_structs']['Daf']['nodes'][v]['nodes'].append(vol)
#
# essay = [n for ns in index['alt_structs']['Essay']['nodes'][-1]['nodes'] for n in ns['nodes']]
# for node in essay:
#     node['wholeRef'] = get_new_raw_ref(node['wholeRef'])
#     node['refs'] = [get_new_raw_ref(ref) for ref in node['refs']]
#
server = 'http://localhost:9000'
# post_index(index, server=server)

index = post_index({'title': 'Zohar TNNNG'}, 'http://localhost:9000', 'GET')
daf = [node for n in index['alt_structs']['Daf']['nodes'] for node in n['nodes'][-1]['nodes']]
essay = [n for ns in index['alt_structs']['Essay']['nodes'][-1]['nodes'] for n in ns['nodes']]
for node in daf + essay:
    node['refs'] = [Ref(ref).normal() for ref in node['refs']]
    node['wholeRef'] = Ref(node['wholeRef']).normal()
post_index(index, server=server)


