import django
django.setup()
from sefaria.model import *
import csv
import re
from sefaria.utils.hebrew import gematria
from sefaria.utils.talmud import section_to_daf, daf_to_section
from sources.functions import post_link, post_text, post_index, add_term

name = 'Ketem Paz'
zohar = 'Zohar'
title = f'{name} on {zohar}'
intro = 'Introduction'
author_intro = f"Author's {intro}"
pub_intro = f"Publisher's {intro}"
approbation = 'Approbation'
addenda = 'Addenda'
strings = {
    name: 'כתם פז',
    zohar: 'ספר הזהר',
    intro: 'הקדמה',
    author_intro: 'הקדמת המחבר',
    pub_intro: 'הקדמת המגיה',
    approbation: 'הסכמה',
    addenda: 'תוספות'
}
strings[title] = f'{strings[name]} על {strings[zohar]}'

def handle_text(string):
    for start, end in [(11, 33), (44, 55), (11, 22), (55, 22)]:
        string = re.sub(f'{start}(.*?){end}', r'<b>\1</b>', string)
    return re.sub('@|\d', '', string)

texts = {'default': []}
page = parasha = ''
parashot = {}
links = []
with open('parsed.csv') as fp:
    for row in csv.DictReader(fp):
        if not row['page']:
            subtitle = [key for key in strings if strings[key]==row['parasha']][0]
            if subtitle not in texts:
                texts[subtitle] = []
            texts[subtitle].append(handle_text(row['text']))
        elif row['page']:
            if row['page'] != page:
                page = row['page']
                segment = 0
            segment += 1
            daf, amud = row['page'].split()
            index = gematria(daf) * 2 + gematria(amud) - 73
            if row['parasha'] and row['parasha'] not in parashot:
                if parasha:
                    parashot[parasha] += f'-{last}'
                parasha = row['parasha']
                parashot[parasha] = f'{title} {section_to_daf(index+1)}:{segment}'
            last = f'{section_to_daf(index+1)}:{segment}'
            ref = f'{title} {last}'
            if len(texts['default']) < index + 1:
                texts['default'] += [[] for _ in range(index+1-len(texts['default']))]
            texts['default'][index].append(handle_text(row['text']))
        if row['ref']:
            links.append({
                'refs': [ref, row['ref']],
                'auto': True,
                'type': 'commentary',
                'generated_by': 'ketem paz parser'
            })
    parashot[parasha] += f'-{last}'

schema = SchemaNode()
schema.add_primary_titles(title, strings[title])
nodes = []
alts = {'Parasha': {'nodes': nodes}}
for subtitle in [approbation, pub_intro, author_intro]:
    node = JaggedArrayNode()
    node.add_primary_titles(subtitle, strings[subtitle])
    node.sectionNames = ['Paragraph']
    node.addressTypes = ['Integer']
    node.depth = 1
    schema.append(node)
    nodes.append({
        'nodeType': "ArrayMapNode",
        'depth': 0,
        'wholeRef': f'{title}, {subtitle}',
        'addressTypes': [
            "Integer"
        ],
        'sectionNames': [
            "Paragraph"
        ],
        'titles': [
            {
                'primary': True,
                'lang': "en",
                'text': subtitle
            },
            {
                'primary': True,
                'lang': "he",
                'text': strings[subtitle]
            }
        ]
    })
node = JaggedArrayNode()
node.depth = 2
node.key = 'default'
node.default = True
node.sectionNames = ['Daf', 'Paragraph']
node.addressTypes = ['Talmud', 'Integer']
schema.append(node)
schema.validate()

for parasha in parashot:
    he_parasha = re.sub('פרשת | יעקב', '', parasha)
    if parasha == strings[intro]:
        en_parasha = intro
    elif parasha == strings[addenda]:
        en_parasha = addenda
    else:
        en_parasha = [term.get_primary_title() for term in TermSet({'category': 'Torah Portions'}) if he_parasha in term.get_titles()][0]
    nodes.append({
        'nodeType': "ArrayMapNode",
        'depth': 0,
        'wholeRef': parashot[parasha],
        'addressTypes': [
            "Talmud"
        ],
        'sectionNames': [
            "Daf"
        ],
        # 'includeSections': True,
        # 'startingAddress': str(daf_to_section(parashot[parasha].split()[-1].split(':')[0])),
        'titles': [
            {
                'primary': True,
                'lang': "en",
                'text': en_parasha
            },
            {
                'primary': True,
                'lang': "he",
                'text': he_parasha
            }
        ]
    })
    # ref = Ref(parashot[parasha])
    # d = ref._core_dict()
    # all_pages = []
    # for i in range(ref.sections[0], ref.toSections[0]+1):
    #     d['sections'] = d['toSections'] = [i]
    #     all_pages.append(Ref(_obj=d))
    # non_empties = {x.context_ref() for x in ref.all_segment_refs()}
    # if len(non_empties) > len(all_pages) / 2:
    #     nodes[-1]['skipped_addresses'] = [r.sections[0] for r in all_pages if r not in non_empties]
    # elif len(non_empties) != len(all_pages):
    #     nodes[-1]['addresses'] = [r.sections[0] for r in all_pages if r in non_empties]

server = 'https://new-shmuel.cauldron.sefaria.org'
# server = 'http://localhost:9000'
add_term(name, strings[name], server=server)

index = {
    'title': title,
    'categories': ["Kabbalah", zohar],
    'dependence': "Commentary",
    'base_text_titles': [zohar],
    'collective_title': name,
    'schema': schema.serialize(),
    'alt_structs': alts,
    # 'default_struct': "Parasha",
}
post_index(index, server=server)

for text in texts:
    sub = '' if text == 'default' else f', {text}'
    text_version = {
        'versionTitle': 'ketem',
        'versionSource': '',
        'language': 'he',
        'text': texts[text]}
    post_text(f'{title}{sub}', text_version, server=server)

post_link(links, server=server, skip_lang_check=False, VERBOSE=False)
