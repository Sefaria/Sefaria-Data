import json
import re
import django
import csv
django.setup()
from sefaria.model import *
from sources.functions import post_index

server = 'http://localhost:9000'
# server = 'https://bdb.cauldron.sefaria.org'
NAME = 'Zohar TNNG'
PARASHA_OLD_TO_NEW = {}
MAAMAR_OLD_TO_NEW = {}
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

def maamar_nodes(parasha_alt_node, address, node):
    global NAME, PARASHA_OLD_TO_NEW, x, y
    skip = 0
    for m, maamar in enumerate(parasha_alt_node['nodes']):
        sn = JaggedArrayNode()
        sn.add_primary_titles(f"Maamar {maamar['titles'][0]['text']}", maamar['titles'][1]['text'])
        sn.add_structure(['Paragraph'])
        sn.addressTypes = ['Integer']
        sn.depth = 1
        # if skip != 0:
            # sn.offset = skip
        skip += len(Ref(f"Zohar TNG {m+1}").all_subrefs())
        node.append(sn)

        MAAMAR_OLD_TO_NEW[(x, y)] = maamar['titles'][0]['text']
        y += 1

def parasha_node(parasha_alt_node, address=''):
    global y
    y = 1
    node = SchemaNode()
    node.add_primary_titles(parasha_alt_node['titles'][0]['text'], parasha_alt_node['titles'][1]['text'])
    subaddress = address + parasha_alt_node['titles'][0]['text']
    maamar_nodes(parasha_alt_node, subaddress, node)
    return node

old = library.get_index('Zohar TNG')
x, y = 1, 1
for c, chumash in enumerate(old.alt_structs['Maamar']['nodes']):
    if c != 0:
        node = SchemaNode()
        node.add_primary_titles(chumash['titles'][0]['text'], chumash['titles'][1]['text'])
        record.append(node)
        for p, parash in enumerate(chumash['nodes']):
            sn = parasha_node(parash, f"{chumash['titles'][0]['text']}, ")
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
    maamar = d['sections'][1] if len(d['sections']) > 1 else ''
    to_parasha = d['toSections'][0]
    to_maamar = d['toSections'][1] if len(d['toSections']) > 1 else ''
    d['sections'] = d['sections'][-1] if len(d['sections']) > 2 else []
    d['toSections'] = d['toSections'][-1] if len(d['toSections']) > 2 else []
    d['toSections'] =  d['sections']
    d['book'] = f'Zohar TNNG, {PARASHA_OLD_TO_NEW[parasha]}{MAAMAR_OLD_TO_NEW[(parasha, maamar)]}'
    r = Ref(f'Zohar TNNG, {PARASHA_OLD_TO_NEW[parasha]}')
    d['index_node'] = r.index_node
    d['index'] = r.index
    return Ref(_obj=d).normal()

def change_refs(string):
    for ref in re.findall('Zohar TNG.*?"', string):
        new = change_ref(ref.replace('"', ''))
        string = re.sub(ref, f'{new}"', string)
    return string

# for node in old.alt_structs['Maamar']['nodes'][6]['nodes']:
#     for subnode in node['nodes']:
#         subnode['refs'] = [r.normal() for r in Ref(subnode['wholeRef']).all_context_refs()]
# maamar = json.dumps(old.alt_structs['Maamar'])
# maamar = change_refs(maamar)
# maamar = json.loads(maamar)

#temp #
# pages = json.dumps(old.alt_structs['Pages'])
# pages = change_refs(pages)
# pages = json.loads(pages)

index_dict = {'title': NAME,
              'categories': ['Kabbalah', 'Zohar'],
              'schema': record.serialize(),
              'default_struct': 'Pages',
              # 'alt_structs': {'Pages': pages}
              }
# post_index(index_dict, server=server)

def get_refs(node, parasha=''):
    if parasha == 'bla':
        parasha = node['titles'][0]['text']
    if 'nodes' in node:
        for n in node['nodes']:
            yield from get_refs(n, 'bla' if parasha==True else parasha)
    else:
        yield node['refs'], parasha

# for c, chumash in enumerate(old.alt_structs['Maamar']['nodes']):
#     cname = chumash['titles'][0]['text']
#     for refs, parasha in get_refs(chumash, c != 0):
#         parasha = f', {parasha}' if parasha else ''
#         for ref in refs:
with open('zohar - zohar.csv') as fp:
    for row in csv.DictReader(fp):
        ref = row['ref']
        sections = Ref(ref).sections
        maamar = MAAMAR_OLD_TO_NEW[tuple(sections[:-1])]
        c = CHUMASH_TO_NEW[sections[0]]
        chumash = old.alt_structs['Maamar']['nodes'][c[1]]
        cname = c[0]
        parasha = PARASHA_OLD_TO_NEW[sections[0]]
        print(ref, f'{NAME}, {parasha}, Maamar {maamar} {Ref(ref).sections[-1]}')
        newr = Ref(f'{NAME}, {parasha}, Maamar {maamar} {Ref(ref).sections[-1]}')
        for v in ['Sulam', 'Torat Emet', 'Hebrew Torat Emet [he]']:
            vkey = v.lower() if 'Hebrew' not in v else 'hebrew'
            tc = newr.text('he', vtitle=v)
            tc.text = row[vkey]
            tc.save()
