import csv
import re
import django
django.setup()
from sefaria.model import *
from sefaria.utils.hebrew import gematria
from sefaria.utils.talmud import section_to_daf
from sources.functions import post_link, post_text, post_index, add_term

name = 'Ohr HaChamah'
hname = 'אור החמה'
title = f'{name} on Zohar'
text = []
links = []
parashot = []
remain = ''
with open('ohr for post.csv') as fp:
    for r, row in enumerate(csv.DictReader(fp)):
        if r in [0, 7084, 15092]:
            text.append([])
        if row['stream original']:
            row['text'] = f"<b>{row['stream original']}</b><br>{row['text']}"
        if row['page']:
            page = gematria(row['page'].split()[0]) * 2 + gematria(row['page'].split()[1]) - 72
            if page < len(text[-1]):
                row['text'] = f"<small>{row['page']}</small><br>{row['text']}"
            else:
                text[-1] += [[] for _ in range(page - len(text[-1]))]
        rowtext = ' '.join(row['text'].split())
        rowtext = re.sub('@\d\d( *)(.*?)( *)@\d\d', r'\1<b>\2</b>\3', rowtext)
        rowtext = re.sub('[@\d]', '', rowtext)
        rowtext = re.sub('\{ *[\[\(]?[א-ת"\*] *[\)\]] *(.*?)\}', r'<sup class="footnote-marker">*</sup><i class="footnote">\1</i>', rowtext)
        if re.search('[\{\}]', rowtext):
            print(rowtext)
        if row['text'].startswith('@88') and len(row['text']) < 23:
            remain = f'<b>{rowtext}</b><br>'
            continue
        else:
            rowtext = remain + rowtext
            remain = ''
        text[-1][-1].append(rowtext)
        ref = f'{title} {len(text)}:{section_to_daf(len(text[-1]))}:{len(text[-1][-1])}'
        if row['base ref']:
            links.append({
                'refs': [row['base ref'], ref],
                'auto': True,
                'type': 'commentary',
                'generated_by': 'ohr hachamah parser'
            })

server = 'https://new-shmuel.cauldron.sefaria.org'
server = 'http://localhost:9000'
add_term(name, hname, server=server)

subtitles = [("Author's Introduction", 'הקדמת המחבר'), ('Preface', 'הקדמה לספר')]


schema = SchemaNode()
schema.add_primary_titles(title, f'{hname} על ספר הזהר')
for subtitle in subtitles:
    node = JaggedArrayNode()
    node.add_primary_titles(*subtitle)
    node.sectionNames = ['Paragraph']
    node.addressTypes = ['Integer']
    node.depth = 1
    schema.append(node)
node = JaggedArrayNode()
node.depth = 3
node.key = 'default'
node.default = True
node.sectionNames = ['Volume', 'Daf', 'Paragraph']
node.addressTypes = ['Integer', 'Talmud', 'Integer']
schema.append(node)
schema.validate()
index = {
    'title': title,
    'categories': ["Kabbalah", 'Zohar'],
    'dependence': "Commentary",
    'base_text_titles': ['Zohar'],
    'collective_title': name,
    'schema': schema.serialize(),
}
post_index(index, server=server)

for i in range(3):
    temp = [[] for _ in range(3)]
    temp[i] = text[i]
    text_version = {
        'versionTitle': f'Ohr Hachama, Peremyshl, 1896-1898, Vol. {i+1}',
        'versionSource': 'https://www.nli.org.il/he/books/NNL_ALEPH001148825/NLI',
        'language': 'he',
        'text': temp}
    post_text(title, text_version, server=server)

post_link(links, server=server, skip_lang_check=False, VERBOSE=False)
