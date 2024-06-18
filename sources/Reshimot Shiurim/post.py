import csv
import re
import django
django.setup()
from sefaria.model import *
from sources.functions import post_text, post_link
from sefaria.utils.hebrew import gematria
from sefaria.utils.talmud import section_to_daf

title = 'Reshimot Shiurim'
server = 'http://localhost:8000'
server = 'https://ahs-yomi.cauldron.sefaria.org'

for masechet in ['Sanhedrin', 'Horayot']:
    with open(f'{title} {masechet}.csv') as fp:
        data = list(csv.DictReader(fp))

    book = f'{title} on {masechet}'
    if masechet == 'Sanhedrin':
        nodes = {'Introduction': [], 'Foreword': [], 'data': [], 'Appendix; Commentary on Hilkhot Melakhim': []}
        current = 'Introduction'
        for row in data:
            if row['part'] == 'פרק דיני ממונות בשלשה':
                current = 'data'
            elif row['part'] == 'דברים אחדים':
                current = 'Foreword'
            elif row['part'] == 'נספח; שיעורי רבינו על הלכות מלכים':
                current = 'Appendix; Commentary on Hilkhot Melakhim'
            nodes[current].append(row)
        for key in nodes:
            if key == 'data':
                continue
            version = {
                'versionTitle': 'Reshimot Shiurim, Kiddushin, New York, 2022',
                'versionSource': 'https://www.nli.org.il/he/books/NNL_ALEPH990034821070205171/NLI',
                'language': 'he',
                'text': [row['text'] for row in nodes[key]]
            }
            # post_text(f'{book}, {key}', version, server=server)

        data = nodes['data']

    links, text = [], []
    for r, row in enumerate(data):
        if row['page']:
            daf_string = re.sub('ד[ףך]', '', row['page']).split('-')[0]
            daf = gematria(daf_string)
            amud = 2 if daf_string.endswith(':') else 1
            page = daf * 2 + amud - 2
            if len(text) > page:
                print('going reverse', row, len(text), page)
            text += [[] for _ in range(page-len(text))]
        text[-1].append(row['text'])
        length = 0
        for line in data[r+1:]:
            if line['base ref'] or line ['page'] or line['part']:
                break
            length += 1
        ref = Ref(f'{book} {section_to_daf(len(text))}:{len(text[-1])}-{len(text[-1])+length}').normal()
        if row['base ref']:
            links.append({
                'auto': True,
                'type': 'commentary',
                'generated_by': 'reshimot shiurim sanhedrin and horayot',
                'refs': [row['base ref'], ref]
            })
        if 'Rashi' in row['base ref'] or 'Tosafot' in row['base ref']:
            base_ref = ':'.join(row['base ref'].split(' on ')[1].split(':')[:-1])
            links.append({
                'auto': True,
                'type': 'commentary',
                'generated_by': 'reshimot shiurim sanhedrin and horayot',
                'refs': [base_ref, ref]
            })

    print(len(links))
    version['text'] = text
    # post_text(book, version, server=server)
    post_link(links, server=server, VERBOSE=False, skip_lang_check=False)


