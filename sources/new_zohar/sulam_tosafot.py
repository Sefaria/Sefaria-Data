import re
import requests
from bs4 import BeautifulSoup
import django
django.setup()
from sefaria.model import *
from sefaria.utils.hebrew import encode_small_hebrew_numeral
from sources.functions import getGematria, post_index, post_text

name = 'Zohar TNG'
node_num = 53
lengths = [391, 241, 251]
text = [[] for _ in range(node_num-1)]
maamarim = []
nodes = []
for i in range(1, 4):
    part = encode_small_hebrew_numeral(i)
    text.append([])
    nodes.append({'nodes': [],
                  'titles': [{'primary': True,
                                'lang': "en",
                                'text': f'For Volume {"I"*i}'},
                                {'primary': True,
                                'lang': "he",
                                'text': f'כרך {part}'}]})

    for j in range(1, lengths[i-1]+1):
        ot = encode_small_hebrew_numeral(j).replace('יה', 'טו').replace('יו', 'טז')
        # print(ot)
        with open(f'sulam/תוספות {part}/אות {ot}.html') as fp:
            soup = BeautifulSoup(fp.read(), 'html.parser')

        maamar = soup.ul.li.string
        maamar = re.findall('מאמר,? (.*?)$|(מעשה .*?)$', maamar)[0]
        maamar = [x for x in maamar if x][0]
        maamar = ' '.join(maamar.split()[:-1])
        if maamarim and maamar == maamarim[-1]:
            pass
        else:
            maamarim.append(maamar)
            m = len(nodes[-1]['nodes']) + 1
            nodes[-1]['nodes'].append({'nodeType': "ArrayMapNode",
                        'depth': 1,
                        'wholeRef': f"{name} {node_num+i-1}:{m}",
                        'addressTypes': ['Integer'],
                        'sectionNames': ['Paragraph'],
                        'refs': [x.normal() for x in Ref(f"{name} {node_num+i-1}:{m}").all_segment_refs() if x.text('he').text],
                        'titles': [{'primary': True,
                                    'lang': "en",
                                    'text': str(m)},
                                    {'primary': True,
                                    'lang': "he",
                                    'text': maamar}]})
            text[-1].append([])

        seg = soup.find('div', class_='text_data_1')
        seg.h3.decompose()
        seg = re.sub('<[^>]*>', '', str(seg))
        seg = ' '.join(seg.split())
        seg = re.sub(f'^{ot}\) *', '', seg)
        text[-1][-1].append(seg)

text_version = {'title': name,
                'versionTitle': f'Sulam, Tosafot',
                'versionSource': "",
                'language': 'he',
                'text': text
                }
server = 'http://localhost:9000'
post_text(name, text_version, server=server)

par_nodes = [{'nodeType': "ArrayMapNode",
                        'depth': 1,
                        'wholeRef': f"{name} {node_num}",
                        'addressTypes': ['Integer'],
                        'sectionNames': ['Paragraph'],
                        'refs': [x.normal() for x in Ref(f"{name} {node_num+i-1}").all_segment_refs() if x.text('he').text],
                        'titles': [{'primary': True,
                                'lang': "en",
                                'text': f'For Volume {"I"*i}'},
                                {'primary': True,
                                'lang': "he",
                                'text': f'לכרך {encode_small_hebrew_numeral(i)}'}]} for i in range(1, 4)]
index = requests.get('http://localhost:9000/api/v2/raw/index/Zohar_TNG').json()
index['alt_structs']['Maamar']['nodes'].append({'nodes': nodes,
                                             'titles': [{'primary': True,
                                                         'lang': "en",
                                                         'text': f'Addenda'},
                                                        {'primary': True,
                                                         'lang': "he",
                                                         'text': f'תוספות'}]})
index['alt_structs']['Paragraph']['nodes'].append({'nodes': par_nodes,
                                             'titles': [{'primary': True,
                                                         'lang': "en",
                                                         'text': f'Addenda'},
                                                        {'primary': True,
                                                         'lang': "he",
                                                         'text': f'תוספות'}]})
print(par_nodes[0])
post_index(index, server=server)
