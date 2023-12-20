import csv
import re
import django
django.setup()
from sefaria.model import *
from sources.functions import post_index, post_link
from collections import defaultdict
from sefaria.utils.hebrew import encode_hebrew_numeral

index = post_index({'title': 'Mekhilta DeRabbi Yishmael'}, method='GET', server='https://piaseczno.cauldron.sefaria.org')
with open('/Users/yishaiglasner/Downloads/makhilta-exodus-mapping updated - makhilta-exodus-mapping.csv') as fp:
    data = list(csv.DictReader(fp))

d = defaultdict(lambda: [])
for row in data:
    ex, mek = row['exodus'], row['mekhilta']
    d[ex].append(mek)
d = {k: Ref(f'{v[0]}-{v[-1]}').normal() for k, v in d.items()}
chapters = [re.findall('Exodus (\d*):', ex)[0] for ex in d]
new = {}
for ch in chapters:
    if ch not in new:
        new[ch] = [(re.findall(':(\d*)(?:$|\-)', k)[0], d[k]) for k in d if re.search(f'Exodus {ch}:', k)]
nodes = []
links = []
for ch in new:
    for r in new[ch]:
        links.append({
            'refs': [f'Malbim on Exodus {ch}:{r[0]}', r[1].replace(' Beeri', '')],
            'auto': True,
            'type': 'commentary',
            'generated_by': 'new malbim mekhilta linker'
        })
    node = {
        'nodeType': "ArrayMapNode",
        'depth': 1,
        'addressTypes': ['Integer'],
        'sectionNames': ['Verse'],
        'refs': [x[1].replace(' Beeri', '') for x in new[ch]],
        'titles': [
            {
                'primary': True,
                'text': f"Chapter {ch}",
                'lang': "en"
            },
            {
                'primary': True,
                'text': f"פרק {encode_hebrew_numeral(int(ch))}",
                'lang': "he"
            }
        ]
    }
    try:
        node['wholeRef'] = Ref(f'{Ref(new[ch][0][1]).all_segment_refs()[0]}-{Ref(new[ch][-1][1]).all_segment_refs()[-1]}').normal().replace(' Beeri', '')
    except:
        node['wholeRef'] = Ref(f'{Ref(new[ch][0][1]).all_segment_refs()[0]}-{Ref(" ".join(new[ch][0][1].split()[:-1])).all_segment_refs()[-1]}').normal().replace(' Beeri', '')
    verses = [int(x[0]) for x in new[ch]]
    if verses[0] != 1:
        node['startingAddress'] = str(verses[0])
    if any(v not in verses for v in range(verses[0], verses[-1])):
        missings = [v for v in range(verses[0], verses[-1]) if v not in verses]
        if len(verses) > len(missings):
            node['skipped_addresses'] = missings
        else:
            node['addresses'] = verses
    nodes.append(node)
index['alt_structs'] = {'Chapter': {'nodes': nodes}}
post_index(index,  server='https://piaseczno.cauldron.sefaria.org')
post_link(links, server='https://piaseczno.cauldron.sefaria.org')
