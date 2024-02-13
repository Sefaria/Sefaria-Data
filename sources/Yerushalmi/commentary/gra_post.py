import django
django.setup()
import csv
from sources.functions import add_category, post_text, post_index
from sefaria.model import *
import re

with open('gra.csv') as fp:
    data = list(csv.DictReader(fp))
data.sort(key=lambda row: bool(re.search('כתב יד (?:ב|2)', row['file'])) + bool(re.search('נוסח אחר', row['file'])))

mases = {}
ky_for_mas = {}
for row in data:
    mas = row['masechet']
    if mas not in mases:
        mases[mas] = []
        ky_for_mas[mas] = {}
    kitvei_yad = ky_for_mas[mas]
    text = mases[mas]

    ref = row['base text ref']
    perek, halakha, seg = ref.split()[-1].split('-')[0].split(':')
    perek, halakha, seg = int(perek), int(halakha), int(seg)
    if len(text) < perek:
        text += [[] for _ in range(perek - len(text))]
    if len(text[perek-1]) < halakha:
        text[perek-1] += [[] for _ in range(halakha - len(text[perek-1]))]
    if len(text[perek-1][halakha-1]) < seg:
        text[perek-1][halakha-1] += [[] for _ in range(seg - len(text[perek-1][halakha-1]))]

    comment = row['comment']
    file = re.sub('(שביעית|תרומות|מעשרות)\.', r'\1 כתב יד א.', row['file'])
    if 'כתב יד' in file:
        if (perek, halakha, seg) not in kitvei_yad:
            kitvei_yad[(perek, halakha, seg)] = []
        title = re.findall('כתב יד[^\.]*', file)[0].replace('1', 'א').replace('2', 'ב')
        if title not in kitvei_yad[(perek, halakha, seg)]:
            #add title
            kitvei_yad[(perek, halakha, seg)].append(title)
            comment = f'<b>{title}</b><br>{comment}'

    text[perek-1][halakha-1][seg-1].append(comment)

server = 'http://localhost:8000'
server = 'https://new-shmuel.cauldron.sefaria.org'

com = 'Beur HaGra'
categories = ["Talmud", "Yerushalmi", "Commentary", com]
add_category(com, categories, server=server)

for mas in mases:
    base_title = f'Jerusalem Talmud {mas}'
    title = f'{com} on {base_title}'
    base_index = library.get_index(base_title)
    he_base = base_index.get_title('he')
    record = JaggedArrayNode()
    record.add_primary_titles(title, f'ביאור הגר"א על {he_base}')
    record.add_structure(['Chapter', 'Halakhah', 'Segment', 'Comment'])
    record.addressTypes = ['Perek', 'Halakhah', 'Integer', 'Integer']
    record.toc_zoom = 2
    record.validate()
    index_dict = {'collective_title': com,
                  'title': title,
                  'categories': categories,
                  'schema': record.serialize(),
                  'dependence': 'Commentary',
                  'base_text_titles': [base_title],
                  'base_text_mapping': 'many_to_one',
                  'order': base_index.order
                  }
    post_index(index_dict, server=server)

    text_version = {
        'versionTitle': f'Piotrków, 1898-1900',
        'versionSource': "https://www.nli.org.il/he/books/NNL_ALEPH001886777/NLI",
        'language': 'he',
        'text': mases[mas],
    }
    post_text(title, text_version, server=server, index_count='on')

