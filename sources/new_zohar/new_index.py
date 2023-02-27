import json
import re
import django
import csv
django.setup()
from sefaria.model import *
from sources.functions import post_index

server = 'http://localhost:9000'
NAME = 'Zohar TNNG'
PARASHA_OLD_TO_NEW = {}
CHUMASH_TO_NEW = {1: ('Introduction', 0)}
for i in range(2, 14):
    CHUMASH_TO_NEW[i] = ('Genesis', 1)
for i in range(14, 26):
    CHUMASH_TO_NEW[i] = ('Exodus', 2)
for i in range(26, 36):
    CHUMASH_TO_NEW[i] = ('Leviticus', 3)
for i in range(36, 46):
    CHUMASH_TO_NEW[i] = ('Numbers', 4)
for i in range(46, 53):
    CHUMASH_TO_NEW[i] = ('Dueteronomy', 5)
for i in range(53, 56):
    CHUMASH_TO_NEW[i] = ('Addenda', 6)
hname = 'זוהר הדור הבא הבא'
record = SchemaNode()
record.add_primary_titles(NAME, hname)


def parasha_node(parasha_alt_node, address=''):
    node = JaggedArrayNode()
    node.add_primary_titles(parasha_alt_node['titles'][0]['text'], parasha_alt_node['titles'][1]['text'])
    node.add_structure(['Chapter', 'Paragraph'])
    node.addressTypes = ['Integer', 'Integer']
    node.depth = 2
    skip = 0
    skips = []
    address += f", {parasha_alt_node['titles'][0]['text']}"
    for maamar in Ref(f'{NAME}{address}').all_subrefs():
        skips.append(skip)
        skip += len(maamar.all_segment_refs())
    node.skip_nums = {'2': skips}
    return node

old = library.get_index('Zohar TNG')
x, y = 1, 1
for c, chumash in enumerate(old.alt_structs['Maamar']['nodes']):
    if c != 0:
        node = SchemaNode()
        node.add_primary_titles(chumash['titles'][0]['text'], chumash['titles'][1]['text'])
        record.append(node)
        for p, parash in enumerate(chumash['nodes']):
            sn = parasha_node(parash, f", {chumash['titles'][0]['text']}")
            node.append(sn)
            PARASHA_OLD_TO_NEW[x] = f"{chumash['titles'][0]['text']}, {parash['titles'][0]['text']}"
            x += 1
    else:
        sn = parasha_node(chumash)
        record.append(sn)
        PARASHA_OLD_TO_NEW[x] = chumash['titles'][0]['text']
        x += 1

record.toc_zoom = 1
record.validate()


def change_ref(ref):
    d = Ref(ref)._core_dict()
    parasha = d['sections'][0]
    # maamar = d['sections'][1] if len(d['sections']) > 1 else ''
    # to_parasha = d['toSections'][0]
    # to_maamar = d['toSections'][1] if len(d['toSections']) > 1 else ''
    d['sections'] = d['sections'][1:]
    d['toSections'] = d['toSections'][1:]
    d['book'] = f'Zohar TNNG, {PARASHA_OLD_TO_NEW[parasha]}'
    r = Ref(f'Zohar TNNG, {PARASHA_OLD_TO_NEW[parasha]}')
    d['index_node'] = r.index_node
    d['index'] = r.index
    return Ref(_obj=d).normal()

def change_refs(string):
    for ref in re.findall('Zohar TNG.*?"', string):
        new = change_ref(ref.replace('"', ''))
        string = re.sub(ref, f'{new}"', string)
    return string

for node in old.alt_structs['Maamar']['nodes'][6]['nodes']:
    for subnode in node['nodes']:
        subnode['refs'] = [r.normal() for r in Ref(subnode['wholeRef']).all_context_refs()]
maamar = json.dumps(old.alt_structs['Maamar'])
maamar = change_refs(maamar)
maamar = json.loads(maamar)
pages = json.dumps(old.alt_structs['Pages'])
pages = change_refs(pages)
pages = json.loads(pages)

index_dict = {'title': NAME,
              'categories': ['Kabbalah', 'Zohar'],
              'schema': record.serialize(),
              'default_struct': 'Pages',
              'alt_structs': {'Pages': pages, 'Maamar': maamar}
              }
post_index(index_dict, server=server)

def get_refs(node, parasha=''):
    if parasha == 'bla':
        parasha = node['titles'][0]['text']
    if 'nodes' in node:
        for n in node['nodes']:
            yield from get_refs(n, 'bla' if parasha==True else parasha)
    else:
        yield node['refs'], parasha

with open('zohar - zohar.csv') as fp:
    for row in csv.DictReader(fp):
        ref = row['ref']
        sections = Ref(ref).sections
        c = CHUMASH_TO_NEW[sections[0]]
        chumash = old.alt_structs['Maamar']['nodes'][c[1]]
        cname = c[0]
        parasha = PARASHA_OLD_TO_NEW[sections[0]]
        ntref = f'{NAME}, {parasha} {":".join([str(s) for s in sections[1:]])}'
        newr = Ref(ntref)
        for v in ['Sulam', 'Torat Emet', 'Hebrew Torat Emet [he]']:
            vkey = v.lower() if 'Hebrew' not in v else 'hebrew'
            tc = newr.text('he', vtitle=v)
            tc.text = row[vkey]
            tc.save()

