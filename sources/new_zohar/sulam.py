import re
import sys
import copy
import time
from collections import OrderedDict
import django
django.setup()
from sefaria.model import *
from sources.functions import getGematria, post_index, post_text

text = []
parashot = OrderedDict()
old = 0
for chumash in ['הקדמה', 'בראשית', 'שמות', 'ויקרא', 'במדבר', 'דברים']:
    print(chumash)
    parashot[chumash] = OrderedDict()
    with open(f'sulam/{chumash}.txt') as fp:
        data = fp.readlines()

    newdata = []
    for line in data:
        line = re.sub('[﻿]', '', line)
        line = ' '.join(line.split())
        if not line:
            newdata.append(line)
            continue
        if re.search('^זוהר מהדורת הסולם -', line):
            parasha = re.findall('^זוהר מהדורת הסולם - (.*?) מאמר', line)
            if parasha:
                maamar = re.findall('מאמר(.*)$', line)[0]
                if parasha == ['הקדמה']:
                    parasha = 'הקדמה'
                else:
                    parasha = parasha[0].split(None, 1)[1].replace('פרשת', '').strip()
                if 'בראשית' in parasha:
                    parasha = 'בראשית'
                if ' - המשך' in parasha:
                    parasha = parasha.replace(' - המשך', '')
                    i = -2
                else:
                    i = -1
            elif 'פקודי' in line:
                parasha = 'פקודי'
                maamar = line.split('פקודי')[1].strip()
            elif 'ספרא דצניעותא' in line:
                parasha = 'ספרא דצניעותא'
                maamar = line.split('ספרא דצניעותא')[1].strip()
            else:
                print('unknown section', line)

            if parasha not in parashot[chumash]:
                parashot[chumash][parasha] = [maamar]
                old = 0
                text.append([[]])
            if maamar not in parashot[chumash][parasha]:
                parashot[chumash][parasha].append(maamar)
                text[i].append([])

        elif re.search('^\[אות ', line):
            new = getGematria(re.findall('^\[אות ([א-ת]*)', line)[0])
            if new != old + 1:
                if new > old:
                    print(f'@77 ב{parasha} חסר - אות {new} באה אחרי {old}', line)
                else:
                    print(f'@88 ב{parasha} כפל - אות {new} באה אחרי {old}', line)
                pass
            old = new
            # if len(text[i][-1]) < new -1:
            #     text[i][-1] += ['' for _ in range(new - len(text[i][-1]) - 1)]
            if not re.search('^\[אות [א-ת]{,5}(?:/[א-ד])?\]', line):
                print('problem with ot', line)
            text[i][-1].append(re.sub('^\[אות [א-ת]{,4}\]', '', line).strip())

        elif re.search('^סליק|ברוך|עד כאן', line):
            text[i][-1][-1] += f'<br>{line}'

        else:
            print('@99 להלן שורה או פסקה יתומה:', line)
            pass

        newdata.append(line)

    # with open(f'sulam/{chumash} לתיקון.txt', 'w') as fp:
    #     fp.write('\n'.join(newdata))

def get_en_parasha(parasha):
    for term in library.get_term_dict():
        term = library.get_term(term)
        if term and parasha in term.get_titles():
            return term.get_primary_title()
    return {'ספרא דצניעותא': 'Sifra DiTzniuta',
            'בחקותי': 'Bechukotai',
            'האדרא רבא קדישא': 'Idra Rabba',
            'שלח לך': "Sh'lach",
            'האדרא זוטא קדישא': 'Idra Zuta',
            'הקדמה': 'Introduction'}[parasha]

server = 'http://localhost:9000'
# server = 'https://bdb.cauldron.sefaria.org'
name = 'Zohar TNG'
hname = 'זוהר הדור הבא'
record = JaggedArrayNode()
record.add_primary_titles(name, hname)
record.add_structure(['Parasha', 'Chapter', 'Paragraph'])
record.addressTypes = ['Integer', 'Integer', 'Integer']
record.depth = 3
record.toc_zoom = 1
record.validate()

index_dict = {'title': name,
              'categories': ['Kabbalah', 'Zohar'],
              'default_struct': 'Maamar',
              'schema': record.serialize()}
post_index(index_dict, server=server)

c = 1
text_to_post = []
for p, par in enumerate(text, 1):
    text_to_post.append(par)
    size = sum([sys.getsizeof(z) for x in text_to_post for y in x for z in y])
    if size > 4900000 or p == len(text):
        text_version = {'title': name,
            'versionTitle': f'Sulam{c}',
            'versionSource': "",
            'language': 'he',
            'text': text_to_post
        }
        c += 1
        post_text(name, text_version, server=server)
        text_to_post = [[] for _ in text_to_post]

time.sleep(100)
alts = []
pars = []
p = 0
for chumash in parashot:
    node = ({'nodes': [],
                'titles': [{'primary': True,
                            'lang': "en",
                            'text': Ref(chumash).normal() if chumash != 'הקדמה' else 'Introduction'},
                            {'primary': True,
                            'lang': "he",
                            'text': chumash}]})
    alts.append(copy.deepcopy(node))
    pars.append(copy.deepcopy(node))
    for parasha in parashot[chumash]:
        start = 1
        if parasha == 'האדרא זוטא קדישא':
            start = 23

        p += 1
        if chumash == 'הקדמה':
            pars[0] = {'nodeType': "ArrayMapNode",
                        'depth': 1,
                        'wholeRef': f"{name} {p}",
                        'addressTypes': ['Integer'],
                        'sectionNames': ['Paragraph'],
                        'refs': [x.normal() for x in Ref(f"{name} {p}").all_segment_refs() if x.text('he').text],
                        'titles': pars[0]['titles']}
        else:
            titles = [{'primary': True,
                        'lang': "en",
                        'text': get_en_parasha(parasha)},
                        {'primary': True,
                        'lang': "he",
                        'text': parasha.replace(' קדישא', '')}]
            alts[-1]['nodes'].append({'nodes': [],
                    'titles': titles})
            pars[-1]['nodes'].append({'nodeType': "ArrayMapNode",
                            'depth': 1,
                            'wholeRef': f"{name} {p}",
                            'addressTypes': ['Integer'],
                            'sectionNames': ['Paragraph'],
                            'refs': [x.normal() for x in Ref(f"{name} {p}").all_segment_refs() if x.text('he').text],
                            'titles': titles})
        for m, maamar in enumerate(parashot[chumash][parasha], 1):
            node = ({'nodeType': "ArrayMapNode",
                        'depth': 1,
                        'wholeRef': f"{name} {p}:{m}",
                        'addressTypes': ['Integer'],
                        'sectionNames': ['Paragraph'],
                        'refs': [x.normal() for x in Ref(f"{name} {p}:{m}").all_segment_refs() if x.text('he').text],
                        'titles': [{'primary': True,
                                    'lang': "en",
                                    'text': str(m)},
                                    {'primary': True,
                                    'lang': "he",
                                    'text': maamar}]})
            if start != 1:
                node['startingAddress'] = start
            if chumash != 'הקדמה':
                alts[-1]['nodes'][-1]['nodes'].append(node)
            else:
                alts[-1]['nodes'].append(node)
            start += len(Ref(f"{name} {p}:{m}").all_segment_refs())
            if parasha == 'האזינו' and start == 23:
                start = 202
            elif parasha == 'בראשית' and start == 483:
                start = 1

print(pars)
index_dict['alt_structs'] = {'Maamar': {'nodes': alts}, 'Paragraph': {'nodes': pars}}
post_index(index_dict, server=server)
