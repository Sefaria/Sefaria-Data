import re
import csv
import django
django.setup()
from sefaria.model import *
from sources.functions import post_index, post_text, post_link, getGematria, add_term
from sefaria.utils.talmud import section_to_daf

def hande_text(text):
    text = re.sub('@\d*', '', text)
    text = ' '.join(text.split())
    if '.' in text:
        dh, com = text.split('.', 1)
        if len(dh.split()) < 20:
            text = f'<b>{dh}</b> {com}'
    return text

def get_parasha_names(parasha):
    alts = library.get_index('Zohar TNNNG').alt_structs['Daf']['nodes']
    if parasha == 'שלח':
        parasha = 'שלח לך'
    for vol in alts:
        for node in vol['nodes']:
            if node['titles'][1]['text'] == parasha:
                return node['titles'][0]['text'], node['titles'][1]['text']
    print('not finding', parasha)

server = 'http://localhost:9000'
term = 'Mikdash Melekh'
hterm = 'מקדש מלך'
name = f'{term} on Zohar'
hname = f'{hterm} על ספר הוהר'
remezname = 'RaMaZ Commentary'
hremezname = 'פירוש הרמ"ז'
record = SchemaNode()
record.add_primary_titles(name, hname)
record.key = name
node = JaggedArrayNode()
node.default = True
node.key = 'default'
node.depth = 3
node.add_structure(['Volume', 'Daf', 'Paragraph'])
node.addressTypes = ['Volume', 'Talmud', 'Integer']
record.append(node)
node = JaggedArrayNode()
node.add_primary_titles(remezname, hremezname)
node.depth = 3
node.add_structure(['Volume', 'Daf', 'Paragraph'])
node.addressTypes = ['Volume', 'Talmud', 'Integer']
record.append(node)

defa = [[[]]]
remez = [[[]]]
links = []
parashot_def = []
parashot_remez = []
text = defa
with open('mikdash links.csv') as fp:
    data = csv.DictReader(fp)

    for row in data:
        ends = []
        for text in [defa, remez]:
            part = len(text)
            daf = len(text[part-1])
            par = len(text[part-1][daf-1])
            end = f'{part}:{section_to_daf(daf)}:{par}'
            ends.append(end)

        if row['parasha'] and row['parasha'] in ['ויקרא', 'שמות']:
            defa.append([[]])
            remez.append([[]])

        if row['page']:
            page = row['page']
            page = getGematria(page.split()[0]) * 2 + getGematria(page.split()[1]) - 72

        text = remez if row['clue'] else defa
        text[-1] += [[] for _ in range(page - len(text[-1]))]

        starts = []
        for t in [defa, remez]:
            part = len(t)
            daf = len(t[part-1])
            par = len(t[part-1][daf-1]) + 1
            start = f'{part}:{section_to_daf(daf)}:{par}'
            starts.append(start)

        node = f', {remezname}' if row['clue'] else ''
        parashot = parashot_remez if row['clue'] else parashot_def
        segment = starts[1] if row['clue'] else starts[0]

        if row['parasha']:
            for i, parashot in enumerate([parashot_def, parashot_remez]):
                if parashot:
                    parashot[-1]['end'] = ends[i]
                parashot.append({'name': row['parasha'], 'start': starts[i]})

        if row['base ref']:
            links.append({
                'refs': [f'{name}{node} {segment}', row['base ref'].replace(' TNNNG', '')],
                'auto': True,
                'type': 'commentary',
                'generated_by': 'mikdash melekh parser'
            })

        text[-1][page-1].append(hande_text(row['text']))

for parashot, text in zip([parashot_def, parashot_remez], [defa, remez]):
    part = len(text)
    daf = len(text[part - 1])
    par = len(text[part - 1][daf - 1])
    end = f'{part}:{section_to_daf(daf)}:{par}'
    parashot[-1]['end'] = end

index_dict = {'title': name,
              'categories': ['Kabbalah', 'Zohar'],
              'schema': record.serialize(),
              'dependence': "Commentary",
              'base_text_titles': ["Zohar"],
              'collective_title': term}

add_term(term, hterm, server=server)
post_index(index_dict, server=server)
text_version = {
    'versionTitle': 'Zholkva, 1864',
    'versionSource': 'https://www.nli.org.il/he/books/NNL_ALEPH990018376830205171/NLI',
    'language': 'he',
    'text': defa}
post_text(name, text_version, server=server, index_count='on')
text_version['text'] = remez
post_text(f'{name}, {remezname}', text_version, server=server, index_count='on')

nodes = []
for parasha in parashot_def:
    print(parasha)
    ref = f'{name} {parasha["start"]}-{parasha["end"]}'
    try:
        ref = Ref(ref).normal()
    except:
        print('problem with:', parasha)
        continue
    titles = get_parasha_names(parasha['name'])
    nodes.append({
        'nodeType': 'ArrayMapNode',
        'depth': 0,
        'wholeRef': ref,
        'addressTypes': ['Talmud'],
        'sectionNames': ['Daf'],
        'startingAddress': parasha["start"].split(':')[0],
        'titles': [{'primary': True, 'lang': 'en', 'text': titles[0]}, {'primary': True, 'lang': 'he', 'text': titles[1]}]
    })
nodes.append({
    'nodes': [],
    'titles': [{'primary': True, 'lang': 'en', 'text': remezname}, {'primary': True, 'lang': 'he', 'text': hremezname}]
})
for parasha in parashot_remez:
    print(parasha)
    ref = f'{name}, {remezname} {parasha["start"]}-{parasha["end"]}'
    try:
        ref = Ref(ref).normal()
    except:
        print('problem with:', parasha)
        continue
    titles = get_parasha_names(parasha['name'])
    nodes[-1]['nodes'].append({
        'nodeType': 'ArrayMapNode',
        'depth': 0,
        'wholeRef': ref,
        'addressTypes': ['Talmud'],
        'sectionNames': ['Daf'],
        'startingAddress': parasha["start"].split(':')[0],
        'titles': [{'primary': True, 'lang': 'en', 'text': titles[0]}, {'primary': True, 'lang': 'he', 'text': titles[1]}]
    })


index_dict = {'title': name,
              'categories': ['Kabbalah', 'Zohar'],
              'schema': record.serialize(),
              'default_struct': 'Parasha',
              'alt_structs': {'Parasha': {'nodes': nodes}},
              'dependence': "Commentary",
              'base_text_titles': ["Zohar"],
              'collective_title': term}
post_index(index_dict, server=server)

post_link(links, server=server, skip_lang_check=True, VERBOSE=False)
