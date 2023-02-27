import django
django.setup()
from sefaria.model import *
import json
import re
import copy
from sources.functions import post_index, post_text

server = 'http://localhost:9000'
index = post_index({'title': 'Zohar TNNG'}, method='GET', server=server)
index['schema']['nodes'] = [index['schema']['nodes'][0]] + [node for chumash in index['schema']['nodes'][1:-1] for node in chumash['nodes']] + [index['schema']['nodes'][-1]]
index['alt_structs']['Maamar']['nodes'] = [index['alt_structs']['Maamar']['nodes'][0]] + [node for chumash in index['alt_structs']['Maamar']['nodes'][1:-1] for node in chumash['nodes']] + [index['alt_structs']['Maamar']['nodes'][-1]]
for i in range(3):
    for node in index['alt_structs']['Maamar']['nodes'][-1]['nodes'][i]['nodes']:
        node['refs'] = [r.normal() for r in Ref(node['wholeRef']).all_segment_refs()]
        start = int(node['refs'][0].split(':')[-1])
        if start != 1:
            node['startingAddress'] = start
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    index['alt_structs']['Pages']['nodes'] = [
    {'titles':  [
                        {
                            "primary" : True,
                            "lang" : "en",
                            "text" : "Volume I"
                        },
                        {
                            "primary" : True,
                            "lang" : "he",
                            "text" : "כרך א"
                        }
                    ],
    'nodes' : [index['alt_structs']['Pages']['nodes'][0]] + index['alt_structs']['Pages']['nodes'][1]['nodes'],
    },
    {'titles': [
        {
            "primary": True,
            "lang": "en",
            "text": "Volume II"
        },
        {
            "primary": True,
            "lang": "he",
            "text": "כרך ב"
        }
    ],
        'nodes': index['alt_structs']['Pages']['nodes'][2]['nodes'],
    },
    {'titles': [
        {
            "primary": True,
            "lang": "en",
            "text": "Volume III"
        },
        {
            "primary": True,
            "lang": "he",
            "text": "כרך ג"
        }],
        'nodes': [node for chumash in index['alt_structs']['Pages']['nodes'][3:] for node in chumash['nodes']]
    }
]
index = json.dumps(index)
index = re.sub('TNNG(?:, (?:Genesis|Exodus|Leviticus|Numbers|Deuteronomy))?', 'TNNNG', index)
index = json.loads(index)
index['schema']['titles'][0]['text'] = 'זוהר הדור הבא הבא הבא'
# post_index(index, server=server)

for version in VersionSet({'title': 'Zohar TNNG'}):
    new = version.contents()
    new['title'] = 'Zohar TNNNG'
    new['chapter'] = {'Introduction': version.chapter['Introduction']}
    for chumash in ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']:
        for parasha in version.chapter[chumash]:
            new['chapter'][parasha] = version.chapter[chumash][parasha]
    new['chapter']['Addenda'] = version.chapter['Addenda']
    v = Version(new)
    v.save()
